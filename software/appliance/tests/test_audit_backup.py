from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

APPLIANCE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APPLIANCE_DIR))

from audit_backup import AuditBackup  # noqa: E402


class AuditBackupTests(unittest.TestCase):
    def make_backup(self, temp: Path, mounted: list[bool]) -> tuple[AuditBackup, Path, Path]:
        source = temp / "source.jsonl"
        mount = temp / "mount"
        mount.mkdir(exist_ok=True)
        events = temp / "events.jsonl"
        backup = AuditBackup(
            {"agent-sessions": source},
            mount,
            temp / "state/cursors.json",
            events,
            is_mount=lambda unused: mounted[0],
        )
        return backup, source, events

    @staticmethod
    def events(path: Path) -> list[dict]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_gap_is_reported_once_and_recovery_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mounted = [False]
            backup, source, events = self.make_backup(Path(raw), mounted)
            source.write_text("one\n", encoding="utf-8")
            self.assertFalse(backup.run_once())
            self.assertFalse(backup.run_once())
            self.assertEqual([row["kind"] for row in self.events(events)], ["audit_backup_gap"])
            mounted[0] = True
            self.assertTrue(backup.run_once())
            self.assertEqual(
                [row["kind"] for row in self.events(events)],
                ["audit_backup_gap", "audit_backup_recovered"],
            )
            self.assertEqual(
                (Path(raw) / "mount/agent-sessions.jsonl").read_text(encoding="utf-8"),
                "one\n",
            )

    def test_cursor_copies_only_new_bytes_across_processes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            mounted = [True]
            backup, source, events = self.make_backup(temp, mounted)
            source.write_text("one\n", encoding="utf-8")
            self.assertTrue(backup.run_once())
            source.write_text("one\ntwo\n", encoding="utf-8")
            restarted, _, _ = self.make_backup(temp, mounted)
            self.assertTrue(restarted.run_once())
            self.assertEqual(
                (temp / "mount/agent-sessions.jsonl").read_text(encoding="utf-8"),
                "one\ntwo\n",
            )
            self.assertEqual([], self.events(events))

    def test_truncation_restarts_source_and_records_loss_signal(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            mounted = [True]
            backup, source, events = self.make_backup(temp, mounted)
            source.write_text("a-long-first-record\n", encoding="utf-8")
            self.assertTrue(backup.run_once())
            source.write_text("new\n", encoding="utf-8")
            self.assertTrue(backup.run_once())
            self.assertEqual(self.events(events)[0]["kind"], "audit_source_truncated")
            self.assertTrue(
                (temp / "mount/agent-sessions.jsonl").read_text(encoding="utf-8").endswith("new\n")
            )

    def test_copytruncate_regrowth_past_cursor_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            mounted = [True]
            backup, source, events = self.make_backup(temp, mounted)
            source.write_text("original-record\n", encoding="utf-8")
            self.assertTrue(backup.run_once())
            source.write_text("replacement-record-is-longer\n", encoding="utf-8")
            self.assertTrue(backup.run_once())
            row = self.events(events)[0]
            self.assertEqual(row["kind"], "audit_source_truncated")
            self.assertTrue(row["prior_tail_changed"])
            copied = (temp / "mount/agent-sessions.jsonl").read_text(encoding="utf-8")
            self.assertEqual(copied, "original-record\nreplacement-record-is-longer\n")


if __name__ == "__main__":
    unittest.main()
