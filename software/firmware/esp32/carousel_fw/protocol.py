"""Line protocol Pi <-> ESP32. Spec: docs/protocol-esp32.md (MicroPython-compatible)."""

from carousel_fw import PROTO_VERSION
from carousel_fw.machine_logic import MotionError


class Dispatcher:
    def __init__(self, machine):
        self.m = machine

    def handle(self, line):
        """Handle one request line, return one response line (without newline)."""
        parts = line.strip().split()
        if not parts:
            return "ERR EMPTY"
        cmd = parts[0].upper()
        args = parts[1:]
        try:
            return self._dispatch(cmd, args)
        except MotionError as e:
            return ("ERR %s %s" % (e.code, e.msg)).rstrip()
        except (ValueError, IndexError):
            return "ERR BAD_ARGS %s" % cmd
        finally:
            # heartbeat counts from the *end* of a command: HOME or a half turn takes longer than hb_timeout_s
            self.m.touch()

    def _dispatch(self, cmd, a):
        m = self.m
        if cmd == "PING":
            return "OK PONG %d" % PROTO_VERSION
        if cmd == "CFG":
            m.configure(a[0], a[1])
            return "OK CFG %s" % a[0]
        if cmd == "HOME":
            return "OK AT %d" % m.home()
        if cmd == "GOTO":
            return "OK AT %d" % m.goto(int(a[0]))
        if cmd == "JOG":
            return "OK POS %d" % m.jog(int(a[0]))
        if cmd == "UNLOCK":
            return "OK UNLOCKING %d %d" % (int(a[0]), m.unlock(int(a[0]), int(a[1])))
        if cmd == "LOCK":
            m.lock(int(a[0]))
            return "OK LOCKED %d" % int(a[0])
        if cmd == "STATUS":
            return "OK STATUS " + m.status()
        if cmd == "CLEAR":
            m.clear()
            return "OK CLEARED"
        if cmd == "DISABLE":
            m.lock_all()
            m.hw.enable(False)
            m.homed = False
            m.sector = -1
            return "OK DISABLED"
        return "ERR UNKNOWN %s" % cmd
