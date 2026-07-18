import struct
import unittest

from robotd.protocol import (Frame, FrameParser, MessageType, crc16_ccitt,
                             decode_status, drive_frame, STATUS_STRUCT)


class ProtocolTests(unittest.TestCase):
    def test_known_crc_vector(self):
        self.assertEqual(crc16_ccitt(b"123456789"), 0x29B1)

    def test_fragmented_frame_round_trip(self):
        encoded = drive_frame(42, -123, 456).encode()
        parser = FrameParser()
        self.assertEqual(parser.feed(encoded[:3]), [])
        self.assertEqual(parser.feed(encoded[3:9]), [])
        frames = parser.feed(encoded[9:])
        self.assertEqual(frames, [Frame(MessageType.DRIVE, 42, struct.pack("<hh", -123, 456))])

    def test_bad_crc_does_not_hide_following_frame(self):
        bad = bytearray(Frame(MessageType.HEARTBEAT, 1).encode())
        bad[-1] ^= 0xFF
        good = Frame(MessageType.STOP, 2).encode()
        frames = FrameParser().feed(b"noise" + bad + good)
        self.assertEqual(frames, [Frame(MessageType.STOP, 2, b"")])

    def test_oversize_rejected(self):
        with self.assertRaises(ValueError):
            Frame(MessageType.EVENT, 1, b"x" * 65).encode()

    def test_status_decode(self):
        payload = STATUS_STRUCT.pack(1234, 5, 0x3F, 2, 12750, 10, -20, 300, -400)
        status = decode_status(payload)
        self.assertEqual(status["uptime_ms"], 1234)
        self.assertEqual(status["released_mask"], 0x3F)
        self.assertEqual(status["tilt_cdeg"], -400)


if __name__ == "__main__":
    unittest.main()
