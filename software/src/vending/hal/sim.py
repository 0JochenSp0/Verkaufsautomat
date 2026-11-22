"""Simulator: runs the *real* ESP32 firmware logic against a mechanical model.

    FakeMechanics  – duck-typed `hw` for carousel_fw.machine_logic.Machine
    SimTransport   – LineTransport that feeds the firmware Dispatcher in-process

Requires `software/firmware/esp32` on sys.path (added automatically below).
"""

from __future__ import annotations

import collections
import sys
from collections.abc import Callable
from pathlib import Path

_FW = Path(__file__).resolve().parents[3] / "firmware" / "esp32"
if str(_FW) not in sys.path:
    sys.path.insert(0, str(_FW))

from carousel_fw.machine_logic import Config, Machine  # noqa: E402
from carousel_fw.protocol import Dispatcher  # noqa: E402


class FakeMechanics:
    """Mechanical model of carousel, sensors, locks and flaps.

    True position `true_pos` (steps from the home magnet edge). The home sensor is active for
    `home_width` steps after the edge, the index sensor within ±`index_window` of each sector centre.
    Fault injection: `blocked` (every move stalls), `stall_after` (stall once after n steps),
    `slip_steps` (silently lose steps on every move).
    """

    def __init__(self, steps_per_rev: int, sectors: int, levels: int = 3, home_offset: int = 0,
                 home_width: int = 300, index_window: int = 400, start_pos: int = 12345):
        self.rev = steps_per_rev
        self.sectors = sectors
        self.levels = levels
        self.home_offset = home_offset
        self.home_width = home_width
        self.index_window = index_window
        self.true_pos = start_pos % steps_per_rev
        self.enabled = False
        self.locks = [False] * levels
        self.flaps = [True] * levels       # True = closed
        self.door = True
        self.blocked = False
        self.stall_after: int | None = None
        self.slip_steps = 0
        self.total_steps = 0
        self.moves = 0

    def reconfigure(self, steps_per_rev: int, sectors: int, levels: int, home_offset: int) -> None:
        self.rev, self.sectors, self.levels, self.home_offset = steps_per_rev, sectors, levels, home_offset
        self.true_pos %= self.rev
        self.locks = (self.locks + [False] * levels)[:levels]
        self.flaps = (self.flaps + [True] * levels)[:levels]

    # --- hw interface used by Machine ---
    def enable(self, on: bool) -> None:
        self.enabled = on

    def home_active(self) -> bool:
        return 0 <= self.true_pos < self.home_width

    def index_active(self) -> bool:
        for s in range(self.sectors):
            centre = (self.home_offset + (s * self.rev + self.sectors // 2) // self.sectors) % self.rev
            d = (self.true_pos - centre) % self.rev
            if min(d, self.rev - d) <= self.index_window:
                return True
        return False

    def lock(self, level: int, energised: bool) -> None:
        self.locks[level] = energised

    def flap_closed(self, level: int) -> bool:
        return self.flaps[level]

    def door_closed(self) -> bool:
        return self.door

    def move(self, delta: int, speed: int, accel: int, stop_when=None):
        if not self.enabled:
            return 0, "stall"
        self.moves += 1
        sign = 1 if delta > 0 else -1
        n = abs(delta)
        if self.blocked:
            n_ok = min(n, 50)
            self._advance(sign * n_ok)
            return sign * n_ok, "stall"
        if self.stall_after is not None and self.stall_after < n:
            k = self.stall_after
            self.stall_after = None
            self._advance(sign * k)
            return sign * k, "stall"
        if stop_when is None:
            self._advance(sign * n, slip=True)
            return sign * n, "done"
        for i in range(n):
            if stop_when():
                return sign * i, "stop"
            self._advance(sign)
        return sign * n, "done"

    def _advance(self, steps: int, slip: bool = False) -> None:
        real = steps
        if slip and self.slip_steps:
            real = steps - (self.slip_steps if steps > 0 else -self.slip_steps)
        self.true_pos = (self.true_pos + real) % self.rev
        self.total_steps += abs(steps)

    # --- customer / operator actions ---
    def open_flap(self, level: int) -> bool:
        """Customer pulls the flap. Opens only if the solenoid is energised (fail-secure)."""
        if self.locks[level]:
            self.flaps[level] = False
            return True
        return False

    def force_flap(self, level: int) -> None:
        self.flaps[level] = False

    def close_flap(self, level: int) -> None:
        self.flaps[level] = True


class SimClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, s: float) -> None:
        self.t += s


class SimTransport:
    """In-process transport: each written line is handled by the firmware Dispatcher.

    Like the real main loop, Machine.tick() runs on every read, so events appear as they would on UART.
    `CFG` lines are mirrored into the mechanics model so the simulation stays consistent.
    """

    def __init__(self, mech: FakeMechanics | None = None, clock: Callable[[], float] | None = None):
        self.clock = clock or SimClock()
        self.mech = mech or FakeMechanics(steps_per_rev=96000, sectors=4)
        cfg = Config()
        cfg.steps_per_rev, cfg.sectors, cfg.levels = self.mech.rev, self.mech.sectors, self.mech.levels
        self.machine = Machine(self.mech, cfg, clock=self.clock)
        self.dispatcher = Dispatcher(self.machine)
        self._out: collections.deque[str] = collections.deque()

    def write_line(self, line: str) -> None:
        self._out.extend(self.machine.tick())
        self._out.append(self.dispatcher.handle(line))
        parts = line.split()
        if parts and parts[0] == "CFG" and parts[1] in ("steps_per_rev", "sectors", "levels", "home_offset"):
            c = self.machine.cfg
            self.mech.reconfigure(c.steps_per_rev, c.sectors, c.levels, c.home_offset)
            self.machine._flaps = [self.mech.flap_closed(i) for i in range(c.levels)]

    def read_line(self, timeout: float) -> str | None:
        self._out.extend(self.machine.tick())
        return self._out.popleft() if self._out else None

    def close(self) -> None:
        pass
