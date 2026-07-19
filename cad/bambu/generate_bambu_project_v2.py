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

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad" / "bambu"))
sys.path.insert(0, str(ROOT / "cad" / "python"))

import generate_bambu_project as gb  # noqa: E402
import robot_body_v2_inventory as inv  # noqa: E402

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
    layout = gb.build_layout(manifest)
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
        gb.render_plate_contact_sheet(OUTPUT, layout, contact_sheet_path=CONTACT_SHEET,
                                  title="Codex Robot Body v2 - P1S Plate Layout")
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)
    print(
        "BAMBU_V2_PROJECT_VALID "
        f"parts={len(manifest['parts'])} plates={len(layout)} "
        f"groups={len({p['filament_group'] for p in layout})} output={OUTPUT}"
    )


if __name__ == "__main__":
    main()
