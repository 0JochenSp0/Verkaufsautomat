"""Hardware-independent machine logic for the ESP32 co-processor.

MicroPython-compatible: no dataclasses, enum, typing at runtime.
The hardware object `hw` is duck-typed and must provide:

    hw.enable(on: bool)
    hw.move(delta_steps: int, speed_sps: int, accel_sps2: int, stop_when) -> (moved_steps: int, reason: str)
        reason: "done" | "stall" | "stop"   (stop = stop_when() became true)
    hw.home_active() -> bool
    hw.index_active() -> bool
    hw.lock(level: int, energised: bool)     # level 0..levels-1, energised = unlock solenoid
    hw.flap_closed(level: int) -> bool
    hw.door_closed() -> bool                  # main (service) door

Position convention: `pos` counts steps from the home-sensor trigger edge (forward = +).
Sector s centre lies at  home_offset + round(s * steps_per_rev / sectors).
"""


class Fault:
    NONE = "NONE"
    NOT_HOMED = "NOT_HOMED"
    HOME_FAIL = "HOME_FAIL"
    STALL = "STALL"
    INDEX = "INDEX"
    HEARTBEAT = "HEARTBEAT"


class MotionError(Exception):
    def __init__(self, code, msg=""):
        Exception.__init__(self, code)
        self.code = code
        self.msg = msg


class Config:
    INT_KEYS = (
        "steps_per_rev", "sectors", "levels", "max_speed", "accel", "home_speed",
        "home_offset", "backoff", "retries", "unlock_max_s", "hb_timeout_s",
    )
    FLOAT_KEYS = ("home_max_factor",)

    def __init__(self):
        self.steps_per_rev = 200 * 16 * 30
        self.sectors = 4
        self.levels = 3
        self.max_speed = 4000
        self.accel = 6000
        self.home_speed = 1500
        self.home_offset = 0
        self.backoff = 800
        self.retries = 1
        self.home_max_factor = 1.15
        self.unlock_max_s = 60
        self.hb_timeout_s = 10

    def set(self, key, value):
        if key in self.INT_KEYS:
            v = int(value)
        elif key in self.FLOAT_KEYS:
            v = float(value)
        else:
            raise MotionError("BAD_KEY", key)
        if key in ("steps_per_rev", "sectors", "levels") and v <= 0:
            raise MotionError("BAD_VALUE", key)
        setattr(self, key, v)


class Machine:
    def __init__(self, hw, cfg=None, clock=None):
        self.hw = hw
        self.cfg = cfg or Config()
        self.clock = clock  # callable returning seconds (float)
        self.homed = False
        self.pos = 0
        self.sector = -1
        self.fault = Fault.NONE
        self.lock_deadline = {}      # level -> deadline (s)
        self._flaps = [True] * self.cfg.levels
        self._door = True
        self.last_rx = self._now()
        self.safe = False
        self._init_inputs()

    # ---------- helpers ----------
    def _now(self):
        return self.clock() if self.clock else 0.0

    def _init_inputs(self):
        self._flaps = [self.hw.flap_closed(i) for i in range(self.cfg.levels)]
        self._door = self.hw.door_closed()

    def sector_target(self, s):
        c = self.cfg
        return (c.home_offset + (s * c.steps_per_rev + c.sectors // 2) // c.sectors) % c.steps_per_rev

    def _shortest(self, target):
        rev = self.cfg.steps_per_rev
        d = (target - self.pos) % rev
        if d > rev // 2:
            d -= rev
        return d

    def _move(self, delta, speed, stop_when=None):
        moved, reason = self.hw.move(delta, speed, self.cfg.accel, stop_when)
        self.pos = (self.pos + moved) % self.cfg.steps_per_rev
        return reason

    def _all_flaps_closed(self):
        return all(self.hw.flap_closed(i) for i in range(self.cfg.levels))

    def _check_can_move(self):
        if self.lock_deadline:
            raise MotionError("LOCK_ACTIVE", "release locks before moving")
        if not self._all_flaps_closed():
            raise MotionError("FLAP_OPEN", "never rotate with an open flap")

    def touch(self):
        """Called on every received command (heartbeat)."""
        self.last_rx = self._now()

    # ---------- motion ----------
    def home(self):
        self._check_can_move()
        self.fault = Fault.NONE
        self.safe = False
        self.homed = False
        self.sector = -1
        self.hw.enable(True)
        c = self.cfg
        # leave the sensor first if we are sitting on it
        if self.hw.home_active():
            self._move(c.steps_per_rev // 8, c.home_speed, lambda: not self.hw.home_active())
        attempts = 0
        while True:
            reason = self._move(int(c.steps_per_rev * c.home_max_factor), c.home_speed,
                                self.hw.home_active)
            if reason == "stop":
                break
            if reason == "stall" and attempts < c.retries:
                attempts += 1
                self._move(-c.backoff, c.home_speed)
                continue
            self.fault = Fault.HOME_FAIL
            raise MotionError(Fault.HOME_FAIL, reason)
        self.pos = 0
        self.homed = True
        return self.goto(0)

    def goto(self, s):
        c = self.cfg
        if not self.homed:
            raise MotionError(Fault.NOT_HOMED)
        if self.fault != Fault.NONE:
            raise MotionError("FAULT_ACTIVE", self.fault)
        if s < 0 or s >= c.sectors:
            raise MotionError("BAD_SECTOR", str(s))
        self._check_can_move()
        target = self.sector_target(s)
        attempts = 0
        while True:
            delta = self._shortest(target)
            reason = self._move(delta, c.max_speed) if delta else "done"
            if reason == "done":
                break
            if reason == "stall" and attempts < c.retries:
                attempts += 1
                back = -c.backoff if delta > 0 else c.backoff
                self._move(back, c.home_speed)
                continue
            self._enter_fault(Fault.STALL)
            raise MotionError(Fault.STALL, "sector %d" % s)
        if not self.hw.index_active():
            self._enter_fault(Fault.INDEX)
            raise MotionError(Fault.INDEX, "sector %d" % s)
        self.sector = s
        return s

    def _enter_fault(self, f):
        self.fault = f
        self.homed = False
        self.sector = -1

    def clear(self):
        self.fault = Fault.NONE
        self.safe = False

    # ---------- locks ----------
    def unlock(self, level, seconds):
        c = self.cfg
        if level < 0 or level >= c.levels:
            raise MotionError("BAD_LEVEL", str(level))
        if not self.homed or self.sector < 0 or self.fault != Fault.NONE:
            raise MotionError("NOT_READY", "not positioned")
        if self.lock_deadline:
            raise MotionError("LOCK_ACTIVE", "one flap at a time")
        if not self.hw.flap_closed(level):
            raise MotionError("FLAP_OPEN", str(level))
        seconds = max(1, min(int(seconds), c.unlock_max_s))
        self.lock_deadline[level] = self._now() + seconds
        self.hw.lock(level, True)
        return seconds

    def lock(self, level):
        self.hw.lock(level, False)
        self.lock_deadline.pop(level, None)

    def lock_all(self):
        for i in range(self.cfg.levels):
            self.hw.lock(i, False)
        self.lock_deadline = {}

    # ---------- periodic ----------
    def tick(self):
        """Poll inputs, enforce lock deadlines and heartbeat. Returns list of event strings."""
        ev = []
        now = self._now()
        for i in range(self.cfg.levels):
            closed = self.hw.flap_closed(i)
            if closed != self._flaps[i]:
                self._flaps[i] = closed
                ev.append("EVT FLAP %d %s" % (i, "CLOSED" if closed else "OPEN"))
                if not closed and i not in self.lock_deadline:
                    ev.append("EVT ALARM FLAP_FORCED %d" % i)
        for level in list(self.lock_deadline):
            if not self.hw.flap_closed(level):
                # latch bolt is free now; de-energise, it snaps back in when the flap closes
                self.lock(level)
                ev.append("EVT LOCK %d RELEASED OPENED" % level)
            elif now >= self.lock_deadline[level]:
                self.lock(level)
                ev.append("EVT LOCK %d RELEASED TIMEOUT" % level)
        door = self.hw.door_closed()
        if door != self._door:
            self._door = door
            ev.append("EVT DOOR %s" % ("CLOSED" if door else "OPEN"))
        if not self.safe and now - self.last_rx > self.cfg.hb_timeout_s:
            self.enter_safe()
            ev.append("EVT SAFE HEARTBEAT")
        return ev

    def enter_safe(self):
        self.lock_all()
        self.hw.enable(False)
        self.safe = True
        self._enter_fault(Fault.HEARTBEAT)

    def status(self):
        c = self.cfg
        flaps = "".join("1" if self.hw.flap_closed(i) else "0" for i in range(c.levels))
        locks = "".join("1" if i in self.lock_deadline else "0" for i in range(c.levels))
        return "homed=%d sector=%d pos=%d fault=%s flaps=%s locks=%s door=%d" % (
            1 if self.homed else 0, self.sector, self.pos, self.fault, flaps, locks,
            1 if self.hw.door_closed() else 0)
