"""Builder tools for the v2 printed-only body — NOT installed parts.

Bench aids printed alongside the proofs, in the same PETG the structure
uses.  Like the assembly fixture, these are tool pieces: no PRINTED_PARTS
entries, no D028 budget impact, no Bambu body-project plates.

1. tool_jig_insert_flat   — single-bore guide plate: a 45-degree funnel
                            over a snug guide bore holds one M3 x 5.7
                            heat-set insert square on any flat boss face
                            while the iron presses.
2. tool_jig_insert_pairs  — double-ended pair plate: one row carries the
                            22.0 mm bore pair (motor-saddle cap
                            stations), the other the 23.0 mm pair (pan
                            arm-capture cover bosses); each row is
                            engraved with its spacing.
3. tool_jig_insert_well   — flat jig with a 4 mm guide snout (8.0 OD)
                            that reaches bores recessed below neighboring
                            features (battery-rail posts between the deck
                            lip, tray bosses beside walls) and keeps the
                            insert square at the mouth.  Modeled in its
                            print pose: snout up, funnel opening down
                            (the 45-degree funnel cone self-supports).
4. tool_grease_doser      — single-dose scoop: a spherical-cap bowl
                            (r8 sphere, 3.5 deep, ~0.26 mL) meters one
                            charge for the neck journal + thrust face;
                            the 45-degree underbevel at the nose is the
                            wipe edge.

All are zero-support in the as-modeled pose and under 40 x 40 mm.

Run from the repo root:
    .venv-cad/bin/python cad/python/robot_body_v2_tools.py
Exports (STL + manifest) land under cad/exports/v2/tools/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import robot_body_v2_inventory as inv  # noqa: E402
from build123d import (  # noqa: E402
    Align, Axis, Box, Cone, Cylinder, Pos, Rot, Sphere, Text,
    extrude, fillet, export_stl,
)

F = inv.FASTENER
EXPORT_DIR = Path(__file__).resolve().parents[2] / "cad" / "exports" / "v2" / "tools"

GUIDE_BORE_R = (F["insert_od"] + 0.3) / 2   # 2.45: square slide fit on the insert knurl
FUNNEL_DEPTH = 3.0                          # 45-degree funnel wall
FUNNEL_TOP_R = GUIDE_BORE_R + FUNNEL_DEPTH  # 5.45
PLATE_T = 5.5                               # leaves a 2.5 straight guide land
SNOUT_LEN = 4.0
SNOUT_R = 4.0
PAIR_SPACINGS = (22.0, 23.0)                # motor-saddle caps / pan cover bosses


def pad(l, w, h):
    b = Box(l, w, h)
    return Pos(0, 0, h / 2) * fillet(b.edges().filter_by(Axis.Z), 3.0)


def engrave(label, size=3.0, depth=0.3):
    return extrude(Text(label, font_size=size, align=(Align.CENTER, Align.CENTER)),
                   amount=depth + 0.05)


def funnel_bore(x, y):
    """Countersunk guide: straight bore + 45-degree funnel opening at the top."""
    cut = Pos(x, y, PLATE_T / 2) * Cylinder(GUIDE_BORE_R, PLATE_T + 2)
    cut += Pos(x, y, PLATE_T - FUNNEL_DEPTH) * Cone(
        GUIDE_BORE_R, FUNNEL_TOP_R, FUNNEL_DEPTH,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    cut += Pos(x, y, PLATE_T + 0.45) * Cylinder(FUNNEL_TOP_R, 1.0)
    return cut


def jig_insert_flat():
    return pad(24, 24, PLATE_T) - funnel_bore(0, 0)


def jig_insert_pairs():
    plate = pad(36, 24, PLATE_T)
    for row, spacing in zip((6.0, -6.0), PAIR_SPACINGS):
        for sx in (1, -1):
            plate -= funnel_bore(sx * spacing / 2, row)
        plate -= Pos(0, row, PLATE_T - 0.3) * engrave(f"{spacing:.0f}")
    return plate


def jig_insert_well():
    # Print pose as modeled: snout rising, funnel opening downward — the
    # funnel is then a 45-degree cone ceiling, which self-supports.
    tool = pad(20, 20, PLATE_T)
    tool += Pos(0, 0, PLATE_T + SNOUT_LEN / 2) * Cylinder(SNOUT_R, SNOUT_LEN)
    tool -= Pos(0, 0, (PLATE_T + SNOUT_LEN) / 2) * Cylinder(
        GUIDE_BORE_R, PLATE_T + SNOUT_LEN + 2)
    tool -= Pos(0, 0, 0) * Cone(FUNNEL_TOP_R, GUIDE_BORE_R, FUNNEL_DEPTH,
                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    tool -= Pos(0, 0, -0.45) * Cylinder(FUNNEL_TOP_R, 1.0)
    return tool


def grease_doser():
    # Spherical-cap bowl: r8 sphere cut 3.5 deep into the 5-thick nose pad
    # -> cap volume pi*h^2*(3r-h)/3 = ~263 mm^3, one journal+thrust dose.
    tool = Pos(-14, 0, 1.25) * Box(20, 8, 2.5)          # handle
    tool += Pos(2, 0, 2.5) * Cylinder(8.0, 5.0)          # nose pad
    tool -= Pos(2, 0, 9.5) * Sphere(8.0)                 # bowl (rim opens at Z 5)
    # Wipe edge: a 45-degree underbevel plane through (X 6, Z 0)..(X 11,
    # Z 5) thins the +X nose rim to a ~1 mm blade without touching the
    # bowl wall (min wall ~1.5 at X 7).
    tool -= Pos(18.07, 0, -2.07) * Rot(0, -45, 0) * Box(30, 18, 20)
    return tool


TOOLS = {
    "tool_jig_insert_flat": (
        jig_insert_flat,
        "single-boss flat-face jig: set the insert in the funnel, rest the "
        "plate on the boss face over the bore, press with the iron; lift the "
        "jig once the insert is started square"),
    "tool_jig_insert_pairs": (
        jig_insert_pairs,
        "paired-boss jig: the engraved 22 row spans the motor-saddle cap "
        "stations, the 23 row the pan arm-capture cover bosses; the second "
        "bore registers on the neighboring insert or empty bore"),
    "tool_jig_insert_well": (
        jig_insert_well,
        "deep-well jig: the 8.0 OD x 4 snout drops past neighboring rails "
        "and lips (battery-rail posts, tray bosses) so recessed bores still "
        "get a square start; flip from the print pose to use funnel-up"),
    "tool_grease_doser": (
        grease_doser,
        "single-dose scoop for the PETG-safe pan grease: one level ~0.26 mL "
        "bowl charges the neck journal + thrust face; drag the 45-degree "
        "nose blade across the bore rim to wipe and spread"),
}


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in EXPORT_DIR.glob("tool_*.stl"):
        stale.unlink()
    manifest = {
        "fastener": {"insert": F["insert"], "screw": F["screw"]},
        "role": "builder bench tools; not registry parts, no budget impact",
        "tools": {},
    }
    for name, (fn, note) in TOOLS.items():
        solid = fn()
        bb = solid.bounding_box()
        export_stl(solid, str(EXPORT_DIR / f"{name}.stl"))
        manifest["tools"][name] = {
            "stl": f"{name}.stl",
            "material": "PETG",
            "supports": "none",
            "span_mm": [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)],
            "note": note,
        }
        print(f"{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, "
              f"solids {len(solid.solids())}")
    (EXPORT_DIR / "codex_robot_body_v2_tools_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{len(TOOLS)} tools exported to {EXPORT_DIR}")


if __name__ == "__main__":
    main()
