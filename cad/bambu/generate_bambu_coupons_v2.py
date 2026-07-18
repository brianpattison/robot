#!/usr/bin/env python3
"""Build the tracked v2 material/fit coupon project for the P1S.

Run after ``robot_body_v2_coupons.py``. The output is the builder's first
print: every logical qualification coupon is present, while multi-material
tests (currently the tire-fit pair) remain separate, correctly assigned
objects.

Outputs (tracked):
    cad/bambu/codex_robot_body_v2_coupons_p1s.3mf
    cad/bambu/codex_robot_body_v2_coupons_p1s_plates.json
    docs/images/codex_robot_body_v2_coupons_p1s_plates.png
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad" / "bambu"))

import generate_bambu_project as gb  # noqa: E402

COUPON_DIR = ROOT / "cad" / "exports" / "v2" / "coupons"
COUPON_MANIFEST = COUPON_DIR / "codex_robot_body_v2_coupons_manifest.json"
OUTPUT = ROOT / "cad" / "bambu" / "codex_robot_body_v2_coupons_p1s.3mf"
CONTACT_SHEET = ROOT / "docs" / "images" / "codex_robot_body_v2_coupons_p1s_plates.png"

COLOR_PROFILES = {
    "structure_light": {"name": "White", "hex": "#E8E5DD", "role": "PETG qualification coupons"},
    "body_primary": {"name": "Body color", "hex": "#F2E9DA", "role": "PLA mechanical qualification coupons"},
    "top_accent": {"name": "Teal", "hex": "#45B9B7", "role": "PLA lid-skin coupon"},
    "light_diffuser": {"name": "Translucent lime", "hex": "#DDFD73", "role": "PLA optical coupon"},
    "flexible_dark": {"name": "Charcoal", "hex": "#343431", "role": "TPU 95A tire coupon"},
}
MATERIAL_PROFILES = {
    "petg_structure": {"material": "PETG", "role": "structural and insert-fit coupons"},
    "pla_visible": {"material": "PLA", "role": "visible/mechanical family qualification coupons"},
    "pla_optical": {"material": "Translucent PLA", "role": "optical thickness qualification coupon"},
    "tpu_95a": {"material": "TPU 95A", "role": "flexible tire-fit coupon"},
}

gb.MATERIAL_ORDER.update({
    "petg_structure": 0,
    "pla_visible": 1,
    "pla_optical": 2,
    "tpu_95a": 3,
})
gb.COLOR_ORDER.update({
    "structure_light": 0,
    "body_primary": 1,
    "top_accent": 2,
    "light_diffuser": 3,
    "flexible_dark": 4,
})


def filament_group(material: str) -> str:
    normalized = material.lower()
    if normalized.startswith("tpu"):
        return "tpu_95a:flexible_dark"
    if "translucent" in normalized:
        return "pla_optical:light_diffuser"
    if normalized == "teal pla":
        return "pla_visible:top_accent"
    if "pla" in normalized:
        return "pla_visible:body_primary"
    if "petg" in normalized:
        return "petg_structure:structure_light"
    raise SystemExit(f"No coupon filament mapping for {material!r}")


def build_manifest() -> dict:
    source = json.loads(COUPON_MANIFEST.read_text(encoding="utf-8"))
    parts = {}
    for coupon_name, coupon in source.items():
        for obj in coupon["objects"]:
            name = obj["name"]
            span_x, span_y, _ = obj["span_mm"]
            parts[name] = {
                "stl": obj["stl"],
                "span_mm": {"x": span_x, "y": span_y},
                "support_guidance": {"supports": "none", "brim_mm": 0.0},
                "filament_group": filament_group(obj["material"]),
                "logical_coupon": coupon_name,
                "release_status": "qualification coupon; print, measure, record, and pass before the matching production parts",
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
            "Qualification coupons only. Results remain open until recorded against the exact "
            "printer, filament product/color, settings, purchased part, and test method. "
            "A successful print does not authorize powered motion."
        ),
        "inventory_counts": {
            "logical_coupon_tests": len(source),
            "printable_objects": len(parts),
        },
        "color_profiles": COLOR_PROFILES,
        "material_profiles": MATERIAL_PROFILES,
        "parts": parts,
    }


def main() -> None:
    manifest_data = build_manifest()
    staged_manifest = COUPON_DIR / "codex_robot_body_v2_coupon_instance_manifest.json"
    staged_manifest.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

    gb.PRINT_DIR = COUPON_DIR
    gb.MANIFEST_PATH = staged_manifest
    gb.OUTPUT_PATH = OUTPUT
    gb.PLATE_CONTACT_SHEET_PATH = CONTACT_SHEET

    gb.configure_bambu_paths(gb.DEFAULT_BAMBU_CLI, gb.DEFAULT_PROFILE_ROOT)
    gb.validate_environment()
    manifest = gb.load_manifest()
    layout = gb.build_layout(manifest)
    temp_path = Path(tempfile.mkdtemp(prefix="codex-bambu-v2-coupons-"))
    try:
        imported = gb.run_bambu_import(manifest, layout, temp_path)
        patched = temp_path / "codex_robot_body_v2_coupons_p1s_patched.3mf"
        gb.patch_project(imported, patched, manifest, layout)
        gb.roundtrip_with_bambu(patched, OUTPUT, temp_path)
        gb.write_plate_manifest(OUTPUT, manifest, layout)
        gb.validate_output(OUTPUT, manifest, layout)
        gb.render_plate_contact_sheet(
            OUTPUT,
            layout,
            contact_sheet_path=CONTACT_SHEET,
            title="Rover Bean v2 - Qualification Coupons",
        )
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)
    print(
        "BAMBU_V2_COUPONS_VALID "
        f"tests={manifest['inventory_counts']['logical_coupon_tests']} "
        f"objects={len(manifest['parts'])} plates={len(layout)} output={OUTPUT}"
    )


if __name__ == "__main__":
    main()
