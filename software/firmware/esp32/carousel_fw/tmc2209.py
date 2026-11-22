"""Minimal TMC2209 single-wire UART register writer (MicroPython/CPython).

⚠️ Register values are starting points from the datasheet and must be tuned on
the M1 test bench (SGTHRS in particular). StallGuard4 only works in StealthChop.
"""

GCONF = 0x00
IHOLD_IRUN = 0x10
TCOOLTHRS = 0x14
SGTHRS = 0x40
CHOPCONF = 0x6C

_MRES = {256: 0, 128: 1, 64: 2, 32: 3, 16: 4, 8: 5, 4: 6, 2: 7, 1: 8}


def crc8(data):
    """CRC8 as specified in the TMC2209 datasheet (poly x^8+x^2+x+1, LSB-first)."""
    crc = 0
    for byte in data:
        for _ in range(8):
            if ((crc >> 7) ^ (byte & 0x01)) & 0x01:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
            byte >>= 1
    return crc


def write_datagram(addr, reg, value):
    d = [0x05, addr & 0x03, (reg | 0x80) & 0xFF,
         (value >> 24) & 0xFF, (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF]
    d.append(crc8(d))
    return bytes(d)


def chopconf_for(microsteps, base=0x10000053):
    if microsteps not in _MRES:
        raise ValueError("microsteps")
    return (base & ~(0x0F << 24)) | (_MRES[microsteps] << 24)


class TMC2209:
    def __init__(self, uart, addr=0):
        self.uart = uart
        self.addr = addr

    def write(self, reg, value):
        self.uart.write(write_datagram(self.addr, reg, value))

    def setup(self, microsteps=16, irun=16, ihold=6, sgthrs=60, tcoolthrs=0xFFFFF):
        # pdn_disable (bit6) so UART works, mstep_reg_select (bit7) so MRES is used
        self.write(GCONF, (1 << 6) | (1 << 7))
        self.write(CHOPCONF, chopconf_for(microsteps))
        self.write(IHOLD_IRUN, (ihold & 0x1F) | ((irun & 0x1F) << 8) | (6 << 16))
        self.write(TCOOLTHRS, tcoolthrs)
        self.write(SGTHRS, sgthrs & 0xFF)
