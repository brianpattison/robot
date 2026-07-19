import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from robot_dashboard.server import (BlackboxTail, DashboardServer, RobotdProxy, decode_flags,
                                    derive_display_state, require_permitted_bind)
from robotd.daemon import Blackbox, RobotDaemon
from robotd.transport import SimulatorTransport


async def http_request(port: int, method: str, path: str, body: dict | None = None) -> tuple[int, bytes]:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    encoded = json.dumps(body).encode() if body is not None else b""
    request = (f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n"
               f"Content-Type: application/json\r\nContent-Length: {len(encoded)}\r\n"
               "Connection: close\r\n\r\n").encode() + encoded
    writer.write(request)
    await writer.drain()
    raw = await asyncio.wait_for(reader.read(-1), 5)
    writer.close()
    await writer.wait_closed()
    head, _, payload = raw.partition(b"\r\n\r\n")
    status = int(head.split(b" ", 2)[1])
    return status, payload


async def http_json(port: int, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    status, payload = await http_request(port, method, path, body)
    return status, json.loads(payload)


class DashboardStackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="dashboard-test-")
        root = Path(self.temp.name)
        self.socket_path = root / "robotd.sock"
        self.blackbox_path = root / "blackbox.jsonl"
        self.daemon = RobotDaemon(SimulatorTransport(), self.socket_path,
                                  Blackbox(self.blackbox_path))
        self.daemon_task = asyncio.create_task(self.daemon.run())
        for _ in range(200):
            if self.socket_path.exists():
                break
            await asyncio.sleep(0.01)
        self.assertTrue(self.socket_path.exists())
        self.dashboard = DashboardServer(RobotdProxy(self.socket_path),
                                         BlackboxTail(self.blackbox_path), "127.0.0.1", 0)
        _, self.port = await self.dashboard.start()

    async def asyncTearDown(self) -> None:
        self.dashboard.stop()
        assert self.dashboard.server is not None
        self.dashboard.server.close()
        await self.dashboard.server.wait_closed()
        self.daemon.stop()
        await asyncio.wait_for(self.daemon_task, 2)
        self.temp.cleanup()

    async def wait_for_firmware_link(self) -> dict:
        for _ in range(100):
            _, payload = await http_json(self.port, "GET", "/api/status")
            if payload.get("connected"):
                return payload
            await asyncio.sleep(0.02)
        self.fail("robotd never reported a firmware link from the simulator")

    async def test_index_page_serves_supervision_ui(self) -> None:
        status, payload = await http_request(self.port, "GET", "/")
        self.assertEqual(status, 200)
        text = payload.decode()
        self.assertIn("Rover Bean Dashboard", text)
        self.assertIn("Supervision tool only", text)
        self.assertIn("cannot", text)
        self.assertIn("No camera stream on the bench baseline", text)

    async def test_status_decodes_flags_and_bumpers(self) -> None:
        payload = await self.wait_for_firmware_link()
        self.assertTrue(payload["robotd_reachable"])
        self.assertEqual(payload["display_state"], "idle (stopped)")
        self.assertFalse(payload["safety_flags"]["motor_enable"])
        self.assertFalse(payload["safety_flags"]["estop_latched"])
        zones = payload["bumpers"]
        self.assertEqual(len(zones), 6)
        self.assertTrue(all(zone["loop_closed"] and not zone["latched"] for zone in zones))

    async def test_drive_is_clamped_applied_logged_and_expires(self) -> None:
        await self.wait_for_firmware_link()
        status, response = await http_json(self.port, "POST", "/api/drive",
                                           {"linear_mm_s": 9999, "angular_mrad_s": -9999})
        self.assertEqual(status, 200)
        self.assertEqual(response["sent"], {"linear_mm_s": 350, "angular_mrad_s": -1500})
        self.assertTrue(response["result"]["firmware_clamps"])
        for _ in range(50):
            _, payload = await http_json(self.port, "GET", "/api/status")
            if payload["firmware"].get("linear_mm_s") == 350:
                break
            await asyncio.sleep(0.02)
        self.assertEqual(payload["firmware"]["linear_mm_s"], 350)
        self.assertEqual(payload["display_state"], "driving")
        await asyncio.sleep(0.4)  # single setpoint: the simulator's 250 ms lease expires it
        _, payload = await http_json(self.port, "GET", "/api/status")
        self.assertEqual(payload["firmware"]["linear_mm_s"], 0)
        self.assertEqual(payload["firmware"]["angular_mrad_s"], 0)
        records = [json.loads(line) for line in self.blackbox_path.read_text().splitlines()]
        drive = [r for r in records if r.get("operation") == "drive"]
        self.assertTrue(drive)
        self.assertEqual(drive[-1]["source"], "dashboard")
        self.assertEqual(drive[-1]["request"]["linear_mm_s"], 350)

    async def test_head_and_stop_round_trip(self) -> None:
        await self.wait_for_firmware_link()
        status, response = await http_json(self.port, "POST", "/api/head",
                                           {"pan_cdeg": 9000, "tilt_cdeg": -9000})
        self.assertEqual(status, 200)
        self.assertEqual(response["sent"], {"pan_cdeg": 6000, "tilt_cdeg": -2000})
        for _ in range(50):
            _, payload = await http_json(self.port, "GET", "/api/status")
            if payload["firmware"].get("pan_cdeg") == 6000:
                break
            await asyncio.sleep(0.02)
        self.assertEqual(payload["firmware"]["pan_cdeg"], 6000)
        self.assertEqual(payload["firmware"]["tilt_cdeg"], -2000)
        status, response = await http_json(self.port, "POST", "/api/stop")
        self.assertEqual(status, 200)
        self.assertTrue(response["result"]["accepted"])

    async def test_invalid_clear_bumper_propagates_robotd_error(self) -> None:
        await self.wait_for_firmware_link()
        status, response = await http_json(self.port, "POST", "/api/clear_bumper",
                                           {"zone_mask": 999})
        self.assertEqual(status, 400)
        self.assertFalse(response["ok"])
        self.assertIn("zone_mask", response["error"])

    async def test_blackbox_tail_endpoint_returns_records(self) -> None:
        await self.wait_for_firmware_link()
        await http_json(self.port, "POST", "/api/stop")
        status, payload = await http_json(self.port, "GET", "/api/blackbox?lines=100")
        self.assertEqual(status, 200)
        kinds = [record["kind"] for record in payload["records"]]
        self.assertIn("robotd_start", kinds)
        self.assertIn("command", kinds)

    async def test_event_stream_emits_status_and_blackbox(self) -> None:
        await self.wait_for_firmware_link()
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write(b"GET /api/events HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        await writer.drain()
        collected = b""
        for _ in range(100):
            chunk = await asyncio.wait_for(reader.read(4096), 5)
            if not chunk:
                break
            collected += chunk
            if b"event: status" in collected and b"event: blackbox" in collected:
                break
        writer.close()
        await writer.wait_closed()
        self.assertIn(b"text/event-stream", collected)
        self.assertIn(b"event: blackbox", collected)
        self.assertIn(b"event: status", collected)
        status_line = next(line for line in collected.split(b"\n\n")
                           if line.strip().startswith(b"event: status"))
        payload = json.loads(status_line.split(b"data: ", 1)[1])
        self.assertIn("display_state", payload)

    async def test_unknown_route_is_404(self) -> None:
        status, response = await http_json(self.port, "GET", "/api/nope")
        self.assertEqual(status, 404)
        self.assertFalse(response["ok"])

    async def raw_request(self, request: bytes) -> bytes:
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write(request)
        await writer.drain()
        raw = await asyncio.wait_for(reader.read(-1), 5)
        writer.close()
        await writer.wait_closed()
        return raw

    async def test_foreign_host_header_is_rejected(self) -> None:
        raw = await self.raw_request(
            b"GET /api/status HTTP/1.1\r\nHost: robot.attacker.example\r\n"
            b"Connection: close\r\n\r\n")
        self.assertIn(b"403 Forbidden", raw)
        self.assertIn(b"non-local Host", raw)

    async def test_post_without_json_content_type_is_rejected(self) -> None:
        body = b'{"linear_mm_s": 100, "angular_mrad_s": 0}'
        raw = await self.raw_request(
            b"POST /api/drive HTTP/1.1\r\nHost: 127.0.0.1\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"Connection: close\r\n\r\n" + body)
        self.assertIn(b"415 Unsupported Media Type", raw)
        records = ([] if not self.blackbox_path.exists()
                   else self.blackbox_path.read_text().splitlines())
        drives = [line for line in records if '"operation":"drive"' in line]
        self.assertEqual(drives, [], "a cross-origin-style POST must never reach robotd")


class DashboardUnitTests(unittest.IsolatedAsyncioTestCase):
    async def test_status_reports_robotd_unreachable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dashboard-down-test-") as temp:
            missing_socket = Path(temp) / "missing.sock"
            dashboard = DashboardServer(RobotdProxy(missing_socket, timeout=0.2),
                                        BlackboxTail(None), "127.0.0.1", 0)
            _, port = await dashboard.start()
            try:
                status, payload = await http_json(port, "GET", "/api/status")
            finally:
                dashboard.stop()
                assert dashboard.server is not None
                dashboard.server.close()
                await dashboard.server.wait_closed()
            self.assertEqual(status, 200)
            self.assertFalse(payload["robotd_reachable"])
            self.assertEqual(payload["display_state"], "robotd unreachable")

    def test_flag_decode_matches_firmware_bit_order(self) -> None:
        flags = decode_flags(0x41)
        self.assertTrue(flags["estop_latched"])
        self.assertTrue(flags["wiring_fault"])
        self.assertFalse(flags["motor_enable"])
        self.assertEqual(len(flags), 8)

    def test_display_state_prefers_safety_conditions(self) -> None:
        base = {"connected": True, "firmware": {"flags": 0, "linear_mm_s": 0,
                                                "angular_mrad_s": 0}}
        self.assertEqual(derive_display_state(base), "idle (stopped)")
        base["firmware"]["flags"] = (1 << 5) | (1 << 6)
        self.assertEqual(derive_display_state(base), "bumper loop open")
        base["firmware"]["flags"] = (1 << 0) | (1 << 5)
        self.assertEqual(derive_display_state(base), "E-stop latched")
        self.assertEqual(derive_display_state({"connected": False}), "firmware link down")

    def test_bind_guard_defaults_to_loopback_only(self) -> None:
        require_permitted_bind("127.0.0.1", expose_lan=False)
        require_permitted_bind("::1", expose_lan=False)
        require_permitted_bind("localhost", expose_lan=False)
        with self.assertRaises(SystemExit):
            require_permitted_bind("0.0.0.0", expose_lan=False)
        with self.assertRaises(SystemExit):
            require_permitted_bind("192.168.1.20", expose_lan=False)
        require_permitted_bind("0.0.0.0", expose_lan=True)

    def test_blackbox_tail_reads_incrementally_and_survives_truncation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="dashboard-tail-test-") as temp:
            path = Path(temp) / "blackbox.jsonl"
            tail = BlackboxTail(path)
            self.assertEqual(tail.read_new(), [])
            path.write_text('{"kind":"one"}\n{"kind":"two"}\n')
            self.assertEqual([r["kind"] for r in tail.read_new()], ["one", "two"])
            self.assertEqual(tail.read_new(), [])
            with path.open("a") as stream:
                stream.write('{"kind":"three"}\n{"kind":"part')
            self.assertEqual([r["kind"] for r in tail.read_new()], ["three"])
            with path.open("a") as stream:
                stream.write('ial"}\n')
            self.assertEqual([r["kind"] for r in tail.read_new()], ["partial"])
            path.write_text('{"kind":"fresh"}\n')
            self.assertEqual([r["kind"] for r in tail.read_new()], ["fresh"])


if __name__ == "__main__":
    unittest.main()
