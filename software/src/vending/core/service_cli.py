"""Service-mode CLI for the M1 bench (and later on-site service).

    python -m vending.core.service_cli --sim               # against the simulator
    python -m vending.core.service_cli --port /dev/ttyAMA0 # against the real ESP32

Commands: status | home | goto <sector> | next | present <position> | unlock <level> [s] |
          lock <level> | clear | disable | events | soak <n> | layout | help | quit
"""

from __future__ import annotations

import argparse
import logging
import shlex
import sys
import time

from vending import config as config_mod
from vending.core.motion_service import MotionService
from vending.hal.interfaces import HalError
from vending.hal.esp32 import Esp32Carousel, SerialTransport


def build(args: argparse.Namespace) -> tuple[MotionService, object]:
    cfg = config_mod.load(args.params)
    if args.sim:
        from vending.hal.sim import FakeMechanics, SimTransport

        mech = FakeMechanics(cfg.steps_per_rev, cfg.sectors_per_level, cfg.levels, cfg.home_offset_steps)
        # real clock so unlock timeouts and the heartbeat behave like on the bench
        transport = SimTransport(mech, clock=time.monotonic)
    else:
        transport = SerialTransport(args.port, args.baud)
    rev_timeout = cfg.move_timeout_s(cfg.steps_per_rev, cfg.home_speed_sps)
    driver = Esp32Carousel(transport, move_timeout=rev_timeout)
    svc = MotionService(driver, cfg)
    svc.connect()
    svc.start_keepalive()
    return svc, transport


def run_command(svc: MotionService, argv: list[str]) -> str:
    d, cfg = svc.d, svc.cfg
    cmd, *a = argv
    if cmd == "status":
        return str(svc.status())
    if cmd == "home":
        return f"homed, at sector {d.home()}"
    if cmd == "goto":
        return f"at sector {d.goto(int(a[0]))}"
    if cmd == "next":
        return f"at sector {svc.next_sector()}"
    if cmd == "present":
        lvl = svc.present(int(a[0]))
        return f"position {a[0]} behind flap {lvl}"
    if cmd == "unlock":
        return f"flap {a[0]} unlocked for {d.unlock(int(a[0]), int(a[1]) if len(a) > 1 else 10)} s"
    if cmd == "lock":
        d.lock(int(a[0]))
        return "locked"
    if cmd == "clear":
        d.clear()
        return "cleared"
    if cmd == "disable":
        d.disable()
        return "motor disabled, all locks released"
    if cmd == "events":
        return "\n".join(f"{e.kind} {' '.join(e.args)}" for e in d.poll_events()) or "(none)"
    if cmd == "soak":
        r = svc.soak(int(a[0]) if a else 500)
        lines = [f"{r.moves} moves, {len(r.errors)} errors, {r.duration_s:.1f} s -> {'PASS' if r.ok else 'FAIL'}"]
        lines += [f"  #{i}: {msg}" for i, msg in r.errors[:20]]
        return "\n".join(lines)
    if cmd == "layout":
        return (f"{cfg.levels} levels x {cfg.sectors_per_level} sectors = {cfg.positions} positions, "
                f"{cfg.steps_per_rev} steps/rev")
    if cmd == "help":
        return __doc__ or ""
    raise ValueError(f"unknown command {cmd!r}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Vending machine service CLI")
    ap.add_argument("--sim", action="store_true", help="use the simulator instead of the ESP32")
    ap.add_argument("--port", default="/dev/ttyAMA0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--params", default=str(config_mod.DEFAULT_PARAMS))
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("command", nargs="*", help="run a single command and exit")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    svc, transport = build(args)
    try:
        if args.command:
            print(run_command(svc, args.command))
            return 0
        print(run_command(svc, ["layout"]))
        while True:
            try:
                line = input("service> ").strip()
            except EOFError:
                break
            if not line:
                continue
            if line in ("quit", "exit"):
                break
            try:
                print(run_command(svc, shlex.split(line)))
            except HalError as e:
                print(f"HAL ERROR: {e.code} {e.msg}")
            except (ValueError, IndexError) as e:
                print(f"error: {e}")
    finally:
        svc.stop_keepalive()
        transport.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
