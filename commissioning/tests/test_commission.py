from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from commission import verify  # noqa: E402


class CommissioningAcceptanceTests(unittest.TestCase):
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
