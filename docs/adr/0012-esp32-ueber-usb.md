# ADR 0012 – ESP32 über USB statt Pi-UART

**Status:** angenommen (2026-11-23). Löst in ADR 0007 die Abschnitte „Verbindung“ und „Update“ ab. Chip, MicroPython, Protokoll v1 und Pinbelegung aus ADR 0007 gelten weiter.

## Kontext
Laut ADR 0007 sollte der Pi den ESP32 über seine UART (GPIO14/15) betreiben und über GPIO23/24 (EN/GPIO0) flashen. Am Prüfstand hängt der ESP32-DevKit jetzt per USB-Kabel am Pi und wird dort sicher erkannt (CP2102, `10c4:ea60`). Der Betreiber will alles auf USB umstellen. Die CP2102 auf dem DevKit sitzt am UART0 (GPIO1/3) des ESP32. Für die Firmware ist das dieselbe Leitung wie vorher.

## Entscheidung
- **Verbindung:** USB-Kabel Pi ↔ DevKit. Darüber laufen Protokoll v1, ROM-Bootloader, REPL und die 5-V-Versorgung des ESP32. `main.py` und das Protokoll bleiben unverändert.
- **Gerätename:** Die udev-Regel `/etc/udev/rules.d/99-esp32.rules` legt den Symlink `/dev/esp32` an (VID/PID der CP2102). Dieser Name ist der Default in `SerialTransport`, `service_cli` und `flash.sh`.
- **Port öffnen:** `SerialTransport` lässt DTR und RTS so, wie Linux sie beim Öffnen setzt, nämlich beide gleichzeitig an. Dann bleibt die Auto-Reset-Schaltung ruhig. Nacheinander abgeschaltet (pyserial `dtr = rts = False`) erzeugen sie kurz „nur RTS“ → EN low → Reset (am Prüfstand gemessen, 2026-11-23).
- **Update:** `flash.sh` geht nur noch über USB. esptool setzt den ESP32 über DTR/RTS selbst in den Bootloader (`--before default_reset`). Der Ablauf bleibt sonst gleich: gepinntes Image samt SHA-256, `write_flash --erase-all`, `mpremote cp`, `PING`.
- **Pi-Pins:** GPIO14/15 und 23/24 werden frei. Die serielle Konsole und `dtoverlay=disable-bt` werden für den ESP32 nicht mehr gebraucht. Bluetooth bleibt trotzdem aus, weil es nicht genutzt wird.

## Alternativen
- **Pi-UART + GPIO23/24 (ADR 0007):** Dafür braucht es keinen USB-Stecker, aber mehr Verdrahtung, `raspi-config`, gpiod im Flash-Skript und einen ungetesteten Reset-Pfad. Abgelöst.
- **Beide Wege in `flash.sh`:** mehr Code für einen Weg, den niemand mehr nutzt.
- **`/dev/ttyUSB0` bzw. by-id-Symlink:** ohne Systemdatei. `ttyUSB0` kann sich aber bei weiteren USB-Seriell-Geräten ändern. Der Betreiber hat sich für einen eigenen Namen entschieden.

## Folgen
- 🔶 In ADR 0007 hatte ich gegen USB argumentiert (Stecker im Gerät, Reset beim Öffnen des Ports). Inzwischen sitzen Pi und ESP32 gemeinsam in der Box im Innenraum (ADR 0009). Das Kabel bleibt kurz und innerhalb der Box. Einen Reset beim Öffnen gibt es nicht, solange DTR und RTS gemeinsam gesetzt bleiben (gemessen). Kommt doch einer, meldet `STATUS` dann `cfg=0`, und `MotionService` verbindet neu.
- ⚠️ **Steckverbindung:** Das Kabel braucht eine Zugentlastung und einen gesicherten Stecker, denn der Kompressor vibriert. Fällt die Verbindung aus, geht der ESP32 nach `hb_timeout_s` in SAFE, und der Verkauf ist gesperrt.
- ⚠️ **Versorgung über den Pi:** Ein Reboot oder Absturz des Pi kann den ESP32 mit zurücksetzen. Das bleibt fail-secure: Die Pull-downs halten die Schloss-Gates unten, der Pull-up hält TMC-EN oben. Gemessen wird das in der M1-Abnahme.
- ⚠️ **GPIO1/3 nicht extern beschalten.** Die CP2102 treibt diese Pins.
- ⚠️ **udev-Regel nach VID/PID:** Ein zweiter CP2102 am Pi würde ebenfalls passen. Dann zusätzlich über `ATTRS{serial}` oder `KERNELS` (USB-Port) unterscheiden.
- esptool kommt per pipx statt aus apt, weil dem Debian-Paket der ESP32-Stub fehlt (siehe ADR 0010).
- Die EN-Reset-Tests der M1-Abnahme laufen jetzt über den EN-Taster des DevKits statt über einen Pi-GPIO.
