"""Shared filament-mass / print-time PLANNING estimates for the v2 guide outputs.

Both renderers (the PDF book and the interactive site) import this module so
they always publish the same numbers. Everything here is a screen-grade
planning estimate derived from the exported print STL volumes and the
inventory's effective-density constants — it is NOT release data, and every
consumer must label it "planning estimate — confirm in the slicer".
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "python"))

import robot_body_v2_inventory as inv  # noqa: E402

PRINT_READY = ROOT / "cad" / "exports" / "v2" / "print_ready"
PRINT_MANIFEST = PRINT_READY / "codex_robot_body_v2_print_manifest.json"

# Conservative P1S throughput at the project's 0.2 mm / 4-wall baseline.
GRAMS_PER_HOUR = {"PETG": 40.0, "PLA": 44.0, "TPU": 16.0}


def binary_stl_volume_mm3(path: Path) -> float:
    """Signed-tetrahedron volume of a binary STL (mm^3)."""
    data = path.read_bytes()
    (count,) = struct.unpack_from("<I", data, 80)
    vol = 0.0
    off = 84
    for _ in range(count):
        f = struct.unpack_from("<12f", data, off)
        x0, y0, z0, x1, y1, z1, x2, y2, z2 = f[3:12]
        vol += (x0 * (y1 * z2 - y2 * z1)
                - y0 * (x1 * z2 - x2 * z1)
                + z0 * (x1 * y2 - x2 * y1))
        off += 50
    return abs(vol) / 6.0


def _family(text: str) -> str:
    up = text.upper()
    if up.startswith("TPU") or "TPU" in up:
        return "TPU"
    if "PLA" in up:
        return "PLA"
    return "PETG"


def plate_estimates(plates: dict) -> dict[int, dict]:
    """plate_number -> {"grams": int, "hours": float} planning estimates."""
    manifest = json.loads(PRINT_MANIFEST.read_text())
    designs = manifest["parts"] if "parts" in manifest else manifest
    density = dict(getattr(inv, "EFFECTIVE_DENSITY", {}))  # g/mm^3, screen-grade

    volumes: dict[str, float] = {}
    out: dict[int, dict] = {}
    for plate in plates["plates"]:
        grams = 0.0
        for part in plate["parts"]:
            base = part["name"].rsplit("_i", 1)[0] if "_i" in part["name"] else part["name"]
            if base not in volumes:
                stl = PRINT_READY / f"{base}_print.stl"
                volumes[base] = binary_stl_volume_mm3(stl) if stl.exists() else 0.0
            entry = designs.get(base, {}) if isinstance(designs, dict) else {}
            fam = _family(entry.get("effective_material_family") or plate["material"])
            rho = density.get(fam) or density.get(fam.title()) or 0.60e-3
            grams += volumes[base] * rho
        rate = GRAMS_PER_HOUR[_family(plate["material"])]
        out[plate["plate_number"]] = {
            "grams": round(grams),
            "hours": max(0.5, round(grams / rate * 2) / 2),
        }
    return out


def totals(estimates: dict[int, dict]) -> tuple[int, float]:
    return (sum(e["grams"] for e in estimates.values()),
            sum(e["hours"] for e in estimates.values()))
