import struct
import time
import unittest

from robotd.protocol import Frame, FrameParser, MessageType, decode_status, drive_frame, head_frame
from robotd.transport import SimulatorTransport


def latest_status(transport):
    frames = FrameParser().feed(transport.read())
    return decode_status([f for f in frames if f.message_type == MessageType.STATUS][-1].payload)


class SimulatorTests(unittest.TestCase):
    def test_firmware_style_clamps_and_lease(self):
        transport = SimulatorTransport()
        transport.write(drive_frame(1, 900, -3000).encode())
        status = latest_status(transport)
        self.assertEqual((status["linear_mm_s"], status["angular_mrad_s"]), (350, -1500))
        time.sleep(0.27)
        transport.write(Frame(MessageType.STATUS_REQUEST, 2).encode())
        status = latest_status(transport)
        self.assertEqual((status["linear_mm_s"], status["angular_mrad_s"]), (0, 0))

    def test_head_clamps(self):
        transport = SimulatorTransport()
        transport.write(head_frame(1, 9000, -5000).encode())
        status = latest_status(transport)
        self.assertEqual((status["pan_cdeg"], status["tilt_cdeg"]), (6000, -2000))

    def test_stop_is_immediate(self):
        transport = SimulatorTransport()
        transport.write(drive_frame(1, 100, 200).encode())
        transport.read()
        transport.write(Frame(MessageType.STOP, 2).encode())
        status = latest_status(transport)
        self.assertEqual((status["linear_mm_s"], status["angular_mrad_s"]), (0, 0))


if __name__ == "__main__":
    unittest.main()
