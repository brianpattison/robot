#!/usr/bin/env python3
"""Validate the v2 harness schedule and generate a cut/label traveler."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "harness" / "harness-v2.json"
DEFAULT_OUTPUT = ROOT / "output" / "harness"
MIN_AWG = {"battery": 12, "motor": 18, "accessory_feed": 14,
           "accessory": 18, "servo": 18, "logic": 24,
           "signal": 24, "safety_signal": 22}


def validate(data: dict, release: bool = False) -> list[str]:
    failures: list[str] = []
    wires = data.get("conductors", [])
    ids = [wire.get("id") for wire in wires]
    if not wires or len(ids) != len(set(ids)):
        failures.append("conductor IDs must be present and unique")
    for wire in wires:
        prefix = wire.get("id", "<missing>")
        for field in ("harness", "from", "to", "function", "class", "awg", "color",
                      "nominal_cut_length_mm", "termination_a", "termination_b"):
            if wire.get(field) in (None, ""):
                failures.append(f"{prefix}: missing {field}")
        wire_class = wire.get("class")
        awg = wire.get("awg", 99)
        if wire_class not in MIN_AWG:
            failures.append(f"{prefix}: unknown class {wire_class!r}")
        elif awg > MIN_AWG[wire_class]:
            failures.append(f"{prefix}: AWG {awg} is smaller than class baseline AWG {MIN_AWG[wire_class]}")
        if wire.get("nominal_cut_length_mm", 0) <= wire.get("service_loop_mm", 0):
            failures.append(f"{prefix}: nominal length must exceed service loop")
        if release:
            for field in ("measured_cut_length_mm", "continuity_pass", "pull_test_pass"):
                if wire.get(field) in (None, False):
                    failures.append(f"{prefix}: release evidence missing {field}")
    if release:
        if not data.get("electrical_release"):
            failures.append("manifest electrical_release is false")
        evidence = data.get("physical_evidence", {})
        for field in ("first_article_serial", "reviewed_by", "review_date"):
            if not evidence.get(field):
                failures.append(f"physical evidence missing {field}")
        for field in ("branch_fuse_values_released", "selective_fault_test_passed", "thermal_soak_passed"):
            if evidence.get(field) is not True:
                failures.append(f"physical evidence not passed: {field}")
        for connector in data.get("connectors", []):
            if not connector.get("exact_housing") or not connector.get("exact_contacts"):
                failures.append(f"{connector.get('id')}: exact housing/contacts not released")
            if connector.get("release_blocker"):
                failures.append(f"{connector.get('id')}: unresolved release blocker")
    return failures


def generate(data: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fields = ["id", "harness", "from", "to", "function", "class", "awg", "color",
              "nominal_cut_length_mm", "service_loop_mm", "termination_a", "termination_b",
              "measured_cut_length_mm", "continuity_pass", "pull_test_pass"]
    with (output / "harness-v2-cut-traveler.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data["conductors"])
    labels = []
    for wire in data["conductors"]:
        labels.extend((f"{wire['id']} A | {wire['from']}", f"{wire['id']} B | {wire['to']}"))
    (output / "harness-v2-labels.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--release", action="store_true", help="require all physical evidence and released terminals/fuses")
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    failures = validate(data, release=args.release)
    generate(data, args.output)
    if failures:
        print("HARNESS_GATE_FAIL")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print(f"HARNESS_GATE_PASS conductors={len(data['conductors'])} release={args.release}")


if __name__ == "__main__":
    main()
