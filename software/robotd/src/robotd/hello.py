"""Bench wake-up script: Rover Bean says hello by looking around, head only.

This is the mid-build milestone check, not a control surface. It talks to an
already-running robotd exactly like robotctl does, so every command crosses the
same firmware envelope and lands in the blackbox with source "hello". It never
starts robotd and it never touches the drive base.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import shutil
import subprocess
import uuid

PAN_SWEEP_CDEG = 2000  # +/-20 degrees: a gentle look, nowhere near the firmware cap
TILT_UP_CDEG = 800     # +8 degrees: a small, friendly glance upward
STEP_CDEG = 400        # pan glide step so the sweep is slow, not a snap


def say(message: str) -> None:
    print(message, flush=True)


def play_greeting(sound: Path) -> None:
    """Play one user-supplied WAV if a system player exists. Never required."""
    player = shutil.which("afplay") or shutil.which("aplay")
    if not player:
        say("(No sound player found on this machine, so Rover Bean stays quiet.)")
        return
    subprocess.run([player, str(sound)], check=False)


class HelloSession:
    """One Unix-socket connection to robotd, request/response per line."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

    async def call(self, op: str, **fields: object) -> dict:
        request = {"id": uuid.uuid4().hex, "op": op, "source": "hello", **fields}
        self.writer.write((json.dumps(request, separators=(",", ":")) + "\n").encode())
        await self.writer.drain()
        response = json.loads(await asyncio.wait_for(self.reader.readline(), 5))
        if not response.get("ok"):
            raise SystemExit(f"robotd said no: {response.get('error', 'unknown error')}")
        return response.get("result", {})

    async def head(self, pan_cdeg: int, tilt_cdeg: int) -> None:
        await self.call("head", pan_cdeg=pan_cdeg, tilt_cdeg=tilt_cdeg)

    async def glide_pan(self, start_cdeg: int, end_cdeg: int, tilt_cdeg: int,
                        step_pause: float) -> None:
        step = STEP_CDEG if end_cdeg > start_cdeg else -STEP_CDEG
        for pan in range(start_cdeg + step, end_cdeg, step):
            await self.head(pan, tilt_cdeg)
            await asyncio.sleep(step_pause)
        await self.head(end_cdeg, tilt_cdeg)

    async def report_head(self) -> None:
        status = await self.call("status")
        firmware = status.get("firmware") or {}
        if "pan_cdeg" in firmware:
            say(f"  (head is at pan {firmware['pan_cdeg'] / 100:.1f} deg, "
                f"tilt {firmware['tilt_cdeg'] / 100:.1f} deg)")


async def run_hello(socket_path: Path, sound: Path | None,
                    step_pause: float = 0.15, pose_pause: float = 0.6) -> None:
    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
    except OSError as exc:
        raise SystemExit(
            f"Rover Bean is not answering at {socket_path} ({exc}).\n"
            "Start robotd yourself first, then run robot-hello again.")
    session = HelloSession(reader, writer)
    try:
        status = await session.call("status")
        if not status.get("connected"):
            raise SystemExit(
                "robotd is running, but the firmware link is down, so the head "
                "cannot move. Check the Pico connection (or --simulate) and try again.")
        say("Rover Bean is waking up...")
        if sound:
            play_greeting(sound)
        say("Centering the head.")
        await session.head(0, 0)
        await asyncio.sleep(pose_pause)
        say("Rover Bean is looking around... first to the left.")
        await session.glide_pan(0, -PAN_SWEEP_CDEG, 0, step_pause)
        await asyncio.sleep(pose_pause)
        await session.report_head()
        say("Now to the right.")
        await session.glide_pan(-PAN_SWEEP_CDEG, PAN_SWEEP_CDEG, 0, step_pause)
        await asyncio.sleep(pose_pause)
        await session.report_head()
        say("And back to the middle.")
        await session.glide_pan(PAN_SWEEP_CDEG, 0, 0, step_pause)
        await asyncio.sleep(pose_pause)
        say("A quick look up to say hello.")
        await session.head(0, TILT_UP_CDEG)
        await asyncio.sleep(pose_pause)
        say("Settling back to center.")
        await session.head(0, 0)
        await asyncio.sleep(pose_pause)
        await session.report_head()
        say("That's the whole hello. Rover Bean is awake and listening.")
    finally:
        writer.close()
        await writer.wait_closed()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", type=Path, default=Path("/run/robotd/robotd.sock"))
    parser.add_argument("--sound", type=Path,
                        help="optional WAV played via afplay/aplay; silent by default")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    asyncio.run(run_hello(args.socket, args.sound))


if __name__ == "__main__":
    main()
