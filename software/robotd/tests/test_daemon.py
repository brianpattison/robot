import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from robotd.daemon import Blackbox, RobotDaemon
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


if __name__ == "__main__":
    unittest.main()
