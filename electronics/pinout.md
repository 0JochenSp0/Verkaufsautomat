# Pinbelegung

## ESP32 (klassisch, WROOM-32 DevKit) – `software/firmware/esp32/main.py`
Entscheidung und Begründung: ADR 0007.

| GPIO | Funktion | Richtung | Bemerkung |
|---|---|---|---|
| GPIO1 (TX0) | UART0 TX → Pi RXD (GPIO15) | out | Protokoll, Flashen und REPL über dieselbe Leitung, 3,3 V direkt |
| GPIO3 (RX0) | UART0 RX ← Pi TXD (GPIO14) | in | |
| EN | Reset ← Pi GPIO23 | in | Pi zieht nur auf low oder bleibt hochohmig, Pull-up und RC sitzen auf dem DevKit |
| GPIO0 | BOOT ← Pi GPIO24 | in | Pi zieht nur auf low oder bleibt hochohmig. Low beim Reset startet den Bootloader |
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
| GPIO2 | LED (onboard) | out | Lebenszeichen. Strapping-Pin, keine externe Last anschließen |

**Nicht belegen:** GPIO5, 12, 14 und 15 (Strapping-Pins bzw. Signale beim Booten; GPIO12 high beim Reset → falsche Flash-Spannung) und GPIO6–11 (interner Flash).

⚠️ Den USB-Anschluss am DevKit **nie gleichzeitig** mit der Pi-UART nutzen. Die CP2102 auf dem Board hängt ebenfalls an GPIO1/3.

Sensorleitungen aus dem Innenraum bekommen RC-Filter, TVS-Diode (3,3 V) und Steckverbinder IP67 (M8/M12).

## Raspberry Pi 3B
| GPIO | Funktion | Bemerkung |
|---|---|---|
| 14 / 15 | UART (PL011, `/dev/ttyAMA0`) ↔ ESP32 UART0 | `dtoverlay=disable-bt`, serielle Konsole aus |
| 23 | ESP32 EN (Reset) | nur low oder Eingang. `config.txt`: `gpio=23,24=ip,np` |
| 24 | ESP32 GPIO0 (BOOT) | nur low oder Eingang |
| 2 / 3 | I²C – DS3231 RTC | `dtoverlay=i2c-rtc,ds3231` |
| 4 | 1-Wire DS18B20 (4 Fühler) | 4,7 kΩ Pull-up, `dtoverlay=w1-gpio` |
| 17 | Relais Kühlschrank (über Treiber) | **M3**: Relais-/Schützspule 24 V über MOSFET |
| 27 | Relais Innenraumheizung (optional) | M3 |
| 22 | Heizung Elektronikfach 24 V (MOSFET) | M3, zusätzlich Bimetall-Thermostat in Reihe |
| 5 / 6 / 13 / 19 | Taster ◀ ▶ OK Abbruch | Pull-up, aktiv low |
| 12 | Taster-LED-Ring (PWM) | über MOSFET |
| 26 | Schlüsselschalter Service | Pull-up |
| HDMI/DSI | Display | |
