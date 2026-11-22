"""End-to-end: MotionService -> Esp32Carousel -> line protocol -> firmware logic -> FakeMechanics."""

import unittest

import _paths  # noqa: F401

from vending import config as config_mod
from vending.core import service_cli
from vending.core.motion_service import MotionService
from vending.hal.interfaces import HalError
from vending.hal.esp32 import Esp32Carousel
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
        mech.stall_after = 10           # single stall -> retried transparently
        self.assertTrue(svc.soak(20, seed=2).ok)

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


if __name__ == "__main__":
    unittest.main()
