import asyncio
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from robotd import hello
from robotd.daemon import Blackbox, RobotDaemon
from robotd.transport import SimulatorTransport


class HelloScriptTests(unittest.IsolatedAsyncioTestCase):
    async def test_hello_sequence_lands_in_blackbox_and_recenters(self) -> None:
        with tempfile.TemporaryDirectory(prefix="robot-hello-test-") as temp:
            root = Path(temp)
            socket = root / "robotd.sock"
            log = root / "blackbox.jsonl"
            transport = SimulatorTransport()
            daemon = RobotDaemon(transport, socket, Blackbox(log))
            running = asyncio.create_task(daemon.run())
            for _ in range(100):
                if socket.exists():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(socket.exists())
            for _ in range(100):
                if daemon.state.connected:
                    break
                await asyncio.sleep(0.02)
            self.assertTrue(daemon.state.connected,
                            "the simulator never brought the firmware link up")

            narration = io.StringIO()
            with contextlib.redirect_stdout(narration):
                await hello.run_hello(socket, None, step_pause=0, pose_pause=0)
            self.assertIn("Rover Bean is looking around", narration.getvalue())

            daemon.stop()
            await asyncio.wait_for(running, 2)
            records = [json.loads(line) for line in log.read_text().splitlines()]
            heads = [r for r in records if r.get("operation") == "head"]
            self.assertTrue(heads, "the hello session sent no head commands")
            self.assertTrue(all(r["source"] == "hello" for r in heads))
            pans = [r["request"]["pan_cdeg"] for r in heads]
            self.assertIn(-hello.PAN_SWEEP_CDEG, pans)
            self.assertIn(hello.PAN_SWEEP_CDEG, pans)
            last = heads[-1]["request"]
            self.assertEqual((last["pan_cdeg"], last["tilt_cdeg"]), (0, 0))
            self.assertEqual((transport.pan, transport.tilt), (0, 0),
                             "the head must finish back at center")

    async def test_hello_refuses_kindly_when_robotd_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="robot-hello-down-test-") as temp:
            missing = Path(temp) / "missing.sock"
            with self.assertRaises(SystemExit) as caught:
                await hello.run_hello(missing, None, step_pause=0, pose_pause=0)
            self.assertIn("Start robotd yourself first", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
