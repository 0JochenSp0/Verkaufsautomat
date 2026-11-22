"""Tests for the ESP32 firmware logic (runs under CPython against FakeMechanics)."""

import unittest

import _paths  # noqa: F401
from carousel_fw.machine_logic import Config, Fault, Machine, MotionError
from carousel_fw.protocol import Dispatcher
from carousel_fw.tmc2209 import chopconf_for, crc8, write_datagram

from vending.hal.sim import FakeMechanics, SimClock

REV = 96000
N = 4


def make(**mech_kw):
    mech = FakeMechanics(REV, N, levels=3, **mech_kw)
    cfg = Config()
    cfg.steps_per_rev, cfg.sectors, cfg.levels = REV, N, 3
    clock = SimClock()
    m = Machine(mech, cfg, clock=clock)
    return m, mech, clock


class HomingAndMotion(unittest.TestCase):
    def test_home_from_arbitrary_position(self):
        for start in (0, 1, 150, 40000, REV - 1):
            m, mech, _ = make(start_pos=start)
            self.assertEqual(m.home(), 0, start)
            self.assertTrue(m.homed)
            self.assertTrue(mech.index_active())

    def test_home_offset(self):
        m, mech, _ = make(home_offset=5000)
        m.cfg.home_offset = 5000
        m.home()
        self.assertEqual(mech.true_pos, 5000)

    def test_goto_all_sectors_shortest_path(self):
        m, mech, _ = make()
        m.home()
        for s in (1, 3, 2, 0, 3):
            before = mech.total_steps
            self.assertEqual(m.goto(s), s)
            self.assertEqual(mech.true_pos, m.sector_target(s))
            self.assertLessEqual(mech.total_steps - before, REV // 2)

    def test_goto_requires_homing(self):
        m, _, _ = make()
        with self.assertRaises(MotionError) as cm:
            m.goto(1)
        self.assertEqual(cm.exception.code, Fault.NOT_HOMED)

    def test_single_stall_faults_by_default(self):
        m, mech, _ = make()
        m.home()
        mech.stall_after = 1000
        with self.assertRaises(MotionError) as cm:
            m.goto(2)
        self.assertEqual(cm.exception.code, Fault.STALL)
        self.assertFalse(m.homed)

    def test_single_stall_is_retried_when_enabled(self):
        m, mech, _ = make()
        m.cfg.retries = 1
        m.home()
        mech.stall_after = 1000
        self.assertEqual(m.goto(2), 2)
        self.assertEqual(m.fault, Fault.NONE)

    def test_persistent_block_faults_and_unhomes(self):
        m, mech, _ = make()
        m.home()
        mech.blocked = True
        with self.assertRaises(MotionError) as cm:
            m.goto(2)
        self.assertEqual(cm.exception.code, Fault.STALL)
        self.assertFalse(m.homed)
        self.assertEqual(m.fault, Fault.STALL)
        with self.assertRaises(MotionError):
            m.goto(1)

    def test_lost_steps_detected_by_index(self):
        m, mech, _ = make()
        m.home()
        mech.slip_steps = 2000          # far outside the index window
        with self.assertRaises(MotionError) as cm:
            m.goto(1)
        self.assertEqual(cm.exception.code, Fault.INDEX)

    def test_never_rotate_with_open_flap(self):
        m, mech, _ = make()
        m.home()
        mech.force_flap(1)
        with self.assertRaises(MotionError) as cm:
            m.goto(2)
        self.assertEqual(cm.exception.code, "FLAP_OPEN")

    def test_home_fail_when_sensor_missing(self):
        m, mech, _ = make(home_width=0)
        with self.assertRaises(MotionError) as cm:
            m.home()
        self.assertEqual(cm.exception.code, Fault.HOME_FAIL)


class Locks(unittest.TestCase):
    def test_unlock_only_when_positioned(self):
        m, _, _ = make()
        with self.assertRaises(MotionError):
            m.unlock(0, 10)

    def test_unlock_open_release_cycle(self):
        m, mech, clock = make()
        m.home()
        m.unlock(1, 30)
        self.assertTrue(mech.locks[1])
        self.assertFalse(mech.open_flap(0), "other flaps stay locked")
        self.assertTrue(mech.open_flap(1))
        ev = m.tick()
        self.assertIn("EVT FLAP 1 OPEN", ev)
        self.assertIn("EVT LOCK 1 RELEASED OPENED", ev)
        self.assertFalse(mech.locks[1], "solenoid de-energised once flap is open")
        mech.close_flap(1)
        self.assertIn("EVT FLAP 1 CLOSED", m.tick())

    def test_unlock_timeout(self):
        m, mech, clock = make()
        m.home()
        m.unlock(0, 5)
        clock.advance(4.9)
        m.touch()
        self.assertEqual(m.tick(), [])
        clock.advance(0.2)
        self.assertIn("EVT LOCK 0 RELEASED TIMEOUT", m.tick())
        self.assertFalse(mech.locks[0])

    def test_unlock_capped(self):
        m, _, _ = make()
        m.home()
        self.assertEqual(m.unlock(0, 9999), m.cfg.unlock_max_s)

    def test_only_one_flap_at_a_time_and_no_motion_while_unlocked(self):
        m, _, _ = make()
        m.home()
        m.unlock(0, 10)
        with self.assertRaises(MotionError):
            m.unlock(1, 10)
        with self.assertRaises(MotionError):
            m.goto(1)

    def test_forced_flap_raises_alarm(self):
        m, mech, _ = make()
        mech.force_flap(2)
        ev = m.tick()
        self.assertIn("EVT ALARM FLAP_FORCED 2", ev)

    def test_heartbeat_loss_enters_safe_state(self):
        m, mech, clock = make()
        m.home()
        m.unlock(0, 60)
        clock.advance(m.cfg.hb_timeout_s + 1)
        ev = m.tick()
        self.assertIn("EVT SAFE HEARTBEAT", ev)
        self.assertFalse(any(mech.locks))
        self.assertFalse(mech.enabled)
        self.assertFalse(m.homed)
        self.assertEqual(m.tick(), [], "safe event only once")


class ProtocolTest(unittest.TestCase):
    def test_roundtrip(self):
        m, _, _ = make()
        d = Dispatcher(m)
        self.assertEqual(d.handle("PING"), "OK PONG 1")
        self.assertEqual(d.handle("GOTO 1"), "ERR NOT_HOMED")
        self.assertEqual(d.handle("HOME"), "OK AT 0")
        self.assertEqual(d.handle("GOTO 3"), "OK AT 3")
        self.assertTrue(d.handle("STATUS").startswith("OK STATUS homed=1 sector=3"))
        self.assertEqual(d.handle("CFG nonsense 1"), "ERR BAD_KEY nonsense")
        self.assertEqual(d.handle("GOTO"), "ERR BAD_ARGS GOTO")
        self.assertEqual(d.handle("FOO"), "ERR UNKNOWN FOO")
        self.assertEqual(d.handle("UNLOCK 2 10"), "OK UNLOCKING 2 10")


class TmcTest(unittest.TestCase):
    def test_datagram_shape(self):
        dg = write_datagram(0, 0x00, 0x000000C0)
        self.assertEqual(len(dg), 8)
        self.assertEqual(dg[0], 0x05)
        self.assertEqual(dg[2], 0x80)
        self.assertEqual(dg[-1], crc8(dg[:-1]))

    def test_crc_changes_with_data(self):
        self.assertNotEqual(crc8(bytes([5, 0, 0x80, 0, 0, 0, 1])), crc8(bytes([5, 0, 0x80, 0, 0, 0, 2])))

    def test_microstep_encoding(self):
        self.assertEqual((chopconf_for(16) >> 24) & 0x0F, 4)
        self.assertEqual((chopconf_for(256) >> 24) & 0x0F, 0)


if __name__ == "__main__":
    unittest.main()
