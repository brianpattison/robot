"""Inventory-driven validator for the v2 printed-only body (Phase 2).

Contract (plan, revised Phase 2): the registered inventory in
`robot_body_v2_inventory.py` is the authority. An envelope that was never
registered is itself a failure mode — this validator therefore starts
from the registry and the D028 printed-part registry, not from whatever
happens to be modeled.

Checks in this increment:
1. Registry hygiene: unique envelope names; every printed part declares
   an orientation and a justification; the after-merges part count meets
   the D028 budget.
2. Box-level layout: the packing screen must pass (run as a subprocess;
   its exit code gates this validator).
3. Bed fit: every primary solid fits 240 x 240 x 250 in its print pose.
4. BREP interference: primary solids vs every item/service envelope —
   intersection volume above 1 mm^3 fails (planar contact is 0 and
   passes). Keepout envelopes are air contracts checked at box level and
   are excluded here, since several are bounded by the very structure
   being built (arches, roof hardware).
5. D028 overhang audit: per primary solid, in its declared print pose
   (an axis-aligned UP vector, so flipped and side-printed parts audit
   correctly), downward-facing surfaces beyond 50 degrees fail unless
   they are bed contact, inside an allowlisted region (the rollover
   band or the arched wheel openings), or a horizontal ceiling whose
   narrow span qualifies as a bridge (<= 30 mm in the print plane).

Gate mode (--gate) additionally fails on every ESTIMATE-basis envelope:
the D027 gate cannot close while any envelope is still an estimate.

Run from the repo root:
    .venv-cad/bin/python cad/python/validate_robot_body_v2.py [--gate]
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import robot_body_v2 as v2  # noqa: E402
import robot_body_v2_inventory as inv  # noqa: E402
from build123d import Box, Pos  # noqa: E402

BED_XY, BED_Z = 240.0, 250.0
OVERHANG_LIMIT_DEG = 50.0
BRIDGE_LIMIT = 30.0
MIN_FACE_AREA = 10.0  # mm^2; ignore slivers
FAILS: list[str] = []
WARNS: list[str] = []


def check_registry():
    names = [e.name for e in inv.ENVELOPES]
    if len(names) != len(set(names)):
        FAILS.append("registry: duplicate envelope names")
    for p in inv.PRINTED_PARTS:
        if not p.orientation or not p.justification:
            FAILS.append(f"registry: printed part '{p.name}' missing orientation/justification")
    draft, after, budget = inv.budget_report()
    if after > budget:
        FAILS.append(f"D028 budget: {after} parts after owed merges > budget {budget}")
    if draft > budget:
        WARNS.append(f"D028 budget: draft {draft} > {budget}; {draft - budget} owed merges pending")
    est = [e.name for e in inv.ENVELOPES if "ESTIMATE" in e.basis]
    return est


def check_box_screen():
    screen = Path(__file__).parent / "packing_study_printed_only.py"
    r = subprocess.run([sys.executable, str(screen)], capture_output=True, text=True)
    if r.returncode != 0:
        FAILS.append("box screen: packing_study_printed_only.py failed:\n" + r.stdout[-800:])


def check_bed_fit(solids):
    for name, solid in solids.items():
        bb = solid.bounding_box()
        if bb.size.X > BED_XY or bb.size.Y > BED_XY:
            FAILS.append(f"bed fit: {name} plan {bb.size.X:.1f} x {bb.size.Y:.1f} exceeds {BED_XY}")
        if bb.size.Z > BED_Z:
            FAILS.append(f"bed fit: {name} height {bb.size.Z:.1f} exceeds {BED_Z}")


# Keepouts that must contain NO printed material (air contracts the solids
# themselves must honor — unlike arch/roof keepouts, which are bounded by
# the very structure being built).
SOLID_FREE_KEEPOUTS = {"mdds10_thermal"}


def check_interference(solids):
    envs = [b for b in inv.boxes()
            if b[1] in ("item", "service") or b[0].rstrip("~m") in SOLID_FREE_KEEPOUTS]
    for sname, solid in solids.items():
        for e in envs:
            name, _, _, x0, x1, y0, y1, z0, z1 = e
            box = Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)
            vol = (solid & box).volume
            if vol > 1.0:
                FAILS.append(f"interference: {sname} intrudes {vol:.0f} mm^3 into envelope '{name}'")


def check_overhangs(solids):
    for sname, solid in solids.items():
        up = v2.PRINT_UP.get(sname, (0, 0, 1))
        regions = v2.OVERHANG_ALLOW_REGIONS.get(sname, [])
        bb = solid.bounding_box()
        corners = [(x, y, z) for x in (bb.min.X, bb.max.X)
                   for y in (bb.min.Y, bb.max.Y) for z in (bb.min.Z, bb.max.Z)]
        bed_h = min(cx * up[0] + cy * up[1] + cz * up[2] for cx, cy, cz in corners)
        # Face spans for the bridge rule are measured in the print plane
        # (the bbox axes orthogonal to the axis-aligned UP vector).
        span_axes = [i for i, u in enumerate(up) if u == 0]
        bad_area = 0.0
        worst = 0.0
        for f in solid.faces():
            try:
                area = f.area
                if area < MIN_FACE_AREA:
                    continue
                c = f.center()
                n = f.normal_at(c)
            except Exception:
                continue
            nz = n.X * up[0] + n.Y * up[1] + n.Z * up[2]
            ch = c.X * up[0] + c.Y * up[1] + c.Z * up[2]
            if nz >= -math.sin(math.radians(OVERHANG_LIMIT_DEG)):
                continue  # not a >50-degree downward face in the print pose
            # Bed contact is fine.
            if abs(ch - bed_h) < 0.5:
                continue
            # Allowlisted regions (rollover band, arched openings).
            if any(r[0] <= c.X <= r[1] and r[2] <= c.Y <= r[3] and r[4] <= c.Z <= r[5]
                   for r in regions):
                continue
            # Horizontal ceilings may qualify as bridges by narrow span.
            # Effective width = min(bbox span, 2*area/perimeter): rings and
            # frames read as their strip width, not their overall extent.
            if nz < -0.985:
                fb = f.bounding_box()
                sizes = (fb.size.X, fb.size.Y, fb.size.Z)
                span = min(sizes[span_axes[0]], sizes[span_axes[1]])
                try:
                    perim = sum(w.length for w in f.wires())
                    span = min(span, 2.0 * area / perim)
                except Exception:
                    pass
                if span <= BRIDGE_LIMIT:
                    continue
            bad_area += area
            worst = max(worst, math.degrees(math.asin(min(1.0, -nz))))
        if bad_area > 0:
            FAILS.append(f"overhang: {sname} has {bad_area:.0f} mm^2 beyond "
                         f"{OVERHANG_LIMIT_DEG:.0f} deg (worst {worst:.0f} deg) outside allowances")


def main():
    gate = "--gate" in sys.argv
    estimates = check_registry()
    check_box_screen()
    solids = v2.primary_solids()
    check_bed_fit(solids)
    check_interference(solids)
    check_overhangs(solids)

    if estimates:
        msg = f"{len(estimates)} ESTIMATE-basis envelopes remain: {', '.join(estimates)}"
        (FAILS if gate else WARNS).append(("gate: " if gate else "gate-open: ") + msg)

    draft, after, budget = inv.budget_report()
    print(f"v2 validator — body {inv.BODY_L} x {inv.BODY_W} x {inv.BODY_H}; "
          f"parts draft {draft} / after merges {after} / budget {budget}")
    for w in WARNS:
        print("  WARN:", w)
    for f_ in FAILS:
        print("  FAIL:", f_)
    if FAILS:
        print(f"RESULT: FAIL ({len(FAILS)} failures, {len(WARNS)} warnings)")
        sys.exit(1)
    print(f"RESULT: PASS with {len(WARNS)} warnings"
          + ("" if gate else " (dev mode; --gate enforces the estimate rule)"))


if __name__ == "__main__":
    main()
