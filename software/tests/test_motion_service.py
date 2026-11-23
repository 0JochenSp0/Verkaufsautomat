"""End-to-end: MotionService -> Esp32Carousel -> line protocol -> firmware logic -> FakeMechanics."""

import collections
import os
import unittest

import _paths  # noqa: F401

from vending import config as config_mod
from vending.core import service_cli
from vending.core.motion_service import MotionService
from vending.hal.interfaces import HalError
from vending.hal.esp32 import Esp32Carousel, SerialTransport
from vending.hal.sim import FakeMechanics, SimTransport


def make_service():
    cfg = config_mod.load()
    mech = FakeMechanics(cfg.steps_per_rev, cfg.sectors_per_level, cfg.levels, cfg.home_offset_steps)
    transport = SimTransport(mech)
    svc = MotionService(Esp32Carousel(transport), cfg)
    svc.connect()
    return svc, mech, transport


class MotionServiceTest(unittest.TestCase):
    def test_config_from_params(self):
        cfg = config_mod.load()
        self.assertEqual(cfg.levels, 3)
        self.assertGreaterEqual(cfg.positions, 10)
        self.assertEqual(cfg.position_to_level_sector(cfg.sectors_per_level + 1), (1, 1))
        with self.assertRaises(ValueError):
            cfg.position_to_level_sector(cfg.positions)

    def test_status_parsing(self):
        svc, _, _ = make_service()
        st = svc.status()
        self.assertFalse(st.homed)
        self.assertEqual(len(st.flaps_closed), 3)
        svc.ensure_homed()
        self.assertTrue(svc.status().ready)

    def test_present_every_position(self):
        svc, mech, _ = make_service()
        svc.ensure_homed()
        for p in range(svc.cfg.positions):
            level = svc.present(p)
            self.assertEqual(level, p // svc.cfg.sectors_per_level)
            self.assertEqual(svc.status().sector, p % svc.cfg.sectors_per_level)
            self.assertTrue(mech.index_active())

    def test_service_mode_next_wraps(self):
        svc, _, _ = make_service()
        svc.ensure_homed()
        seen = [svc.next_sector() for _ in range(svc.cfg.sectors_per_level + 1)]
        self.assertEqual(seen[-1], seen[0])
        self.assertEqual(sorted(set(seen)), list(range(svc.cfg.sectors_per_level)))

    def test_soak_500_passes(self):
        svc, _, _ = make_service()
        r = svc.soak(500, seed=1)
        self.assertTrue(r.ok, r.errors[:5])
        self.assertEqual(r.moves, 500)

    def test_soak_reports_and_recovers_from_block(self):
        svc, mech, _ = make_service()
        svc.ensure_homed()
        mech.stall_after = 10           # single stall -> FAULT (no auto-retry), soak re-homes
        r = svc.soak(20, seed=2)
        self.assertEqual(len(r.errors), 1, r.errors)
        self.assertIn("STALL", r.errors[0][1])
        self.assertEqual(r.moves, 20)

    def test_block_surfaces_as_hal_error(self):
        svc, mech, _ = make_service()
        svc.ensure_homed()
        mech.blocked = True
        with self.assertRaises(HalError) as cm:
            svc.d.goto((svc.status().sector + 1) % svc.cfg.sectors_per_level)
        self.assertEqual(cm.exception.code, "STALL")
        self.assertEqual(svc.status().fault, "STALL")
        mech.blocked = False
        svc.ensure_homed()              # clears fault and re-homes
        self.assertTrue(svc.status().ready)

    def test_purchase_like_unlock_flow_with_events(self):
        svc, mech, _ = make_service()
        svc.ensure_homed()
        level = svc.present(svc.cfg.sectors_per_level * 2 + 1)
        svc.d.unlock(level, 30)
        self.assertTrue(mech.open_flap(level))
        kinds = [(e.kind, e.args) for e in svc.d.poll_events()]
        self.assertIn(("FLAP", (str(level), "OPEN")), kinds)
        self.assertIn(("LOCK", (str(level), "RELEASED", "OPENED")), kinds)
        mech.close_flap(level)
        self.assertIn(("FLAP", (str(level), "CLOSED")), [(e.kind, e.args) for e in svc.d.poll_events()])

    def test_cli_commands(self):
        svc, _, _ = make_service()
        self.assertIn("positions", service_cli.run_command(svc, ["layout"]))
        self.assertIn("homed", service_cli.run_command(svc, ["home"]))
        self.assertIn("PASS", service_cli.run_command(svc, ["soak", "50"]))
        with self.assertRaises(ValueError):
            service_cli.run_command(svc, ["bogus"])

    def test_esp32_reset_is_detected_and_reconfigured(self):
        svc, _, t = make_service()
        svc.ensure_homed()
        t.machine.configured = False                 # as after a WDT reset: defaults, no CFG yet
        t.machine.cfg.unlock_max_s = 99
        svc.ensure_homed()
        self.assertTrue(svc.status().configured)
        self.assertEqual(t.machine.cfg.unlock_max_s, svc.cfg.unlock_max_s)

    def test_cli_jog_and_cfg(self):
        svc, mech, _ = make_service()
        service_cli.run_command(svc, ["home"])
        self.assertIn("pos 300", service_cli.run_command(svc, ["jog", "300"]))
        self.assertIn("temporary", service_cli.run_command(svc, ["cfg", "sgthrs", "80"]))
        self.assertEqual(mech.driver[1], 80)


class ScriptedTransport:
    """Each written line releases the next batch of reply lines (like a slow ESP32)."""

    def __init__(self, batches):
        self.batches = collections.deque(batches)
        self.written: list[str] = []
        self.buf: collections.deque[str] = collections.deque()

    def write_line(self, line):
        self.written.append(line)
        self.buf.extend(self.batches.popleft() if self.batches else [])

    def read_line(self, timeout):
        return self.buf.popleft() if self.buf else None

    def close(self):
        pass


STATUS_OK = "OK STATUS homed=1 sector=1 pos=0 fault=NONE flaps=111 locks=000 door=1 cfg=1"


class RequestMatchingTest(unittest.TestCase):
    def test_late_reply_is_dropped_by_resync(self):
        t = ScriptedTransport([[], ["OK AT 1", "OK PONG 1"], [STATUS_OK]])
        d = Esp32Carousel(t)
        with self.assertRaises(HalError) as cm:
            d.goto(1)                                # reply comes too late
        self.assertEqual(cm.exception.code, "TIMEOUT")
        self.assertEqual(d.status().sector, 1)       # not confused by the late "OK AT 1"
        self.assertEqual(t.written, ["GOTO 1", "PING", "STATUS"])

    def test_wrong_keyword_and_wrong_sector_are_errors(self):
        d = Esp32Carousel(ScriptedTransport([["OK AT 3"]]))
        with self.assertRaises(HalError) as cm:
            d.clear()
        self.assertEqual(cm.exception.code, "PROTO")
        d = Esp32Carousel(ScriptedTransport([["EVT DOOR OPEN", "OK AT 1"]]))
        with self.assertRaises(HalError) as cm:
            d.goto(2)
        self.assertEqual(cm.exception.code, "POSITION")
        self.assertEqual(d.poll_events()[0].kind, "DOOR")


class SerialTransportTest(unittest.TestCase):
    def test_read_line_with_zero_timeout_reads_the_port(self):
        master, slave = os.openpty()
        t = SerialTransport(os.ttyname(slave))
        try:
            self.assertIsNone(t.read_line(0.0))
            os.write(master, b"EVT FLAP 0 OPEN\r\n")
            self.assertEqual(t.read_line(0.0), "EVT FLAP 0 OPEN")
        finally:
            t.close()
            os.close(master)
            os.close(slave)


if __name__ == "__main__":
    unittest.main()
