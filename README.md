# Verkaufsautomat für Wachteleier und Honig

Ein selbst gebauter Automat, an dem Kundinnen und Kunden rund um die Uhr Wachteleier und Honig aus eigener Erzeugung kaufen. Bezahlt wird mit dem Handy über PayPal. Stand: 23.11.2026, **Planungs- und Prototypphase: Noch läuft keine Hardware.**

Diese Seite gibt einen Überblick mit den technischen Eckdaten und den bekannten Risiken. Schaltpläne, Zustandsautomaten und alle Parameter stehen in [`docs/technik.md`](docs/technik.md).

---

## So kauft man

1. **Taster drücken:** **A** für Eier, **B** für Honig, darunter **Abbruch**.
2. **Mit dem Handy bezahlen:** Das Display zeigt Produkt, Preis (bei Honig auch €/kg) und einen QR-Code. QR-Code scannen und in PayPal freigeben. Dafür bleiben 3 Minuten.
3. **Ware entnehmen:** Der Automat dreht das Fach vor die Klappe und entriegelt nur diese eine Klappe. Klappe öffnen, Ware nehmen, Klappe zufallen lassen.

**Abbruch** oder der andere Produkttaster beenden den Kauf. Abgebucht wird dann nichts.

| LED an A bzw. B | Bedeutung |
|---|---|
| 🟢 grün | kaufbar |
| 🔴 rot | nicht kaufbar: ausverkauft, Eier gesperrt (Temperatur, Legedatum, Fühler), Störung, Haupttür offen oder Uhr nicht synchron. Ein Tastendruck zeigt den Grund auf dem Display. |
| 🟢 grün blinkend | Kauf läuft bzw. Klappe ist frei |
| ⚫ aus | außer Betrieb |

---

## Aufbau

| Baugruppe | Lösung | Eckdaten |
|---|---|---|
| Gehäuse | Gebrauchter Kühlschrank, Kältekreis unangetastet, Holzverkleidung mit XPS-Dämmung | Verflüssiger bleibt belüftet. Der Pi schaltet den Kühlschrank über ein Schütz mit 24-V-Spule. |
| Tür | Eigenbau aus Multiplex und XPS mit 3 Ausgabeklappen, Originalscharniere und -dichtung | Klappen oben angeschlagen, schließen durch Schwerkraft. Ein Kragen hält den Spalt zum Karussell unter 8 mm. |
| Karussell | 3 Ebenen auf einer Welle (Ø 20 mm). Jedes Fach nimmt 1 Eierschachtel **oder** 1 Glas 500 g auf. | Ø ≈ 403 mm, 4 Fächer à 90° je Ebene, also **12 Fächer**. ⚠️ Gerechnet mit Platzhaltermaßen (`cad/params/params.json`). Start mit 1 Ebene. |
| Antrieb | NEMA 17 mit selbsthemmendem Schneckengetriebe ≈ 1:30, Treiber TMC2209 | Von Hand nicht drehbar. Blockade per StallGuard, Position über Hall-Sensoren (Home und ein Index-Magnet je Fach). Jede Fahrt wird am Ziel geprüft. |
| Schlösser | Fail-secure-Hubmagnet 24 V mit Schnappfalle, Reed-Kontakt je Klappe | Stromlos verriegelt. Höchstens 1 Schloss gleichzeitig, höchstens 60 s. |
| Steuerung | Raspberry Pi 3B: Kauf, PayPal, Journal, Klima, Display, Taster. ESP32 (MicroPython): Motor, Sensoren, Schlösser | Verbunden per USB, zeilenbasiertes ASCII-Protokoll. Der ESP32 erzwingt die Sicherheitsregeln selbst und schaltet nach 10 s ohne Heartbeat alles ab. |
| Elektronikbox | SELV-Box (IP54) unten im Innenraum, nur Ethernet, 24-V-PTC-Heizung | 230 V nur außen im IP65-Verteiler (Elektrofachkraft). |
| Versorgung | 24-V-Netzteil 100 W, Sicherung je Zweig | ≈ 9 W Grundlast, ≈ 70 W Spitze |
| Bedienung | 3 Edelstahltaster, A und B mit Zweifarb-LED, Display 3,5–5″ | Der Betreiber arbeitet über die Kommandozeile (`service_cli`), eine Web-UI gibt es nicht. |

---

## Kaufablauf

```
Taster A/B → Fach wählen (Eier: ältestes Legedatum zuerst)
  → PayPal-Order anlegen (Orders API v2), QR mit Freigabelink, Countdown 3 min
  → Status alle 2 s abfragen, bis der Kunde freigegeben hat
  → Karussell fahren, ESP32 bestätigt das Fach per Index-Sensor
  → erst jetzt Geld einziehen (Capture)
  → nur die Klappe dieser Ebene entriegeln
  → Reed: Klappe auf und wieder zu = ausgegeben
```

Jeder Schritt steht in einem SQLite-Journal, **bevor** er ausgeführt wird. Nach einem Stromausfall liest der Pi das Journal und räumt auf: Eine nicht eingezogene Order verfällt. Ein Kauf, der bezahlt, aber nicht ausgegeben wurde, wird automatisch erstattet, und der Betreiber bekommt eine Meldung.

**Sicherheitsregeln** (nicht verhandelbar):
1. Keine Capture vor verifizierter Positionierung.
2. Schlösser sind fail-secure, jede Entriegelung ist zeitlich begrenzt.
3. Journal vor Aktion.
4. Im Zweifel zugunsten des Kunden: bezahlt, aber nicht nachweislich ausgegeben, heißt Rückerstattung.
5. Verkauf nur mit synchroner Uhr, referenziertem Karussell, 24 V im Fenster und ohne aktiven Fehler.
6. 230 V nur außen, Abnahme durch eine Elektrofachkraft.

⚠️ „Ausgegeben“ heißt nur: Die Klappe war offen und ist wieder zu. Ob die Ware wirklich entnommen wurde, misst niemand. Eine Füllstandserkennung ist als Option (M3b) geplant.

---

## Kühlung, Heizung, Jahreszeiten

- **Regelung:** Ein Luftfühler steuert den Kühlschrank. Er schaltet bei 13,5 °C ein und bei 11,0 °C aus. Mindestzeiten: 5 min ein, 6 min aus, dazu 6 min Anlaufsperre nach dem Booten. Das Originalthermostat steht auf „kalt“ und dient nur als Backstop.
- **Eier-Sperre:** Ein Fühler auf der Eier-Ebene sperrt den Eierverkauf in diesen Fällen:
  - Temperatur außerhalb von 10–15 °C
  - Fühlerfehler
  - Uhr nicht synchron
  - ab dem 28. Tag nach dem Legen (§ 22 Abs. 3 Tier-LMHV)
- **Winter:** Ab etwa 10 °C Umgebungstemperatur abwärts läuft der Kompressor nicht mehr an, der Innenraum wird so kalt wie draußen. Die Eier sperren dann von selbst, und es gibt nur Honig. **Eier gibt es damit praktisch nur in der warmen Jahreshälfte.**
- **Elektronikbox:** Eine 24-V-PTC-Heizung hält die Box über +5 °C und mindestens 3 K über der Innenluft, gegen Kondensat und Frost. Grund: Der USB- und Ethernet-Chip des Pi 3B ist nur ab 0 °C spezifiziert.

---

## Stand

| Meilenstein | Inhalt | Stand |
|---|---|---|
| M0 | Planung, Repo, Konzept, ADRs | ✅ fertig |
| M1 | Karussell als Prüfstand auf dem Tisch | Software, Firmware und Protokoll laufen im Simulator (48 Tests grün). ⚠️ Die Firmware lief noch nie auf einem echten ESP32. Teile nicht bestellt, Maße noch Platzhalter. |
| M2 | PayPal-Sandbox, Kaufablauf mit Journal und Recovery, Display, Taster, LEDs | offen |
| M3 | Einbau in den Kühlschrank, Tür, Klimaregelung, Boxheizung | offen |
| M4 | 4 Wochen Feldtest | offen |

Checklisten: [`docs/milestones.md`](docs/milestones.md). Teilelisten: [`docs/bom/`](docs/bom/) (M2/M3 ≈ 780 €, ohne Kühlschrank und Elektrofachkraft).

---

## Bekannte Risiken

Aus der Machbarkeitsprüfung vom 23.11.2026. Noch nicht entschieden, Einzelheiten in [`docs/milestones.md`](docs/milestones.md#offene-punkte-aus-der-machbarkeitsprüfung-2026-11-23).

- ⚠️ **Wirtschaftlichkeit:** 12 Fächer ergeben eine kleine Füllung. Die PayPal-Gebühr (Größenordnung ≈ 2,99 % + 0,39 €, Konditionen prüfen) liegt bei 3 € bei ≈ 16 %. Bei einer Rückerstattung bleibt die Fixgebühr verloren. Kaufen kann nur, wer PayPal hat. 🔶 Vorschlag: Honig-Ebenen mit 8 Fächern à 45° und Eier-Ebenen mit 4 Fächern auf einem gemeinsamen 45°-Raster, das ergibt bis zu 20 Fächer.
- ⚠️ **Klappe und Ausstoßfeder:** Die Feder öffnet die Klappe beim Entriegeln 5 mm, der Reed meldet dann sofort „offen“. Die Rückerstattung bei „nie geöffnet“ greift so nie. Eine angelehnte Klappe blockiert jede Fahrt. Abhilfe: Schaltpunkt des Reed bei 15–20 mm, Zeitlimit für offene Klappen.
- ⚠️ **Kälte-Alarm:** Die Regel „Luft < 9 °C bei Relais aus“ soll ein klebendes Relais erkennen, löst aber jeden Wintertag aus. Vorschlag: Hilfskontakt am Schütz als Rückmeldung.
- ⚠️ **Eier-Fühler:** Er sitzt auf einer Ebene, die Fächer sind aber universal. In einem Kühlschrank ohne Umluft unterscheiden sich die Ebenen um mehrere Kelvin. Ein Umluftlüfter kommt dazu, wenn der 72-h-Test das zeigt.
- ⚠️ **Winterbetrieb:**
  - Das Getriebefett wird zäh, StallGuard kann fälschlich eine Blockade melden.
  - Der Pi muss kalt booten, bevor die Heizung läuft.
  - Beides prüft eine eigene Kältenacht-Abnahme.
- ⚠️ **Ungemessen:**
  - Kühlschrank-, Schachtel- und Glasmaße fehlen.
  - Die echte Schrittrate der MicroPython-Schleife ist unbekannt.
  - Die Fachzahl ist vorläufig.
- ⚠️ **Rechtliches:** Ob die Kleinmengenregel für Wachteln gilt, ist offen (Q7). Die Pflichten aus dem Verpackungsgesetz (LUCID) sind noch nicht geprüft. Beides vor den Käufen für M3 klären, nicht erst vor dem Feldtest.

---

## Rechtliches in Kürze

Keine Rechtsberatung. Vor dem Start klärt der Betreiber mit Lebensmittelüberwachung, Veterinäramt und Steuerberatung:
- Registrierung
- Etiketten (LMIV, HonigV)
- Kleinmengenregel für Wachteln
- Verpackungsgesetz
- steuerliche Einordnung

Für den Live-Betrieb braucht es ein PayPal-Geschäftskonto. Einzelheiten: [`docs/legal.md`](docs/legal.md).

---

## Offene Fragen

Kühlschrankmodell und Innenmaße, Schachtel- und Glasmaße, Fehlerstrom-Schutzschalter und Elektrofachkraft am Standort, Benachrichtigungskanal, Preise, Glasrücknahme. Vollständige Liste: [`docs/requirements.md`](docs/requirements.md).

---

## Für die Entwicklung

- Gesamtplan mit Schaltplänen und Steuerlogik: [`docs/technik.md`](docs/technik.md)
- Protokoll Pi ↔ ESP32: [`docs/protocol-esp32.md`](docs/protocol-esp32.md)
- Entscheidungen: [`docs/adr/`](docs/adr/)
- Arbeitsregeln: [`CLAUDE.md`](CLAUDE.md)
- Laufzeit: System-Python aus apt, kein Docker, keine venv (ADR 0010). Die Firmware-Logik läuft unverändert auch im Simulator, die Tests prüfen also den echten Firmware- und Protokollcode.

```bash
cd software && export PYTHONPATH=src:firmware/esp32:../cad/lib
python3 -m unittest discover -s tests -v       # Tests ohne Hardware
python3 -m vending.core.service_cli --sim      # Servicemodus gegen den Simulator
python3 ../cad/lib/geometry.py                 # Sektorrechner
```
