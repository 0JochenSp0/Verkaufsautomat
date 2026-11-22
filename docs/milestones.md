# Meilensteine

## M0 – Gerüst ✅ (2026-11-21)
- [x] Ordnerstruktur, README, CLAUDE.md, .gitignore
- [x] Konzept, Anforderungen, Rechtliches, ADR 0001–0006, Pi-Coprozessor-Protokoll
- [ ] `git init` und erster Commit. Git ist auf dem Entwicklungs-Pi noch nicht installiert.

## M1 – Karussell-Prototyp auf dem Tisch (läuft)
Software, ohne Hardware:
- [x] `cad/params/params.json`, alle Maße als Parameter
- [x] `cad/lib/geometry.py`: Sektorrechner mit Tests, CLI-Tabelle
- [x] `cad/macros/carousel.py`: FreeCAD-Makro, parametrisch (nicht ausgeführt, FreeCAD fehlt)
- [x] HAL-Interfaces und Simulator
- [x] Coprozessor-Firmware: Motion-Logik (Homing, Index, Stall, Retry), Protokoll-Parser, Heartbeat, `main.py`
- [x] UART-Client (heute `vending.hal.esp32`)
- [x] Umstieg auf ESP32 mit Flashen über den Pi (ADR 0007) und Docker-Laufzeit (ADR 0008)
- [ ] ESP32-Abnahme am Prüfstand: `flash.sh`, `soak 500`, Fail-secure beim Flashen messen
- [x] Motion-Service und Servicemodus-CLI
- [x] BOM M1, Aufbauanleitung M1

Hardware (Betreiber):
- [ ] Teile nach `docs/bom/m1.md` beschaffen
- [ ] Prüfstand nach `docs/assembly/m1-pruefstand.md` aufbauen

Abnahme:
- [ ] 500 zufällige Positionierungen ohne Fehlposition (`service_cli soak 500`)
- [ ] Blockade in unter 2 s erkannt, mit 1 Retry, danach FAULT
- [ ] Nach Stromtrennung Neustart mit Referenzfahrt
- [ ] Karussell lässt sich von Hand nicht verdrehen (Selbsthemmung)

## M2 – Zahlung in der PayPal-Sandbox
- [ ] PayPal-Client (OAuth, Orders, Capture, Refund, Request-Id)
- [ ] Kauf-Zustandsmaschine mit SQLite-Journal und Recovery
- [ ] Display-UI (pygame, QR mit segno, Countdown, Grundpreis)
- [ ] Benachrichtigungen
- [ ] Abnahme: alle Sonderfälle aus konzept.md §6 als Sim-Tests und manuell in der Sandbox, Stromausfalltest in jedem Zustand

## M3 – Einbau in den Kühlschrank
- [ ] Ersatztür mit Klappen (Makros `door.py`, `flap.py`), Schlösser, Reed-Kontakte
- [ ] Verkleidung mit Verflüssiger-Lüftung (`cladding.py`)
- [ ] Elektronikfach mit Heizung, 230-V-Verteiler (Abnahme Elektrofachkraft)
- [ ] Temperaturregelung 10–15 °C, Eier-Sperren, Web-UI für die Belegung
- [ ] Deployment: Container als Dauerdienst (`restart`, Healthcheck), Host-Watchdog. 🔶 `privileged` auf einzelne Geräte umstellen (ADR 0008)
- [ ] Abnahme: 72-h-Temperaturlog im Fenster, Fail-secure-Test aller Klappen

## M4 – Feldtest
- [ ] Behörden-Checkliste in `legal.md` erledigt, PayPal-Geschäftskonto aktiv
- [ ] 4 Wochen Betrieb, Auswertung von Fehlkäufen, Rückerstattungen, Temperatur und Kondensat
