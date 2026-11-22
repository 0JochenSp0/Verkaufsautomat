# ADR 0009 – Elektronikbox mit Pi und ESP32 im Innenraum unten

**Status:** angenommen (2026-11-22). Ersetzt den Ort „oben vorn, hinter dem Display“ aus konzept.md §4. Geändert am 2026-11-22: Die Heizung ist zurückgestellt (siehe Entscheidung).

## Kontext
Bisher war das Elektronikfach außen oben vorn vorgesehen, hinter dem Display. Der Betreiber will Pi und ESP32 im Innenraum unterbringen, in einer leicht beheizten Box im unteren Teil des Schranks. Geheizt wird nur, wenn es nachts richtig kalt wird.

## Entscheidung
- **Ort:** eine SELV-Box (Pi 3B, ESP32, TMC2209, MOSFETs, DC/DC) unten im Innenraum neben der Motorplatte. Der Zugang erfolgt über die Haupttür.
- **Gehäuse:** IP54 oder besser, mit Druckausgleichs-Membran. Glatte, abwischbare Oberfläche, weil die Box im Lebensmittelraum steht. Der Deckel ist tropfdicht, falls ein Glas oder Ei darüber ausläuft.
- **Heizung: zurückgestellt.** Die Box wird zunächst ohne Heizung gebaut. Im 72-h-Test misst ein vorübergehend eingebauter DS18B20 die Box gegen die Innenluft. Nur wenn dabei Kondensat oder Frostgefahr erkennbar ist, kommt eine 24-V-Heizung dazu (keine 230 V im Innenraum): über GPIO22 unter ca. +5 °C bzw. +3 K über der Innenluft, Bimetall in Reihe als Backstop. Platz, Kabel und GPIO22 bleiben dafür reserviert.
- **Netzwerk:** nur Ethernet. ⚠️ Der Kühlschrankkorpus schirmt WLAN ab, und der Pi 3B hat keinen Antennenanschluss.
- **230 V bleibt außen** im IP65-Verteiler mit dem 24-V-Netzteil. In den Innenraum gehen nur 24 V, Ethernet und die Relais-Steuerleitung nach außen.

## Alternativen
- **Außen oben hinter dem Display** (bisher): kurze Displayleitung, aber Sonne, Frost, Insekten und lange Leitungen zu Motor und Sensoren.
- **Außen in der Verkleidung unten:** Die Leitungen zum Motor wären kurz, aber auch dort gibt es Frost und Insekten, und es braucht eine weitere Korpusdurchführung.

## Folgen
- ✅ Kurze Leitungen zu Motor, Hall-Sensoren und künftigen Füllstandssensoren (M3b, die I²C-Länge entschärft sich). Die Box ist vor Sonne, Insekten und Zugriff von außen geschützt.
- ✅ Im Sommer liegt der Innenraum bei 10–15 °C, das ist günstig für Pi und Netzteil. Die Abwärme (ca. 3–5 W) belastet den Kühlschrank kaum.
- ⚠️ **Kondensat:** Unten ist es am kältesten und feuchtesten (Tropfwasser vom Verdampfer, Luftfeuchte beim Öffnen). Die Eigenwärme des Pi hält die Box schon einige Kelvin über der Innenluft. Das muss im 72-h-Test gemessen werden (Box- gegen Innentemperatur). Wenn die Eigenwärme nicht reicht, statt reinem Frostschutz einen festen Abstand von ca. +3 K zur Innenluft halten.
- ⚠️ **Display und Taster in der Tür:** Die Leitungen laufen über die Scharnierschleife zur Box. HDMI ist dick und steif, DSI-Flachbänder sind kurz. Displaytyp und Leitung bei der Auswahl auf Länge und Biegezyklen prüfen.
- ⚠️ **Platz:** Die Box nimmt Höhe oder Grundfläche unten weg (Kompressorstufe hinten unten). Ob 3 Ebenen plus Antrieb plus Box passen, entscheidet Q2 (Innenmaße). Die Boxmaße kommen als Parameter in `params.json`.
- Korpusdurchführung für 24 V, Ethernet und Relaisleitung: wie gehabt erst per Wärmebild prüfen (konzept.md §3).
- Wartung: SD-Karte und Flash-Zugang nur bei offener Haupttür. Dabei sind ohnehin keine Verkäufe möglich (F9).
