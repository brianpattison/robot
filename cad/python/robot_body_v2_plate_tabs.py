"""Per-plate QC proof tabs for the v2 body plates.

Every body plate carries one small printed tab in a bed corner — a
self-check that the printer is still dialed before the builder commits
hours to the next plate. Each tab prints in the SAME filament group as
its plate and proves three things at plate scale:

- the recessed plate label ("RB P3") — first-layer and fine-detail check,
- one heat-set insert test bore at the registry `insert_bore` diameter,
- one M3 clearance hole at the registry `clearance_hole` diameter.

Tabs are QC pieces, NOT installed robot parts: they never join the part
registry, the 40-part budget, or the 45-piece inventory. They live
entirely at the print/plate layer (`cad/bambu/generate_bambu_project_v2.py`
stages one per plate and records it under the plate's `qc_tab` key).

The slab is 3.2 mm — the D026 clamp-stack wall — so the clearance hole
doubles as a screw pass check. The insert is 5.7 mm long, so this bore
checks diameter and top-face seating, not full-depth engagement (the
dedicated insert proof covers that).

Run from the repo root:
    .venv-cad/bin/python cad/python/robot_body_v2_plate_tabs.py
Exports land under cad/exports/v2/plate_tabs/ (gitignored).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import robot_body_v2_inventory as inv  # noqa: E402
from build123d import (  # noqa: E402
    Align, Axis, Box, Cylinder, Pos, Text, extrude, fillet, export_stl,
)

F = inv.FASTENER
EXPORT_DIR = Path(__file__).resolve().parents[2] / "cad" / "exports" / "v2" / "plate_tabs"

TAB_L = 20.0
TAB_W = 14.0
TAB_H = 3.2               # one D026 clamp-stack wall
TAB_CORNER_R = 2.0
# The label is RECESSED 0.4 mm rather than raised: sunken strokes cannot
# curl, string, or detach the way two-layer raised text can, and they keep
# the top face flat for caliper checks. 0.4 mm = two 0.2 mm layers, enough
# for the slicer to resolve the strokes crisply.
TEXT_DEPTH = 0.4
TEXT_SIZE = 3.4
TEXT_Y = 3.4              # label band (top half of the tab face)
HOLE_Y = -3.0             # bore band (bottom half); >= 1.7 mm wall to the edge
HOLE_X = 4.5


def build_plate_tab(label: str):
    """One flat QC tab: recessed "RB <label>" plus the two registry bores.

    Zero supports by construction: a flat slab, top-face recessed text,
    and vertical through-holes only.
    """
    tab = Box(TAB_L, TAB_W, TAB_H)
    tab = fillet(tab.edges().filter_by(Axis.Z), TAB_CORNER_R)
    tab = Pos(0, 0, TAB_H / 2) * tab
    mark = extrude(
        Text(f"RB {label}", font_size=TEXT_SIZE, align=(Align.CENTER, Align.CENTER)),
        amount=TEXT_DEPTH,
    )
    mark_bb = mark.bounding_box()
    if mark_bb.size.X > TAB_L - 2.0 * TAB_CORNER_R or mark_bb.size.Y > TAB_W / 2.0:
        raise SystemExit(f"QC tab label 'RB {label}' does not fit the {TAB_L} x {TAB_W} face.")
    tab -= Pos(0, TEXT_Y, TAB_H - TEXT_DEPTH) * mark
    tab -= Pos(-HOLE_X, HOLE_Y, TAB_H / 2) * Cylinder(F["insert_bore"] / 2, TAB_H + 2)
    tab -= Pos(HOLE_X, HOLE_Y, TAB_H / 2) * Cylinder(F["clearance_hole"] / 2, TAB_H + 2)
    return tab


def export_plate_tab(label: str) -> tuple[Path, tuple[float, float, float]]:
    """Build and export one tab STL; return its path and XYZ span."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    solid = build_plate_tab(label)
    bb = solid.bounding_box()
    path = EXPORT_DIR / f"qc_tab_{label.lower()}.stl"
    export_stl(solid, str(path))
    return path, (bb.size.X, bb.size.Y, bb.size.Z)


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in EXPORT_DIR.glob("qc_tab_*.stl"):
        stale.unlink()
    # The tracked body release currently packs 13 plates; the Bambu adapter
    # regenerates whichever labels its layout actually needs, so this
    # standalone run is a smoke test plus a browsable export set.
    labels = [f"P{i}" for i in range(1, 14)]
    for label in labels:
        path, span = export_plate_tab(label)
        print(f"{path.name}: {span[0]:.1f} x {span[1]:.1f} x {span[2]:.1f}  "
              f"[insert_bore {F['insert_bore']}, clearance {F['clearance_hole']}]")
    print(f"{len(labels)} QC tabs exported to {EXPORT_DIR}")


if __name__ == "__main__":
    main()
