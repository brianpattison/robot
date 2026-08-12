"""Build the tracked v2 Bambu Studio P1S project from the v2 print chain.

Adapts the v2 print manifest (one entry per part DESIGN with quantities)
into the v1 generator's per-instance schema, stages instance STL copies,
and drives the proven v1 machinery end to end: pack by filament group,
CLI import, patch, Bambu round-trip, plate manifest, contact sheet, and
validation.

Run the v2 chain first (model -> validator -> print), then:
    .venv-cad/bin/python cad/bambu/generate_bambu_project_v2.py

Outputs (tracked, the deliberate exception to the exports ignore rule):
    cad/bambu/codex_robot_body_v2_p1s.3mf
    cad/bambu/codex_robot_body_v2_p1s_plates.json
    docs/images/codex_robot_body_v2_p1s_plates.png
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad" / "bambu"))
sys.path.insert(0, str(ROOT / "cad" / "python"))

import generate_bambu_project as gb  # noqa: E402
import robot_body_v2_inventory as inv  # noqa: E402
import robot_body_v2_plate_tabs as tabs  # noqa: E402

V2_PRINT_DIR = ROOT / "cad" / "exports" / "v2" / "print_ready"
V2_MANIFEST = V2_PRINT_DIR / "codex_robot_body_v2_print_manifest.json"
STAGING = ROOT / "cad" / "exports" / "v2" / "bambu_staging"
OUTPUT = ROOT / "cad" / "bambu" / "codex_robot_body_v2_p1s.3mf"
PLATES_JSON = ROOT / "cad" / "bambu" / "codex_robot_body_v2_p1s_plates.json"
CONTACT_SHEET = ROOT / "docs" / "images" / "codex_robot_body_v2_p1s_plates.png"

COLOR_PROFILES = {
    slot: {"name": data["name"], "hex": data["hex"], "role": data["role"]}
    for slot, data in inv.DEFAULT_THEME.items()
}
MATERIAL_PROFILES = {
    "pla_visible": {"material": "PLA", "role": "direct visible cosmetic parts; physical fit/temperature gates open"},
    "pla_qualified_enclosure": {"material": "PLA", "role": "shell/head only after exact-filament physical qualification"},
    "pla_optical": {"material": "Translucent PLA", "role": "light diffusers; optical/thermal gates open"},
    "petg_structure": {"material": "PETG", "role": "white general and enclosure-fallback structure"},
    "petg_wear": {"material": "PETG", "role": "black motion and wear structure"},
    "petg_service": {"material": "PETG", "role": "red battery, safety-board, and motor retainers"},
    "tpu_95a": {"material": "TPU 95A", "role": "tires, bumper halves, battery pads"},
}
gb.MATERIAL_ORDER.update({
    "petg_structure": 0,
    "petg_wear": 1,
    "petg_service": 2,
    "pla_qualified_enclosure": 3,
    "pla_visible": 4,
    "pla_optical": 5,
    "tpu_95a": 6,
})
gb.COLOR_ORDER.update({slot: i for i, slot in enumerate((
    "structure_light", "structure_wear", "safety_service", "body_primary",
    "dark_panel", "light_diffuser", "top_accent", "flexible_dark",
))})
# Designs whose left/right twin is a separate solid: each prints once, not
# at the registry quantity (which already counts both sides).
PER_SIDE_DESIGNS = {"front_pod_left_v2", "front_pod_right_v2", "bumper_front_v2", "bumper_rear_v2"}


def filament_group(entry: dict) -> str:
    """Derive one material/color group from canonical inventory fields."""
    family = entry["effective_material_family"]
    role = entry["mechanical_role"]
    slot = entry["effective_color_slot"]
    if family == "PLA":
        profile = ("pla_optical" if role == "optical" else
                   "pla_qualified_enclosure" if role == "qualified_enclosure" else
                   "pla_visible")
    elif family == "PETG":
        profile = ("petg_service" if slot == "safety_service" else
                   "petg_wear" if slot == "structure_wear" else
                   "petg_structure")
    elif family == "TPU":
        profile = "tpu_95a"
    else:
        raise SystemExit(f"unsupported effective material family {family}")
    return f"{profile}:{slot}"


def build_instance_manifest() -> dict:
    v2 = json.loads(V2_MANIFEST.read_text(encoding="utf-8"))
    if v2.get("pending"):
        raise SystemExit("v2 print manifest still lists pending parts; model them first.")
    STAGING.mkdir(parents=True, exist_ok=True)
    for old in STAGING.glob("*.stl"):
        old.unlink()
    parts = {}
    for design, entry in sorted(v2["parts"].items()):
        group = filament_group(entry)
        qty = 1 if design in PER_SIDE_DESIGNS else int(entry["qty"])
        span_x, span_y, _ = entry["print_span_mm"]
        brim = 4.0 if max(span_x, span_y) >= 150.0 else 0.0
        src = V2_PRINT_DIR / f"{design}_print.stl"
        for i in range(1, qty + 1):
            name = design if qty == 1 else f"{design}_i{i}"
            stl = f"{name}.stl"
            shutil.copyfile(src, STAGING / stl)
            parts[name] = {
                "stl": stl,
                "span_mm": {"x": span_x, "y": span_y},
                "support_guidance": {"supports": "none", "brim_mm": brim},
                "filament_group": group,
                "registry_part": entry["registry_part"],
                "mechanical_role": entry["mechanical_role"],
                "requested_material_family": entry["requested_material_family"],
                "effective_material_family": entry["effective_material_family"],
                "qualification": entry["qualification"],
                "qualification_status": entry["qualification_status"],
                "optional": entry["optional"],
                "release_status": "prototype: material proofs + purchased-part fit gates apply",
            }
    return {
        "printer_target": {
            "model": "Bambu Lab P1S",
            "nozzle_diameter_mm": 0.4,
            "bed_size_mm": gb.BED_SIZE,
            "edge_margin_mm": gb.BED_EDGE_MARGIN,
            "plate_type": gb.PLATE_TYPE,
        },
        "release_warning": (
            "Prototype v2 plates. Generate, print, and record the material-specific proofs "
            "before any large part. The D027 CAD packing gate is closed; all "
            "named physical, electrical, firmware, and commissioning gates remain "
            "open. Nothing here authorizes powered motion."
        ),
        "color_profiles": COLOR_PROFILES,
        "material_profiles": MATERIAL_PROFILES,
        "inventory_counts": v2["inventory_counts"],
        "fasteners": {
            "screws": f"{inv.fastener_tally()[0]} x {inv.FASTENER['screw']}",
            "inserts": f"{inv.fastener_tally()[1]} x {inv.FASTENER['insert']}",
        },
        "parts": parts,
    }


SOLO_SPAN = 232.0  # parts larger than this get a dedicated centered plate


def pack_group_with_solo(group, names, parts):
    """Plate-filling parts (tray, shell, bumper halves) take a dedicated
    plate centered on the bed with no brim/spacing pad — a solo part needs
    no inter-object spacing, and 238 <= the 240 mm safe area. Everything
    else uses the original v1 packer."""
    import dataclasses
    solo = [n for n in names
            if max(parts[n]["span_mm"]["x"], parts[n]["span_mm"]["y"]) > SOLO_SPAN]
    rest = [n for n in names if n not in solo]
    plates = []
    for n in sorted(solo):
        sx, sy = parts[n]["span_mm"]["x"], parts[n]["span_mm"]["y"]
        if max(sx, sy) > gb.BED_SIZE - 2.0 * gb.BED_EDGE_MARGIN:
            raise SystemExit(f"{n} exceeds the P1S safe area even solo.")
        plates.append([gb.Placement(name=n, group=group, plate_in_group=0,
                                    x=gb.BED_SIZE / 2.0, y=gb.BED_SIZE / 2.0,
                                    rotated_90=False, span_x=sx, span_y=sy, brim_mm=0.0)])
    if rest:
        plates.extend(_original_pack_group(group, rest, parts))
    return [[dataclasses.replace(pl, plate_in_group=i + 1) for pl in plate]
            for i, plate in enumerate(plates)]


_original_pack_group = gb.pack_group
gb.pack_group = pack_group_with_solo


# ---------------------------------------------------------------------------
# Per-plate QC proof tabs. Second pass over the finished layout: every body
# plate gets one small printed tab (recessed plate label + the two registry
# bores) in a bed corner, in the plate's own filament group. Tabs are QC
# pieces, not robot parts — they never touch the part registry, the 40-part
# budget, or the 45-piece inventory, and the plates JSON records them under
# a separate `qc_tab` key so the guide's plate table and inventory grid
# never see them.
# ---------------------------------------------------------------------------
QC_TAB_ROLE = "qc_tab"
QC_TAB_RELEASE_STATUS = (
    "QC proof tab: printer self-check only; never installed on the robot; "
    "outside the 40-part budget and the 45-piece inventory"
)


def _spacing_envelope(x, y, span_x, span_y, brim_mm):
    """The exact envelope validate_output enforces between neighbors."""
    pad = brim_mm + gb.OBJECT_SPACING / 2.0
    return gb.Rect(x - span_x / 2.0 - pad, y - span_y / 2.0 - pad,
                   span_x + 2.0 * pad, span_y + 2.0 * pad)


def _tab_fits(cx, cy, span, placements):
    lo, hi = gb.BED_EDGE_MARGIN, gb.BED_SIZE - gb.BED_EDGE_MARGIN
    sx, sy = span
    if not (lo - 1e-6 <= cx - sx / 2.0 and cx + sx / 2.0 <= hi + 1e-6
            and lo - 1e-6 <= cy - sy / 2.0 and cy + sy / 2.0 <= hi + 1e-6):
        return False
    tab_rect = _spacing_envelope(cx, cy, sx, sy, 0.0)
    return all(
        not gb.intersects(tab_rect, _spacing_envelope(p.x, p.y, p.span_x, p.span_y, p.brim_mm))
        for p in placements
    )


def _tab_positions(span):
    """Bed-corner candidates first, then a sweep along the bed edges.

    The packer fills the safe area from its lower-left origin, so the
    top-right corner is tried first.
    """
    lo, hi = gb.BED_EDGE_MARGIN, gb.BED_SIZE - gb.BED_EDGE_MARGIN
    sx, sy = span
    xs = (hi - sx / 2.0, lo + sx / 2.0)
    ys = (hi - sy / 2.0, lo + sy / 2.0)
    corners = [(x, y) for y in ys for x in xs]
    yield from corners
    step = 2.0
    x = hi - sx / 2.0 - step
    while x >= lo + sx / 2.0:
        for y in ys:
            yield (x, y)
        x -= step
    y = hi - sy / 2.0 - step
    while y >= lo + sy / 2.0:
        for x in xs:
            yield (x, y)
        y -= step


def _shift_solo_for_tab(plate, span):
    """A solo plate-filling part (tray, shell) is centered and can leave no
    corner room. Slide it against one margin edge along whichever axis has
    slack, opening a strip for the tab on the opposite side. Mutates the
    plate's single placement; returns True when a strip >= tab + spacing
    opened."""
    (p,) = plate["placements"]
    lo = gb.BED_EDGE_MARGIN
    usable = gb.BED_SIZE - 2.0 * gb.BED_EDGE_MARGIN
    slack_x = usable - p.span_x - 2.0 * p.brim_mm
    slack_y = usable - p.span_y - 2.0 * p.brim_mm
    for slack, axis, part_span, tab_need in (
        (slack_y, "y", p.span_y, span[1] + gb.OBJECT_SPACING),
        (slack_x, "x", p.span_x, span[0] + gb.OBJECT_SPACING),
    ):
        if slack >= tab_need:
            low_center = lo + p.brim_mm + part_span / 2.0
            plate["placements"][0] = dataclasses.replace(p, **{axis: low_center})
            return True
    return False


def add_qc_tabs(manifest: dict, layout: list[dict]) -> None:
    """Generate, stage, and place exactly one QC tab per body plate."""
    parts = manifest["parts"]
    for plate in layout:
        number = plate["plate_number"]
        label = f"P{number}"
        name = f"qc_tab_p{number}"
        stl_source, (span_x, span_y, _) = tabs.export_plate_tab(label)
        shutil.copyfile(stl_source, STAGING / f"{name}.stl")
        span = (span_x, span_y)
        position = next((c for c in _tab_positions(span)
                         if _tab_fits(*c, span, plate["placements"])), None)
        if position is None and len(plate["placements"]) == 1:
            if _shift_solo_for_tab(plate, span):
                position = next((c for c in _tab_positions(span)
                                 if _tab_fits(*c, span, plate["placements"])), None)
        if position is None:
            raise SystemExit(
                f"Plate {number} leaves no corner room for its QC tab; "
                "refusing to ship the plate without its printer self-check."
            )
        plate["placements"].append(gb.Placement(
            name=name, group=plate["filament_group"],
            plate_in_group=plate["placements"][0].plate_in_group,
            x=position[0], y=position[1], rotated_90=False,
            span_x=span_x, span_y=span_y, brim_mm=0.0,
        ))
        material = manifest["material_profiles"][plate["material_profile"]]["material"]
        parts[name] = {
            "stl": f"{name}.stl",
            "span_mm": {"x": span_x, "y": span_y},
            "support_guidance": {"supports": "none", "brim_mm": 0.0},
            "filament_group": plate["filament_group"],
            "registry_part": None,  # QC piece: no registry entry, by design
            "mechanical_role": QC_TAB_ROLE,
            "requested_material_family": material,
            "effective_material_family": material,
            "qualification": None,
            "qualification_status": "not_required: per-plate QC piece",
            "optional": False,
            "release_status": QC_TAB_RELEASE_STATUS,
        }


def write_plate_manifest_with_qc_tabs(output, manifest, layout) -> None:
    """Run the engine writer, then move each plate's tab out of `parts`
    into a separate additive `qc_tab` object so downstream consumers of
    `parts`/`part_count`/`inventory_counts` (guide plate table, inventory
    grid, release checker) never drift."""
    _original_write_plate_manifest(output, manifest, layout)
    path = gb.plate_manifest_path(output)
    payload = json.loads(path.read_text(encoding="utf-8"))
    for plate in payload["plates"]:
        kept = [p for p in plate["parts"] if p.get("mechanical_role") != QC_TAB_ROLE]
        tab_entries = [p for p in plate["parts"] if p.get("mechanical_role") == QC_TAB_ROLE]
        if len(tab_entries) != 1:
            raise SystemExit(
                f"Plate {plate['plate_number']} carries {len(tab_entries)} QC tabs; expected exactly 1."
            )
        plate["parts"] = kept
        plate["part_count"] = len(kept)
        tab = tab_entries[0]
        plate["qc_tab"] = {
            "name": tab["name"],
            "center_mm": tab["center_mm"],
            "span_xy_mm": tab["span_xy_mm"],
            "release_status": QC_TAB_RELEASE_STATUS,
        }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def validate_output_with_qc_tabs(output, manifest, layout) -> None:
    """Engine validation first — the tabs ride in `layout`, so the margin,
    spacing, and exactly-once-inventory checks already cover them — then
    prove from the re-opened 3MF that every plate carries exactly its own
    QC tab."""
    _original_validate_output(output, manifest, layout)
    with zipfile.ZipFile(output) as archive:
        settings_root = ET.fromstring(archive.read("Metadata/model_settings.config"))
    id_to_name = {
        obj.attrib["id"]: Path(obj.find("metadata[@key='name']").attrib["value"]).stem
        for obj in settings_root.findall("object")
    }
    plates = settings_root.findall("plate")
    if len(plates) != len(layout):
        raise SystemExit("QC tab check: 3MF plate count does not match the layout.")
    for plate_element, plate in zip(plates, layout):
        names = [
            id_to_name[instance.find("metadata[@key='object_id']").attrib["value"]]
            for instance in plate_element.findall("model_instance")
        ]
        tabs_here = [n for n in names
                     if manifest["parts"][n]["mechanical_role"] == QC_TAB_ROLE]
        expected = f"qc_tab_p{plate['plate_number']}"
        if tabs_here != [expected]:
            raise SystemExit(
                f"Plate {plate['plate_number']} carries QC tabs {tabs_here}; expected [{expected!r}]."
            )
    print(
        "BAMBU_V2_QC_TABS_VALID "
        f"qc_tabs={len(plates)} one_per_plate=yes "
        "margins_and_spacing=engine-checked filament=matches-plate"
    )


_original_write_plate_manifest = gb.write_plate_manifest
gb.write_plate_manifest = write_plate_manifest_with_qc_tabs
_original_validate_output = gb.validate_output
gb.validate_output = validate_output_with_qc_tabs


def main() -> None:
    manifest_data = build_instance_manifest()
    staged_manifest = STAGING / "codex_robot_body_v2_instance_manifest.json"
    staged_manifest.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

    gb.PRINT_DIR = STAGING
    gb.MANIFEST_PATH = staged_manifest
    gb.OUTPUT_PATH = OUTPUT
    gb.PLATE_MANIFEST_PATH = PLATES_JSON
    gb.PLATE_CONTACT_SHEET_PATH = CONTACT_SHEET

    gb.configure_bambu_paths(gb.DEFAULT_BAMBU_CLI, gb.DEFAULT_PROFILE_ROOT)
    gb.validate_environment()
    manifest = gb.load_manifest()
    # Pass 1: the tab-free layout decides the plate count and each plate's
    # filament group. Pass 2 then adds one QC tab per finished plate — the
    # tabs must never influence how the real parts pack.
    layout = gb.build_layout(manifest)
    add_qc_tabs(manifest, layout)
    staged_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temp_path = Path(tempfile.mkdtemp(prefix="codex-bambu-v2-"))
    try:
        imported = gb.run_bambu_import(manifest, layout, temp_path)
        patched = temp_path / "codex_robot_body_v2_p1s_patched.3mf"
        gb.patch_project(imported, patched, manifest, layout)
        gb.roundtrip_with_bambu(patched, OUTPUT, temp_path)
        gb.write_plate_manifest(OUTPUT, manifest, layout)
        plate_manifest = json.loads(PLATES_JSON.read_text(encoding="utf-8"))
        plate_manifest["generated_by"] = "cad/bambu/generate_bambu_project_v2.py"
        PLATES_JSON.write_text(json.dumps(plate_manifest, indent=2) + "\n", encoding="utf-8")
        gb.validate_output(OUTPUT, manifest, layout)
        # The contact sheet reads its thumbnails from the 3MF (QC tabs stay
        # visible on every plate image); the layout only feeds the caption's
        # part count, which must keep quoting the 45 robot pieces.
        sheet_layout = [
            {**plate, "placements": [
                p for p in plate["placements"]
                if manifest["parts"][p.name]["mechanical_role"] != QC_TAB_ROLE
            ]}
            for plate in layout
        ]
        gb.render_plate_contact_sheet(OUTPUT, sheet_layout, contact_sheet_path=CONTACT_SHEET,
                                  title="Codex Robot Body v2 - P1S Plate Layout")
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)
    robot_parts = sum(
        1 for part in manifest["parts"].values()
        if part["mechanical_role"] != QC_TAB_ROLE
    )
    print(
        "BAMBU_V2_PROJECT_VALID "
        f"parts={robot_parts} plates={len(layout)} "
        f"groups={len({p['filament_group'] for p in layout})} output={OUTPUT}"
    )


if __name__ == "__main__":
    main()
