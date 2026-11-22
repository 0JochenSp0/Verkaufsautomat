# Meilensteine

## M0 – Gerüst ✅ (2026-11-21)
- [x] Ordnerstruktur, README, CLAUDE.md, .gitignore
- [x] Konzept, Anforderungen, Rechtliches, ADR 0001–0006, Pi-Coprozessor-Protokoll
- [x] `git init` und erster Commit, Remote auf GitHub

## M1 – Karussell-Prototyp auf dem Tisch (läuft)
Software, ohne Hardware:
- [x] `cad/params/params.json`, alle Maße als Parameter
- [x] `cad/lib/geometry.py`: Sektorrechner mit Tests, CLI-Tabelle
- [x] `cad/macros/carousel.py`: FreeCAD-Makro, parametrisch (nicht ausgeführt, FreeCAD fehlt)
- [x] HAL-Interfaces und Simulator
- [x] Coprozessor-Firmware: Motion-Logik (Homing, Index, Stall), Protokoll-Parser, Heartbeat, `main.py`. Die automatische Wiederholung nach einem Stall ist aus (`retries` = 0, 2026-11-22).
- [x] UART-Client (heute `vending.hal.esp32`)
- [x] Umstieg auf ESP32 mit Flashen über den Pi (ADR 0007)
- [x] Laufzeit ohne Docker und ohne venv: System-Python mit apt-Paketen (ADR 0010, ersetzt ADR 0008)
- [ ] ESP32-Abnahme am Prüfstand: `flash.sh`, `soak 500`, Fail-secure beim Flashen messen
- [x] Motion-Service und Servicemodus-CLI
- [x] BOM M1, Aufbauanleitung M1
- [ ] ⚠️ `MotionService.present()` prüft `OK AT <s>` gegen den Zielsektor. Heute tut das nur `soak`, der Verkaufspfad ignoriert die Antwort (Sicherheitsregel 1).
- [ ] `Esp32Carousel.request()`: Antwort-Schlüsselwort gegen den Befehl prüfen (`GOTO` → `AT`, `UNLOCK` → `UNLOCKING` …) und nach einem `TIMEOUT` per `PING` neu synchronisieren. Vor jedem Senden bereits wartende Zeilen lesen (nur `EVT` behalten). Sonst kann eine verspätete Antwort dem nächsten Befehl zugeordnet werden. 🔶 Das ersetzt die vorgeschlagenen Sequenznummern und CRC (siehe unten).
- [ ] 24-V-Überwachung: Spannungsteiler an GPIO35 (ADC1, frei). `STATUS` meldet `v24=<mV>`, Verkauf nur bei 24 V im Fenster. Spec in `protocol-esp32.md` ist als „geplant“ eingetragen.
- [ ] ⚠️ Heartbeat nach langen Fahrten: `Dispatcher.handle` setzt die Empfangszeit erst *vor* dem Befehl. `HOME` (≈ 60 s) und jede Fahrt über 10 s enden deshalb in `SAFE HEARTBEAT`. Fix: nach dem Befehl erneut `touch()`. Sim-Test mit `FakeMechanics`, die die `SimClock` um Schritte/Geschwindigkeit weiterstellt (im Audit 2026-11-22 nachgestellt).
- [ ] Kalibrierung ohne Neuflashen: `CFG sgthrs` und `CFG irun` direkt an den TMC, Befehl `JOG <steps>` (nur unreferenziert), CLI-Befehle `cfg` und `jog`. Heute braucht jeder neue StallGuard-Wert ein `flash.sh` mit Löschen, weil `mpremote` die laufende Firmware nicht unterbrechen kann.
- [ ] ESP32-Reset erkennen: `STATUS` meldet `cfg=0`, bis ein `CFG` kam. `MotionService.ensure_homed()` ruft dann zuerst `connect()` auf. Sonst laufen nach einem WDT-Reset `home_offset` und `unlock_max_s` auf Defaults.
- [ ] TMC2209-`setup()` bei jedem `HOME` erneut schreiben (nach einem Ausfall der Motorsicherung stehen die Register auf Defaults).
- [ ] `CFG levels` liest in der Firmware die Klappeneingänge neu ein. Die Korrektur in `SimTransport.write_line` entfällt dann, damit der Simulator nichts verdeckt.
- [ ] `SerialTransport.read_line(0)` liest wirklich einmal von der Schnittstelle (heute zeigt `events` nur, was der Keepalive zufällig mitgenommen hat).
- [ ] Datenordner zentral: `vending.config.DATA_DIR = REPO_ROOT / "data"`, alle Pfade (Journal, Secrets, Cache) davon ableiten.

Hardware (Betreiber):
- [ ] Teile nach `docs/bom/m1.md` beschaffen. Motor mit **zweitem Wellenende** oder Getriebe mit Handrad-Aufnahme wählen (Notbetrieb, siehe M3).
- [ ] TVS-Diode (≈ 26 V) zusätzlich zu den 100 µF an VM des TMC2209, gegen Rückspeisung beim Bremsen (TMC2209 max. 29 V)
- [ ] Prüfstand nach `docs/assembly/m1-pruefstand.md` aufbauen

Abnahme:
- [ ] 500 zufällige Positionierungen ohne Fehlposition (`service_cli soak 500`)
- [ ] Blockade in unter 2 s erkannt, sofort FAULT (keine automatische Wiederholung)
- [ ] Nach Stromtrennung Neustart mit Referenzfahrt
- [ ] Karussell lässt sich von Hand nicht verdrehen (Selbsthemmung)
- [ ] Jeden Sensor einzeln abziehen (Hall HOME, Hall INDEX, Reed, Türkontakt, UART-Leitung): Der Fehler wird erkannt und Verkauf ist nicht möglich.

## M2 – Zahlung in der PayPal-Sandbox
- [ ] PayPal-Client (OAuth, Orders, Capture, Refund, Request-Id)
- [ ] Kauf-Zustandsmaschine mit SQLite-Journal und Recovery. `UNLOCK` wird nie automatisch wiederholt. Nach einem Timeout entscheidet `STATUS`.
- [ ] Hardware-Ereignisse (`EVT`, FAULT, `HalError`) mit Zeitstempel in einer SQLite-Tabelle speichern
- [ ] Display-UI (pygame, kleines Display, QR mit segno, Countdown, Produkt, Preis, Grundpreis) und Bedienung nach ADR 0011: Taster A/B/Abbruch (Wechsel und Abbruch ohne Capture), Sektorwahl (Eier: ältestes Legedatum zuerst, Honig: kürzester Weg)
- [ ] Taster-LEDs (F13): Zustand je Produkt aus Bestand und Sperren ableiten (grün, rot, grün blinkend, aus). Neue HAL-Schnittstelle mit Simulator, Sim-Test jeder Sperre → rot
- [ ] BOM M2/M3 ([`bom/m2-m3.md`](bom/m2-m3.md)) beim Bestellen prüfen und mit echten Typen ergänzen
- [ ] Benachrichtigungen nur bei FAULT, Temperaturalarm, Zahlungsfehler oder Rückerstattung und leerem Bestand (F8). Normale Neustarts nur ins Journal.
- [ ] Autostart als systemd-Dienst (`Restart=always`, `WatchdogSec`, `sd_notify` per stdlib-Socket), läuft als normaler Benutzer (ADR 0010)
- [ ] Abnahme: alle Sonderfälle aus konzept.md §6 als Sim-Tests und manuell in der Sandbox, Stromausfalltest in jedem Zustand
- [ ] Abnahme: randomisierter Sim-Test mit festem Seed, ≥ 100 Läufe, Stromausfall bzw. Netzabbruch an zufälliger Stelle. Invarianten: keine Capture ohne Positionierung, keine doppelte Capture, bezahlt und nicht ausgegeben → Rückerstattung.
- [ ] Abnahme Sandbox: Netzwerk in jedem Kaufzustand trennen → keine Entriegelung ohne Capture

## M3 – Einbau in den Kühlschrank
- [ ] Erster Einbau mit **1 Ebene**: 1 Klappe, 1 Schloss, 1 Reed. Welle, Motor, Lager und Tür sind für 3 Ebenen ausgelegt. ⚠️ Dafür `carousel.levels: 1` in `params.json` setzen oder die Reed-Eingänge 2 und 3 auf GND brücken, sonst blockiert der ESP32 jede Fahrt mit `FLAP_OPEN`.
- [ ] Ersatztür mit Klappen (Makros `door.py`, `flap.py`), zunächst nur eine Klappe mit Schloss und Reed ausgerüstet
- [ ] Verkleidung mit Verflüssiger-Lüftung (`cladding.py`)
- [ ] Elektronikbox im Innenraum unten (ADR 0009): IP54, tropfdicht, Ethernet, zunächst **ohne Heizung** (Platz, Kabel und GPIO22 reserviert). Boxmaße in `params.json`, Platz gegen Q2 prüfen. 230-V-Verteiler außen (Abnahme Elektrofachkraft).
- [ ] Display und Taster: Leitung über die Scharnierschleife zur Box, Displaytyp nach Leitungslänge auswählen (⚠️ HDMI steif, DSI kurz)
- [ ] Glasrücknahme nach Entscheidung Q9. Bei Variante (b) Rückgabesektor in der Sektorzahl einplanen.
- [ ] CAD: Sektoreinsätze einzeln entnehmbar und spülbar. Motorplatte, Hall-Halter und Schlösser ohne Komplettzerlegung erreichbar. Sensorhalter mit Langlöchern (Maße in `params.json`). Platz und Kabelweg für 3 Füllstandssensoren im Türkragen reservieren (M3b).
- [ ] Gummipuffer unter der Motorplatte, nur falls der Prüfstand Körperschall zeigt
- [ ] Temperaturregelung durch den Pi (`vending.climate`): Relais an GPIO17, Werte aus konzept.md §4 als Parameter, 2 Fühler (Luft, Eier-Ebene), kein Außenfühler. Sim-Test mit Fake-Fühlern und Fake-Uhr (Mindestzeiten, Anlaufsperre, Fühlerfehler, Laufzeit- und Kälte-Alarm). Eier-Sperren. Temperaturlog dauerhaft mit Zeitstempel in SQLite (Nachweis „möglichst konstant“).
- [ ] Betreiber-CLI (`service_cli` erweitern): Belegung, Status (bereit/Fehler, Temperatur, verfügbare Fächer), Temperaturverlauf, Journal mit Rückerstattungen, Sektor manuell sperren, Reinigung eintragen
- [ ] Tägliche Sicherung von `./data` (`sqlite3 .backup`) auf einen zweiten Datenträger
- [ ] `docs/betrieb.md`: Notöffnung (Haupttür mit Schlüssel, Karussell stromlos per Handrad drehen), Wiederanlauf nach Stromausfall, Reinigung, Wartung
- [ ] Hardware-Watchdog (`RuntimeWatchdogSec`) aktiv, Dienst aus M2 im Dauerbetrieb
- [ ] Abnahme: 72-h-Temperaturlog im Fenster, dabei mit einem vorübergehenden Fühler Box gegen Innenluft messen (Kondensat-Abstand, ADR 0009). Wenn nötig: Boxheizung mit Bimetall an GPIO22 nachrüsten. Fail-secure-Test aller Klappen.
- [ ] Abnahme: 72 h Dauerbetrieb mit simulierten Käufen (Sandbox), keine unerklärten Neustarts
- [ ] Abnahme: 500 Entriegelungs- und Klappenzyklen je Ebene ohne Ausfall
- [ ] Abnahme: Stromtrennung mindestens 2× in jedem Journal-Zustand, danach korrekte Recovery
- [ ] Danach Ebenen 2 und 3 nachrüsten (Böden, Klappen, Schlösser, Reed), Klappenzyklen-Abnahme je neuer Ebene wiederholen

## M3b – Füllstandserkennung (optional, nach M3)
Plausibilitätsprüfung, keine Bestandsquelle. Das Journal bleibt führend.
- [ ] Konzept `docs/fuellstandserkennung.md`: Sensorposition, Messablauf, Kalibrierung, Fehlerfälle, Tests
- [ ] Versuch an 1 Fach: VL53L1X (ToF) gegen ein wasserfestes Ultraschallmodul (z. B. JSN-SR04T). Glas, Schachtel, leer, Produkt im Nachbarfach, Kondensat (Klappe bei warmer, feuchter Luft öffnen). ⚠️ Das Konzept schließt optische Sensoren wegen Kondensat bisher aus. Der Versuch muss das widerlegen.
- [ ] Messung im Stillstand an der Ausgabeposition: Je Ebene sitzt ein Sensor im Türkragen und sieht den Sektor hinter der Klappe. Nach „Klappe zu“ prüft er die Entnahme. Nach dem Befüllen scannt der Servicemodus alle Sektoren. 🔶 Eine Messung während der Fahrt ist nicht nötig.
- [ ] Anschluss am Pi, nicht am ESP32: Der ESP32 hat keine freien Ausgänge mehr. Bei ToF I²C mit TCA9548A oder XSHUT an freien Pi-GPIOs. Die Box sitzt im Innenraum (ADR 0009), die I²C-Leitungen bleiben kurz. Neue HAL-Schnittstelle mit Simulator.
- [ ] Regeln: Kein Echo oder unplausibler Wert ist ein Sensorfehler, nicht „leer“. Weicht die Messung vom Journal ab, wird der Sektor gesperrt und der Betreiber benachrichtigt. Der Bestand wird nie automatisch hochgezählt. Die Rückerstattungslogik bleibt unverändert.
- [ ] Entscheidung als ADR
- [ ] Abnahme: 500 Messungen je Zustand am Versuchsfach ohne Fehlklassifikation

## M4 – Feldtest
- [ ] Behörden-Checkliste in `legal.md` erledigt, PayPal-Geschäftskonto aktiv
- [ ] Kostenrechnung vor Live-Betrieb: BOM-Summe, PayPal-Fixgebühr je Kauf, Strom → Mindestpreise (Q6)
- [ ] 4 Wochen Betrieb, Auswertung von Fehlkäufen, Rückerstattungen, Temperatur und Kondensat
- [ ] Wartungsplan aus dem Feldtest in `docs/betrieb.md`

## Optional nach M4
- [ ] Web-UI im LAN (Belegung, Status, Journal), nur falls die Betreiber-CLI im Alltag nicht reicht
- [ ] Schloss-Rückmeldekontakt, falls der Feldtest Klappen zeigt, die zu, aber nicht verriegelt sind

## Bewertung externer Verbesserungsvorschläge (2026-11-22)
Übernommene Punkte stehen oben in den Meilensteinen. Nicht übernommen wurden:

| Vorschlag | Grund |
|---|---|
| Mechanische Endanschläge | Das Karussell dreht endlos in beide Richtungen (kürzester Weg). Überlast decken StallGuard, Index-Prüfung und Selbsthemmung ab. |
| Separate Motorstrommessung | StallGuard und Index-Prüfung erkennen Blockaden. |
| 🔶 CRC und Sequenznummern | Die Leitung ist kurz und liegt im selben Gehäuse. Verwechslungen fängt die Echo- und Schlüsselwortprüfung ab (M1), die Sicherheitsinvarianten erzwingt der ESP32 selbst. Ein CRC würde die Handbedienung über die REPL erschweren. |
| Fernwartungsmodus | Die Admin-UI läuft bewusst nur im LAN. Störungen meldet F8. |
| Wartungsintervall-Zähler | Die Last ist gering. |
| 1 000 statt 500 Positionierungen | 500 reichen als M1-Abnahme, die Langzeit deckt der 72-h-Lauf in M3 ab. |
| 17 neue Doku-Dateien in Unterordnern | Konzept, Anforderungen, ADRs und Meilensteine decken das ab. Neu kommen nur `betrieb.md` und `fuellstandserkennung.md` dazu. |
| Bereits im Plan | Watchdog (Pi und ESP32), getrennte Versorgung, steckbare IP67-Stecker, Kondensat, Kabel über die Scharnierseite, Heartbeat, Quittierung jedes Befehls, Tür- und Klappenkontakte, Referenzfahrt beim Start, Recovery nach Stromausfall, Rollenteilung Pi/ESP32. |

## Verschlankung (2026-11-22)
Ziel: so wenig Hardware, Software und Fehlerquellen wie möglich, ohne an Sicherheit zu sparen. Übernommen:
- Kein Docker und keine venv (ADR 0010).
- Keine RTC.
- 2 statt 4 DS18B20, kein Außenfühler.
- Keine Innenraumheizung (Q8).
- Boxheizung nur bei Bedarf.
- Kein Schloss-Rückmeldekontakt.
- Kein automatischer Stall-Retry.
- Kein `SG_RESULT`-Logging.
- Web-UI zurückgestellt zugunsten der Betreiber-CLI.
- Weniger Benachrichtigungen.
- Erster Einbau mit 1 Ebene.
- Füllstandserkennung bleibt optional (M3b).

Nicht übernommen:

| Vorschlag | Grund |
|---|---|
| Eigenständiger Thermostat, Pi überwacht nur | Entscheidung des Betreibers: Der Pi regelt (Schaltlog, Mindestzeiten). Das Originalthermostat auf „kalt“ ist der Backstop, bei einem Pi-Ausfall ist der Kühlschrank aus und die Eier sind gesperrt (ADR 0001). |
| 🔶 StallGuard als Blockadeerkennung streichen | Er ist schon gebaut und kostet nur einen Pin. Ohne ihn drückt der Motor bei einer Blockade die ganze Fahrt weiter, bis die Index-Prüfung greift. Gestrichen ist nur die automatische Wiederholung. |
| Neue Softwarestruktur (`controller.py`, `hardware/` …) | Die vorhandene Struktur (HAL mit Simulator, `core`, `payment`, `climate`, `ui`) ist bereits eine Ein-Prozess-App mit Modulen. Ein Umbau bringt keinen Nutzen. |
| graphify-Hooks und Skill-Pflicht entfernen | Entscheidung des Betreibers: Sie bleiben. Sie betreffen nur die Entwicklung, nicht den Automaten. |
| WLAN-Hardware streichen | War nie geplant. (Status-LEDs sind seit ADR 0011 als Produkt-LEDs an den Tastern geplant.) |
