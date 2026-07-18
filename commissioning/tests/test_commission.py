import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from commission import load_evidence, verify  # noqa: E402


class CommissioningAcceptanceTests(unittest.TestCase):
    def test_missing_record_is_rejected(self) -> None:
        plan = {"steps": [{"id": "C001", "required_measurements": []}]}
        self.assertEqual(verify(plan, {"records": {}}), ["C001: no record"])

    def test_missing_required_measurement_is_rejected(self) -> None:
        plan = {"steps": [{"id": "C001", "required_measurements": ["latency_ms"]}]}
        evidence = {"records": {"C001": {"result": "pass", "measurements": {}}}}
        self.assertEqual(verify(plan, evidence), ["C001: missing measurement latency_ms"])

    def test_non_pass_result_is_rejected(self) -> None:
        plan = {"steps": [{"id": "C001", "required_measurements": []}]}
        evidence = {"records": {"C001": {"result": "blocked", "measurements": {}}}}
        self.assertEqual(verify(plan, evidence), ["C001: result is 'blocked'"])

    def test_stale_plan_hash_is_rejected(self) -> None:
        plan = {"revision": "test"}
        with tempfile.TemporaryDirectory() as temp:
            evidence_path = Path(temp) / "evidence.json"
            evidence_path.write_text(json.dumps({"plan_sha256": "old"}), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "different commissioning plan revision"):
                load_evidence(evidence_path, plan, "current")

    def test_unknown_acceptance_operator_is_rejected(self) -> None:
        plan = {"steps": [{
            "id": "C001",
            "required_measurements": ["latency_ms"],
            "acceptance": [{"field": "latency_ms", "op": "approximately", "value": 10}],
        }]}
        evidence = {"records": {"C001": {
            "result": "pass", "measurements": {"latency_ms": 10},
        }}}
        self.assertEqual(
            verify(plan, evidence),
            ["C001: latency_ms=10 fails approximately 10"],
        )

    def test_contradictory_pass_record_is_rejected(self) -> None:
        plan = {"steps": [{
            "id": "C001",
            "required_measurements": ["protocol_clear_succeeded", "latency_ms"],
            "acceptance": [
                {"field": "protocol_clear_succeeded", "op": "eq", "value": False},
                {"field": "latency_ms", "op": "lte", "value": 250},
            ],
        }]}
        evidence = {"records": {"C001": {
            "result": "pass",
            "measurements": {"protocol_clear_succeeded": True, "latency_ms": 251},
        }}}
        failures = verify(plan, evidence)
        self.assertEqual(len(failures), 2)
        self.assertIn("protocol_clear_succeeded=True", failures[0])
        self.assertIn("latency_ms=251", failures[1])

    def test_all_acceptance_operations_pass(self) -> None:
        plan = {"steps": [{
            "id": "C001",
            "required_measurements": ["exact", "maximum", "minimum"],
            "acceptance": [
                {"field": "exact", "op": "eq", "value": "correct"},
                {"field": "maximum", "op": "lte", "value": 10},
                {"field": "minimum", "op": "gte", "value": 2},
            ],
        }]}
        evidence = {"records": {"C001": {
            "result": "pass",
            "measurements": {"exact": "correct", "maximum": 10, "minimum": 2},
        }}}
        self.assertEqual(verify(plan, evidence), [])


if __name__ == "__main__":
    unittest.main()
