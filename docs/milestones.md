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
- [x] Coprozessor-Firmware: Motion-Logik (Homing, Index, Stall, Retry), Protokoll-Parser, Heartbeat, `main.py`
- [x] UART-Client (heute `vending.hal.esp32`)
- [x] Umstieg auf ESP32 mit Flashen über den Pi (ADR 0007) und Docker-Laufzeit (ADR 0008)
- [ ] ESP32-Abnahme am Prüfstand: `flash.sh`, `soak 500`, Fail-secure beim Flashen messen
- [x] Motion-Service und Servicemodus-CLI
- [x] BOM M1, Aufbauanleitung M1
- [ ] ⚠️ `MotionService.present()` prüft `OK AT <s>` gegen den Zielsektor. Heute tut das nur `soak`, der Verkaufspfad ignoriert die Antwort (Sicherheitsregel 1).
- [ ] `Esp32Carousel.request()`: Antwort-Schlüsselwort gegen den Befehl prüfen (`GOTO` → `AT`, `UNLOCK` → `UNLOCKING` …) und nach einem `TIMEOUT` per `PING` neu synchronisieren. Sonst kann eine verspätete Antwort dem nächsten Befehl zugeordnet werden. 🔶 Das ersetzt die vorgeschlagenen Sequenznummern und CRC (siehe unten).
- [ ] 24-V-Überwachung: Spannungsteiler an GPIO35 (ADC1, frei). `STATUS` meldet `v24=<mV>`, Verkauf nur bei 24 V im Fenster. Spec in `protocol-esp32.md` ergänzen.
- [ ] StallGuard-Wert (`SG_RESULT`) je Fahrt mitloggen, als Trend für Verschleiß und Schwergängigkeit. Eine eigene Strommessung ist nicht nötig.

Hardware (Betreiber):
- [ ] Teile nach `docs/bom/m1.md` beschaffen. Motor mit **zweitem Wellenende** oder Getriebe mit Handrad-Aufnahme wählen (Notbetrieb, siehe M3).
- [ ] TVS-Diode (≈ 26 V) zusätzlich zu den 100 µF an VM des TMC2209, gegen Rückspeisung beim Bremsen (TMC2209 max. 29 V)
- [ ] Prüfstand nach `docs/assembly/m1-pruefstand.md` aufbauen

Abnahme:
- [ ] 500 zufällige Positionierungen ohne Fehlposition (`service_cli soak 500`)
- [ ] Blockade in unter 2 s erkannt, mit 1 Retry, danach FAULT
- [ ] Nach Stromtrennung Neustart mit Referenzfahrt
- [ ] Karussell lässt sich von Hand nicht verdrehen (Selbsthemmung)
- [ ] Jeden Sensor einzeln abziehen (Hall HOME, Hall INDEX, Reed, Türkontakt, UART-Leitung): Der Fehler wird erkannt und Verkauf ist nicht möglich.

## M2 – Zahlung in der PayPal-Sandbox
- [ ] PayPal-Client (OAuth, Orders, Capture, Refund, Request-Id)
- [ ] Kauf-Zustandsmaschine mit SQLite-Journal und Recovery. `UNLOCK` wird nie automatisch wiederholt. Nach einem Timeout entscheidet `STATUS`.
- [ ] Hardware-Ereignisse (`EVT`, FAULT, `HalError`) mit Zeitstempel in einer SQLite-Tabelle speichern
- [ ] Display-UI (pygame, QR mit segno, Countdown, Grundpreis)
- [ ] Benachrichtigungen
- [ ] Abnahme: alle Sonderfälle aus konzept.md §6 als Sim-Tests und manuell in der Sandbox, Stromausfalltest in jedem Zustand
- [ ] Abnahme: randomisierter Sim-Test mit festem Seed, ≥ 100 Läufe, Stromausfall bzw. Netzabbruch an zufälliger Stelle. Invarianten: keine Capture ohne Positionierung, keine doppelte Capture, bezahlt und nicht ausgegeben → Rückerstattung.
- [ ] Abnahme Sandbox: Netzwerk in jedem Kaufzustand trennen → keine Entriegelung ohne Capture

## M3 – Einbau in den Kühlschrank
- [ ] Ersatztür mit Klappen (Makros `door.py`, `flap.py`), Schlösser, Reed-Kontakte
- [ ] Verkleidung mit Verflüssiger-Lüftung (`cladding.py`)
- [ ] Elektronikbox im Innenraum unten (ADR 0009): IP54, tropfdicht, 24-V-Heizung, Ethernet. Boxmaße in `params.json`, Platz gegen Q2 prüfen. 230-V-Verteiler außen (Abnahme Elektrofachkraft).
- [ ] Display und Taster: Leitung über die Scharnierschleife zur Box, Displaytyp nach Leitungslänge auswählen (⚠️ HDMI steif, DSI kurz)
- [ ] Glasrücknahme nach Entscheidung Q9. Bei Variante (b) Rückgabesektor in der Sektorzahl einplanen.
- [ ] CAD: Sektoreinsätze einzeln entnehmbar und spülbar. Motorplatte, Hall-Halter und Schlösser ohne Komplettzerlegung erreichbar. Sensorhalter mit Langlöchern (Maße in `params.json`). Platz und Kabelweg für 3 Füllstandssensoren im Türkragen reservieren (M3b).
- [ ] Gummipuffer unter der Motorplatte, nur falls der Prüfstand Körperschall zeigt
- [ ] Temperaturregelung durch den Pi (`vending.climate`): Relais an GPIO17, Werte aus konzept.md §4 als Parameter, Sim-Test mit Fake-Fühlern und Fake-Uhr (Mindestzeiten, Anlaufsperre, Fühlerfehler, Laufzeit- und Kälte-Alarm). Eier-Sperren. Temperaturlog dauerhaft mit Zeitstempel in SQLite (Nachweis „möglichst konstant“).
- [ ] Web-UI: Belegung, Statusübersicht (bereit/Fehler, Temperatur, verfügbare Fächer), Temperaturverlauf, Journal mit Rückerstattungen, Sektor manuell sperren, Reinigung eintragen
- [ ] Tägliche Sicherung von `./data` (`sqlite3 .backup`) auf einen zweiten Datenträger
- [ ] `docs/betrieb.md`: Notöffnung (Haupttür mit Schlüssel, Karussell stromlos per Handrad drehen), Wiederanlauf nach Stromausfall, Reinigung, Wartung
- [ ] Deployment: Container als Dauerdienst (`restart`, Healthcheck), Host-Watchdog. 🔶 `privileged` auf einzelne Geräte umstellen (ADR 0008)
- [ ] Abnahme: 72-h-Temperaturlog im Fenster, dabei Box gegen Innenluft (Kondensat-Abstand, ADR 0009). Fail-secure-Test aller Klappen.
- [ ] Abnahme: 72 h Dauerbetrieb mit simulierten Käufen (Sandbox), keine unerklärten Neustarts
- [ ] Abnahme: 500 Entriegelungs- und Klappenzyklen je Ebene ohne Ausfall
- [ ] Abnahme: Stromtrennung mindestens 2× in jedem Journal-Zustand, danach korrekte Recovery

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

## Bewertung externer Verbesserungsvorschläge (2026-11-22)
Übernommene Punkte stehen oben in den Meilensteinen. Nicht übernommen wurden:

| Vorschlag | Grund |
|---|---|
| Mechanische Endanschläge | Das Karussell dreht endlos in beide Richtungen (kürzester Weg). Überlast decken StallGuard, Index-Prüfung und Selbsthemmung ab. |
| Separate Motorstrommessung | Der TMC2209 liefert die Last bereits über StallGuard (`SG_RESULT`, siehe M1). |
| 🔶 CRC und Sequenznummern | Die Leitung ist kurz und liegt im selben Gehäuse. Verwechslungen fängt die Echo- und Schlüsselwortprüfung ab (M1), die Sicherheitsinvarianten erzwingt der ESP32 selbst. Ein CRC würde die Handbedienung über die REPL erschweren. |
| Fernwartungsmodus | Die Admin-UI läuft bewusst nur im LAN. Störungen meldet F8. |
| Wartungsintervall-Zähler | Die Last ist gering. Verschleiß zeigt der StallGuard-Trend. |
| 1 000 statt 500 Positionierungen | 500 reichen als M1-Abnahme, die Langzeit deckt der 72-h-Lauf in M3 ab. |
| 17 neue Doku-Dateien in Unterordnern | Konzept, Anforderungen, ADRs und Meilensteine decken das ab. Neu kommen nur `betrieb.md` und `fuellstandserkennung.md` dazu. |
| Bereits im Plan | Watchdog (Pi und ESP32), getrennte Versorgung, steckbare IP67-Stecker, Kondensat, Kabel über die Scharnierseite, Heartbeat, Quittierung jedes Befehls, Tür- und Klappenkontakte, Referenzfahrt beim Start, Recovery nach Stromausfall, Rollenteilung Pi/ESP32. |
