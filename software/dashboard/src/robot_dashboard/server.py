"""Localhost supervision dashboard: a read-mostly HTTP client of robotd.

The dashboard is a development and supervision tool, not a safety device. It
talks to the local robotd Unix socket exactly like any other client, so the
Pico firmware envelope (clamps, leases, watchdog, latched stops) applies to
everything this page can send. It cannot clear an E-stop, bypass the bumper
rule, or exceed the firmware caps.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import ipaddress
import json
from pathlib import Path
import signal
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .ui import DASHBOARD_HTML

# Mirror of firmware/pico2-safety/include/safety_core.h; keep bit order identical.
SAFETY_FLAGS: tuple[tuple[str, int], ...] = (
    ("estop_latched", 1 << 0),
    ("charger_present", 1 << 1),
    ("low_battery", 1 << 2),
    ("heartbeat_stale", 1 << 3),
    ("motion_lease_stale", 1 << 4),
    ("bumper_latched", 1 << 5),
    ("wiring_fault", 1 << 6),
    ("motor_enable", 1 << 7),
)

# Fixed bench-baseline firmware caps (docs/body-protocol-v1.md). The dashboard
# clamps to the same values only so the UI never claims to request more than
# the firmware will apply; the firmware clamp remains authoritative.
LINEAR_CAP_MM_S = 350
ANGULAR_CAP_MRAD_S = 1500
PAN_CAP_CDEG = 6000
TILT_CAP_CDEG = 2000
BUMPER_ZONES = 6

MAX_BODY_BYTES = 64 * 1024
MAX_BLACKBOX_TAIL = 500


class DashboardError(Exception):
    pass


def decode_flags(flags: int) -> dict[str, bool]:
    return {name: bool(flags & bit) for name, bit in SAFETY_FLAGS}


def decode_bumpers(released_mask: int, latched_mask: int) -> list[dict[str, Any]]:
    zones = []
    for zone in range(BUMPER_ZONES):
        bit = 1 << zone
        zones.append({
            "zone": zone,
            "loop_closed": bool(released_mask & bit),
            "latched": bool(latched_mask & bit),
        })
    return zones


def derive_display_state(status: dict[str, Any]) -> str:
    """Coarse human label. Safety conditions win; the flags stay visible anyway."""
    if not status.get("connected"):
        return "firmware link down"
    firmware = status.get("firmware") or {}
    flags = decode_flags(int(firmware.get("flags", 0)))
    if flags["estop_latched"]:
        return "E-stop latched"
    if flags["wiring_fault"]:
        return "bumper loop open"
    if flags["bumper_latched"]:
        return "bumper latched"
    if flags["charger_present"]:
        return "charger inhibit"
    if flags["low_battery"]:
        return "low battery"
    if flags["heartbeat_stale"]:
        return "host heartbeat stale"
    if firmware.get("linear_mm_s") or firmware.get("angular_mrad_s"):
        return "driving"
    return "idle (stopped)"


def clamp(value: int, cap: int) -> int:
    return max(-cap, min(cap, value))


class RobotdProxy:
    """One-shot Unix-socket client mirroring robotctl's request shape."""

    def __init__(self, socket_path: Path, timeout: float = 1.0) -> None:
        self.socket_path = socket_path
        self.timeout = timeout
        self._counter = 0

    async def call(self, op: str, **fields: Any) -> dict[str, Any]:
        self._counter += 1
        request = {"id": f"dashboard-{self._counter}", "op": op, "source": "dashboard", **fields}
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(str(self.socket_path)), self.timeout)
        except (OSError, asyncio.TimeoutError) as exc:
            raise DashboardError(f"robotd unreachable at {self.socket_path}: {exc}") from exc
        try:
            writer.write((json.dumps(request, separators=(",", ":")) + "\n").encode())
            await writer.drain()
            line = await asyncio.wait_for(reader.readline(), self.timeout)
        except (OSError, asyncio.TimeoutError) as exc:
            raise DashboardError(f"robotd request failed: {exc}") from exc
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
        if not line:
            raise DashboardError("robotd closed the connection without a response")
        response = json.loads(line)
        if not response.get("ok"):
            raise DashboardError(str(response.get("error", "robotd rejected the request")))
        return response.get("result", {})


class BlackboxTail:
    """Incremental reader of the append-only robotd blackbox JSONL."""

    def __init__(self, path: Path | None) -> None:
        self.path = path
        self.offset = 0

    def read_new(self) -> list[dict[str, Any]]:
        if not self.path or not self.path.exists():
            return []
        size = self.path.stat().st_size
        if size < self.offset:
            self.offset = 0  # rotation or truncation: restart from the top
        if size == self.offset:
            return []
        with self.path.open("rb") as stream:
            stream.seek(self.offset)
            data = stream.read(size - self.offset)
        # Only consume complete lines so a mid-write read never splits a record.
        last_newline = data.rfind(b"\n")
        if last_newline < 0:
            return []
        self.offset += last_newline + 1
        records = []
        for raw in data[:last_newline].splitlines():
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError:
                records.append({"kind": "unparsed_blackbox_line", "raw": raw.decode("utf-8", "replace")})
        return records

    def tail(self, limit: int) -> list[dict[str, Any]]:
        if not self.path or not self.path.exists():
            return []
        lines = self.path.read_bytes().splitlines()
        records = []
        for raw in lines[-limit:]:
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError:
                records.append({"kind": "unparsed_blackbox_line", "raw": raw.decode("utf-8", "replace")})
        return records


def is_loopback_host(host: str) -> bool:
    if host in ("localhost",):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def require_permitted_bind(host: str, expose_lan: bool) -> None:
    if is_loopback_host(host):
        return
    if not expose_lan:
        raise SystemExit(
            f"refusing to bind non-loopback host {host!r}: the MVP dashboard is local-only. "
            "Pass --expose-lan only for a deliberately shared bench network.")


@dataclass
class HttpRequest:
    method: str
    target: str
    headers: dict[str, str]
    body: bytes

    @property
    def path(self) -> str:
        return urlsplit(self.target).path

    @property
    def query(self) -> dict[str, list[str]]:
        return parse_qs(urlsplit(self.target).query)

    def json_body(self) -> dict[str, Any]:
        if not self.body:
            return {}
        parsed = json.loads(self.body)
        if not isinstance(parsed, dict):
            raise ValueError("request body must be a JSON object")
        return parsed


class DashboardServer:
    def __init__(self, proxy: RobotdProxy, blackbox: BlackboxTail,
                 host: str = "127.0.0.1", port: int = 8072) -> None:
        self.proxy = proxy
        self.blackbox = blackbox
        self.host = host
        self.port = port
        self.server: asyncio.AbstractServer | None = None
        self.stopping = asyncio.Event()

    # -- HTTP plumbing -----------------------------------------------------

    @staticmethod
    async def _read_request(reader: asyncio.StreamReader) -> HttpRequest | None:
        request_line = await reader.readline()
        if not request_line:
            return None
        parts = request_line.decode("latin-1").split()
        if len(parts) != 3:
            raise DashboardError("malformed HTTP request line")
        method, target, _version = parts
        headers: dict[str, str] = {}
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
            name, _, value = line.decode("latin-1").partition(":")
            headers[name.strip().lower()] = value.strip()
        length = int(headers.get("content-length", "0") or "0")
        if length > MAX_BODY_BYTES:
            raise DashboardError("request body too large")
        body = await reader.readexactly(length) if length else b""
        return HttpRequest(method.upper(), target, headers, body)

    @staticmethod
    def _response_bytes(status: str, content_type: str, body: bytes,
                        extra_headers: tuple[str, ...] = ()) -> bytes:
        headers = [f"HTTP/1.1 {status}", f"Content-Type: {content_type}",
                   f"Content-Length: {len(body)}", "Cache-Control: no-store",
                   "Connection: close", *extra_headers, "", ""]
        return "\r\n".join(headers).encode("latin-1") + body

    async def _send_json(self, writer: asyncio.StreamWriter, payload: dict[str, Any],
                         status: str = "200 OK") -> None:
        body = json.dumps(payload, sort_keys=True).encode()
        writer.write(self._response_bytes(status, "application/json", body))
        await writer.drain()

    # -- API handlers ------------------------------------------------------

    async def _status_payload(self) -> dict[str, Any]:
        try:
            status = await self.proxy.call("status")
        except DashboardError as exc:
            return {"robotd_reachable": False, "error": str(exc),
                    "display_state": "robotd unreachable"}
        firmware = status.get("firmware") or {}
        payload: dict[str, Any] = {"robotd_reachable": True, **status}
        payload["display_state"] = derive_display_state(status)
        if firmware:
            payload["safety_flags"] = decode_flags(int(firmware.get("flags", 0)))
            payload["bumpers"] = decode_bumpers(int(firmware.get("released_mask", 0)),
                                                int(firmware.get("latched_mask", 0)))
        return payload

    async def _handle_command(self, request: HttpRequest) -> dict[str, Any]:
        body = request.json_body()
        op = request.path.removeprefix("/api/")
        if op == "drive":
            sent = {"linear_mm_s": clamp(int(body.get("linear_mm_s", 0)), LINEAR_CAP_MM_S),
                    "angular_mrad_s": clamp(int(body.get("angular_mrad_s", 0)), ANGULAR_CAP_MRAD_S)}
            result = await self.proxy.call("drive", **sent)
        elif op == "head":
            sent = {"pan_cdeg": clamp(int(body.get("pan_cdeg", 0)), PAN_CAP_CDEG),
                    "tilt_cdeg": clamp(int(body.get("tilt_cdeg", 0)), TILT_CAP_CDEG)}
            result = await self.proxy.call("head", **sent)
        elif op == "stop":
            sent = {}
            result = await self.proxy.call("stop")
        elif op == "clear_bumper":
            sent = {"zone_mask": int(body.get("zone_mask", 0))}
            result = await self.proxy.call("clear_bumper", **sent)
        else:
            raise DashboardError(f"unknown command {op!r}")
        return {"ok": True, "sent": sent, "result": result}

    async def _stream_events(self, writer: asyncio.StreamWriter) -> None:
        headers = ["HTTP/1.1 200 OK", "Content-Type: text/event-stream",
                   "Cache-Control: no-store", "Connection: close", "", ""]
        writer.write("\r\n".join(headers).encode("latin-1"))
        await writer.drain()

        def event(name: str, payload: Any) -> bytes:
            return f"event: {name}\ndata: {json.dumps(payload, sort_keys=True)}\n\n".encode()

        writer.write(event("blackbox", self.blackbox.tail(50)))
        last_sent: str | None = None
        last_emit = 0.0
        loop = asyncio.get_running_loop()
        try:
            while not self.stopping.is_set():
                payload = await self._status_payload()
                encoded = json.dumps(payload, sort_keys=True)
                now = loop.time()
                if encoded != last_sent or now - last_emit >= 2.0:
                    writer.write(event("status", payload))
                    last_sent, last_emit = encoded, now
                new_records = await asyncio.to_thread(self.blackbox.read_new)
                if new_records:
                    writer.write(event("blackbox", new_records))
                await writer.drain()
                await asyncio.sleep(0.2)
        except (ConnectionResetError, BrokenPipeError, OSError):
            return

    # -- dispatch ----------------------------------------------------------

    @staticmethod
    def _host_header_is_local(request: HttpRequest) -> bool:
        host = request.headers.get("host", "")
        if host.startswith("["):  # [::1]:port
            name = host.partition("]")[0].lstrip("[")
        else:
            name = host.partition(":")[0]
        return is_loopback_host(name)

    async def _dispatch(self, request: HttpRequest, writer: asyncio.StreamWriter) -> None:
        # Browsers attach the page's Host; a DNS-rebinding page arrives with a
        # foreign one. Only enforced for the default loopback bind.
        if is_loopback_host(self.host) and not self._host_header_is_local(request):
            await self._send_json(writer, {"ok": False,
                                           "error": "rejected non-local Host header"},
                                  status="403 Forbidden")
            return
        if request.method == "POST" and not request.headers.get(
                "content-type", "").startswith("application/json"):
            # Cross-origin "simple" requests cannot carry this content type, so
            # requiring it forces a CORS preflight this server never grants.
            await self._send_json(writer, {"ok": False,
                                           "error": "POST requires Content-Type: application/json"},
                                  status="415 Unsupported Media Type")
            return
        if request.method == "GET" and request.path == "/":
            writer.write(self._response_bytes("200 OK", "text/html; charset=utf-8",
                                              DASHBOARD_HTML.encode()))
            await writer.drain()
        elif request.method == "GET" and request.path == "/api/status":
            await self._send_json(writer, await self._status_payload())
        elif request.method == "GET" and request.path == "/api/blackbox":
            limit_raw = (request.query.get("lines") or ["100"])[0]
            limit = max(1, min(MAX_BLACKBOX_TAIL, int(limit_raw)))
            records = await asyncio.to_thread(self.blackbox.tail, limit)
            await self._send_json(writer, {"records": records})
        elif request.method == "GET" and request.path == "/api/events":
            await self._stream_events(writer)
        elif request.method == "POST" and request.path in (
                "/api/drive", "/api/head", "/api/stop", "/api/clear_bumper"):
            await self._send_json(writer, await self._handle_command(request))
        else:
            await self._send_json(writer, {"ok": False, "error": "not found"},
                                  status="404 Not Found")

    async def _handle_client(self, reader: asyncio.StreamReader,
                             writer: asyncio.StreamWriter) -> None:
        try:
            request = await self._read_request(reader)
            if request is None:
                return
            try:
                await self._dispatch(request, writer)
            except (DashboardError, ValueError, json.JSONDecodeError) as exc:
                await self._send_json(writer, {"ok": False, "error": str(exc)},
                                      status="400 Bad Request")
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError, OSError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    # -- lifecycle ---------------------------------------------------------

    async def start(self) -> tuple[str, int]:
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        bound = self.server.sockets[0].getsockname()
        return bound[0], bound[1]

    async def run(self) -> None:
        host, port = await self.start()
        print(f"DASHBOARD_LISTENING {host} {port}", flush=True)
        await self.stopping.wait()
        assert self.server is not None
        self.server.close()
        await self.server.wait_closed()

    def stop(self) -> None:
        self.stopping.set()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", type=Path, default=Path("/run/robotd/robotd.sock"),
                        help="robotd Unix socket path")
    parser.add_argument("--blackbox", type=Path, default=Path("/var/log/robotd/blackbox.jsonl"),
                        help="robotd blackbox JSONL to tail read-only")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8072)
    parser.add_argument("--expose-lan", action="store_true",
                        help="required to bind a non-loopback host")
    return parser.parse_args(argv)


async def async_main(args: argparse.Namespace) -> None:
    server = DashboardServer(RobotdProxy(args.socket), BlackboxTail(args.blackbox),
                             args.host, args.port)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, server.stop)
    await server.run()


def main() -> None:
    args = parse_args()
    require_permitted_bind(args.host, args.expose_lan)
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
