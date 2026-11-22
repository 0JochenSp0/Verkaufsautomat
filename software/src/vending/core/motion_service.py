"""Motion service: maps purchasable positions to carousel sectors and keeps the ESP32 alive."""

from __future__ import annotations

import logging
import random
import threading
import time
from dataclasses import dataclass, field

from vending.config import MachineConfig
from vending.hal.interfaces import CarouselDriver, CarouselStatus, HalError

log = logging.getLogger(__name__)


@dataclass
class SoakResult:
    moves: int = 0
    errors: list[tuple[int, str]] = field(default_factory=list)
    duration_s: float = 0.0

    @property
    def ok(self) -> bool:
        return not self.errors


class MotionService:
    """Position p (0..positions-1) -> level = p // N, sector = p % N. All levels turn together."""

    def __init__(self, driver: CarouselDriver, cfg: MachineConfig):
        self.d = driver
        self.cfg = cfg
        self._ka_stop = threading.Event()
        self._ka_thread: threading.Thread | None = None

    # -- lifecycle --
    def connect(self) -> None:
        """Verify protocol, push configuration. Call after every (re)connect / ESP32 reset."""
        self.d.ping()
        self.d.configure(self.cfg.esp32_settings())

    def start_keepalive(self) -> None:
        if self._ka_thread:
            return
        self._ka_stop.clear()

        def run() -> None:
            while not self._ka_stop.wait(self.cfg.keepalive_s):
                try:
                    self.d.keepalive()
                except HalError as e:
                    log.warning("keepalive failed: %s", e)

        self._ka_thread = threading.Thread(target=run, name="esp32-keepalive", daemon=True)
        self._ka_thread.start()

    def stop_keepalive(self) -> None:
        self._ka_stop.set()
        if self._ka_thread:
            self._ka_thread.join(timeout=5)
        self._ka_thread = None

    # -- operations --
    def status(self) -> CarouselStatus:
        return self.d.status()

    def ensure_homed(self) -> None:
        st = self.d.status()
        if st.fault not in ("NONE",):
            log.info("clearing fault %s before homing", st.fault)
            self.d.clear()
        if not st.homed or st.fault != "NONE":
            self.d.home()

    def present(self, position: int) -> int:
        """Rotate so that `position` sits behind its flap. Returns the level (= flap index)."""
        level, sector = self.cfg.position_to_level_sector(position)
        self.d.goto(sector)
        return level

    def next_sector(self) -> int:
        """Service mode: advance one sector. Returns the new sector."""
        st = self.d.status()
        nxt = 0 if st.sector < 0 else (st.sector + 1) % self.cfg.sectors_per_level
        return self.d.goto(nxt)

    def soak(self, n: int, seed: int | None = None, rehome_on_error: bool = True) -> SoakResult:
        """M1 acceptance test: n random positionings, every error recorded."""
        rng = random.Random(seed)
        res = SoakResult()
        t0 = time.monotonic()
        self.ensure_homed()
        for i in range(n):
            target = rng.randrange(self.cfg.sectors_per_level)
            try:
                got = self.d.goto(target)
                if got != target:
                    res.errors.append((i, f"at {got}, wanted {target}"))
            except HalError as e:
                res.errors.append((i, f"{e.code} {e.msg}".strip()))
                if rehome_on_error:
                    try:
                        self.d.clear()
                        self.d.home()
                    except HalError as e2:
                        res.errors.append((i, f"rehome failed: {e2.code}"))
                        break
            res.moves += 1
        res.duration_s = time.monotonic() - t0
        return res
