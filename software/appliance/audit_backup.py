#!/usr/bin/env python3
"""Best-effort session backup with explicit mount gaps and byte cursors.

This is an availability copy, not a trust anchor. A root-capable Pi process can
tamper with any read-write mount. Commissioning must prove a separate collector.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Callable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class AuditBackup:
    TAIL_WINDOW = 4096

    def __init__(
        self,
        sources: dict[str, Path],
        mount: Path,
        cursor_path: Path,
        event_path: Path,
        is_mount: Callable[[Path], bool] = os.path.ismount,
    ) -> None:
        self.sources = sources
        self.mount = mount
        self.cursor_path = cursor_path
        self.event_path = event_path
        self.is_mount = is_mount
        self.gap = False
        self.cursors = self._load_cursors()

    @staticmethod
    def _append(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

    def _event(self, kind: str, **fields: object) -> None:
        record = {"ts": utc_now(), "kind": kind, **fields}
        self._append(
            self.event_path,
            (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(),
        )

    def _load_cursors(self) -> dict[str, dict[str, int | str]]:
        try:
            payload = json.loads(self.cursor_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}
        cursors: dict[str, dict[str, int | str]] = {}
        for name, value in payload.items():
            if not isinstance(value, dict) or "inode" not in value or "offset" not in value:
                continue
            cursor: dict[str, int | str] = {
                "inode": int(value["inode"]),
                "offset": int(value["offset"]),
            }
            if "tail_len" in value and "tail_sha256" in value:
                cursor["tail_len"] = int(value["tail_len"])
                cursor["tail_sha256"] = str(value["tail_sha256"])
            cursors[str(name)] = cursor
        return cursors

    def _save_cursors(self) -> None:
        self.cursor_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.cursor_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.cursors, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(temp, 0o600)
        os.replace(temp, self.cursor_path)

    def _copy_source(self, name: str, source: Path) -> None:
        try:
            stat = source.stat()
        except FileNotFoundError:
            return
        cursor = self.cursors.get(name, {"inode": stat.st_ino, "offset": 0})
        tail_changed = False
        tail_len = int(cursor.get("tail_len", 0))
        if (cursor["inode"] == stat.st_ino and tail_len > 0 and
                stat.st_size >= int(cursor["offset"])):
            with source.open("rb") as stream:
                stream.seek(int(cursor["offset"]) - tail_len)
                old_tail = stream.read(tail_len)
            tail_changed = hashlib.sha256(old_tail).hexdigest() != cursor.get("tail_sha256")
        if (cursor["inode"] != stat.st_ino or stat.st_size < int(cursor["offset"])
                or tail_changed):
            self._event(
                "audit_source_truncated",
                source=str(source),
                old_inode=cursor["inode"],
                new_inode=stat.st_ino,
                old_offset=cursor["offset"],
                new_size=stat.st_size,
                prior_tail_changed=tail_changed,
            )
            cursor = {"inode": stat.st_ino, "offset": 0}
        with source.open("rb") as stream:
            stream.seek(int(cursor["offset"]))
            payload = stream.read()
        if payload:
            self._append(self.mount / f"{name}.jsonl", payload)
            cursor["offset"] = int(cursor["offset"]) + len(payload)
        cursor["inode"] = stat.st_ino
        cursor_tail_len = min(int(cursor["offset"]), self.TAIL_WINDOW)
        with source.open("rb") as stream:
            stream.seek(int(cursor["offset"]) - cursor_tail_len)
            cursor_tail = stream.read(cursor_tail_len)
        cursor["tail_len"] = cursor_tail_len
        cursor["tail_sha256"] = hashlib.sha256(cursor_tail).hexdigest()
        self.cursors[name] = cursor

    def run_once(self) -> bool:
        if not self.mount.exists() or not self.is_mount(self.mount):
            if not self.gap:
                self._event("audit_backup_gap", mount=str(self.mount))
                self.gap = True
            return False
        if self.gap:
            self._event("audit_backup_recovered", mount=str(self.mount))
            self.gap = False
        for name, source in self.sources.items():
            self._copy_source(name, source)
        self._save_cursors()
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=Path,
                        default=Path("/var/log/agent-sessions/tlog.jsonl"))
    parser.add_argument("--events", type=Path,
                        default=Path("/var/log/rover-audit/events.jsonl"))
    parser.add_argument("--mount", type=Path, default=Path("/mnt/robot-audit"))
    parser.add_argument("--cursor", type=Path,
                        default=Path("/var/lib/rover-bean-audit/cursors.json"))
    parser.add_argument("--interval", type=float, default=0.25)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    backup = AuditBackup(
        {"agent-sessions": args.sessions, "rover-audit-events": args.events},
        args.mount,
        args.cursor,
        args.events,
    )
    if args.once:
        raise SystemExit(0 if backup.run_once() else 2)
    while True:
        backup.run_once()
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
