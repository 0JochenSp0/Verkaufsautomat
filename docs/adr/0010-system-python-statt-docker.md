# ADR 0010 – System-Python mit apt und systemd statt Docker

**Status:** angenommen (2026-11-22). Ersetzt ADR 0008.

## Kontext
ADR 0008 hat Docker als Laufzeit gewählt, weil auf dem Pi pip fehlt. Der Pi 3B hat aber nur 1 GB RAM. Docker-Daemon, Image-Builds und `privileged`-Container kosten Speicher, SD-Karten-Schreibzugriffe und machen die Fehlersuche schwerer. Der Betreiber will deshalb weder Docker noch eine venv.

## Entscheidung
- **Die App läuft mit dem System-Python** (Debian trixie, Python 3.13) direkt aus dem Projektordner. Es gibt kein Paket-Install und keine venv. Aufruf aus `software/` mit `PYTHONPATH=src:firmware/esp32:../cad/lib`. Die Tests setzen den Pfad selbst (`tests/_paths.py`).
- **Abhängigkeiten nur aus apt:**
  - jetzt: `python3-serial`, `gpiod`, `curl`
  - ab M2: `python3-pygame`, `python3-segno`
  - Für HTTPS zu PayPal reicht die stdlib (`urllib`).
- **Werkzeuge außerhalb von apt** kommen per `pipx`. Das betrifft `esptool` (ESP32 flashen), `mpremote` (Dateien auf den ESP32 laden) und `ruff`. Es sind nur Entwicklerwerkzeuge, die App hängt nicht von ihnen ab.
- **Betrieb ab M2:** eine systemd-Unit mit `Restart=always` und `WatchdogSec`. Die App meldet sich per `sd_notify` über einen stdlib-Socket. Dazu kommt der Hardware-Watchdog (`RuntimeWatchdogSec`). Die Recovery liest beim Dienststart das Journal. Die Unit wird mit der Verkaufs-App in M2 geschrieben.
- **Daten** liegen weiter in `./data` (Journal, `secrets.env`, Firmware-Cache). Die App läuft als normaler Benutzer in den Gruppen `dialout`, `gpio` und `video`, nicht als root.
- **Seriell:** `/dev/esp32` (udev-Symlink auf die USB-Brücke des ESP32, ADR 0012).

## Alternativen
- **Docker (ADR 0008):** feste Versionen und reproduzierbar, aber mehr Ressourcen und `privileged` mit vollem Hostzugriff.
- **venv mit pip:** feste Versionen, aber zusätzlicher Platz und Pflegeaufwand. Für vier apt-Pakete lohnt sich das nicht.

## Folgen
- ✅ Weniger RAM und weniger Schichten. Debuggen geht direkt auf dem Host. Die App braucht keine root-Rechte, `privileged` entfällt.
- 🔶 Die Versionen legt Debian fest, nicht das Repo. Ein `apt upgrade` kann sie ändern. Deshalb nach Updates die Tests laufen lassen. Die Firmware-Version ist weiterhin per SHA-256 in `flash.sh` festgelegt.
- ⚠️ esptool aus Debian (4.7) enthält keinen Stub-Flasher für den klassischen ESP32, `--erase-all` scheitert damit (2026-11-23). esptool kommt deshalb per pipx (≥ 5, Bindestrich-Syntax `write-flash`, `default-reset`). Liegt das apt-Paket noch daneben, gewinnt `~/.local/bin` im `PATH`. Besser ist `sudo apt remove esptool`.
- Die SD-Karten-Maßnahmen aus ADR 0008 gelten weiter: Industrie-SD oder SSD, `noatime`, SQLite mit WAL und `synchronous=FULL`, tägliches Backup.
