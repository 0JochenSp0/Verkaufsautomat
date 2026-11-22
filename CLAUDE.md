# CLAUDE.md – Verkaufsautomat Wachteleier & Honig

## Projektkontext
- Grundgerät ist ein **gebrauchter Kühlschrank**. Der Kältekreis bleibt unangetastet. Außen kommt eine Holzverkleidung mit XPS-Dämmung, die Originaltür wird durch eine **eigene Tür** mit 3 Ausgabeklappen ersetzt.
- Innen sitzt ein **Karussell mit 3 Ebenen** auf einer Welle mit einem Antrieb. Die Sektoren sind universal und nehmen entweder 1 Wachteleier-Schachtel oder 1 Glas Honig à 500 g auf. Ziel sind 10–20 Positionen, realistisch ca. 12 bei Ø ≈ 420 mm (siehe `cad/lib/geometry.py`).
- **Ablauf:** Auswahl am Display → PayPal-QR (Orders API v2) → Zahlung freigegeben → Karussell dreht den Sektor vor die Klappe → **dann** Capture → nur die passende Klappe wird entriegelt.
- **Temperatur:** Der Pi regelt den Innenraum auf **10–15 °C** über ein Relais vor dem Kühlschrank. Bei Temperatur außerhalb des Fensters, Sensorfehler oder ab dem 28. Tag nach dem Legen (§ 22 Abs. 3 Tier-LMHV) wird der Eierverkauf gesperrt. Im Winter ist die Kühlung aus und es gibt nur Honig.
- **Hardware:** Raspberry Pi 3B (Logik, UI, Netz), dazu ESP32 (klassisch, WROOM-32) mit MicroPython als Motion-/I/O-Coprozessor über UART0. Der Pi flasht ihn selbst über EN/GPIO0 (ADR 0007). Die Software läuft als Docker-Container im Projektordner (ADR 0008). Schrittmotor mit selbsthemmendem Schneckengetriebe und TMC2209. Hall-Sensoren für Home und Index. Fail-secure-Schlösser, Reed-Kontakte, DS18B20-Fühler.
- **Bedienung:** Display ohne Touch und Edelstahltaster. Die Admin-Web-UI läuft nur im LAN.
- Beide Produkte stammen aus **eigener Erzeugung** (Direktvermarktung).
- Plan und Begründungen: `docs/milestones.md`, `docs/adr/`. Rechtliches: `docs/legal.md`.

## Sicherheitsregeln (nicht verhandelbar)
1. **Keine Capture vor verifizierter Positionierung.** Erst fahren und den Index prüfen, dann `capture`, dann entriegeln.
2. **Schlösser sind fail-secure.** Die Software darf nie annehmen, dass „stromlos = offen“ gilt. Jede Entriegelung ist zeitlich begrenzt.
3. **Journal vor Aktion:** Jeder Zustandswechsel eines Kaufs wird in SQLite geschrieben, *bevor* die Aktion ausgeführt wird. Die Recovery beim Boot liest dieses Journal.
4. **Im Zweifel zugunsten des Kunden:** Bezahlt, aber nicht nachweislich ausgegeben, heißt Rückerstattung plus Meldung an den Betreiber.
5. Verkauf ist nur möglich bei synchronisierter Uhrzeit, referenziertem Karussell und ohne aktiven Fehler.
6. Die 230-V-Seite wird nur dokumentiert. Die Abnahme macht eine Elektrofachkraft. Netz- und Kleinspannung liegen in getrennten Gehäusen.

## Konventionen
- **Sprache:** Code, Bezeichner, Commits und Docstrings auf Englisch, Doku in `docs/` auf Deutsch.
- **Einheiten:** Längen in mm, Winkel im Code in Grad (Suffix `_deg`), Temperaturen in °C, Geld in **Cent als int** (nie float).
- **Parameter:** Alle Maße stehen in `cad/params/params.json`. Weder CAD-Makros noch Software haben hartkodierte Maße. Die Software liest die Sektorzahl aus der Konfiguration.
- **Hardware nur über HAL:** `vending.hal.interfaces`. Jede HAL hat einen Simulator (`vending.hal.sim`), die Tests laufen ohne Hardware.
- **Docker:** Alles läuft über `docker compose run --rm vending …` (Image enthält nur Abhängigkeiten, der Code ist bind-gemountet, Daten in `./data`). Seriell im Container immer `/dev/ttyAMA0`, nie `/dev/serial0`.
- **Tests:** `unittest`-kompatibel (stdlib, damit sie auch ohne Docker und ohne pip auf dem Pi laufen), pytest als Runner erlaubt. Jede Änderung an Zahlung oder Zustandsmaschine braucht einen Simulator-Test.
- **Python:** ≥ 3.11, Typannotationen, `ruff` für Stil und Lint. Möglichst wenige Abhängigkeiten.
- **ESP32-Firmware** (`software/firmware/esp32`): MicroPython. Die Logik liegt in reinen Modulen ohne `machine`-Import, damit sie unter CPython testbar ist. `main.py` darf nichts mit `print` ausgeben, weil UART0 gleichzeitig Protokoll, REPL und Bootloader ist. Strapping-Pins sind tabu (`electronics/pinout.md`).
- **Protokoll Pi↔ESP32:** Zeilenbasiert, ASCII, `CMD arg…\n` → `OK …` / `ERR code …` / asynchron `EVT …`. Spezifiziert in `docs/protocol-esp32.md`.
- **Secrets** (PayPal Client-ID und Secret) liegen nur in `/data/secrets.env`, niemals im Repo.
- **ADRs:** Neue Architekturentscheidungen kommen als `docs/adr/NNNN-titel.md` (Kontext, Entscheidung, Alternativen, Folgen).
- **Risiken und abweichende Meinungen** werden in der Doku mit ⚠️ bzw. 🔶 markiert.

## Skill-Pflicht
Vor jeder Aufgabe prüfen, ob ein vorhandener Skill (Projekt, Plugin oder eingebaut) dazu passt. **Wenn es einen gibt, muss er verwendet werden**: per Skill-Tool aufrufen, bevor die Arbeit beginnt. Nur wenn keiner passt, wird ohne Skill gearbeitet. Bei Konflikten gehen die Sicherheitsregeln und Konventionen dieser Datei vor.

| Aufgabe | Skill |
|---|---|
| Fragen zu Code, Architektur oder Dateibezügen | `graphify` (zuerst `graphify query`), nach Codeänderungen `graphify update .` |
| Code schreiben, ändern, refaktorieren | `ponytail` (per Hook aktiv) |
| Review einer Änderung oder vor einem Commit | `ponytail-review` (Pflicht bei Zahlung, Zustandsmaschine, Journal, Protokoll), für Sicherheitsthemen zusätzlich `security-review` |
| Repo-Audit, Meilenstein-Abschluss | `ponytail-audit` und `ponytail-debt` |
| Modulstruktur verbessern | `improve-codebase-architecture` (mit Angabe des Bereichs) |
| Vereinfachen ohne Bugsuche | `simplify` |
| Diagramme, Charts, Berichtsseiten | `dataviz`, `artifact-design` bzw. `artifact-diagramming` |
| Claude-Code-Einstellungen, Hooks, Berechtigungen | `update-config` |
| Kein passender Skill vorhanden, aber die Aufgabe kommt öfter vor | `find-skills` (suchen, prüfen, dann den Nutzer fragen) |

In der Antwort kurz nennen, welcher Skill benutzt wurde. Wenn keiner passte, ebenfalls kurz sagen.

## Arbeitsweise (ponytail)
Das Plugin `ponytail@ponytail` ist auf Projektebene aktiv (`.claude/settings.json`, Modus `full`). Es gilt: die kleinste vollständige Änderung, stdlib zuerst, kein Code „für später“.
- **Vorrang:** Die Sicherheitsregeln oben stehen über ponytail. Journal-Schreibvorgänge, Zeitlimits für Entriegelungen, Recovery, Rückerstattung, Index-Prüfung und Plausibilitätsprüfungen der Sensoren sind niemals „überflüssiger Code“ und werden nicht weggekürzt.
- **HAL ist kein YAGNI:** Jede HAL-Schnittstelle hat zwei Implementierungen (Hardware und Simulator). Diese Abstraktion bleibt bestehen.
- **Abkürzungen kennzeichnen:** Eine bewusste Vereinfachung mit bekannter Grenze bekommt einen Code-Kommentar `# shortcut: <limit>, <when to upgrade>` (auf Englisch, wie der Code). `/ponytail-debt` sammelt diese Kommentare.
- **Review:** Vor jedem Commit, der Zahlung, Zustandsmaschine, Journal oder ESP32-Protokoll berührt, läuft `/ponytail-review`. Es ersetzt nicht den Pflicht-Simulatortest.
- **Meilenstein-Abschluss:** `/ponytail-audit` für das ganze Repo und `/ponytail-debt`. Das Ergebnis kommt als offene Punkte in `docs/milestones.md`.
- **Architektur:** `/improve-codebase-architecture` (Projekt-Skill) nur gezielt aufrufen, mit Angabe des Bereichs.

## Kommandos
```bash
python3 cad/lib/geometry.py [--params cad/params/params.json]     # Sektorrechner
docker compose build                                                                  # einmalig bzw. nach Dockerfile-Änderung
docker compose run --rm vending python -m unittest discover -s tests -v
docker compose run --rm vending python -m unittest discover -s tests -k test_home_offset   # einzelner Test
docker compose run --rm vending python -m vending.core.service_cli --sim
docker compose run --rm vending python -m vending.core.service_cli --port /dev/ttyAMA0     # echte Hardware
docker compose run --rm vending ruff check .
docker compose run --rm vending firmware/esp32/flash.sh                                  # ESP32 komplett neu flashen
cd software && python3 -m unittest discover -s tests -v                                  # ohne Docker (stdlib, tests/_paths.py setzt sys.path)
freecadcmd cad/macros/carousel.py                                  # (FreeCAD nötig) erzeugt cad/out/carousel.FCStd/.step
```

## Architektur (dateiübergreifend)
- **Eine Firmware-Logik, zwei Laufzeiten:** `firmware/esp32/carousel_fw/` (`machine_logic.Machine`, `protocol.Dispatcher`) läuft auf dem ESP32 *und* im Simulator. `vending.hal.sim` importiert genau diesen Code: `FakeMechanics` ersetzt die Pins, `SimTransport` speist Zeilen direkt in den `Dispatcher`. Tests und `--sim` prüfen damit die echte Firmware samt Protokoll. Nur `firmware/esp32/main.py` (Pins, WDT, stdin-Protokoll, Schrittschleife) und `flash.sh` ist hardwaregebunden und ungetestet.
- **Kette:** `core.service_cli` → `core.motion_service.MotionService` (Position → Ebene/Sektor, Keepalive-Thread) → `hal.esp32.Esp32Carousel` (Zeilenprotokoll, sammelt `EVT`) → `SerialTransport` (UART) oder `SimTransport`.
- **Konfiguration:** `vending.config.load()` leitet `MachineConfig` aus `cad/params/params.json` ab. `MotionService.connect()` schickt nach jedem (Re)Connect alle Werte als `CFG` an den ESP32, denn der startet nach einem Reset mit Defaults.
- **Noch leer (Platzhalter für M2/M3):** `vending.payment`, `vending.ui`, `vending.web`, `vending.climate`. Journal, Kaufzustandsmaschine und Recovery existieren noch nicht.

## Stand
- M0 (Gerüst) ist erledigt. M1 (Karussell-Prototyp) läuft: Geometrierechner, Karussell-Makro, HAL, Simulator, ESP32-Firmware (noch nicht am Gerät getestet) und Service-CLI.
- Umgebung: Git ist eingerichtet (Branch `main`, ohne Remote). GitHub-CLI `gh` liegt in `~/.local/bin` (Release-Binary, Update manuell). Auf dem Host fehlen pip, pytest, ruff und FreeCAD. pyserial, esptool, mpremote und ruff gibt es im Container. Docker muss der Nutzer per `sudo apt install docker.io docker-compose` selbst installieren.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. When the answer is under a Markdown heading, `graphify section "<heading>"` prints that section's text, so the .md need not be opened. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
