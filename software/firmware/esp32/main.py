"""ESP32 (classic WROOM-32) entry point – binds machine_logic to real pins. MicroPython only.

Pinout: electronics/pinout.md. Flashing and file upload from the Pi: firmware/esp32/flash.sh.

The Pi protocol runs on UART0 (GPIO1/3) via the DevKit's USB bridge (CP2102), the same port as the ROM bootloader and the REPL.
That is why the protocol goes through sys.stdin/sys.stdout, Ctrl-C is disabled and nothing
in this file may print().
"""

import select
import sys
import time

import micropython
from machine import UART, WDT, Pin  # MicroPython

from carousel_fw.machine_logic import Config, Machine
from carousel_fw.protocol import Dispatcher
from carousel_fw.tmc2209 import TMC2209

# ---- pins (see electronics/pinout.md); avoid strapping pins 0/2/5/12/15 and flash pins 6-11 ----
UART_TMC = UART(2, baudrate=115200, tx=17, rx=16)
STEP = Pin(26, Pin.OUT, value=0)
DIR = Pin(27, Pin.OUT, value=0)
EN_N = Pin(25, Pin.OUT, value=1)           # TMC2209 EN is active low, external 10k pull-up
DIAG = Pin(34, Pin.IN)                     # StallGuard output, high = stall (input-only pin)
HOME = Pin(32, Pin.IN, Pin.PULL_UP)        # hall, active low
INDEX = Pin(33, Pin.IN, Pin.PULL_UP)       # hall, active low
LOCKS = [Pin(n, Pin.OUT, value=0) for n in (4, 18, 19)]      # MOSFET gates, high = unlock, 10k pull-down
FLAPS = [Pin(n, Pin.IN, Pin.PULL_UP) for n in (21, 22, 23)]  # reed, closed = low
DOOR = Pin(13, Pin.IN, Pin.PULL_UP)        # main door contact, closed = low
LED = Pin(2, Pin.OUT, value=0)             # onboard LED (strapping pin: LED only, no external load)
TMC = TMC2209(UART_TMC)                    # registers are written by Machine before every HOME/JOG
_wdt = None                                # hardware watchdog, created in run()


def _feed():
    if _wdt is not None:
        _wdt.feed()


class Esp32HW:
    def enable(self, on):
        EN_N.value(0 if on else 1)

    def setup_driver(self, irun, sgthrs):
        TMC.setup(irun=irun, sgthrs=sgthrs)

    def home_active(self):
        return HOME.value() == 0

    def index_active(self):
        return INDEX.value() == 0

    def lock(self, level, energised):
        LOCKS[level].value(1 if energised else 0)

    def flap_closed(self, level):
        return FLAPS[level].value() == 0

    def door_closed(self):
        return DOOR.value() == 0

    def move(self, delta, speed, accel, stop_when=None):
        # shortcut: busy-loop stepping, jitter from FreeRTOS tick/GC; move to esp32.RMT if M1 soak shows lost steps
        if delta == 0:
            return 0, "done"
        DIR.value(1 if delta > 0 else 0)
        sign = 1 if delta > 0 else -1
        n = abs(delta)
        v0 = 200.0
        v = v0
        moved = 0
        ignore_stall = 400              # StallGuard is unreliable at low speed during ramp-up
        while moved < n:
            if stop_when is not None and stop_when():
                return sign * moved, "stop"
            if moved > ignore_stall and DIAG.value():
                return sign * moved, "stall"
            STEP.value(1)
            time.sleep_us(2)
            STEP.value(0)
            remaining = n - moved
            # trapezoid: accelerate, cruise, decelerate (v^2 = 2*a*s)
            v_dec = (v0 * v0 + 2 * accel * remaining) ** 0.5
            v = min(speed, v_dec, (v * v + 2 * accel) ** 0.5)
            time.sleep_us(max(int(1_000_000 / v) - 2, 10))
            moved += 1
            if moved & 0x3FF == 0:
                _feed()
        return sign * moved, "done"


class MonoClock:
    """Seconds since boot without the ticks_ms() wrap-around."""

    def __init__(self):
        self._last = time.ticks_ms()
        self._acc_ms = 0

    def __call__(self):
        now = time.ticks_ms()
        self._acc_ms += time.ticks_diff(now, self._last)
        self._last = now
        return self._acc_ms / 1000


def run():
    global _wdt
    micropython.kbd_intr(-1)  # a stray 0x03 on the line must not stop the firmware
    _wdt = WDT(timeout=3000)  # resets the ESP32 (-> pins high-Z = locked, motor off) if the loop hangs
    hw = Esp32HW()
    m = Machine(hw, Config(), clock=MonoClock())
    d = Dispatcher(m)
    rx = select.poll()
    rx.register(sys.stdin, select.POLLIN)
    buf = b""
    while True:
        while rx.poll(0):
            buf += sys.stdin.buffer.read(1)
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            sys.stdout.write(d.handle(line.decode("ascii", "ignore")) + "\n")
        for ev in m.tick():
            sys.stdout.write(ev + "\n")
        LED.value(not LED.value())
        _feed()
        time.sleep_ms(20)


run()
