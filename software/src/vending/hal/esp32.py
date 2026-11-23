"""CarouselDriver implementation talking to the ESP32 over a line transport (UART or simulator)."""

from __future__ import annotations

import collections
import os
import threading
import time
from typing import Protocol

from vending.hal.interfaces import CarouselStatus, Event, HalError

SUPPORTED_PROTO = 1
# keyword after "OK" for each command; anything else is a reply to some other request
REPLY = {"PING": "PONG", "CFG": "CFG", "HOME": "AT", "GOTO": "AT", "JOG": "POS", "UNLOCK": "UNLOCKING",
         "LOCK": "LOCKED", "STATUS": "STATUS", "CLEAR": "CLEARED", "DISABLE": "DISABLED"}


class LineTransport(Protocol):
    def write_line(self, line: str) -> None: ...
    def read_line(self, timeout: float) -> str | None: ...
    def close(self) -> None: ...


class SerialTransport:
    """Serial transport over the DevKit USB bridge. pyserial if installed, else raw termios (Linux)."""

    def __init__(self, port: str = "/dev/esp32", baud: int = 115200):
        self._buf = b""
        try:
            import serial  # type: ignore[import-not-found]

            # DTR/RTS drive GPIO0/EN through the DevKit auto-reset circuit. Leave both asserted
            # (Linux sets them together on open): clearing them one by one pulses EN = reset.
            self._ser = serial.Serial(port, baud, timeout=0.05)
            self._fd = None
        except ImportError:
            import termios
            import tty

            self._ser = None
            self._fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            tty.setraw(self._fd)
            attrs = termios.tcgetattr(self._fd)
            speed = getattr(termios, f"B{baud}")
            attrs[4] = attrs[5] = speed
            termios.tcsetattr(self._fd, termios.TCSANOW, attrs)

    def write_line(self, line: str) -> None:
        data = (line + "\n").encode("ascii")
        if self._ser is not None:
            self._ser.write(data)
        else:
            os.write(self._fd, data)

    def _read_some(self) -> bytes:
        if self._ser is not None:
            return self._ser.read(256)
        import select

        r, _, _ = select.select([self._fd], [], [], 0.05)
        return os.read(self._fd, 256) if r else b""

    def read_line(self, timeout: float) -> str | None:
        deadline = time.monotonic() + timeout
        while b"\n" not in self._buf:
            self._buf += self._read_some()      # read at least once, also for timeout=0
            if b"\n" not in self._buf and time.monotonic() >= deadline:
                return None
        line, self._buf = self._buf.split(b"\n", 1)
        return line.decode("ascii", "replace").strip()

    def close(self) -> None:
        if self._ser is not None:
            self._ser.close()
        elif self._fd is not None:
            os.close(self._fd)


class Esp32Carousel:
    """Thread-safe request/response client. EVT lines are queued for poll_events()."""

    def __init__(self, transport: LineTransport, default_timeout: float = 3.0,
                 move_timeout: float = 60.0):
        self.t = transport
        self.default_timeout = default_timeout
        self.move_timeout = move_timeout
        self._events: collections.deque[Event] = collections.deque()
        self._lock = threading.RLock()
        self._stale = False      # a request timed out: its late reply may still be on the line

    # -- core --
    def request(self, line: str, timeout: float | None = None) -> list[str]:
        """Send a command; return the tokens after 'OK'. Raises HalError on ERR/timeout."""
        timeout = self.default_timeout if timeout is None else timeout
        with self._lock:
            if self._stale:
                self._resync()
            self.t.write_line(line)
            try:
                parts = self._await_reply(line, timeout)
            except HalError as e:
                if e.code == "TIMEOUT":
                    self._stale = True
                raise
            expected = REPLY.get(line.split()[0].upper())
            if expected and (len(parts) < 2 or parts[1] != expected):
                self._stale = True
                raise HalError("PROTO", f"{line!r} answered with {' '.join(parts)!r}")
            return parts[1:]

    def _await_reply(self, line: str, timeout: float) -> list[str]:
        """Read until an OK/ERR line; queue EVT lines, ignore noise (e.g. the MicroPython boot banner)."""
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            resp = self.t.read_line(remaining) if remaining > 0 else None
            if resp is None:
                raise HalError("TIMEOUT", line)
            if resp.startswith("EVT "):
                self._events.append(Event.parse(resp))
                continue
            parts = resp.split()
            if parts and parts[0] == "OK":
                return parts
            if parts and parts[0] == "ERR":
                raise HalError(parts[1] if len(parts) > 1 else "ERR", " ".join(parts[2:]))

    def _resync(self) -> None:
        """Send PING and drop every reply up to its PONG, so a late answer cannot match the next request."""
        self.t.write_line("PING")
        deadline = time.monotonic() + self.move_timeout * 2      # the ESP32 may still be homing
        while True:
            try:
                parts = self._await_reply("PING (resync)", deadline - time.monotonic())
            except HalError as e:
                if e.code == "TIMEOUT":
                    raise
                continue                                          # a late ERR of the old request
            if parts[1:2] == ["PONG"]:
                self._stale = False
                return

    # -- CarouselDriver --
    def ping(self) -> int:
        r = self.request("PING")
        version = int(r[1])
        if version != SUPPORTED_PROTO:
            raise HalError("PROTO", f"esp32 speaks v{version}, need v{SUPPORTED_PROTO}")
        return version

    def configure(self, settings: dict[str, int]) -> None:
        for k, v in settings.items():
            self.request(f"CFG {k} {v}")

    def home(self) -> int:
        return int(self.request("HOME", self.move_timeout * 2)[1])

    def goto(self, sector: int) -> int:
        got = int(self.request(f"GOTO {sector}", self.move_timeout)[1])
        if got != sector:
            raise HalError("POSITION", f"at {got}, wanted {sector}")
        return got

    def jog(self, steps: int) -> int:
        return int(self.request(f"JOG {steps}", self.move_timeout)[1])

    def unlock(self, level: int, seconds: int) -> int:
        return int(self.request(f"UNLOCK {level} {seconds}")[2])

    def lock(self, level: int) -> None:
        self.request(f"LOCK {level}")

    def clear(self) -> None:
        self.request("CLEAR")

    def disable(self) -> None:
        self.request("DISABLE")

    def keepalive(self) -> None:
        self.request("PING")

    def status(self) -> CarouselStatus:
        r = self.request("STATUS")
        kv = dict(tok.split("=", 1) for tok in r[1:])
        return CarouselStatus(
            homed=kv["homed"] == "1",
            sector=int(kv["sector"]),
            pos=int(kv["pos"]),
            fault=kv["fault"],
            flaps_closed=tuple(c == "1" for c in kv["flaps"]),
            locks_active=tuple(c == "1" for c in kv["locks"]),
            door_closed=kv["door"] == "1",
            configured=kv["cfg"] == "1",
        )

    def poll_events(self, wait: float = 0.0) -> list[Event]:
        with self._lock:
            line = self.t.read_line(wait)
            while line is not None:
                if line.startswith("EVT "):
                    self._events.append(Event.parse(line))
                line = self.t.read_line(0.0)
            out = list(self._events)
            self._events.clear()
            return out
