"""Framed UART protocol shared conceptually with the Pico safety firmware."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct

SOF = b"\xA5\x5A"
VERSION = 1
MAX_PAYLOAD = 64


class MessageType(IntEnum):
    HEARTBEAT = 0x01
    DRIVE = 0x02
    STOP = 0x03
    CLEAR_BUMPER = 0x04
    STATUS_REQUEST = 0x05
    HEAD = 0x06
    ACK = 0x80
    STATUS = 0x81
    EVENT = 0x82


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


@dataclass(frozen=True)
class Frame:
    message_type: int
    sequence: int
    payload: bytes = b""

    def encode(self) -> bytes:
        if len(self.payload) > MAX_PAYLOAD:
            raise ValueError("payload exceeds 64-byte protocol limit")
        body = struct.pack("<BBHH", VERSION, int(self.message_type), self.sequence & 0xFFFF,
                           len(self.payload)) + self.payload
        return SOF + body + struct.pack("<H", crc16_ccitt(body))


class FrameParser:
    """Incremental resynchronizing parser; malformed data refreshes nothing."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[Frame]:
        self._buffer.extend(data)
        frames: list[Frame] = []
        while True:
            start = self._buffer.find(SOF)
            if start < 0:
                self._buffer[:] = self._buffer[-1:] if self._buffer[-1:] == SOF[:1] else b""
                break
            if start:
                del self._buffer[:start]
            if len(self._buffer) < 8:
                break
            version, message_type, sequence, length = struct.unpack_from("<BBHH", self._buffer, 2)
            if version != VERSION or length > MAX_PAYLOAD:
                del self._buffer[0]
                continue
            total = 2 + 6 + length + 2
            if len(self._buffer) < total:
                break
            body = bytes(self._buffer[2:2 + 6 + length])
            expected = struct.unpack_from("<H", self._buffer, 2 + 6 + length)[0]
            if crc16_ccitt(body) != expected:
                del self._buffer[0]
                continue
            payload = bytes(self._buffer[8:8 + length])
            frames.append(Frame(message_type, sequence, payload))
            del self._buffer[:total]
        return frames


def drive_frame(sequence: int, linear_mm_s: int, angular_mrad_s: int) -> Frame:
    return Frame(MessageType.DRIVE, sequence, struct.pack("<hh", linear_mm_s, angular_mrad_s))


def head_frame(sequence: int, pan_cdeg: int, tilt_cdeg: int) -> Frame:
    return Frame(MessageType.HEAD, sequence, struct.pack("<hh", pan_cdeg, tilt_cdeg))


STATUS_STRUCT = struct.Struct("<IHBBHhhhh")


def decode_status(payload: bytes) -> dict[str, int]:
    if len(payload) != STATUS_STRUCT.size:
        raise ValueError(f"STATUS payload must be {STATUS_STRUCT.size} bytes")
    values = STATUS_STRUCT.unpack(payload)
    keys = ("uptime_ms", "flags", "released_mask", "latched_mask", "battery_mv",
            "linear_mm_s", "angular_mrad_s", "pan_cdeg", "tilt_cdeg")
    return dict(zip(keys, values, strict=True))


# Mirror of the EVENT 0x82 stop-latency payload in docs/body-protocol-v1.md;
# keep field order identical to firmware/pico2-safety/src/pico_main.c.
STOP_EVENT_STRUCT = struct.Struct("<BHIIH")
STOP_EVENT_TYPE = 0x01


def decode_stop_event(payload: bytes) -> dict[str, int]:
    if len(payload) != STOP_EVENT_STRUCT.size:
        raise ValueError(f"EVENT payload must be {STOP_EVENT_STRUCT.size} bytes")
    event_type, cause_flags, observed_ms, enacted_ms, dropped = STOP_EVENT_STRUCT.unpack(payload)
    if event_type != STOP_EVENT_TYPE:
        raise ValueError(f"unknown EVENT type 0x{event_type:02x}")
    return {"event_type": event_type, "cause_flags": cause_flags,
            "observed_ms": observed_ms, "enacted_ms": enacted_ms,
            "latency_ms": max(0, enacted_ms - observed_ms), "dropped_events": dropped}
