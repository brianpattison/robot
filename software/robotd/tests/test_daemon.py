import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from robotd.daemon import Blackbox, RobotDaemon, parse_args
from robotd.transport import SimulatorTransport


class DaemonTests(unittest.IsolatedAsyncioTestCase):
    async def test_blackbox_records_mirror_gap_and_recovery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="robotd-blackbox-test-") as temp:
            root = Path(temp)
            local = root / "local" / "blackbox.jsonl"
            mirror = root / "mirror" / "blackbox.jsonl"
            mirror.parent.mkdir()
            blackbox = Blackbox(local, mirror)
            mounted = False

            def ismount(_path: object) -> bool:
                return mounted

            with patch("robotd.daemon.os.path.ismount", side_effect=ismount):
                await blackbox.write("first")
                mounted = True
                await blackbox.write("second")

            local_records = [json.loads(line) for line in local.read_text().splitlines()]
            mirror_records = [json.loads(line) for line in mirror.read_text().splitlines()]
            self.assertEqual([record["kind"] for record in local_records],
                             ["first", "audit_mirror_gap", "second", "audit_mirror_recovered"])
            self.assertEqual([record["kind"] for record in mirror_records],
                             ["audit_mirror_recovered", "second"])

    async def test_socket_commands_are_logged_and_motion_expires(self) -> None:
        with tempfile.TemporaryDirectory(prefix="robotd-daemon-test-") as temp:
            root = Path(temp)
            socket = root / "robotd.sock"
            log = root / "blackbox.jsonl"
            daemon = RobotDaemon(SimulatorTransport(), socket, Blackbox(log))
            running = asyncio.create_task(daemon.run())
            for _ in range(100):
                if socket.exists():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(socket.exists())

            async def request(payload: dict) -> dict:
                reader, writer = await asyncio.open_unix_connection(str(socket))
                writer.write((json.dumps(payload) + "\n").encode())
                await writer.drain()
                response = json.loads(await reader.readline())
                writer.close()
                await writer.wait_closed()
                return response

            response = await request({"id": "drive-1", "op": "drive", "source": "test",
                                      "linear_mm_s": 999, "angular_mrad_s": -9999})
            self.assertTrue(response["ok"])
            await asyncio.sleep(0.35)
            status = await request({"id": "status-1", "op": "status", "source": "test"})
            self.assertTrue(status["ok"])
            self.assertEqual(status["result"]["firmware"]["linear_mm_s"], 0)
            self.assertEqual(status["result"]["firmware"]["angular_mrad_s"], 0)

            daemon.stop()
            await asyncio.wait_for(running, 2)
            records = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(records[0]["kind"], "robotd_start")
            self.assertTrue(any(record.get("operation") == "drive" for record in records))
            self.assertEqual(records[-1]["kind"], "robotd_stop")
            self.assertFalse(socket.exists())

    async def test_status_reads_and_uptime_ticks_do_not_spam_blackbox(self) -> None:
        with tempfile.TemporaryDirectory(prefix="robotd-quiet-test-") as temp:
            root = Path(temp)
            socket = root / "robotd.sock"
            log = root / "blackbox.jsonl"
            daemon = RobotDaemon(SimulatorTransport(), socket, Blackbox(log))
            running = asyncio.create_task(daemon.run())
            for _ in range(100):
                if socket.exists():
                    break
                await asyncio.sleep(0.01)

            async def request(payload: dict) -> dict:
                reader, writer = await asyncio.open_unix_connection(str(socket))
                writer.write((json.dumps(payload) + "\n").encode())
                await writer.drain()
                response = json.loads(await reader.readline())
                writer.close()
                await writer.wait_closed()
                return response

            # Let several 10 Hz status frames land, polling like a dashboard would.
            for index in range(5):
                response = await request({"id": f"status-{index}", "op": "status",
                                          "source": "test"})
                self.assertTrue(response["ok"])
                await asyncio.sleep(0.06)
            daemon.stop()
            await asyncio.wait_for(running, 2)
            records = [json.loads(line) for line in log.read_text().splitlines()]
            status_commands = [r for r in records if r.get("operation") == "status"]
            self.assertEqual(status_commands, [])
            firmware_updates = [r for r in records if r["kind"] == "firmware_status"]
            self.assertEqual(len(firmware_updates), 1,
                             "an idle simulator must log exactly the initial firmware status")


class HeadTrimTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    async def _request(socket: Path, payload: dict) -> dict:
        reader, writer = await asyncio.open_unix_connection(str(socket))
        writer.write((json.dumps(payload) + "\n").encode())
        await writer.drain()
        response = json.loads(await reader.readline())
        writer.close()
        await writer.wait_closed()
        return response

    async def _start_daemon(self, root: Path, **trim: int) -> tuple[RobotDaemon, asyncio.Task, Path, Path]:
        socket = root / "robotd.sock"
        log = root / "blackbox.jsonl"
        daemon = RobotDaemon(SimulatorTransport(), socket, Blackbox(log), **trim)
        running = asyncio.create_task(daemon.run())
        for _ in range(100):
            if socket.exists():
                break
            await asyncio.sleep(0.01)
        self.assertTrue(socket.exists())
        return daemon, running, socket, log

    async def test_head_trim_shifts_frames_and_journals_raw_plus_trimmed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="robotd-trim-test-") as temp:
            daemon, running, socket, log = await self._start_daemon(
                Path(temp), head_trim_pan_cdeg=300, head_trim_tilt_cdeg=-200)
            response = await self._request(socket, {"id": "head-1", "op": "head",
                                                    "source": "test",
                                                    "pan_cdeg": 1000, "tilt_cdeg": 500})
            self.assertTrue(response["ok"])
            self.assertEqual(response["result"]["trimmed_pan_cdeg"], 1300)
            self.assertEqual(response["result"]["trimmed_tilt_cdeg"], 300)
            # The simulator transport records what actually went over the wire.
            self.assertEqual((daemon.transport.pan, daemon.transport.tilt), (1300, 300))
            status = await self._request(socket, {"id": "status-1", "op": "status",
                                                  "source": "test"})
            self.assertEqual(status["result"]["head_trim"],
                             {"pan_cdeg": 300, "tilt_cdeg": -200})
            daemon.stop()
            await asyncio.wait_for(running, 2)
            records = [json.loads(line) for line in log.read_text().splitlines()]
            head = next(r for r in records if r.get("operation") == "head")
            self.assertEqual(head["request"]["pan_cdeg"], 1000)
            self.assertEqual(head["request"]["tilt_cdeg"], 500)
            self.assertEqual(head["response"]["trimmed_pan_cdeg"], 1300)
            self.assertEqual(head["response"]["trimmed_tilt_cdeg"], 300)

    async def test_zero_trim_sends_exactly_the_requested_angles(self) -> None:
        with tempfile.TemporaryDirectory(prefix="robotd-notrim-test-") as temp:
            daemon, running, socket, _log = await self._start_daemon(Path(temp))
            response = await self._request(socket, {"id": "head-1", "op": "head",
                                                    "source": "test",
                                                    "pan_cdeg": 1000, "tilt_cdeg": 500})
            self.assertTrue(response["ok"])
            self.assertEqual(response["result"]["trimmed_pan_cdeg"], 1000)
            self.assertEqual(response["result"]["trimmed_tilt_cdeg"], 500)
            self.assertEqual((daemon.transport.pan, daemon.transport.tilt), (1000, 500))
            status = await self._request(socket, {"id": "status-1", "op": "status",
                                                  "source": "test"})
            self.assertEqual(status["result"]["head_trim"], {"pan_cdeg": 0, "tilt_cdeg": 0})
            daemon.stop()
            await asyncio.wait_for(running, 2)

    async def test_head_trim_is_clamped_to_one_spline_tooth(self) -> None:
        args = parse_args(["--simulate", "--head-trim-pan-cdeg", "9000",
                           "--head-trim-tilt-cdeg", "-9000"])
        self.assertEqual(args.head_trim_pan_cdeg, 9000)
        self.assertEqual(args.head_trim_tilt_cdeg, -9000)
        with tempfile.TemporaryDirectory(prefix="robotd-clamp-test-") as temp:
            root = Path(temp)
            daemon = RobotDaemon(SimulatorTransport(), root / "robotd.sock",
                                 Blackbox(root / "blackbox.jsonl"),
                                 head_trim_pan_cdeg=args.head_trim_pan_cdeg,
                                 head_trim_tilt_cdeg=args.head_trim_tilt_cdeg)
            self.assertEqual(daemon.head_trim_pan_cdeg, 800)
            self.assertEqual(daemon.head_trim_tilt_cdeg, -800)


if __name__ == "__main__":
    unittest.main()
