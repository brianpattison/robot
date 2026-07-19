#!/usr/bin/env python3
"""Capture the builder's-book dashboard screenshot from a real bench session.

Boots `robotd --simulate` plus `robot-dashboard` in a throwaway venv-installed
environment, replays the short deterministic supervision session shown in the
book (head aim, a driven-then-released setpoint, a stop), waits for the page's
live SSE state, and screenshots it with headless Chrome into
`docs/images/guide_v2/dashboard_bench.png`.

The image is therefore always the shipped dashboard talking to the shipped
simulator over the real socket protocol — never a mockup. Rerun after any
dashboard UI change:

    python3 scripts/capture_dashboard_screenshot.py

Requires: a Python with `software/robotd` + `software/dashboard` installed
(pass its bin dir via --bin, or let the script build a temp venv), and desktop
Chrome for the capture, same as the PDF generator.
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = ROOT / "docs" / "images" / "guide_v2" / "dashboard_bench.png"
PORT = 8072  # the documented default; the page renders its own URL nowhere.


def wait_for(predicate, timeout_s: float, what: str) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise SystemExit(f"timed out waiting for {what}")


def http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            return response.status == 200
    except OSError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bin",
        type=Path,
        default=None,
        help="bin directory containing robotd/robotctl/robot-dashboard "
        "(default: build a temporary venv)",
    )
    args = parser.parse_args()

    if http_ok(f"http://127.0.0.1:{PORT}/"):
        raise SystemExit(
            f"something already serves 127.0.0.1:{PORT} — stop it first, or the "
            "capture would silently photograph the wrong session")

    with tempfile.TemporaryDirectory(prefix="rb-dash-shot-") as tmp:
        tmpdir = Path(tmp)
        if args.bin is None:
            venv = tmpdir / "venv"
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
            subprocess.run(
                [str(venv / "bin" / "pip"), "install", "-q",
                 "-e", str(ROOT / "software" / "robotd"),
                 "-e", str(ROOT / "software" / "dashboard")],
                check=True,
            )
            bindir = venv / "bin"
        else:
            bindir = args.bin

        # AF_UNIX paths must stay short (macOS ~104 bytes): keep the socket in
        # /tmp directly rather than under the (long) temp directory.
        sock = Path(tempfile.mktemp(prefix="rbshot-", suffix=".sock", dir="/tmp"))
        blackbox = tmpdir / "blackbox.jsonl"
        procs: list[subprocess.Popen] = []
        try:
            procs.append(subprocess.Popen(
                [str(bindir / "robotd"), "--simulate",
                 "--socket", str(sock), "--blackbox", str(blackbox)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            wait_for(sock.exists, 10, "robotd socket")

            def ctl(*words: str) -> None:
                subprocess.run(
                    [str(bindir / "robotctl"), "--socket", str(sock),
                     "--source", "agent", *words],
                    check=True, stdout=subprocess.DEVNULL)

            # The short supervision session the book narrates.
            ctl("status")
            ctl("head", "2500", "-800")
            ctl("drive", "120", "0")
            time.sleep(0.35)  # let the 250 ms lease zero the setpoint
            ctl("stop")

            procs.append(subprocess.Popen(
                [str(bindir / "robot-dashboard"), "--socket", str(sock),
                 "--blackbox", str(blackbox), "--port", str(PORT)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            url = f"http://127.0.0.1:{PORT}/"
            wait_for(lambda: http_ok(url), 10, "dashboard HTTP")
            time.sleep(2.0)  # SSE settle: status, flags, and blackbox tail

            OUT.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [CHROME, "--headless=new", "--disable-gpu",
                 "--force-device-scale-factor=2",
                 "--window-size=1600,1000", "--hide-scrollbars",
                 f"--screenshot={OUT}", url],
                check=True, capture_output=True, timeout=120)
            if not OUT.exists() or OUT.stat().st_size < 50_000:
                raise SystemExit("screenshot missing or implausibly small")
            records = [json.loads(line)
                       for line in blackbox.read_text().splitlines()]
            seen = {record["kind"] for record in records}
            seen.update(record.get("operation", "") for record in records)
            for required in ("robotd_start", "head", "drive", "stop"):
                if required not in seen:
                    raise SystemExit(
                        f"expected blackbox record {required!r} missing — "
                        "the captured session is not the one the book narrates")
            print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
        finally:
            for proc in procs:
                proc.terminate()
            for proc in procs:
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            sock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
