#!/usr/bin/env python3
"""Build the P1S Bambu Studio layout project from canonical print-ready STLs.

The script delegates STL import and Bambu preset serialization to Bambu Studio,
then replaces its plate layout with a deterministic, conservative rectangle
packing. Every plate contains exactly one material-profile/color group.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
PRINT_DIR = ROOT / "cad" / "exports" / "print_ready"
MANIFEST_PATH = PRINT_DIR / "codex_robot_body_v1_print_manifest.json"
OUTPUT_PATH = ROOT / "cad" / "bambu" / "codex_robot_body_v1_p1s.3mf"
PLATE_MANIFEST_PATH = ROOT / "cad" / "bambu" / "codex_robot_body_v1_p1s_plates.json"
PLATE_CONTACT_SHEET_PATH = ROOT / "docs" / "images" / "codex_robot_body_v1_p1s_plates.png"

DEFAULT_BAMBU_APP = Path("/Applications/BambuStudio.app")
DEFAULT_BAMBU_CLI = DEFAULT_BAMBU_APP / "Contents" / "MacOS" / "BambuStudio"
DEFAULT_PROFILE_ROOT = DEFAULT_BAMBU_APP / "Contents" / "Resources" / "profiles" / "BBL"
BAMBU_CLI = DEFAULT_BAMBU_CLI
PROFILE_ROOT = DEFAULT_PROFILE_ROOT
MACHINE_PROFILE = PROFILE_ROOT / "machine" / "Bambu Lab P1S 0.4 nozzle.json"
PROCESS_PROFILE = PROFILE_ROOT / "process" / "0.20mm Standard @BBL X1C.json"
PETG_PROFILE = PROFILE_ROOT / "filament" / "Generic PETG HF @BBL P1S 0.4 nozzle.json"
TPU_PROFILE = PROFILE_ROOT / "filament" / "Bambu TPU 95A HF @BBL P1S.json"

BED_SIZE = 256.0
BED_EDGE_MARGIN = 8.0
OBJECT_SPACING = 4.0
PLATE_TYPE = "Textured PEI Plate"

CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD_NS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
ET.register_namespace("", CORE_NS)
ET.register_namespace("p", PROD_NS)

MATERIAL_ORDER = {
    "petg_structural": 0,
    "petg_shell": 1,
    "petg_detail": 2,
    "translucent_petg": 3,
    "tpu_95a": 4,
}
COLOR_ORDER = {
    "cream": 0,
    "teal": 1,
    "dark_teal": 2,
    "charcoal": 3,
    "dark_gray": 4,
    "translucent_lime": 5,
    "blue": 6,
}


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float


@dataclass(frozen=True)
class Placement:
    name: str
    group: str
    plate_in_group: int
    x: float
    y: float
    rotated_90: bool
    span_x: float
    span_y: float
    brim_mm: float


def fail(message: str) -> None:
    raise SystemExit(message)


def configure_bambu_paths(cli: Path, profile_root: Path) -> None:
    """Configure an installed official Bambu Studio CLI and its BBL profiles."""
    global BAMBU_CLI, PROFILE_ROOT
    global MACHINE_PROFILE, PROCESS_PROFILE, PETG_PROFILE, TPU_PROFILE

    BAMBU_CLI = cli.expanduser()
    PROFILE_ROOT = profile_root.expanduser()
    MACHINE_PROFILE = PROFILE_ROOT / "machine" / "Bambu Lab P1S 0.4 nozzle.json"
    PROCESS_PROFILE = PROFILE_ROOT / "process" / "0.20mm Standard @BBL X1C.json"
    PETG_PROFILE = PROFILE_ROOT / "filament" / "Generic PETG HF @BBL P1S 0.4 nozzle.json"
    TPU_PROFILE = PROFILE_ROOT / "filament" / "Bambu TPU 95A HF @BBL P1S.json"


def validate_environment() -> None:
    required = [
        BAMBU_CLI,
        MACHINE_PROFILE,
        PROCESS_PROFILE,
        PETG_PROFILE,
        TPU_PROFILE,
        MANIFEST_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        fail("Missing required Bambu/CAD inputs:\n- " + "\n- ".join(missing))


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    target = manifest.get("printer_target", {})
    if target.get("model") != "Bambu Lab P1S":
        fail("Regenerate print-ready exports with the P1S target before building the 3MF.")
    if float(target.get("nozzle_diameter_mm", 0)) != 0.4:
        fail("The Bambu project generator currently requires the P1S 0.4 mm nozzle target.")
    if not manifest.get("parts"):
        fail("Canonical print manifest contains no parts.")
    return manifest


def intersects(a: Rect, b: Rect) -> bool:
    epsilon = 1e-6
    return not (
        b.x >= a.x + a.w - epsilon
        or b.x + b.w <= a.x + epsilon
        or b.y >= a.y + a.h - epsilon
        or b.y + b.h <= a.y + epsilon
    )


def contained(inner: Rect, outer: Rect) -> bool:
    return (
        inner.x >= outer.x
        and inner.y >= outer.y
        and inner.x + inner.w <= outer.x + outer.w
        and inner.y + inner.h <= outer.y + outer.h
    )


def split_free_rectangles(free_rects: list[Rect], used: Rect) -> list[Rect]:
    split: list[Rect] = []
    for free in free_rects:
        if not intersects(free, used):
            split.append(free)
            continue
        if used.x > free.x:
            split.append(Rect(free.x, free.y, used.x - free.x, free.h))
        if used.x + used.w < free.x + free.w:
            split.append(
                Rect(used.x + used.w, free.y, free.x + free.w - used.x - used.w, free.h)
            )
        if used.y > free.y:
            split.append(Rect(free.x, free.y, free.w, used.y - free.y))
        if used.y + used.h < free.y + free.h:
            split.append(
                Rect(free.x, used.y + used.h, free.w, free.y + free.h - used.y - used.h)
            )
    split = [rect for rect in split if rect.w > 0.01 and rect.h > 0.01]
    pruned: list[Rect] = []
    for i, candidate in enumerate(split):
        if any(i != j and contained(candidate, other) for j, other in enumerate(split)):
            continue
        pruned.append(candidate)
    return pruned


def best_position(free_rects: list[Rect], width: float, height: float):
    options = []
    for rotated, (w, h) in ((False, (width, height)), (True, (height, width))):
        for free in free_rects:
            if w <= free.w + 1e-6 and h <= free.h + 1e-6:
                short = min(free.w - w, free.h - h)
                long = max(free.w - w, free.h - h)
                options.append(((short, long, free.y, free.x, rotated), free, w, h))
    if not options:
        return None
    _, free, width, height = min(options, key=lambda option: option[0])
    rotated = min(options, key=lambda option: option[0])[0][-1]
    return free, width, height, rotated


def pack_group(group: str, names: list[str], parts: dict) -> list[list[Placement]]:
    usable = BED_SIZE - 2.0 * BED_EDGE_MARGIN
    ordered = sorted(
        names,
        key=lambda name: (
            -max(parts[name]["span_mm"]["x"], parts[name]["span_mm"]["y"]),
            -(parts[name]["span_mm"]["x"] * parts[name]["span_mm"]["y"]),
            name,
        ),
    )
    plates: list[dict] = []
    for name in ordered:
        part = parts[name]
        span_x = float(part["span_mm"]["x"])
        span_y = float(part["span_mm"]["y"])
        brim = float(part["support_guidance"]["brim_mm"])
        pad = brim + OBJECT_SPACING / 2.0
        outer_w = span_x + 2.0 * pad
        outer_h = span_y + 2.0 * pad
        if max(outer_w, outer_h) > usable + 1e-6:
            fail(f"{name} plus brim/spacing does not fit the P1S safe area.")

        selected = None
        for plate_index, plate in enumerate(plates):
            option = best_position(plate["free"], outer_w, outer_h)
            if option is not None:
                selected = (plate_index, option)
                break
        if selected is None:
            plates.append({"free": [Rect(0.0, 0.0, usable, usable)], "items": []})
            selected = (len(plates) - 1, best_position(plates[-1]["free"], outer_w, outer_h))

        plate_index, option = selected
        if option is None:
            fail(f"Unable to place {name} on an empty P1S plate.")
        free, used_w, used_h, rotated = option
        used = Rect(free.x, free.y, used_w, used_h)
        plates[plate_index]["free"] = split_free_rectangles(plates[plate_index]["free"], used)

        actual_x = span_y if rotated else span_x
        actual_y = span_x if rotated else span_y
        center_x = BED_EDGE_MARGIN + used.x + pad + actual_x / 2.0
        center_y = BED_EDGE_MARGIN + used.y + pad + actual_y / 2.0
        plates[plate_index]["items"].append(
            Placement(
                name=name,
                group=group,
                plate_in_group=plate_index + 1,
                x=center_x,
                y=center_y,
                rotated_90=rotated,
                span_x=actual_x,
                span_y=actual_y,
                brim_mm=brim,
            )
        )
    return [plate["items"] for plate in plates]


def build_layout(manifest: dict) -> list[dict]:
    parts = manifest["parts"]
    groups: dict[str, list[str]] = defaultdict(list)
    for name, part in parts.items():
        groups[part["filament_group"]].append(name)

    def group_key(group: str):
        material, color = group.split(":", 1)
        return (MATERIAL_ORDER[material], COLOR_ORDER[color], group)

    layout = []
    plate_number = 1
    for group in sorted(groups, key=group_key):
        group_plates = pack_group(group, groups[group], parts)
        material_profile, color_profile = group.split(":", 1)
        material = "TPU 95A" if material_profile == "tpu_95a" else "PETG"
        color_label = color_profile.replace("_", " ").title()
        role_label = {
            "petg_structural": "Structural",
            "petg_shell": "Shell",
            "petg_detail": "Detail",
            "translucent_petg": "Diffuser",
            "tpu_95a": "Flexible",
        }[material_profile]
        for index, placements in enumerate(group_plates, start=1):
            suffix = f" {index} of {len(group_plates)}" if len(group_plates) > 1 else ""
            layout.append(
                {
                    "plate_number": plate_number,
                    "name": f"{color_label} {material} - {role_label}{suffix}",
                    "filament_group": group,
                    "material_profile": material_profile,
                    "material": material,
                    "color_profile": color_profile,
                    "color_hex": manifest["color_profiles"][color_profile]["hex"],
                    "placements": placements,
                }
            )
            plate_number += 1
    return layout


def physical_filaments(layout: list[dict]) -> list[dict]:
    seen = set()
    filaments = []
    for plate in layout:
        key = (plate["material"], plate["color_profile"])
        if key in seen:
            continue
        seen.add(key)
        filaments.append(
            {
                "material": plate["material"],
                "color_profile": plate["color_profile"],
                "color_hex": plate["color_hex"],
            }
        )
    return filaments


def resolve_profile(source: Path, profile_directory: Path) -> dict:
    profile_files = list(profile_directory.rglob("*.json"))
    by_name = {}
    for path in profile_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("name"):
            by_name[data["name"]] = data

    def resolve(data: dict, chain: tuple[str, ...] = ()) -> dict:
        parent_name = data.get("inherits")
        if not parent_name:
            return dict(data)
        if parent_name in chain or parent_name not in by_name:
            fail(f"Cannot resolve Bambu filament inheritance: {' -> '.join(chain + (parent_name,))}")
        merged = resolve(by_name[parent_name], chain + (parent_name,))
        merged.update(data)
        return merged

    resolved = resolve(json.loads(source.read_text(encoding="utf-8")))
    resolved.pop("inherits", None)
    return resolved


def flatten_filament_profile(source: Path, output: Path, filament: dict) -> None:
    resolved = resolve_profile(source, PROFILE_ROOT / "filament")
    material = filament["material"]
    color_name = filament["color_profile"].replace("_", " ").title()
    preset_name = f"Codex {color_name} {material} @ P1S 0.4"
    resolved.update(
        {
            "name": preset_name,
            "from": "User",
            "setting_id": "CODEX_" + uuid.uuid5(uuid.NAMESPACE_URL, preset_name).hex[:12].upper(),
            "instantiation": "true",
            "compatible_printers": ["Bambu Lab P1S 0.4 nozzle"],
            "filament_colour": [filament["color_hex"], filament["color_hex"]],
            "filament_type": ["TPU" if material.startswith("TPU") else "PETG"] * 2,
            "filament_vendor": ["Bambu Lab" if material.startswith("TPU") else "Generic"] * 2,
        }
    )
    output.write_text(json.dumps(resolved, indent=2) + "\n", encoding="utf-8")


def run_bambu_import(manifest: dict, layout: list[dict], temp_dir: Path) -> Path:
    filaments = physical_filaments(layout)
    filament_ids = { (f["material"], f["color_profile"]): i + 1 for i, f in enumerate(filaments) }
    flattened = []
    for index, filament in enumerate(filaments, start=1):
        output = temp_dir / f"filament_{index:02d}.json"
        source = TPU_PROFILE if filament["material"].startswith("TPU") else PETG_PROFILE
        flatten_filament_profile(source, output, filament)
        flattened.append(output)

    flattened_machine = temp_dir / "p1s_0.4_machine.json"
    machine = resolve_profile(MACHINE_PROFILE, PROFILE_ROOT / "machine")
    machine.update(
        {
            "name": "Bambu Lab P1S 0.4 nozzle",
            "from": "system",
            "instantiation": "true",
        }
    )
    flattened_machine.write_text(json.dumps(machine, indent=2) + "\n", encoding="utf-8")

    flattened_process = temp_dir / "codex_robot_0.20_process.json"
    process = resolve_profile(PROCESS_PROFILE, PROFILE_ROOT / "process")
    process.update(
        {
            "name": "0.20mm Standard @BBL X1C",
            "from": "system",
            "instantiation": "true",
            "compatible_printers": ["Bambu Lab P1S 0.4 nozzle"],
            "curr_bed_type": PLATE_TYPE,
            "wall_loops": "4",
            "sparse_infill_density": "25%",
            "sparse_infill_pattern": "gyroid",
        }
    )
    flattened_process.write_text(json.dumps(process, indent=2) + "\n", encoding="utf-8")

    placement_by_name = {
        placement.name: plate for plate in layout for placement in plate["placements"]
    }
    names = sorted(manifest["parts"])
    stls = [PRINT_DIR / manifest["parts"][name]["stl"] for name in names]
    missing = [str(path) for path in stls if not path.exists()]
    if missing:
        fail("Missing canonical print-ready STL files:\n- " + "\n- ".join(missing))
    object_filament_ids = [
        str(filament_ids[(placement_by_name[name]["material"], placement_by_name[name]["color_profile"])])
        for name in names
    ]
    base_name = "codex_robot_body_v1_p1s_import.3mf"
    command = [
        str(BAMBU_CLI),
        "--load-settings",
        f"{flattened_machine};{flattened_process}",
        "--load-filaments",
        ";".join(str(path) for path in flattened),
        "--load-filament-ids",
        ",".join(object_filament_ids),
        "--arrange",
        "0",
        "--ensure-on-bed",
        "--export-3mf",
        base_name,
        "--outputdir",
        str(temp_dir),
        *[str(path) for path in stls],
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        fail(
            "Bambu Studio import failed.\n"
            + completed.stdout[-4000:]
            + "\n"
            + completed.stderr[-4000:]
        )
    output = temp_dir / base_name
    if not output.exists():
        candidates = sorted(temp_dir.glob("*.3mf"))
        if len(candidates) != 1:
            fail("Bambu Studio did not produce the expected import project.")
        output = candidates[0]
    return output


def placement_transform(placement: Placement, original: str) -> str:
    values = [float(value) for value in original.split()]
    z = values[11] if len(values) == 12 else 0.0
    if placement.rotated_90:
        matrix = [0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    else:
        matrix = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    return " ".join(f"{value:.8g}" for value in matrix + [placement.x, placement.y, z])


def plate_origin(plate_number: int, plate_count: int) -> tuple[float, float]:
    """Match Bambu Studio's square plate grid and 20 percent logical gap."""
    columns = int(math.ceil(math.sqrt(plate_count)))
    index = plate_number - 1
    stride = BED_SIZE * 1.2
    return (index % columns) * stride, -(index // columns) * stride


def patch_project(import_project: Path, output: Path, manifest: dict, layout: list[dict]) -> None:
    with zipfile.ZipFile(import_project) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}

    model_root = ET.fromstring(entries["3D/3dmodel.model"])
    settings_root = ET.fromstring(entries["Metadata/model_settings.config"])
    build = model_root.find(f"{{{CORE_NS}}}build")
    if build is None:
        fail("Imported Bambu project has no 3MF build section.")

    object_ids_by_name = {}
    for obj in settings_root.findall("object"):
        metadata = obj.find("metadata[@key='name']")
        if metadata is None:
            continue
        object_ids_by_name[Path(metadata.attrib["value"]).stem] = obj.attrib["id"]
    if set(object_ids_by_name) != set(manifest["parts"]):
        missing = sorted(set(manifest["parts"]) - set(object_ids_by_name))
        extra = sorted(set(object_ids_by_name) - set(manifest["parts"]))
        fail(f"Bambu object inventory mismatch. missing={missing} extra={extra}")

    items_by_id = {item.attrib["objectid"]: item for item in build.findall(f"{{{CORE_NS}}}item")}
    placement_by_name = {
        placement.name: (placement, plate["plate_number"])
        for plate in layout
        for placement in plate["placements"]
    }
    for name, object_id in object_ids_by_name.items():
        item = items_by_id[object_id]
        placement, plate_number = placement_by_name[name]
        origin_x, origin_y = plate_origin(plate_number, len(layout))
        global_placement = Placement(
            name=placement.name,
            group=placement.group,
            plate_in_group=placement.plate_in_group,
            x=placement.x + origin_x,
            y=placement.y + origin_y,
            rotated_90=placement.rotated_90,
            span_x=placement.span_x,
            span_y=placement.span_y,
            brim_mm=placement.brim_mm,
        )
        item.attrib["transform"] = placement_transform(
            global_placement, item.attrib.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0")
        )

    for old_plate in settings_root.findall("plate"):
        settings_root.remove(old_plate)
    assemble = settings_root.find("assemble")
    insert_index = list(settings_root).index(assemble) if assemble is not None else len(settings_root)
    identify_id = 1
    for plate in layout:
        plate_element = ET.Element("plate")
        metadata_values = {
            "plater_id": str(plate["plate_number"]),
            "plater_name": plate["name"],
            "locked": "false",
            "bed_type": PLATE_TYPE,
            "filament_map_mode": "Auto For Flush",
            "gcode_file": "",
        }
        for key, value in metadata_values.items():
            ET.SubElement(plate_element, "metadata", {"key": key, "value": value})
        for placement in plate["placements"]:
            instance = ET.SubElement(plate_element, "model_instance")
            for key, value in (
                ("object_id", object_ids_by_name[placement.name]),
                ("instance_id", "0"),
                ("identify_id", str(identify_id)),
            ):
                ET.SubElement(instance, "metadata", {"key": key, "value": value})
            identify_id += 1
        settings_root.insert(insert_index, plate_element)
        insert_index += 1

    project_settings = json.loads(entries["Metadata/project_settings.config"])
    project_settings.update(
        {
            "curr_bed_type": PLATE_TYPE,
            "printer_model": "Bambu Lab P1S",
            "printer_settings_id": "Bambu Lab P1S 0.4 nozzle",
            "printer_variant": "0.4",
            "nozzle_diameter": ["0.4"],
            "wall_loops": "4",
            "sparse_infill_density": "25%",
            "sparse_infill_pattern": "gyroid",
        }
    )
    entries["3D/3dmodel.model"] = ET.tostring(model_root, encoding="utf-8", xml_declaration=True)
    entries["Metadata/model_settings.config"] = ET.tostring(
        settings_root, encoding="utf-8", xml_declaration=True
    )
    entries["Metadata/project_settings.config"] = (
        json.dumps(project_settings, indent=2) + "\n"
    ).encode("utf-8")

    # Imported thumbnails describe the temporary all-overlapping plate. Omitting
    # them is more honest; Bambu Studio regenerates plate previews when opened.
    for name in list(entries):
        if name.startswith("Metadata/") and name.endswith(".png"):
            del entries[name]

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def roundtrip_with_bambu(patched: Path, output: Path, temp_dir: Path) -> None:
    """Make Bambu Studio rebuild its internal plate list and thumbnails."""
    roundtrip_name = "codex_robot_body_v1_p1s_roundtrip.3mf"
    command = [
        str(BAMBU_CLI),
        "--arrange",
        "0",
        "--export-3mf",
        roundtrip_name,
        "--outputdir",
        str(temp_dir),
        str(patched),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    candidate = temp_dir / roundtrip_name
    if completed.returncode != 0 or not candidate.exists():
        fail(
            "Bambu Studio round-trip failed.\n"
            + completed.stdout[-4000:]
            + "\n"
            + completed.stderr[-4000:]
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate, output)


def write_plate_manifest(output: Path, manifest: dict, layout: list[dict]) -> None:
    payload = {
        "project": output.name,
        "generated_by": "cad/bambu/generate_bambu_project.py",
        "printer": {
            "model": "Bambu Lab P1S",
            "nozzle_diameter_mm": 0.4,
            "build_volume_mm": [256, 256, 256],
            "plate_type": PLATE_TYPE,
            "bed_edge_margin_mm": BED_EDGE_MARGIN,
            "minimum_object_spacing_mm": OBJECT_SPACING,
        },
        "warning": manifest["release_warning"],
        "global_project_baseline": {
            "layer_height_mm": 0.20,
            "wall_loops": 4,
            "infill_percent": 25,
            "infill_pattern": "gyroid",
            "note": "Plate-specific material-profile recommendations below remain authoritative; review every plate before slicing.",
        },
        "material_profiles": manifest["material_profiles"],
        "color_profiles": manifest["color_profiles"],
        "plates": [],
    }
    for plate in layout:
        profile = manifest["material_profiles"][plate["material_profile"]]
        payload["plates"].append(
            {
                "plate_number": plate["plate_number"],
                "name": plate["name"],
                "filament_group": plate["filament_group"],
                "material": plate["material"],
                "color_profile": plate["color_profile"],
                "color_hex": plate["color_hex"],
                "recommended_process": profile,
                "part_count": len(plate["placements"]),
                "parts": [
                    {
                        "name": p.name,
                        "center_mm": [round(p.x, 3), round(p.y, 3)],
                        "rotated_z_degrees": 90 if p.rotated_90 else 0,
                        "span_xy_mm": [round(p.span_x, 3), round(p.span_y, 3)],
                        "brim_mm": p.brim_mm,
                        "release_status": manifest["parts"][p.name]["release_status"],
                    }
                    for p in plate["placements"]
                ],
            }
        )
    PLATE_MANIFEST_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def render_plate_contact_sheet(output: Path, layout: list[dict]) -> None:
    columns = 5
    tile_width = 312
    tile_height = 354
    margin = 28
    header_height = 92
    rows = math.ceil(len(layout) / columns)
    canvas = Image.new(
        "RGB",
        (margin * 2 + columns * tile_width, header_height + margin + rows * tile_height),
        "#F4E9D8",
    )
    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf", 32
        )
        label_font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Arial.ttf", 16
        )
        number_font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf", 17
        )
    except OSError:
        title_font = label_font = number_font = ImageFont.load_default()
    draw.text(
        (margin, 20),
        "Codex Robot Body v1 - P1S Plate Layout",
        fill="#20272B",
        font=title_font,
    )
    draw.text(
        (margin, 58),
        f"{sum(len(plate['placements']) for plate in layout)} parts / {len(layout)} plates / P1S 0.4 mm / Textured PEI / one material and color per plate",
        fill="#526066",
        font=label_font,
    )

    with zipfile.ZipFile(output) as archive:
        for index, plate in enumerate(layout):
            row, column = divmod(index, columns)
            x = margin + column * tile_width
            y = header_height + row * tile_height
            draw.rounded_rectangle(
                (x + 6, y + 6, x + tile_width - 8, y + tile_height - 10),
                radius=18,
                fill="#FFFDF8",
                outline="#D6C9B7",
                width=2,
            )
            draw.rounded_rectangle(
                (x + 18, y + 18, x + 48, y + 48),
                radius=7,
                fill=plate["color_hex"],
            )
            draw.text(
                (x + 58, y + 21),
                f"Plate {plate['plate_number']:02d}",
                fill="#20272B",
                font=number_font,
            )

            thumbnail_name = f"Metadata/plate_{plate['plate_number']}.png"
            thumbnail = Image.open(io.BytesIO(archive.read(thumbnail_name))).convert("RGB")
            thumbnail = ImageOps.contain(
                thumbnail, (276, 244), Image.Resampling.LANCZOS
            )
            canvas.paste(
                thumbnail,
                (x + (tile_width - thumbnail.width) // 2, y + 58),
            )

            words = plate["name"].split()
            lines = []
            current = ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if (
                    draw.textlength(candidate, font=label_font) > tile_width - 34
                    and current
                ):
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
            for line_index, line in enumerate(lines[:2]):
                draw.text(
                    (x + 18, y + 305 + line_index * 20),
                    line,
                    fill="#343E43",
                    font=label_font,
                )

    PLATE_CONTACT_SHEET_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PLATE_CONTACT_SHEET_PATH, optimize=True)


def validate_output(output: Path, manifest: dict, layout: list[dict]) -> None:
    with zipfile.ZipFile(output) as archive:
        settings_root = ET.fromstring(archive.read("Metadata/model_settings.config"))
        project_settings = json.loads(archive.read("Metadata/project_settings.config"))
    names = []
    group_by_name = {name: part["filament_group"] for name, part in manifest["parts"].items()}
    plates = settings_root.findall("plate")
    id_to_name = {}
    for obj in settings_root.findall("object"):
        metadata = obj.find("metadata[@key='name']")
        id_to_name[obj.attrib["id"]] = Path(metadata.attrib["value"]).stem
    for plate in plates:
        plate_names = [
            id_to_name[instance.find("metadata[@key='object_id']").attrib["value"]]
            for instance in plate.findall("model_instance")
        ]
        names.extend(plate_names)
        if len({group_by_name[name] for name in plate_names}) != 1:
            fail("A generated plate mixes material-profile/color groups.")
    actual_plate_names = [
        plate.find("metadata[@key='plater_name']").attrib["value"] for plate in plates
    ]
    expected_plate_names = [plate["name"] for plate in layout]
    if actual_plate_names != expected_plate_names:
        fail("Bambu Studio round-trip did not preserve the canonical plate names/order.")
    expected_part_count = len(manifest["parts"])
    if len(names) != expected_part_count or set(names) != set(manifest["parts"]) or len(names) != len(set(names)):
        fail(
            f"Final 3MF does not contain each of the {expected_part_count} "
            "canonical parts exactly once."
        )
    if len(plates) != len(layout):
        fail(f"Expected {len(layout)} plates, found {len(plates)}.")
    if project_settings.get("printer_model") != "Bambu Lab P1S":
        fail("Final 3MF printer model is not P1S.")
    if project_settings.get("curr_bed_type") != PLATE_TYPE:
        fail("Final 3MF plate type is not Textured PEI Plate.")
    for plate in layout:
        for item in plate["placements"]:
            half_x = item.span_x / 2.0 + item.brim_mm
            half_y = item.span_y / 2.0 + item.brim_mm
            if not (
                BED_EDGE_MARGIN - 1e-6 <= item.x - half_x
                and item.x + half_x <= BED_SIZE - BED_EDGE_MARGIN + 1e-6
                and BED_EDGE_MARGIN - 1e-6 <= item.y - half_y
                and item.y + half_y <= BED_SIZE - BED_EDGE_MARGIN + 1e-6
            ):
                fail(f"{item.name} exceeds the reserved P1S plate area.")
        for index, first in enumerate(plate["placements"]):
            first_rect = Rect(
                first.x - first.span_x / 2.0 - first.brim_mm - OBJECT_SPACING / 2.0,
                first.y - first.span_y / 2.0 - first.brim_mm - OBJECT_SPACING / 2.0,
                first.span_x + 2.0 * first.brim_mm + OBJECT_SPACING,
                first.span_y + 2.0 * first.brim_mm + OBJECT_SPACING,
            )
            for second in plate["placements"][index + 1 :]:
                second_rect = Rect(
                    second.x - second.span_x / 2.0 - second.brim_mm - OBJECT_SPACING / 2.0,
                    second.y - second.span_y / 2.0 - second.brim_mm - OBJECT_SPACING / 2.0,
                    second.span_x + 2.0 * second.brim_mm + OBJECT_SPACING,
                    second.span_y + 2.0 * second.brim_mm + OBJECT_SPACING,
                )
                if intersects(first_rect, second_rect):
                    fail(f"P1S packing envelopes overlap: {first.name} and {second.name}.")

    with tempfile.TemporaryDirectory(prefix="codex-bambu-info-") as info_dir:
        info = subprocess.run(
            [str(BAMBU_CLI), "--info", str(output)],
            text=True,
            capture_output=True,
            cwd=info_dir,
        )
    reported_part_count = sum(
        int(match.group(1))
        for match in re.finditer(
            r"^\s*number_of_parts\s*=\s*(\d+)\s*$",
            info.stdout,
            flags=re.MULTILINE,
        )
    )
    if info.returncode != 0 or reported_part_count != expected_part_count:
        fail(
            f"Bambu Studio could not read all {expected_part_count} objects "
            f"from the final 3MF (reported {reported_part_count}).\n"
            f"stdout:\n{info.stdout[-2000:]}\n"
            f"stderr:\n{info.stderr[-2000:]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument(
        "--bambu-cli",
        type=Path,
        default=Path(os.environ.get("BAMBU_STUDIO_CLI", DEFAULT_BAMBU_CLI)),
        help="Official Bambu Studio CLI executable (env: BAMBU_STUDIO_CLI).",
    )
    parser.add_argument(
        "--profile-root",
        type=Path,
        default=Path(
            os.environ.get("BAMBU_STUDIO_PROFILE_ROOT", DEFAULT_PROFILE_ROOT)
        ),
        help="Bambu Studio resources/profiles/BBL directory (env: BAMBU_STUDIO_PROFILE_ROOT).",
    )
    args = parser.parse_args()

    configure_bambu_paths(args.bambu_cli, args.profile_root)
    validate_environment()
    manifest = load_manifest()
    layout = build_layout(manifest)
    temp_path = Path(tempfile.mkdtemp(prefix="codex-bambu-p1s-"))
    try:
        imported = run_bambu_import(manifest, layout, temp_path)
        patched = temp_path / "codex_robot_body_v1_p1s_patched.3mf"
        patch_project(imported, patched, manifest, layout)
        roundtrip_with_bambu(patched, args.output, temp_path)
        write_plate_manifest(args.output, manifest, layout)
        validate_output(args.output, manifest, layout)
        render_plate_contact_sheet(args.output, layout)
    finally:
        if args.keep_temp:
            print(f"BAMBU_TEMP {temp_path}")
        else:
            shutil.rmtree(temp_path, ignore_errors=True)

    print(
        "BAMBU_PROJECT_VALID "
        f"printer=P1S nozzle=0.4mm parts={len(manifest['parts'])} plates={len(layout)} "
        f"groups={len({plate['filament_group'] for plate in layout})} "
        f"output={args.output}"
    )


if __name__ == "__main__":
    main()
