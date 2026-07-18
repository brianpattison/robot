#!/usr/bin/env python3
"""Record and verify Rover Bean commissioning evidence without hand-waving."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "commissioning" / "plan-v2.json"
DEFAULT_EVIDENCE = ROOT / "output" / "commissioning" / "evidence-v2.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_plan() -> tuple[dict, str]:
    raw = PLAN_PATH.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def load_evidence(path: Path, plan: dict, plan_hash: str) -> dict:
    if path.exists():
        evidence = json.loads(path.read_text(encoding="utf-8"))
        if evidence.get("plan_sha256") != plan_hash:
            raise SystemExit("Evidence belongs to a different commissioning plan revision.")
        return evidence
    return {"plan_revision": plan["revision"], "plan_sha256": plan_hash,
            "created_at": now(), "updated_at": now(), "records": {}}


def save(path: Path, evidence: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    evidence["updated_at"] = now()
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_measurements(values: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Measurement must be key=value: {value!r}")
        key, raw = value.split("=", 1)
        lowered = raw.lower()
        if lowered in ("true", "false"):
            parsed: Any = lowered == "true"
        else:
            try:
                parsed = int(raw)
            except ValueError:
                try:
                    parsed = float(raw)
                except ValueError:
                    parsed = raw
        result[key] = parsed
    return result


def verify(plan: dict, evidence: dict) -> list[str]:
    failures = []
    for step in plan["steps"]:
        record = evidence["records"].get(step["id"])
        if not record:
            failures.append(f"{step['id']}: no record")
            continue
        if record.get("result") != "pass":
            failures.append(f"{step['id']}: result is {record.get('result')!r}")
        for field in step.get("required_measurements", []):
            if field not in record.get("measurements", {}) or record["measurements"][field] in (None, ""):
                failures.append(f"{step['id']}: missing measurement {field}")
        measurements = record.get("measurements", {})
        for rule in step.get("acceptance", []):
            field = rule["field"]
            if field not in measurements or measurements[field] in (None, ""):
                continue
            actual = measurements[field]
            expected = rule["value"]
            operation = rule["op"]
            try:
                if operation == "eq":
                    accepted = actual == expected
                elif operation == "lte":
                    accepted = actual <= expected
                elif operation == "gte":
                    accepted = actual >= expected
                else:
                    accepted = False
            except TypeError:
                accepted = False
            if not accepted:
                failures.append(
                    f"{step['id']}: {field}={actual!r} fails {operation} {expected!r}")
    return failures


def markdown_report(plan: dict, evidence: dict) -> str:
    lines = [f"# Rover Bean commissioning — {plan['revision']}", "",
             f"Evidence updated: {evidence['updated_at']}", "",
             "| ID | Phase | Test | Result | Operator |", "| --- | --- | --- | --- | --- |"]
    for step in plan["steps"]:
        record = evidence["records"].get(step["id"], {})
        lines.append(f"| {step['id']} | {step['phase']} | {step['title']} | {record.get('result', 'OPEN')} | {record.get('operator', '')} |")
    failures = verify(plan, evidence)
    lines.extend(("", "## Release verdict", "",
                  "PASS — every required test and measurement is recorded." if not failures else
                  f"BLOCKED — {len(failures)} required item(s) remain open.", ""))
    if failures:
        lines.extend(f"- {failure}" for failure in failures)
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    run = sub.add_parser("run-automated")
    run.add_argument("step_id")
    record = sub.add_parser("record")
    record.add_argument("step_id")
    record.add_argument("--result", choices=("pass", "fail", "blocked"), required=True)
    record.add_argument("--operator", required=True)
    record.add_argument("--note", default="")
    record.add_argument("--measure", action="append", default=[])
    sub.add_parser("verify")
    report = sub.add_parser("report")
    report.add_argument("--output", type=Path)
    args = parser.parse_args()

    plan, plan_hash = load_plan()
    steps = {step["id"]: step for step in plan["steps"]}
    evidence = load_evidence(args.evidence, plan, plan_hash)
    if args.command == "list":
        for step in plan["steps"]:
            result = evidence["records"].get(step["id"], {}).get("result", "OPEN")
            print(f"{step['id']}  {result:7}  {step['condition']}  {step['title']}")
        return
    if args.command == "run-automated":
        step = steps.get(args.step_id)
        if not step or not step.get("command"):
            raise SystemExit("Step has no safe automated command.")
        completed = subprocess.run(step["command"], cwd=ROOT, text=True, capture_output=True)
        output = (completed.stdout + "\n" + completed.stderr).strip()
        print(output)
        evidence["records"][step["id"]] = {
            "result": "pass" if completed.returncode == 0 else "fail",
            "operator": "commission.py",
            "recorded_at": now(),
            "note": "Safe automated repository check",
            "measurements": {step["required_measurements"][0]: output[-12000:]},
        }
        save(args.evidence, evidence)
        raise SystemExit(completed.returncode)
    if args.command == "record":
        if args.step_id not in steps:
            raise SystemExit(f"Unknown step {args.step_id}")
        evidence["records"][args.step_id] = {
            "result": args.result, "operator": args.operator, "recorded_at": now(),
            "note": args.note, "measurements": parse_measurements(args.measure),
        }
        save(args.evidence, evidence)
        return
    failures = verify(plan, evidence)
    if args.command == "verify":
        if failures:
            print("COMMISSIONING_GATE_BLOCKED")
            for failure in failures:
                print(f"- {failure}")
            raise SystemExit(1)
        print("COMMISSIONING_GATE_PASS")
        return
    text = markdown_report(plan, evidence)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
