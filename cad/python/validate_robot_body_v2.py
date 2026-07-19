"""Inventory-driven validator for the v2 printed-only body (Phase 2).

Contract (plan, revised Phase 2): the registered inventory in
`robot_body_v2_inventory.py` is the authority. An envelope that was never
registered is itself a failure mode — this validator therefore starts
from the registry and the D028 printed-part registry, not from whatever
happens to be modeled.

Checks in this increment (plus, added later: harness route volumes and
connector-insertion sweeps as registered envelopes, solid-free sweep
keepouts, and a screen-grade mass/CG budget with support-polygon limits):
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
from build123d import Axis, Box, Cylinder, Pos  # noqa: E402

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
        if p.material_family not in inv.MATERIAL_FAMILIES:
            FAILS.append(f"D034 material: '{p.name}' has invalid family {p.material_family}")
        if p.mechanical_role not in inv.MECHANICAL_ROLES:
            FAILS.append(f"D034 material: '{p.name}' has invalid role {p.mechanical_role}")
        if p.color_slot not in inv.DEFAULT_THEME:
            FAILS.append(f"D034 material: '{p.name}' has unknown color slot {p.color_slot}")
        if p.qualification not in inv.QUALIFICATION_POLICIES:
            FAILS.append(f"D034 material: '{p.name}' has invalid qualification {p.qualification}")
        if p.qualification_status not in inv.QUALIFICATION_STATUSES:
            FAILS.append(f"D034 material: '{p.name}' has invalid qualification status {p.qualification_status}")
        if p.qualification == "fixed-PETG" and p.material_family != "PETG":
            FAILS.append(f"D034 material: fixed-PETG part '{p.name}' requests {p.material_family}")
        if p.effective_material_family == "PETG" and p.effective_color_slot not in inv.PETG_COLOR_SLOTS:
            FAILS.append(f"D034 material: PETG part '{p.name}' uses non-white/black/red slot {p.effective_color_slot}")
        if p.material_family == "TPU" and not (p.mechanical_role == "flexible" and p.color_slot == "flexible_dark"):
            FAILS.append(f"D034 material: TPU part '{p.name}' changed role/color policy")
        if p.material_family == "PLA" and p.qualification_status == "not-required":
            FAILS.append(f"D034 evidence: PLA part '{p.name}' must expose an open or passed exact-family gate")
        if p.qualification == "physical-gate-required":
            if not p.fallback_material_family or not p.fallback_color_slot:
                FAILS.append(f"D034 material: gated part '{p.name}' lacks automatic fallback")
            if p.qualification_status != "passed" and p.effective_material_family != "PETG":
                FAILS.append(f"D034 material: unqualified '{p.name}' did not fall back to PETG")
    for required in ("shell", "head_shell"):
        p = inv.PART_BY_NAME[required]
        if p.qualification_status == "passed":
            WARNS.append(f"D034 evidence: {required} marked passed; verify the recorded exact-filament evidence")
        elif p.effective_color_slot != "structure_light":
            FAILS.append(f"D034 material: open-gate {required} must fall back to white PETG")
    expected_tpu = {"bumper_half", "tire", "battery_pad_frame"}
    actual_tpu = {p.name for p in inv.PRINTED_PARTS if p.material_family == "TPU"}
    if actual_tpu != expected_tpu:
        FAILS.append(f"D034 material: TPU inventory changed ({sorted(actual_tpu)})")
    skin = inv.PART_BY_NAME.get("lid_skin")
    if not skin or not skin.optional or skin.functional_installed_qty:
        FAILS.append("D034 inventory: lid_skin must remain optional and outside the functional budget")
    if any("lid_skin" in j.name for j in inv.JOINTS):
        FAILS.append("D034 E-stop: optional lid skin must not own a structural joint")
    if inv.SUPPORT_EXCEPTIONS:
        FAILS.append(f"D028 supports: exception list must stay empty ({sorted(inv.SUPPORT_EXCEPTIONS)})")
    draft, after, budget = inv.budget_report()
    if after > budget:
        FAILS.append(f"D028 budget: {after} parts after owed merges > budget {budget}")
    if draft > budget:
        WARNS.append(f"D028 budget: draft {draft} > {budget}; {draft - budget} owed merges pending")
    est = [e.name for e in inv.ENVELOPES if "ESTIMATE" in e.basis]
    for j in inv.JOINTS:
        if not (inv.FASTENER["clamp_min"] <= j.stack <= inv.FASTENER["clamp_max"]):
            FAILS.append(f"D026 clamp stack: joint '{j.name}' stack {j.stack} outside "
                         f"{inv.FASTENER['clamp_min']}..{inv.FASTENER['clamp_max']}")
    engage = inv.FASTENER["screw_len"] - inv.FASTENER["clamp_max"]
    if engage > inv.FASTENER["insert_len"]:
        FAILS.append("D026: screw engagement exceeds insert length")
    return est


def check_box_screen():
    screen = Path(__file__).parent / "packing_study_printed_only.py"
    r = subprocess.run([sys.executable, str(screen)], capture_output=True, text=True)
    if r.returncode != 0:
        FAILS.append("box screen: packing_study_printed_only.py failed:\n" + r.stdout[-800:])


def check_bed_fit(solids):
    for name, solid in solids.items():
        pieces = len(solid.solids())
        if pieces != 1:
            FAILS.append(f"connectivity: {name} is {pieces} disconnected solids")
        bb = solid.bounding_box()
        if bb.size.X > BED_XY or bb.size.Y > BED_XY:
            FAILS.append(f"bed fit: {name} plan {bb.size.X:.1f} x {bb.size.Y:.1f} exceeds {BED_XY}")
        if bb.size.Z > BED_Z:
            FAILS.append(f"bed fit: {name} height {bb.size.Z:.1f} exceeds {BED_Z}")


# Keepouts that must contain NO printed material (air contracts the solids
# themselves must honor — unlike arch/roof keepouts, which are bounded by
# the very structure being built).
SOLID_FREE_KEEPOUTS = {"mdds10_thermal", "sweep_en2", "sweep_mute", "estop_press"}


# A solid may OWN envelope groups that describe the very part it builds
# (the deck solid fills the registered deck-plate envelopes).
SOLID_OWNS = {"deck_v2": {"deck"}}


def check_interference(solids):
    envs = [b for b in inv.boxes()
            if b[1] in ("item", "service") or b[0].rstrip("~m") in SOLID_FREE_KEEPOUTS]
    for sname, solid in solids.items():
        owned = SOLID_OWNS.get(sname, set())
        for e in envs:
            name, _, group, x0, x1, y0, y1, z0, z1 = e
            if group.rstrip("~m") in owned:
                continue
            box = Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)
            hit = solid & box
            vol = 0.0 if hit is None else hit.volume
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


def check_mass_cg(solids):
    total, mx, my, mz = 0.0, 0.0, 0.0, 0.0
    for name, solid in solids.items():
        family = inv.part_for_solid(name).effective_material_family
        rho = inv.EFFECTIVE_DENSITY[family]
        n = inv.SOLID_INSTANCES.get(name, 1)
        m = solid.volume * rho * n
        c = solid.center()
        total += m
        mx += m * c.X
        my += m * c.Y * (0 if n > 1 else 1)  # mirrored instances cancel in Y
        mz += m * c.Z
    for _, m, (x, y, z) in inv.PURCHASED_MASSES + inv.PRINTED_MASS_EXTRAS:
        total += m
        mx += m * x
        my += m * y
        mz += m * z
    cgx, cgy, cgz = mx / total, my / total, mz / total
    ok_x = inv.CG_X_LIMITS[0] <= cgx <= inv.CG_X_LIMITS[1]
    ok_y = abs(cgy) <= inv.CG_Y_LIMIT
    if not ok_x:
        FAILS.append(f"CG: X={cgx:.0f} outside {inv.CG_X_LIMITS} (support polygon margin)")
    if not ok_y:
        FAILS.append(f"CG: |Y|={abs(cgy):.0f} exceeds {inv.CG_Y_LIMIT}")
    return total, cgx, cgy, cgz


def _intersection_volume(a, b):
    hit = a & b
    return 0.0 if hit is None else hit.volume


def check_head_mechanism(solids):
    """Exercise the production pan/tilt geometry, not a second box model.

    The commanded ranges must remain free; contact must appear beyond them at
    both physical hard stops.  Servo *case* envelopes must clear their capture
    frames (the flanges and horns intentionally touch their mounting faces).
    """
    if abs(v2.TILT_LIMIT_DEG - inv.P.head_tilt_limit_degrees) > 1e-6:
        FAILS.append("head: v2 tilt command does not track the drawing-backed Params limit")
    if not (0.25 <= v2.PAN_JOURNAL_CLEARANCE <= 0.45):
        FAILS.append("head: printed pan journal radial clearance left the proof-gated 0.25..0.45 mm band")

    collar, neck = solids["bayonet_collar_v2"], solids["neck_v2"]
    pan_axis = Axis((v2.P.neck_x, 0.0, 0.0), (0.0, 0.0, 1.0))
    for angle in range(-int(v2.PAN_LIMIT_DEG), int(v2.PAN_LIMIT_DEG) + 1, 10):
        vol = _intersection_volume(neck.rotate(pan_axis, float(angle)), collar)
        if vol > 1.0:
            FAILS.append(f"head pan: {vol:.1f} mm^3 collision at commanded {angle} deg")
            break
    for angle in (-70.0, 70.0):
        if _intersection_volume(neck.rotate(pan_axis, angle), collar) < 5.0:
            FAILS.append(f"head pan: {angle:+.0f} deg physical stop does not engage")

    head, yoke = solids["head_shell_v2"], solids["yoke_v2"]
    tilt_axis = Axis((v2.TILT_AXIS_X, 0.0, v2.TILT_AXIS_Z), (0.0, 1.0, 0.0))
    # Sample more densely than the guide's stated endpoints.  A few cubic
    # millimetres of OCC tangent noise are accepted; structural collisions are
    # hundreds to thousands of cubic millimetres (the original placeholder
    # mechanism measured >4,600 mm^3 at +20 degrees).
    for angle in range(-int(v2.TILT_LIMIT_DEG), int(v2.TILT_LIMIT_DEG) + 1, 2):
        vol = _intersection_volume(head.rotate(tilt_axis, float(angle)), yoke)
        if vol > 8.0:
            FAILS.append(f"head tilt: {vol:.1f} mm^3 collision at commanded {angle} deg")
            break
    for angle in (-25.0, 25.0):
        if _intersection_volume(head.rotate(tilt_axis, angle), yoke) < 10.0:
            FAILS.append(f"head tilt: {angle:+.0f} deg physical stop does not engage")

    for label, fit, printed in (
        ("pan servo/collar", v2.pan_servo_body_fit(), collar),
        ("pan servo/plate", v2.pan_servo_body_fit(), solids["head_pan_plate_v2"]),
        ("tilt servo/yoke", v2.tilt_servo_body_fit(), yoke),
    ):
        vol = _intersection_volume(fit, printed)
        if vol > 1.0:
            FAILS.append(f"head: {label} case clearance collision {vol:.1f} mm^3")

    # The full 20 mm camera/servo cable corridor must remain open through the
    # rotating neck.  The drive horn deliberately occupies only the -X side.
    corridor = Pos(v2.P.neck_x, 0.0, (v2.NECK_Z0 + v2.NECK_Z1) / 2) * Cylinder(
        9.5, v2.NECK_Z1 - v2.NECK_Z0)
    vol = _intersection_volume(neck, corridor)
    if vol > 1.0:
        FAILS.append(f"head: neck cable corridor blocked by {vol:.1f} mm^3")


def main():
    gate = "--gate" in sys.argv
    estimates = check_registry()
    check_box_screen()
    solids = v2.primary_solids()
    check_bed_fit(solids)
    check_interference(solids)
    check_overhangs(solids)
    check_head_mechanism(solids)
    total, cgx, cgy, cgz = check_mass_cg(solids)

    if estimates:
        msg = f"{len(estimates)} ESTIMATE-basis envelopes remain: {', '.join(estimates)}"
        (FAILS if gate else WARNS).append(("gate: " if gate else "gate-open: ") + msg)
    unmodeled = [j.name for j in inv.JOINTS if not j.modeled]
    if unmodeled:
        msg = f"{len(unmodeled)} joint families not yet modeled: {', '.join(unmodeled)}"
        (FAILS if gate else WARNS).append(("gate: " if gate else "gate-open: ") + msg)

    draft, after, budget = inv.budget_report()
    screws, inserts = inv.fastener_tally()
    print(f"v2 validator — body {inv.BODY_L} x {inv.BODY_W} x {inv.BODY_H}; "
          f"parts draft {draft} / after merges {after} / budget {budget}; "
          f"fasteners {screws} screws + {inserts} inserts (single SKUs)")
    print(f"mass budget ~{total / 1000:.2f} kg (screen-grade); CG X={cgx:.0f} Y={cgy:.0f} Z={cgz:.0f}"
          f" vs axles {inv.FRONT_AXLE_X:.0f}/{inv.REAR_AXLE_X:.0f}")
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
