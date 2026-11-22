# Aufbauanleitung M1 – Karussell-Prüfstand

Ziel: Ein Karussell (mindestens 1 Ebene, besser 3) auf einer Grundplatte, Antrieb, Sensoren und 1 Testklappe. Gesteuert über Pi 3B und ESP32 (ADR 0007).

## 1. Maße festlegen
1. Kühlschrank-Innenmaße, Eierschachtel und Glas messen, in `cad/params/params.json` eintragen (`TODO_MEASURE`).
2. `python3 cad/lib/geometry.py` → Sektorzahl, Zuschnitt, Fensterbreite prüfen.
3. Mit FreeCAD: `freecadcmd cad/macros/carousel.py` → `cad/out/carousel_cutlist.txt`, `carousel.step`.

## 2. Mechanik
1. Grundplatte (Multiplex, Prüfstand) mit Drehteller-Lager. Unteres Flanschlager mittig.
2. Welle mit Boden(-ronden) und Trennwänden, Magnete je Sektor auf Radius `R − index_magnet_radius_offset` unter dem untersten Boden, **Home-Magnet** auf einem eigenen, kleineren Radius.
3. Motor und Schneckengetriebe unter der Grundplatte, Kupplung auf die Welle.
4. Hall-Sensoren an einem festen Halter: INDEX auf dem Radius der Sektormagnete, HOME auf dem Home-Radius.
5. **Selbsthemmung prüfen:** Motor stromlos, am Rand kräftig drehen. Es darf sich nichts bewegen.

## 3. Elektronik (nur Kleinspannung)
Verdrahtung nach [`electronics/pinout.md`](../../electronics/pinout.md). Die Pull-ups und Pull-downs an EN und an den Schloss-Gates nicht vergessen.
- TMC2209: VM = 24 V (100 µF direkt am Modul), VIO = 3,3 V vom ESP32-DevKit. Motorstrom per UART (`irun` in `tmc2209.py`).
- Schloss: 24 V → Schloss → MOSFET (Drain), Freilaufdiode parallel zum Schloss.

## 4. Software
Pi 3B:
```bash
sudo raspi-config   # Interface Options → Serial: Login-Shell NEIN, Hardware JA
echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt && sudo reboot
```
In `/boot/firmware/config.txt` zusätzlich `gpio=23,24=ip,np` eintragen. Dann hält der Pi die ESP32-Leitungen EN und GPIO0 beim Booten nicht fest.

Pakete (ADR 0010, einmalig, kein Docker, keine venv):
```bash
sudo apt install python3-serial esptool gpiod curl pipx && pipx install mpremote ruff
sudo usermod -aG dialout,gpio $USER   # danach ab- und wieder anmelden (ab M2 zusätzlich video, ADR 0010)
mkdir -p data          # in der Repo-Wurzel
```
ESP32 flashen (vom Pi, USB am DevKit dabei **nicht** stecken):
```bash
cd software && export PYTHONPATH=src:firmware/esp32:../cad/lib
firmware/esp32/flash.sh
```
Erster Test:
```bash
python3 -m vending.core.service_cli --port /dev/ttyAMA0
service> status
service> home
service> next
```

## 5. Einstellen
1. **home_offset_steps:** Nach `home` Sektor 0 mittig vor die Klappe bringen (Schritte zählen bzw. `pos` in `status`) und in `params.json` eintragen.
2. **StallGuard (`sgthrs`)** in `carousel_fw/tmc2209.py`: Mit der Hand bremsen und den Wert erhöhen, bis eine Blockade sicher erkannt wird, normale Fahrten aber nicht abbrechen.
3. **Geschwindigkeit:** `max_speed_sps`. Bei 1:30 braucht eine halbe Umdrehung ca. 12 s bei 4000 sps. Bei Bedarf ein kleineres Übersetzungsverhältnis wählen, sofern es selbsthemmend bleibt.

## 6. Abnahme M1
| Test | Befehl / Vorgehen | Kriterium |
|---|---|---|
| Dauerlauf | `service> soak 500` | 0 Fehler |
| Blockade | Während `goto` blockieren | `STALL` in < 2 s, sofort Fault (keine automatische Wiederholung, `retries` = 0) |
| Stromtrennung | 24 V während der Fahrt trennen, wieder einschalten | Verkauf erst nach `home`. Schloss blieb zu. |
| Heartbeat | Pi-Programm beenden | nach `hb_timeout_s` `SAFE`, Motor stromlos |
| Selbsthemmung | Bei aktivem Schloss am Karussell drehen | keine Bewegung |
| Klappe | `unlock 0 10`, öffnen, schließen | Ereignisse OPEN/RELEASED/CLOSED, Falle rastet ein |
| ⚠️ Fail-secure beim Flashen | Multimeter/Oszi an den Schloss-Gates (GPIO4/18/19) und TMC-EN (GPIO25), dann `flash.sh` und EN-Reset | Gates bleiben die ganze Zeit < 0,5 V, EN bleibt high (Motor aus) |
| Boot-Rauschen | Nach `flash.sh` die Service-CLI starten, ESP32 per EN resetten | CLI meldet keinen Protokollfehler, `status` funktioniert nach `clear` + `home` |
