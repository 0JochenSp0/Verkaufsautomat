# ADR 0007 – ESP32 (klassisch, MicroPython) statt RP2040 Pico, Flashen über den Pi

**Status:** angenommen (2026-11-22). Löst ADR 0002 ab.

## Kontext
Bisher war ein RP2040 Pico als Coprozessor für Motion und I/O vorgesehen (ADR 0002). Der Betreiber will einen ESP32 einsetzen. Der Pi soll ihn selbst flashen können, ohne PC und ohne USB-Kabel im Gerät. Die Anforderungen aus ADR 0002 bleiben gleich: jitterarme Schritte, Homing, Index- und Stall-Prüfung, zeitbegrenzte Schlösser und Heartbeat-Überwachung, auch wenn der Pi ausfällt.

## Entscheidung
- **Chip:** ESP32 klassisch auf einem WROOM-32-DevKit. 🔶 Ich hatte den ESP32-S3 empfohlen, weil er mehr freie GPIOs und weniger Strapping-Fallen hat. Der Betreiber hat sich für den klassischen ESP32 entschieden. Das ist machbar, siehe Risiken.
- **Firmware:** weiterhin **MicroPython**. Die Logik (`carousel_fw/machine_logic.py`, `protocol.py`, `tmc2209.py`) ist unverändert und bleibt unter CPython testbar. Nur `software/firmware/esp32/main.py` ist chipspezifisch.
- **Verbindung:** eine Leitung für alles.
  - Pi GPIO14/15 ↔ ESP32 **UART0** (GPIO3/1). Darüber laufen Protokoll v1, ROM-Bootloader und REPL. `main.py` liest das Protokoll über `sys.stdin`/`sys.stdout`, schaltet Ctrl-C ab und gibt nichts per `print` aus.
  - Pi GPIO23 → **EN**, Pi GPIO24 → **GPIO0**. Der Pi zieht die Leitungen nur auf low oder lässt sie hochohmig.
- **Update:** `software/firmware/esp32/flash.sh` (im Container) flasht immer vollständig neu: Bootloader, `write-flash --erase-all` (ein esptool-Aufruf) mit gepinntem MicroPython-Image samt SHA-256, Reset, `mpremote cp`, `PING`. Konfiguration geht nicht verloren, denn der Pi sendet nach jedem Connect alle `CFG`.
- **Kein WLAN, kein BT, kein OTA.** Die Firmware importiert `network` nicht, Updates kommen nur über den Pi.
- **Protokoll:** unverändert v1, jetzt in `docs/protocol-esp32.md`.

## Alternativen
- **ESP32-S3** (natives USB, mehr GPIOs): empfohlen, nicht gewählt.
- **ESP32-C3/C6:** zu wenige GPIOs für 3 Schlösser, 3 Reeds, Tür, 2 Hall-Sensoren, STEP/DIR/EN/DIAG und TMC-UART.
- **USB-Kabel Pi ↔ DevKit** für Flashen und Betrieb: einfacher zu flashen. Nicht gewählt, weil der USB-Stecker im Kühlschrank stört und die USB-UART-Brücke den Chip beim Öffnen des Ports resetten kann.
- **C++ (Arduino/ESP-IDF):** bessere Timings. Aber die Firmware müsste neu geschrieben werden, und die Simulator-Tests würden sie nicht mehr prüfen.
- **Beim Pico bleiben:** PIO für saubere Schritte, aber nicht gewünscht.

## Folgen
- ⚠️ **Strapping- und Sonderpins:**
  - tabu: GPIO 5, 12, 14 und 15 (Boot-Pegel bzw. Signale beim Booten) und 6–11 (Flash)
  - GPIO 34–39 sind reine Eingänge ohne Pull-up
  - Schloss-Gates liegen auf GPIO 4/18/19, die beim Booten ruhig bleiben, mit 10 kΩ Pull-down
  - Pinbelegung: `electronics/pinout.md`
- ⚠️ **UART0 wird geteilt:** Nach jedem Reset kommen ROM- und MicroPython-Bootmeldungen. Der Pi-Treiber verwirft Zeilen, die nicht mit `OK`, `ERR` oder `EVT` beginnen. Ein Absturz der Firmware landet in der REPL, der Hardware-WDT (3 s) resettet dann.
- ⚠️ **Kein PIO:** Die Schritte erzeugt eine Busy-Loop, die durch den FreeRTOS-Tick und die GC jittert. Für den M1-Prüfstand ist das voraussichtlich genug. Wenn der Soak-Test Schrittverluste zeigt, wird auf `esp32.RMT` umgestellt (`# shortcut:` in `main.py`).
- ⚠️ **USB am DevKit nie gleichzeitig mit der Pi-UART stecken.** Die CP2102 auf dem DevKit hängt ebenfalls an GPIO1/3.
- **Fail-secure bleibt hardwareseitig:** Bei Reset, im Bootloader und beim Flashen sind die GPIOs hochohmig. Die Pull-downs halten die Schlösser zu, der Pull-up an TMC-EN hält den Motor aus. Das muss in der M1-Abnahme gemessen werden.
- Umbenannt: `firmware/pico` → `firmware/esp32`, `vending.hal.pico` → `vending.hal.esp32` (`Esp32Carousel`), params-Schlüssel `pico` → `esp32`.
