#!/usr/bin/env bash
# Full re-flash of the ESP32 from the Pi: MicroPython image + carousel firmware files.
# Run on the Pi from software/:  firmware/esp32/flash.sh   (apt: esptool gpiod curl; pipx: mpremote)
# Wiring (electronics/pinout.md): Pi GPIO14/15 <-> ESP32 GPIO3/1, Pi GPIO23 -> EN, Pi GPIO24 -> GPIO0.
# Stop anything else that uses the UART (service CLI, sales app) before running this.
set -euo pipefail

PORT=${PORT:-/dev/ttyAMA0}
CHIP=${GPIOCHIP:-gpiochip0}
EN=23
BOOT=24
FW_URL=https://micropython.org/resources/firmware/ESP32_GENERIC-20260824-v1.29.0.bin
FW_SHA256=e67ad6015a0a504c1fec9aa9bbf589d0432ed28e62546f4f8dd8a147f8bd95f6
HERE=$(cd "$(dirname "$0")" && pwd)
SW=$(cd "$HERE/../.." && pwd)
FW=$SW/../data/cache/$(basename "$FW_URL")

# gpiod v2: gpioset drives a line only while it runs; gpioget turns it back into an input,
# so the DevKit pull-ups take over (lines are never driven high by the Pi).
declare -A HOLD=()   # line -> pid of the gpioset holding it low
pull_low() { gpioset -c "$CHIP" "$1=0" & HOLD[$1]=$!; }
release() {
  kill "${HOLD[$1]}" 2>/dev/null || true
  wait "${HOLD[$1]}" 2>/dev/null || true
  unset "HOLD[$1]"
  gpioget -c "$CHIP" "$1" >/dev/null
}
reset_pulse() { pull_low $EN; sleep 0.1; release $EN; }
cleanup() { for l in "${!HOLD[@]}"; do release "$l" || true; done; }
trap cleanup EXIT

mkdir -p "$(dirname "$FW")"
[ -f "$FW" ] || curl -fsSL -o "$FW" "$FW_URL"
echo "$FW_SHA256  $FW" | sha256sum -c -

echo "== bootloader"
pull_low $BOOT
sleep 0.05
reset_pulse
sleep 0.3
release $BOOT

esptool --chip esp32 --port "$PORT" --baud 115200 --before no_reset --after no_reset \
  write_flash --erase-all -z 0x1000 "$FW"

echo "== normal boot, upload files"
reset_pulse
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
