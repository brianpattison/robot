"""Local Unix-socket body daemon with UART heartbeat and JSONL blackbox."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import time
from typing import Any

from .protocol import Frame, FrameParser, MessageType, decode_status, drive_frame, head_frame
from .transport import SerialTransport, SimulatorTransport, Transport


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Blackbox:
    def __init__(self, local_path: Path, mirror_path: Path | None = None) -> None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.local_path = local_path
        self.mirror_path = mirror_path
        self.mirror_gap = False
        self.lock = asyncio.Lock()

    @staticmethod
    def _append(path: Path, encoded: str) -> None:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())

    @staticmethod
    def _health_record(kind: str, **fields: Any) -> str:
        record = {"ts": utc_now(), "monotonic_ns": time.monotonic_ns(), "kind": kind, **fields}
        return json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"

    def _write_sync(self, encoded: str) -> None:
        self._append(self.local_path, encoded)
        if not self.mirror_path:
            return
        try:
            if not self.mirror_path.parent.exists() or not os.path.ismount(self.mirror_path.parent):
                raise OSError(f"audit mirror is not mounted: {self.mirror_path.parent}")
            if self.mirror_gap:
                recovered = self._health_record("audit_mirror_recovered",
                                                mirror=str(self.mirror_path))
                self._append(self.local_path, recovered)
                self._append(self.mirror_path, recovered)
                self.mirror_gap = False
            self._append(self.mirror_path, encoded)
        except OSError as exc:
            if not self.mirror_gap:
                gap = self._health_record("audit_mirror_gap", mirror=str(self.mirror_path),
                                          error=str(exc))
                self._append(self.local_path, gap)
                self.mirror_gap = True

    async def write(self, kind: str, **fields: Any) -> None:
        record = {"ts": utc_now(), "monotonic_ns": time.monotonic_ns(), "kind": kind, **fields}
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        async with self.lock:
            await asyncio.to_thread(self._write_sync, encoded)


@dataclass
class RobotState:
    connected: bool = False
    last_status_monotonic: float = 0.0
    firmware: dict[str, int] = field(default_factory=dict)
    last_error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        age_ms = None
        if self.last_status_monotonic:
            age_ms = round((time.monotonic() - self.last_status_monotonic) * 1000)
        return {
            "connected": self.connected,
            "status_age_ms": age_ms,
            "firmware": self.firmware,
            "last_error": self.last_error,
        }


class RobotDaemon:
    def __init__(self, transport: Transport, socket_path: Path, blackbox: Blackbox) -> None:
        self.transport = transport
        self.socket_path = socket_path
        self.blackbox = blackbox
        self.state = RobotState()
        self.parser = FrameParser()
        self.sequence = 0
        self.server: asyncio.AbstractServer | None = None
        self.tasks: list[asyncio.Task] = []
        self.stopping = asyncio.Event()

    def next_sequence(self) -> int:
        self.sequence = (self.sequence + 1) & 0xFFFF
        return self.sequence

    def send(self, frame: Frame) -> None:
        self.transport.write(frame.encode())

    async def heartbeat_loop(self) -> None:
        period = 0.05
        while not self.stopping.is_set():
            started = time.monotonic()
            self.send(Frame(MessageType.HEARTBEAT, self.next_sequence()))
            await asyncio.sleep(max(0, period - (time.monotonic() - started)))

    @staticmethod
    def _without_uptime_tick(status: dict[str, int]) -> dict[str, int]:
        # uptime_ms advances in every frame; treating it as a change would turn
        # the blackbox into a 10 Hz ticker instead of a state-change journal.
        return {key: value for key, value in status.items() if key != "uptime_ms"}

    async def serial_loop(self) -> None:
        request_at = 0.0
        while not self.stopping.is_set():
            now = time.monotonic()
            if now - request_at >= 0.1:
                self.send(Frame(MessageType.STATUS_REQUEST, self.next_sequence()))
                request_at = now
            for frame in self.parser.feed(self.transport.read(0.0)):
                if frame.message_type == MessageType.STATUS:
                    try:
                        new_status = decode_status(frame.payload)
                    except ValueError as exc:
                        self.state.last_error = str(exc)
                        await self.blackbox.write("protocol_error", error=str(exc))
                        continue
                    if self._without_uptime_tick(new_status) != self._without_uptime_tick(
                            self.state.firmware):
                        await self.blackbox.write("firmware_status", status=new_status)
                    self.state.firmware = new_status
                    self.state.last_status_monotonic = time.monotonic()
                    self.state.connected = True
            if self.state.last_status_monotonic and now - self.state.last_status_monotonic > 0.5:
                self.state.connected = False
            await asyncio.sleep(0.01)

    async def process(self, request: dict[str, Any]) -> dict[str, Any]:
        op = request.get("op")
        source = str(request.get("source", "unknown"))[:128]
        if op == "status":
            response = self.state.as_dict()
        elif op == "drive":
            linear = int(request["linear_mm_s"])
            angular = int(request["angular_mrad_s"])
            self.send(drive_frame(self.next_sequence(), linear, angular))
            response = {"accepted": True, "firmware_clamps": True, "lease_ms": 250}
        elif op == "head":
            pan = int(request["pan_cdeg"])
            tilt = int(request["tilt_cdeg"])
            self.send(head_frame(self.next_sequence(), pan, tilt))
            response = {"accepted": True, "firmware_clamps": True}
        elif op == "stop":
            self.send(Frame(MessageType.STOP, self.next_sequence()))
            response = {"accepted": True}
        elif op == "clear_bumper":
            mask = int(request["zone_mask"])
            if not 0 <= mask <= 0x3F:
                raise ValueError("zone_mask must be 0..63")
            self.send(Frame(MessageType.CLEAR_BUMPER, self.next_sequence(), bytes([mask])))
            response = {"accepted": True, "requested_mask": mask}
        else:
            raise ValueError(f"unsupported operation {op!r}")
        if op != "status":
            # Read-only status queries change nothing; logging every supervision
            # poll would drown the action audit trail and grind the SD card.
            await self.blackbox.write("command", source=source, operation=op,
                                      request={k: v for k, v in request.items() if k != "id"},
                                      response=response)
        return response

    async def handle_client(self, reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter) -> None:
        try:
            while line := await reader.readline():
                request_id = None
                try:
                    request = json.loads(line)
                    request_id = request.get("id")
                    result = await self.process(request)
                    response = {"id": request_id, "ok": True, "result": result}
                except Exception as exc:  # client boundary: always return structured error
                    response = {"id": request_id, "ok": False, "error": str(exc)}
                    await self.blackbox.write("command_error", error=str(exc))
                writer.write((json.dumps(response, separators=(",", ":")) + "\n").encode())
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def run(self) -> None:
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        self.socket_path.unlink(missing_ok=True)
        self.send(Frame(MessageType.STOP, self.next_sequence()))
        await self.blackbox.write("robotd_start", socket=str(self.socket_path))
        self.server = await asyncio.start_unix_server(self.handle_client, path=self.socket_path)
        os.chmod(self.socket_path, 0o660)
        self.tasks = [asyncio.create_task(self.heartbeat_loop()),
                      asyncio.create_task(self.serial_loop())]
        for task in self.tasks:
            task.add_done_callback(self._background_done)
        await self.stopping.wait()
        self.server.close()
        await self.server.wait_closed()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.send(Frame(MessageType.STOP, self.next_sequence()))
        self.transport.close()
        self.socket_path.unlink(missing_ok=True)
        await self.blackbox.write("robotd_stop")

    def stop(self) -> None:
        self.stopping.set()

    def _background_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        error = task.exception()
        if error:
            self.state.last_error = f"background task failed: {error}"
            self.stopping.set()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--device", help="Pico UART device, for example /dev/serial0")
    mode.add_argument("--simulate", action="store_true", help="run the deterministic protocol simulator")
    parser.add_argument("--socket", type=Path, default=Path("/run/robotd/robotd.sock"))
    parser.add_argument("--blackbox", type=Path, default=Path("/var/log/robotd/blackbox.jsonl"))
    parser.add_argument("--mirror", type=Path, help="second append-only/off-host JSONL path")
    return parser.parse_args()


async def async_main(args: argparse.Namespace) -> None:
    transport: Transport = SimulatorTransport() if args.simulate else SerialTransport(args.device)
    daemon = RobotDaemon(transport, args.socket, Blackbox(args.blackbox, args.mirror))
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, daemon.stop)
    await daemon.run()


def main() -> None:
    asyncio.run(async_main(parse_args()))


if __name__ == "__main__":
    main()
