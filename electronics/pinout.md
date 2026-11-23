# Pinbelegung

## ESP32 (klassisch, WROOM-32 DevKit) – `software/firmware/esp32/main.py`
Entscheidung und Begründung: ADR 0007, Anbindung an den Pi über USB: ADR 0012.

| GPIO | Funktion | Richtung | Bemerkung |
|---|---|---|---|
| GPIO1 (TX0) / GPIO3 (RX0) | UART0 ↔ CP2102 auf dem DevKit ↔ USB ↔ Pi `/dev/esp32` | | Protokoll, Flashen und REPL über dieselbe Leitung. Nicht extern beschalten |
| EN / GPIO0 | Auto-Reset der CP2102 (RTS → EN, DTR → GPIO0) | in | nur esptool schaltet DTR/RTS. `SerialTransport` lässt beide gemeinsam gesetzt, das löst keinen Reset aus |
| GPIO17 / GPIO16 | UART2 TX/RX → TMC2209 PDN_UART | out/in | Eindraht: TX über 1 kΩ, RX direkt |
| GPIO26 | TMC2209 STEP | out | |
| GPIO27 | TMC2209 DIR | out | |
| GPIO25 | TMC2209 EN (aktiv low) | out | **10 kΩ Pull-up auf 3,3 V**, damit der Motor bei Reset und im Bootloader aus ist |
| GPIO34 | TMC2209 DIAG (StallGuard) | in | reiner Eingang ohne Pull, der TMC treibt push-pull |
| GPIO32 | Hall HOME | in, Pull-up | aktiv low, Open-Drain. Zusätzlich 10 kΩ extern, weil der interne Pull-up schwach ist |
| GPIO33 | Hall INDEX | in, Pull-up | wie HOME |
| GPIO4 / GPIO18 / GPIO19 | Schloss 1–3 (MOSFET-Gate) | out | **10 kΩ Pull-down**, damit das Schloss bei Reset, im Bootloader und beim Flashen zu bleibt |
| GPIO21 / GPIO22 / GPIO23 | Reed Klappe 1–3 | in, Pull-up | geschlossen = low, RC-Filter 1 kΩ/100 nF, TVS |
| GPIO13 | Türkontakt Haupttür | in, Pull-up | geschlossen = low |
| GPIO35 | 24-V-Messung (geplant, M1) | in (ADC1) | Teiler 100 kΩ/10 kΩ + 100 nF, 30 V → 2,73 V bei 11 dB. Reiner Eingang ohne Pull |
| GPIO2 | LED (onboard) | out | Lebenszeichen. Strapping-Pin, keine externe Last anschließen |

**Nicht belegen:** GPIO5, 12, 14 und 15 (Strapping-Pins bzw. Signale beim Booten; GPIO12 high beim Reset → falsche Flash-Spannung) und GPIO6–11 (interner Flash).

⚠️ GPIO1/3 nicht extern beschalten, die CP2102 auf dem Board treibt sie. Versorgung des DevKits über USB vom Pi (ADR 0012).

Sensorleitungen aus dem Innenraum bekommen RC-Filter, TVS-Diode (3,3 V) und Steckverbinder IP67 (M8/M12).

## Raspberry Pi 3B
| GPIO | Funktion | Bemerkung |
|---|---|---|
| USB | ESP32-DevKit (`/dev/esp32`, udev-Regel) | ADR 0012 |
| 14 / 15 | frei | früher UART zum ESP32 (ADR 0007) |
| 23 / 24 | frei | früher ESP32 EN/BOOT (ADR 0007) |
| 2 / 3 | frei (I²C, z. B. Füllstand M3b) | keine RTC, nur NTP (2026-11-22) |
| 4 | 1-Wire DS18B20 (3 Fühler: Luft, Eier-Ebene, Box) | 4,7 kΩ Pull-up, `dtoverlay=w1-gpio` |
| 17 | Relais Kühlschrank (über Treiber) | **M3**: Relais-/Schützspule 24 V über MOSFET |
| 27 | frei | Innenraumheizung gestrichen (Q8) |
| 22 | Heizung Elektronikbox, 24-V-PTC (MOSFET) | 10 kΩ Pull-down, ADR 0009 |
| 5 / 6 / 13 | Taster A (Eier) / B (Honig) / Abbruch (ADR 0011) | Pull-up, aktiv low, RC-Filter |
| 12 / 16 | LED Taster A grün / rot | Low-Side-MOSFET, 10 kΩ Pull-down (Pi aus = LED aus) |
| 20 / 21 | LED Taster B grün / rot | wie A |
| 19 | frei | |
| 26 | Schlüsselschalter Service | Pull-up |
| HDMI/DSI | Display | |
