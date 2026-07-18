import json
from pathlib import Path
import sys
import unittest

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from generate_harness_docs import validate  # noqa: E402


class HarnessGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((HARNESS_ROOT / "harness-v2.json").read_text())

    def test_checked_in_engineering_manifest_passes(self) -> None:
        self.assertEqual(validate(self.manifest), [])

    def test_release_gate_rejects_blank_first_article_evidence(self) -> None:
        failures = validate(self.manifest, release=True)
        self.assertIn("PWR-01: release evidence missing measured_cut_length_mm", failures)
        self.assertIn("manifest electrical_release is false", failures)
        self.assertIn("physical evidence missing first_article_serial", failures)
        # Update this regression only when real first-article evidence is released.


if __name__ == "__main__":
    unittest.main()
