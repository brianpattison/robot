#!/usr/bin/env python3
"""Cross-check the CAD registry against tracked body and coupon releases."""

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
    coupons = load("cad/bambu/codex_robot_body_v2_coupons_p1s_plates.json")

    if body["generated_by"] != "cad/bambu/generate_bambu_project_v2.py":
        raise SystemExit("body plate manifest names the wrong generator")
    if coupons["generated_by"] != "cad/bambu/generate_bambu_coupons_v2.py":
        raise SystemExit("coupon plate manifest names the wrong generator")
    if (functional, spares, optional, total) != (40, 4, 1, 45):
        raise SystemExit("v2 inventory count drift")
    if (screws, inserts) != (47, 47):
        raise SystemExit("v2 fastener count drift")
    if len(body["plates"]) != 13 or sum(p["part_count"] for p in body["plates"]) != total:
        raise SystemExit("body plate count drift")
    if len(coupons["plates"]) != 5 or sum(p["part_count"] for p in coupons["plates"]) != 19:
        raise SystemExit("coupon plate count drift")
    if coupons["inventory_counts"]["logical_coupon_tests"] != 18:
        raise SystemExit("logical coupon count drift")
    print("CAD_RELEASE_PASS body=45/13 coupons=18-tests/19-objects/5-plates joints=47")


if __name__ == "__main__":
    main()
