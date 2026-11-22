# ADR 0008 – Docker als Laufzeit für Entwicklung und Betrieb

**Status:** angenommen (2026-11-22)

## Kontext
Auf dem Pi fehlen pip und andere Werkzeuge (pyserial, esptool, mpremote, ruff). Das Projekt soll im Projektordner als Container laufen, für Entwicklung, Tests, Flashen des ESP32 und später die Verkaufs-App.

## Entscheidung
- **Ein Image** (`Dockerfile`) mit den Abhängigkeiten in festen Versionen. Der **Code ist per Bind-Mount** eingebunden (`./:/app`), deshalb brauchen Änderungen keinen Rebuild. Laufzeitdaten wie SQLite-Journal, `secrets.env` und der Firmware-Cache liegen in `./data` → `/data`. Der Ordner ist in `.gitignore`.
- **Aufruf:** `docker compose run --rm vending <befehl>`. In M1 gibt es noch keinen Dauerdienst. Ab M2 kommt die Verkaufs-App mit `restart: unless-stopped` und Healthcheck dazu. Die Recovery liest dann beim Containerstart das Journal.
- **Installation:** Debian-Pakete `docker.io` und `docker-compose`.
- **Hardwarezugriff:** `privileged: true`. 🔶 Ich hatte empfohlen, nur einzelne Geräte freizugeben (`/dev/ttyAMA0`, `/dev/gpiochip0`, später `/dev/dri`, `/sys/bus/w1`). Mit `privileged` hat der Container, der später PayPal-Secrets und die LAN-Web-UI enthält, vollen Hostzugriff. **Vor M4 auf einzelne Geräte umstellen.**
- **UART-Name im Container:** `/dev/ttyAMA0`. Den udev-Symlink `/dev/serial0` gibt es im Container nicht.
- **Read-only-Root entfällt** (ändert N5). 🔶 Ich hatte eine eigene Datenpartition empfohlen, auf der auch `/var/lib/docker` liegt.
- **Tests:** Sie laufen weiterhin auch ohne Docker mit stdlib (`python3 -m unittest`), damit sie auf jedem Pi funktionieren.

## Alternativen
- **Direkt auf dem Host mit systemd und venv:** weniger Schichten. Aber Abhängigkeiten ohne pip zu verwalten ist mühsam, und Entwicklung und Betrieb würden auseinanderlaufen.
- **Nur einzelne Geräte freigeben:** sicherer, aber mehr Konfiguration. Ist für M4 vorgemerkt.
- **Read-only-Root mit eigener Datenpartition für `/var/lib/docker` und `/data`:** robuster bei Stromausfall, aber aufwendiger einzurichten.

## Folgen
- ⚠️ **SD-Karte:** Ohne read-only Root steigt das Risiko, dass das Dateisystem bei Stromausfall beschädigt wird. Gegenmaßnahmen:
  - Industrie-SD-Karte oder SSD per USB
  - `noatime` (ist schon gesetzt)
  - SQLite mit WAL und `synchronous=FULL`
  - regelmäßiges Backup von `./data`
- ⚠️ **Gruppe `docker`:** Wer in dieser Gruppe ist, hat faktisch root-Rechte auf dem Pi.
- ⚠️ **Speicher:** Der Pi 3B hat nur 1 GB RAM. Image-Builds dauern deshalb länger, und das Image wird bewusst schlank gehalten (`python:3.13-slim`).
- **Watchdog:** Ab M2 übernehmen der Host-Watchdog (systemd `RuntimeWatchdogSec`) und der Container-Neustart. `sd_notify` aus dem Container entfällt, stattdessen gibt es einen Docker-Healthcheck.
