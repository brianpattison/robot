"""UART and deterministic simulator transports for robotd."""

from __future__ import annotations

import os
import select
import struct
import termios
import time
from typing import Protocol

from .protocol import Frame, FrameParser, MessageType, STATUS_STRUCT


class Transport(Protocol):
    def write(self, data: bytes) -> None: ...
    def read(self, timeout: float = 0.0) -> bytes: ...
    def close(self) -> None: ...


class SerialTransport:
    """Small stdlib-only raw 115200 UART transport for Raspberry Pi OS."""

    def __init__(self, device: str) -> None:
        self.fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CLOCAL | termios.CREAD | termios.CS8
        attrs[3] = 0
        attrs[4] = termios.B115200
        attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def write(self, data: bytes) -> None:
        view = memoryview(data)
        while view:
            try:
                written = os.write(self.fd, view)
                view = view[written:]
            except BlockingIOError:
                select.select([], [self.fd], [], 0.1)

    def read(self, timeout: float = 0.0) -> bytes:
        ready, _, _ = select.select([self.fd], [], [], timeout)
        return os.read(self.fd, 4096) if ready else b""

    def close(self) -> None:
        os.close(self.fd)


class SimulatorTransport:
    """Protocol-level bench simulator. It deliberately expires motion."""

    def __init__(self) -> None:
        self.parser = FrameParser()
        self.pending = bytearray()
        self.started = time.monotonic()
        self.last_motion = 0.0
        self.linear = 0
        self.angular = 0
        self.pan = 0
        self.tilt = 0
        self.sequence = 0

    def _status(self) -> bytes:
        if self.last_motion and time.monotonic() - self.last_motion > 0.25:
            self.linear = self.angular = 0
        uptime = int((time.monotonic() - self.started) * 1000)
        payload = STATUS_STRUCT.pack(uptime, 0, 0x3F, 0, 12800, self.linear,
                                     self.angular, self.pan, self.tilt)
        self.sequence = (self.sequence + 1) & 0xFFFF
        return Frame(MessageType.STATUS, self.sequence, payload).encode()

    def write(self, data: bytes) -> None:
        for frame in self.parser.feed(data):
            if frame.message_type == MessageType.DRIVE and len(frame.payload) == 4:
                self.linear, self.angular = struct.unpack("<hh", frame.payload)
                self.linear = max(-350, min(350, self.linear))
                self.angular = max(-1500, min(1500, self.angular))
                self.last_motion = time.monotonic()
            elif frame.message_type == MessageType.STOP:
                self.linear = self.angular = 0
                self.last_motion = 0.0
            elif frame.message_type == MessageType.HEAD and len(frame.payload) == 4:
                self.pan, self.tilt = struct.unpack("<hh", frame.payload)
                self.pan = max(-6000, min(6000, self.pan))
                self.tilt = max(-2000, min(2000, self.tilt))
            if frame.message_type in (MessageType.STATUS_REQUEST, MessageType.DRIVE,
                                      MessageType.STOP, MessageType.HEAD):
                self.pending.extend(self._status())

    def read(self, timeout: float = 0.0) -> bytes:
        if not self.pending and timeout:
            time.sleep(min(timeout, 0.01))
        data = bytes(self.pending)
        self.pending.clear()
        return data

    def close(self) -> None:
        return None
