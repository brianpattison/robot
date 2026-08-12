#!/usr/bin/env python3
"""Cross-check the CAD registry against tracked body and proof releases."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad/python"))

import robot_body_v2_inventory as inventory  # noqa: E402


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def main() -> None:
    functional, spares, optional, total = inventory.inventory_report()
    screws, inserts = inventory.fastener_tally()
    body = load("cad/bambu/codex_robot_body_v2_p1s_plates.json")
    proofs = load("cad/bambu/codex_robot_body_v2_proofs_p1s_plates.json")

    if body["generated_by"] != "cad/bambu/generate_bambu_project_v2.py":
        raise SystemExit("body plate manifest names the wrong generator")
    if proofs["generated_by"] != "cad/bambu/generate_bambu_proofs_v2.py":
        raise SystemExit("proof plate manifest names the wrong generator")
    if (functional, spares, optional, total) != (40, 4, 1, 45):
        raise SystemExit("v2 inventory count drift")
    # 51 joints since D049 (regulator bays); 20 proof objects since D048
    # (proof_horn_capture is a two-object proof).
    if (screws, inserts) != (51, 51):
        raise SystemExit("v2 fastener count drift")
    if len(body["plates"]) != 13 or sum(p["part_count"] for p in body["plates"]) != total:
        raise SystemExit("body plate count drift")
    if len(proofs["plates"]) != 5 or sum(p["part_count"] for p in proofs["plates"]) != 20:
        raise SystemExit("proof plate count drift")
    if proofs["inventory_counts"]["logical_proof_tests"] != 18:
        raise SystemExit("logical proof count drift")
    print("CAD_RELEASE_PASS body=45/13 proofs=18-tests/20-objects/5-plates joints=51")


if __name__ == "__main__":
    main()
