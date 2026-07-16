"""Print-ready export chain for the v2 printed-only body.

Rotates every primary solid into its DECLARED print pose (the same
`PRINT_UP` vectors the D028 overhang audit runs against), grounds it on
the bed at Z=0, re-verifies bed fit in-pose, and writes oriented STLs
plus `codex_robot_body_v2_print_manifest.json` — quantity, material, and
orientation notes from the printed-part registry, with supports "none"
across the entire inventory (any exception would need a named entry in
the D028 exception list, which is empty).

Registry parts that do not yet have solids are listed under "pending"
in the manifest rather than silently omitted.

Run from the repo root, after the validator passes:
    .venv-cad/bin/python cad/python/robot_body_v2_print.py
Exports land under cad/exports/v2/print_ready/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import robot_body_v2 as v2  # noqa: E402
import robot_body_v2_inventory as inv  # noqa: E402
from build123d import Axis, Pos, export_stl  # noqa: E402

EXPORT_DIR = Path(__file__).resolve().parents[2] / "cad" / "exports" / "v2" / "print_ready"
BED_XY = 240.0

# Solid name -> printed-part registry name.
REGISTRY_MAP = {
    "tray_v2": "tray", "shell_v2": "shell", "lid_v2": "lid",
    "bumper_front_v2": "bumper_half", "bumper_rear_v2": "bumper_half",
    "front_pod_left_v2": "front_pod", "front_pod_right_v2": "front_pod",
    "fascia_v2": "fascia", "rear_panel_v2": "rear_panel",
    "controller_tower_v2": "controller_tower", "rear_wheel_v2": "wheel_core_rear",
    "front_wheel_v2": "wheel_front", "tire_v2": "tire",
    "head_shell_v2": "head_shell", "head_faceplate_v2": "head_faceplate",
    "neck_v2": "neck", "bayonet_collar_v2": "bayonet_collar",
    "head_pan_plate_v2": "head_pan_plate", "motor_cap_v2": "motor_clamp_cap",
    "battery_clamp_v2": "battery_clamp_bar", "deck_v2": "deck",
}


def to_print_pose(solid, up):
    """Rotate so the declared UP vector becomes +Z, then ground at Z=0."""
    if up == (0, 0, 1):
        posed = solid
    elif up == (0, 0, -1):
        posed = solid.rotate(Axis.X, 180)
    elif up == (0, 1, 0):
        posed = solid.rotate(Axis.X, 90)
    elif up == (0, -1, 0):
        posed = solid.rotate(Axis.X, -90)
    elif up == (1, 0, 0):
        posed = solid.rotate(Axis.Y, -90)
    elif up == (-1, 0, 0):
        posed = solid.rotate(Axis.Y, 90)
    else:
        raise ValueError(f"unsupported UP {up}")
    bb = posed.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * posed


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    registry = {p.name: p for p in inv.PRINTED_PARTS}
    manifest = {"parts": {}, "pending": [], "fasteners": {}}
    covered = set()
    problems = 0
    for name, solid in v2.primary_solids().items():
        up = v2.PRINT_UP.get(name, (0, 0, 1))
        posed = to_print_pose(solid, up)
        bb = posed.bounding_box()
        if bb.size.X > BED_XY or bb.size.Y > BED_XY:
            print(f"BED FAIL: {name} {bb.size.X:.1f} x {bb.size.Y:.1f} in print pose")
            problems += 1
        export_stl(posed, str(EXPORT_DIR / f"{name}_print.stl"))
        reg = registry.get(REGISTRY_MAP.get(name, ""))
        covered.add(REGISTRY_MAP.get(name, ""))
        manifest["parts"][name] = {
            "registry_part": REGISTRY_MAP.get(name),
            "qty": reg.qty if reg else 1,
            "material": reg.material if reg else "PETG",
            "orientation": reg.orientation if reg else "as exported",
            "supports": "none",
            "print_span_mm": [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)],
        }
        print(f"{name}: print pose {bb.size.X:.0f} x {bb.size.Y:.0f} x {bb.size.Z:.0f}")
    for p in inv.PRINTED_PARTS:
        if p.name not in covered:
            manifest["pending"].append({"registry_part": p.name, "qty": p.qty,
                                        "material": p.material, "orientation": p.orientation})
    screws, inserts = inv.fastener_tally()
    manifest["fasteners"] = {"screws": f"{screws} x {inv.FASTENER['screw']}",
                             "inserts": f"{inserts} x {inv.FASTENER['insert']}"}
    (EXPORT_DIR / "codex_robot_body_v2_print_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"manifest: {len(manifest['parts'])} exported designs, "
          f"{len(manifest['pending'])} registry parts pending solids")
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
