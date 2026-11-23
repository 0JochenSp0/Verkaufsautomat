#!/usr/bin/env bash
# Full re-flash of the ESP32 from the Pi over USB: MicroPython image + carousel firmware files.
# Run on the Pi from software/:  firmware/esp32/flash.sh   (apt: curl; pipx: esptool >= 5, mpremote)
# The DevKit's CP2102 auto-reset circuit (DTR/RTS -> GPIO0/EN) enters the bootloader (ADR 0012).
# Stop anything else that uses the port (service CLI, sales app) before running this.
set -euo pipefail

PORT=${PORT:-/dev/esp32}
FW_URL=https://micropython.org/resources/firmware/ESP32_GENERIC-20260824-v1.29.0.bin
FW_SHA256=e67ad6015a0a504c1fec9aa9bbf589d0432ed28e62546f4f8dd8a147f8bd95f6
HERE=$(cd "$(dirname "$0")" && pwd)
SW=$(cd "$HERE/../.." && pwd)
FW=$SW/../data/cache/$(basename "$FW_URL")

mkdir -p "$(dirname "$FW")"
[ -f "$FW" ] || curl -fsSL -o "$FW" "$FW_URL"
echo "$FW_SHA256  $FW" | sha256sum -c -

echo "== flash MicroPython"
esptool --chip esp32 --port "$PORT" --baud 460800 --before default-reset --after hard-reset \
  write-flash --erase-all -z 0x1000 "$FW"

echo "== upload files"
sleep 5   # first MicroPython boot formats the filesystem
cd "$HERE"
mpremote connect "$PORT" fs cp -r carousel_fw : + fs cp main.py : + reset

echo "== check"
sleep 3
cd "$SW"
PYTHONPATH=src python3 -c "
from vending.hal.esp32 import Esp32Carousel, SerialTransport
print('PONG, protocol v%d' % Esp32Carousel(SerialTransport('$PORT')).ping())
"
