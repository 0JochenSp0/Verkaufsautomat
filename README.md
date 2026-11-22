# Verkaufsautomat – Wachteleier & Honig

DIY-Verkaufsautomat auf Basis eines gebrauchten Kühlschranks. Innen sitzt ein Karussell mit 3 Ebenen, außen drei Ausgabeklappen. Bezahlt wird per PayPal-QR, gesteuert über einen Raspberry Pi 3B.

| Ordner | Inhalt |
|---|---|
| `cad/` | FreeCAD-Makros (parametrisch), Parameter in `cad/params/params.json`, Geometrierechner |
| `electronics/` | Blockschaltbild, Pinbelegung, Leistungsbilanz, später KiCad |
| `software/` | Python-Steuerung (`vending`), ESP32-Firmware (MicroPython) mit Flash-Skript |
| `Dockerfile`, `docker-compose.yml` | Laufzeit für Entwicklung und Betrieb (ADR 0008) |
| `docs/` | Anforderungen, ADRs, Rechtliches, Meilensteine, Aufbauanleitungen, BOM |

Einstieg: [`CLAUDE.md`](CLAUDE.md) (Kontext & Konventionen), [`docs/requirements.md`](docs/requirements.md), [`docs/milestones.md`](docs/milestones.md).

## Entwicklungsumgebung
- **Docker** (Debian-Pakete): `sudo apt install docker.io docker-compose && sudo usermod -aG docker $USER`, danach ab- und wieder anmelden. Dann `mkdir -p data && docker compose build`.
- Ohne Docker laufen nur die Tests und der Sektorrechner (stdlib).
- **Claude Code (optional):** `.claude/settings.json` aktiviert das Plugin `ponytail` und ruft bei jedem Werkzeugaufruf `graphify` auf. Ohne graphify im `PATH` erscheint bei jedem Aufruf eine Hook-Fehlermeldung. Installation: `pipx install graphifyy` (oder in eine venv), dann `/graphify .`. Fremde Skills: `.claude/skills/THIRD_PARTY.md`.

## Schnellstart (ohne Hardware)
```bash
# Sektorrechner mit den aktuellen Parametern
python3 cad/lib/geometry.py

# Tests (stdlib unittest; pytest funktioniert ebenfalls)
cd software && python3 -m unittest discover -s tests -v                                   # ohne Docker (stdlib)
docker compose run --rm vending python -m unittest discover -s tests -v             # im Container (ADR 0008)

# Servicemodus gegen den Simulator
docker compose run --rm vending python -m vending.core.service_cli --sim
```
