# Konzept: DIY-Verkaufsautomat Wachteleier & Honig

> Freigegebener Projektplan vom 2026-11-21, unverändert übernommen. Spätere Änderungen
> stehen als ADR in `docs/adr/` und in `docs/milestones.md`. Dieses Dokument wird nicht nachgepflegt.

## Context
Neues, leeres Projekt (`/home/jochen/Verkaufsautomat`, noch kein Git). Ein gebrauchter Kühlschrank bekommt eine Holz-/XPS-Verkleidung und ein Karussell mit 3 Ebenen. Verkauft wird über PayPal-QR, die Steuerung ist ein Pi 3B mit Python. Das Repo enthält CAD, Elektronik, Software und Doku.

**Entscheidungen aus der Rückfragerunde:**
- **Kühlschrank bleibt.** Der Pi regelt den Innenraum selbst auf **10–15 °C**: Relais vor dem Kompressor, eigene Hysterese. Gelesen habe ich das als: Kühlschrank in die Verkleidung integriert, eigene Regelung statt Originalthermostat.
- **Eigene Ersatztür** aus Multiplex und XPS, die Klappen sind von Anfang an mitkonstruiert. Scharniere und Dichtung kommen vom Original.
- **Bedienung:** Display ohne Touch hinter Polycarbonat, dazu Edelstahl-Vandalismustaster.
- **Herkunft:** Wachteleier und Honig stammen beide aus eigener Erzeugung (Direktvermarktung).

Markierungen: ⚠️ = Risiko, 🔶 = abweichende Meinung bzw. Empfehlung gegen das Ausgangskonzept.

---

## 1. Anforderungen (Kurzfassung, wird `docs/requirements.md`)
**Funktional**
- F1: Es gibt 3 Ebenen auf einer Welle mit einem Antrieb. Sektoren sind universal und nehmen entweder 1 Eierschachtel oder 1 Glas à 500 g auf.
- F2: Je Ebene gibt es eine Ausgabeklappe mit fail-secure-Schloss und Zu-Sensor. Pro Kauf wird genau eine Klappe für genau einen Sektor freigegeben.
- F3: Auswahl, Preis inklusive Grundpreis und dynamischer PayPal-QR laufen über Display und Taster.
- F4: Die Ausgabe erfolgt nur nach bestätigter Zahlung. Automatische Rückerstattung, wenn nicht ausgegeben werden kann.
- F5: Web-UI im LAN für Belegung (Sektor → Produkt, Preis, Legedatum bzw. MHD), Verkaufsjournal und Servicemodus. Im Servicemodus dreht das Karussell Sektor für Sektor, Befüllen über die Haupttür.
- F6: Die Temperaturregelung hält 10–15 °C. Eier werden gesperrt bei Temperatur außerhalb des Fensters (Grenze und Verzögerung als Parameter), bei Sensorfehler und ab dem Abgabeverbot nach Legedatum (§ 22 Abs. 3 Tier-LMHV: ab dem 28. Tag).
- F7: Winterbetrieb: Kühlung aus, nur Honig. Optional kann eine kleine Heizung im Innenraum die Eier auch im Winter auf 10–15 °C halten (offener Punkt).
- F8: Betreiber-Benachrichtigung bei Fehlern, Rückerstattungen, leerem Bestand und Temperaturalarm.

**Nicht-funktional**
- N1: Außen, überdacht. Die Elektronik ist für ca. −20 bis +40 °C Umgebung ausgelegt, mit Kondenswasser und Insekten.
- N2: Stromausfall in jedem Zustand, ohne dass Ware oder Geld verloren geht. Klappen bleiben ohne Strom zu.
- N3: Die Software läuft vollständig mit simulierter Hardware auf dem PC (Tests, Sandbox).
- N4: Alle Maße sind Parameter: Kühlschrank-Innenmaße, Schachtel, Glas, Wandstärken, Spiele.

**Offene Fragen (blockieren den Planstart nicht):**
- Kühlschrankmodell und Klimaklasse.
- Verflüssiger hinten offen oder als Skin-Condenser in den Seitenwänden? ⚠️ Siehe Abschnitt 4.
- Hat der Kühlschrank ein Gefrierfach? Ein Vollraumkühlschrank wird dringend empfohlen.
- Innenmaße, Schachtelmaße (10er oder 18er?), Glastyp (DIB-Glas oder TO82).
- Ist am Standort ein FI/RCD 30 mA vorhanden?
- Wer übernimmt die 230-V-Installation (Elektrofachkraft)?
- Benachrichtigungskanal: E-Mail, ntfy oder Telegram.
- Preise.
- Anzahl der Wachteln, relevant für die Kleinmengengrenze.

---

## 2. Machbarkeit Karussell
**Geometrie** (überschlägig gerechnet: 4 mm Wand, 5 mm Spiel je Seite, 10 mm Abstand zum Rand)

| Ø Karussell | Glas Ø85 | Schachtel 125×98 liegend | Schachtel 150×110 liegend | Schachtel 125 hochkant (40 breit) |
|---|---|---|---|---|
| 380 mm | 8 | 3 | 2 | 6 |
| 420 mm | 9 | 4 | 3 | 8 |
| 450 mm | 10 | 5 | 4 | 10 |

- Den Durchmesser begrenzt **min(Innenbreite, nutzbare Innentiefe)**. Abzuziehen sind Abstand zur Verdampferplatte an der Rückwand und der Abstand zur Tür. Realistisch sind also **≈ 400–420 mm**.
- ⚠️ **Die liegende Eierschachtel bestimmt die Teilung**, nicht das Glas. Bei universalen Sektoren ergeben sich **4 je Ebene, also 12 gesamt**, mit Kartons um 125×98 mm. Bei größeren 18er-Schachteln sind es nur 3 je Ebene (9 gesamt) und das Ziel wird verfehlt.
- Optionen für mehr Positionen, ohne nennenswerten Mehraufwand:
  - (a) Kleinere 10er-Schachtel wählen.
  - (b) Produkt „2 Schachteln gestapelt“ als eine Einheit. Höhe ist durch das Glas ohnehin vorhanden.
  - (c) Später eine 4. Ebene, falls die Innenhöhe reicht. Das braucht eine 4. Klappe und ist damit nicht ohne Zusatzaufwand.
  - Endgültig entscheidet der Geometrierechner in M1, sobald die echten Maße vorliegen.
- Die Ebenenhöhe richtet sich nach dem Glas (ca. 110 mm + Spiel → Teilung ca. 150 mm). 3 Ebenen brauchen also ca. 45–50 cm Höhe. Der Rest bleibt für Lager und Antrieb.
- **Zugriffsschutz** 🔶: Die Trennwände reichen bis zum Rand. Die Fensterbreite an der Türinnenseite ist kleiner als die äußere Sehne eines Sektors, aber größer als die Produktbreite. Ein gebogener Kragen an der Türinnenseite folgt dem Karussellradius, sodass der Spalt unter 8 mm bleibt und kein Finger in den Nachbarsektor kommt.

**Mechanik:** Welle aus Edelstahl, Ø 20 mm. Unten ein Drehteller-Axiallager (Lazy Susan) für die Last, oben ein Führungslager. Böden und Trennwände aus HDPE oder PP-Platte: feuchtefest und abwischbar. Die Last liegt bei maximal ca. 12 × 0,75 kg ≈ 9 kg plus Eigengewicht.

**Antrieb, Empfehlung:** **Schrittmotor NEMA 17/23 + selbsthemmendes Schneckengetriebe (ca. 1:30) + TMC2209**
- Selbsthemmung verhindert, dass ein Kunde das Karussell bei offener Klappe von Hand weiterdreht. Das ist ein Sicherheitsmerkmal und kein Komfort.
- Getriebemotor mit Encoder wäre auch möglich. Der Schrittmotor liefert aber ohne Encoder reproduzierbare Positionen und erkennt Blockaden über StallGuard.

**Referenzierung und Positionserkennung:**
- Ein Hall-Sensor „Home“ und ein Hall-Sensor „Index“, dazu Magnete an jedem Sektor. Nach jeder Fahrt wird geprüft, ob der Index sitzt.
- Referenzfahrt nach jedem Start und nach jedem Fehler.
- Hall-Sensoren und Magnete sind vergossen und unempfindlich gegen Kondenswasser. Optische Sensoren kommen nicht in Frage.

**Echtzeit** 🔶: Python auf Linux erzeugt keine sauberen Schrittpulse. Empfehlung: **Coprozessor mit MicroPython für Motion und I/O**, umgesetzt mit einem **ESP32** (ADR 0007, ursprünglich RP2040 Pico, ADR 0002). Er übernimmt Schritte, Homing, Entprellen und sichere Zustände und ist per UART an den Pi angebunden. Die Software bleibt damit komplett Python. Fallback wäre pigpio-DMA-Waves direkt auf dem Pi 3B. Entschieden in ADR 0002, abgelöst durch ADR 0007.

**Blockade:**
- Erkannt wird sie über StallGuard oder wenn der Index-Impuls nicht rechtzeitig kommt.
- Reaktion: Stopp, kurz zurückfahren, einmal neu versuchen. Klappt das nicht, geht der Automat in FAULT.
- Im Kauf bedeutet FAULT: keine Capture (siehe 6). Der Sektor wird gesperrt und der Betreiber benachrichtigt.

**Kondenswasser:**
- Motor und Getriebe sitzen unten auf einer Grundplatte im Innenraum. Dafür wird kein Loch in den Korpus gebohrt.
- Platinen bekommen Schutzlack, Stecker sind IP67.
- Bei 10–15 °C vereist der Verdampfer kaum. Tropfwasser läuft über die Originalrinne ab, das Karussell hält Abstand zur Rückwand.

---

## 3. Klappen in der (neuen) Tür
**Tür:** Rahmen aus Multiplex, 50–60 mm XPS, innen eine HDPE- oder Alu-Verbundplatte. Die Original-Magnetdichtung wird in eine gefräste Nut übernommen, alternativ eine Universaldichtung. Die Originalscharniere bleiben.

**Klappen:**
- Je Ebene ein Ausschnitt mit eingeklebtem Rahmen. Die Klappe ist ein XPS-Sandwich, oben angeschlagen.
- Sie schließt durch Schwerkraft, mit Dämpfer. Umlaufend EPDM-/Silikon-Hohlprofildichtung.
- Wärmebrücke: Den Rahmen thermisch trennen (Kunststoff/Holz, keine durchgehenden Metallteile). Kondensat an der Außenkante wird bei 10–15 °C innen kaum auftreten.

**Schloss:**
- ⚠️ **Fail-secure-Hubmagnetschloss mit Schnappfalle.** Ohne Strom bleibt es zu, beim Zufallen rastet es selbst ein.
- Ein klassischer Haftmagnet („Maglock“) wäre fail-safe, also ohne Strom offen. Das ist hier ungeeignet.
- Eine Ausstoßfeder öffnet die Klappe beim Entriegeln um ca. 5 mm, damit der Kunde sieht, welche Klappe frei ist.

**Zu-Sensor:** Reedkontakt an der Klappe, optional ein Rückmeldekontakt im Schloss.

**Leitungen:**
- Kabel laufen als Schleife über die Scharnierseite in die Tür. Heizdrähte und Originalleitungen in der Tür entfallen, weil die Tür neu ist.
- ⚠️ Für die Kabeldurchführung im **Korpus** (Motor, Sensoren) zuerst mit Wärmebild bei laufendem Kompressor prüfen. Im Vorderflansch liegt oft ein Heißgas-Rahmenrohr, in den Seitenwänden eventuell der Verflüssiger. Bevorzugt eine vorhandene Durchführung nutzen (Thermostat oder Licht). Sonst ein Loch an einer freien Stelle und mit PU-Schaum abdichten.

---

## 4. Klimaklasse, Temperatur, Elektronikfach
**Klimaklassen** (EN 62552): SN +10…32 °C, N +16…32, ST +16…38, T +16…43.
- Bei 10–15 °C Soll ist die Last deutlich kleiner als bei 4 °C, sodass unter dem Dach auch N/ST meist reichen.
- ⚠️ Unterhalb von +10 °C (SN) läuft der Kompressor außerhalb der Spezifikation. Das passt zum Plan „Kühlung im Winter aus“.

**Regelung:**
- Das Originalthermostat steht auf „kalt“ und dient als Sicherheits-Backstop. Der Pi schaltet das Relais (Schließer) mit Hysterese.
- Mindest-Aus-Zeit 5 min (Druckausgleich), Mindest-Ein-Zeit, und die Zahl der Starts pro Stunde ist begrenzt.
- Fällt der Pi aus, fällt das Relais ab, der Kühlschrank geht aus und die Eier werden über die Temperaturgrenze gesperrt.

**⚠️ Verkleidung:**
- Der Verflüssiger muss frei bleiben. Bei einem Skin-Condenser in den Seitenwänden dürfen diese **nicht** mit XPS gedämmt werden: Luftspalt plus Lüftungsöffnungen unten und oben.
- Bei einem Drahtverflüssiger hinten gilt dasselbe für die Rückseite. Lüftungsquerschnitt nach Herstellerangabe.
- Im Sommer fängt die Holzverkleidung die Sonne ab, die Dämmung ist eher sekundär.

**Elektronikfach** (oben vorn, hinter dem Display, nicht über der Kompressorwärme):
- IP54-Gehäuse mit Druckausgleichs-Membran und PTC-Heizung 10–20 W, die per Thermostat unter ca. +5 °C anspringt und auch Taupunkt-Kondensat verhindert.
- Pi 3B laut Hersteller ca. 0–50 °C (wird geprüft). Display: Industrietyp mit −20…+70 °C wählen, Consumer-LCDs werden unter 0 °C träge.
- Industrielle SD-Karte (pSLC) oder USB-SSD.

---

## 5. Systemarchitektur
```
230 V ─ RCD 30 mA (Bestand prüfen) ─ LS ─┬─ Relais/Installationsschütz ─ Kühlschrank
        [IP65-Verteiler, Netzteil]        ├─ (opt.) Relais ─ Innenraumheizung
                                          ├─ Thermostat ─ PTC-Heizung Elektronikfach
                                          └─ Netzteil 24 V DIN (z. B. 60 W)
24 V (SELV) ─ Sicherungen je Zweig ─┬─ TMC2209 ─ Schrittmotor + Schneckengetriebe
                                    ├─ 3× Low-Side-MOSFET + Freilaufdiode ─ 3 Schlösser 24 V
                                    └─ DC/DC 24→5,1 V 3 A ─ Pi 3B + Display + ESP32
Pi 3B ─UART0 + EN/BOOT─ ESP32 (MicroPython): STEP/DIR/EN/DIAG, Hall Home, Hall Index, 3 Schlösser, 3 Klappen-Reed,
                                 Türkontakt Haupttür, Servicetaster/Schlüsselschalter
Pi 3B direkt: 1-Wire DS18B20 (Innen Eier-Ebene, Innen Luft, Elektronikfach, Außen), Relais-Ausgänge
              (Kühlschrank, Heizungen), Bedientaster, Display (HDMI/DSI), DS3231-RTC (I²C), Ethernet
```
- Die Eingänge aus dem Innenraum sind gegen ESD geschützt (Pull-ups, RC-Filter). Leitungen gehen nicht direkt an GPIOs, ohne Schutz.

---

## 6. Zahlungsablauf (PayPal Orders API v2, intent=CAPTURE)
**Kernidee:** Erst capturen, wenn die Ausgabe technisch gesichert ist. Bei intent=CAPTURE fließt bis zur Capture kein Geld.
```
Kunde      Pi                                  PayPal
 │ wählt ─▶ prüft Sektor frei/Temp ok, reserviert (DB: RESERVED)
 │          POST /v2/checkout/orders ─────────▶ order_id, approve-Link
 │ ◀─ QR(approve-Link), Countdown 3 min (DB: ORDER_CREATED)
 │ scannt, zahlt am Handy ───────────────────▶ status APPROVED
 │          Polling GET /orders/{id} alle 2 s ◀─ APPROVED
 │          Karussell fahren + Index prüfen (DB: POSITIONED)
 │          POST /orders/{id}/capture ────────▶ COMPLETED (capture_id)  (DB: PAID)
 │          Schloss Ebene n öffnen (DB: UNLOCKED)
 │ öffnet Klappe (Reed offen), entnimmt, schließt (Reed zu) (DB: DISPENSED → Sektor leer)
```
**Sonderfälle:**

| Fall | Verhalten |
|---|---|
| Abbruch-Taste oder QR-Timeout | Keine Capture, Reservierung aufheben. Die Order verfällt bei PayPal, Kosten entstehen nicht. |
| Positionierung scheitert (Blockade) | Keine Capture, FAULT, Sektor gesperrt, Meldung an den Betreiber. |
| Capture schlägt fehl oder ist unklar (Netzwerk) | Status erneut abfragen und idempotent wiederholen (PayPal-Request-Id). Danach entweder freigeben oder nicht. |
| Bezahlt, Klappe wird nicht in 2 min geöffnet | Wieder verriegeln, **automatische Rückerstattung** (`POST /v2/payments/captures/{id}/refund`), Meldung an den Betreiber. |
| Bezahlt, Schloss- oder Sensorfehler | Rückerstattung, Ebene sperren, Meldung an den Betreiber. |
| Stromausfall | Die Schlösser bleiben zu (fail-secure). Beim Booten liest die Recovery offene Journaleinträge und fragt den Order-Status ab. Bei COMPLETED ohne „Klappe geöffnet“ wird zurückerstattet. Bei „Klappe war offen“ gilt die Ware als ausgegeben und wird zur Prüfung an den Betreiber gemeldet. Bei APPROVED wird nicht gecaptured, die Order verfällt. |
| Pi hinter NAT | **Nur Polling**, ausschließlich ausgehend über HTTPS. Ein Tunnel oder Webhook ist nicht nötig. Webhooks sind optional später über einen Tunnel, nur als Zusatz. |

- Das Journal liegt in SQLite (WAL, synchronous=FULL) auf der beschreibbaren Datenpartition. Jeder Zustandswechsel wird geschrieben, bevor die Aktion ausgeführt wird.
- ⚠️ **Gebühren:** Bei Kleinbeträgen (ca. 2–5 €) frisst der Fixanteil pro Transaktion einen hohen Prozentsatz. Konditionen des Geschäftskontos prüfen und die Preise danach kalkulieren.

---

## 7. Robustheit Pi 3B
- **OS:** Raspberry Pi OS Lite 64-bit. Die Software läuft als Docker-Container im Projektordner, Daten liegen in `./data` (ADR 0008). 🔶 Ein read-only Root ist nicht vorgesehen. ⚠️ Ohne ihn steigt das Risiko für die SD-Karte bei Stromausfall, deshalb Industrie-SD oder SSD und regelmäßige Backups von `./data`. Logs mit Rotation. Journald nur im RAM, Fehler werden zusätzlich an den Betreiber gemeldet.
- **Watchdog:** Hardware-Watchdog über systemd (`RuntimeWatchdogSec`). Ab M2 überwacht ein Docker-Healthcheck mit `restart: unless-stopped` die App. Der ESP32 fällt in einen sicheren Zustand (Motor stromlos halten, Schlösser zu), wenn der Pi-Heartbeat ausbleibt.
- **Autostart:** systemd-Units für `vending-core` (Zustandsmaschine, PayPal, HAL), `vending-ui` und `vending-web`. Die Display-UI läuft mit pygame/SDL direkt auf KMS, ohne X und ohne Browser, weil 1 GB RAM knapp sind. 🔶
- **Uhrzeit:** NTP (systemd-timesyncd). **Verkäufe sind gesperrt, bis die Zeit synchronisiert ist**, weil TLS, Legedatum-Sperre und Journal davon abhängen. Dazu ein DS3231-RTC-Modul (ca. 3 €) als Rückfall. 🔶 Empfohlen trotz „ohne RTC“: Bei Netzausfall bleibt sonst der Eier-Fristcheck blind.

---

## 8. Elektrische Sicherheit
- Zuleitung über RCD 30 mA Typ A (Bestand prüfen) plus eigenen Leitungsschutz.
- Außen H07RN-F, Verschraubungen IP65/IP67.
- **Getrennte Gehäuse:** 230-V-Verteiler (IP65, DIN-Schiene: Klemmen, Relais oder Installationsschütz für den Kompressor, Netzteil) und SELV-Elektronikfach. Eine 230-V-Leitung kommt nicht ins SELV-Fach. Ausnahme ist die PTC-Heizung: dann als 24-V-Heizung ausführen 🔶, damit das Elektronikfach rein SELV bleibt.
- Schutzleiter am Kühlschrankgehäuse bleibt erhalten, ebenso an allen berührbaren Metallteilen.
- Kompressor-Relais für induktive Last bzw. Motorlast dimensioniert (AC-3/AC-15), mit Varistor oder RC-Glied.
- ⚠️ Die 230-V-Installation nimmt eine Elektrofachkraft ab (DIN VDE 0100). Ich plane und dokumentiere sie, verdrahte sie aber nicht als „fertig“.

---

## 9. Rechtliches (Stand der Recherche, **keine Rechtsberatung**, Bestätigung durch Lebensmittelüberwachung und Steuerberatung nötig)
**Wachteleier**
- **Keine gesetzliche Kühlpflicht gefunden.**
  - Tier-LMHV Anlage 2 (Kleinmengen) und Anlage 5 Kap. IV verlangen: Eier sauber, trocken, frei von Fremdgeruch, vor Stößen und Sonne geschützt, „bei einer – möglichst konstanten – Temperatur“ aufbewahren.
  - § 22 Abs. 3: Die Abgabe an Verbraucher ist ab Ablauf des **28. Tages nach dem Legen** verboten, ein Verstoß ist eine Straftat nach § 23.
  - Der früher zitierte § 20 (5–8 °C ab Tag 18) ist weggefallen.
  - Die Regelung auf 10–15 °C erfüllt „konstant“ gut.
- **Kleinmengen:** § 3 Abs. 2 Nr. 2 Tier-LMHV: „Eier aus eigener Erzeugung von Betrieben mit weniger als 350 Legehennen“. ⚠️ Unklar ist, ob und wie Wachteln darunter fallen. Beim Veterinäramt klären.
- **Vermarktungsnormen** (Erzeugercode, Güteklassen): gelten nach meinem Stand nur für Hühnereier (VO (EU) 2023/2465). Wachteleier sind damit nicht erfasst. Den Geltungsbereich in Art. 1 noch prüfen.
- **Kennzeichnung vorverpackt** (LMIV 1169/2011 Art. 9): Bezeichnung, Nettofüllmenge (Stückzahl), MHD, Aufbewahrungshinweis, Name und Anschrift. Empfohlen zusätzlich das Legedatum, das die Software ohnehin braucht.
- **Registrierung** als Lebensmittelunternehmer (VO (EG) 852/2004 Art. 6). Wachtelhaltung bei der Tierseuchenkasse und nach Viehverkehrsverordnung melden: prüfen.

**Honig** (HonigV + LMIV)
- Bezeichnung „Honig“, Name und Anschrift, MHD, Los (entfällt bei tagesgenauem MHD), Nettofüllmenge in g mit mindestens 4 mm Schriftgröße bei 200–1000 g, Ursprungsland.

**Preisangabe** (PAngV)
- Gesamtpreis (§ 3). **Grundpreis je kg** für Honig (§ 4), also 500 g → €/kg auf dem Display.
- Eier werden nach Stück verkauft, ein Grundpreis entfällt (prüfen).

**PayPal**
- Laut Nutzungsbedingungen muss ein Privatkonto hauptsächlich privat genutzt werden. **Vor Live-Betrieb also auf ein Geschäftskonto umstellen.**
- Die Sandbox funktioniert sofort. Ob Live-REST-Credentials ein Geschäftskonto voraussetzen, wird geprüft (Annahme: ja).

**Steuer und Gewerbe**
- Kleinunternehmer (§ 19 UStG) oder landwirtschaftliche Durchschnittssatzbesteuerung (§ 24 UStG).
- Urproduktion vs. Gewerbe für den Automaten klären: Steuerberatung und Gemeinde.

**Variante ohne Kühlschrank:** Rechtlich voraussichtlich zulässig, aber „möglichst konstant“ ist im Sommer im Holzgehäuse kaum haltbar. Du hast dich für den Kühlschrank entschieden. Die CAD-Parametrik hält ein reines Holzgehäuse trotzdem offen: größerer Durchmesser bedeutet 18–27 Sektoren.

**Quellen:**
- [Tier-LMHV (Volltext)](https://www.gesetze-im-internet.de/tier-lmhv/BJNR182800007.html)
- [Tier-LMHV Anlage 2](https://www.gesetze-im-internet.de/tier-lmhv/anlage_2.html)
- [Tier-LMHV Anlage 5](https://www.gesetze-im-internet.de/tier-lmhv/anlage_5.html)
- [VO (EU) 2023/2465](https://eur-lex.europa.eu/eli/reg/2023/2465/oj?locale=de)
- [HonigV](https://www.gesetze-im-internet.de/honigv_2004/BJNR009200004.html)
- [LWG Bayern – Honig-Etikettierung](https://www.lwg.bayern.de/mam/cms06/bienen/dateien/recht-etikettierung.pdf)
- [PAngV § 4](https://www.gesetze-im-internet.de/pangv%5F2022/__4.html)
- [IHK Aachen – Preisangabe](https://www.ihk.de/aachen/recht/rechtsinformationen/aktuelle-dokumente-zum-thema-recht/preisangabe-im-handel-607416)
- [PayPal-Nutzungsbedingungen DE](https://www.paypal.com/de/webapps/mpp/ua/useragreement-full)
- [PayPal – Kontoumstellung](https://www.paypal.com/de/smarthelp/article/HELP339)
- [Verbraucherportal Bayern – Eierfrische](https://www.verbraucherportal.bayern.de/essen_trinken/hygiene_technologie/pic/eier_frische_neu.pdf) (Sekundärquelle, zitiert den veralteten § 20)

---

## 10. Repo-Struktur
```
Verkaufsautomat/
├─ CLAUDE.md                 Kontext, Konventionen, Sicherheitsregeln (fail-secure, keine Capture vor Positionierung)
├─ README.md
├─ cad/
│  ├─ params/params.json     alle Maße (Kühlschrank innen, Schachtel, Glas, Spiele, Wandstärken)
│  ├─ macros/                FreeCAD-Python: carousel.py, door.py, flap.py, cladding.py, export.py
│  ├─ lib/geometry.py        reine Python-Geometrie (Sektorrechner), ohne FreeCAD testbar
│  └─ out/                   (gitignored) STEP/STL/DXF, Zuschnittlisten
├─ Dockerfile, docker-compose.yml   Laufzeit für Entwicklung und Betrieb (ADR 0008), Daten in ./data
├─ electronics/
│  ├─ schematics/            KiCad-Projekt (später), vorerst Blockschaltbild + Pinbelegung als Markdown
│  ├─ pinout.md
│  └─ power-budget.md
├─ software/
│  ├─ pyproject.toml         Python ≥3.11, uv/pip, pytest, ruff
│  ├─ src/vending/
│  │  ├─ core/               Zustandsmaschine, Journal (SQLite), Recovery
│  │  ├─ hal/                Interfaces + sim.py (Simulator) + esp32.py (UART-Protokoll)
│  │  ├─ payment/            PayPal-Client (Orders, Capture, Refund), Sandbox-Config
│  │  ├─ climate/            Temperaturregelung, Verkaufssperren
│  │  ├─ ui/                 pygame-Display, QR (segno)
│  │  └─ web/                FastAPI-Admin (Belegung, Journal, Service)
│  ├─ firmware/esp32/        MicroPython: motion, homing, IO, Heartbeat, flash.sh
│  └─ tests/
└─ docs/
   ├─ requirements.md
   ├─ adr/                   0001-kuehlschrank-mit-eigener-regelung, 0002-pico-coprozessor (abgelöst),
   │                         0003-paypal-polling-capture-nach-positionierung, 0004-ersatztuer,
   │                         0005-fail-secure-schloesser, 0006-display-taster-statt-touch,
   │                         0007-esp32-statt-pico, 0008-docker-laufzeit
   ├─ legal.md               Abschnitt 9 + Behörden-Checkliste
   ├─ assembly/              Aufbauanleitung je Meilenstein
   └─ bom/                   BOM je Meilenstein (CSV + MD)
```
Konventionen (in CLAUDE.md):
- Code, Bezeichner und Commits auf Englisch, Doku auf Deutsch. Maße in mm, Temperaturen in °C.
- Jede Geometrie hängt an `params.json`. Die Hardware ist ausschließlich über HAL-Interfaces angebunden.
- Jede Zahlungsänderung braucht einen Sim-Test. Secrets nur in `/data/secrets.env`, nie im Repo.

---

## 11. Meilensteine
**M0 – Gerüst (direkt nach Freigabe)**
- `git init`, Struktur, CLAUDE.md, requirements.md, ADR 0001–0006, legal.md, `.gitignore`.

**M1 – Karussell-Prototyp auf dem Tisch**
- Software, ohne Hardware sofort umsetzbar:
  - `cad/lib/geometry.py` (Sektorrechner + Tests, gibt eine Tabelle wie in Abschnitt 2 für die echten Maße aus).
  - FreeCAD-Makro `carousel.py`, parametrisch: Ebenen, Trennwände, Welle, Grundplatte.
  - HAL-Interfaces + Simulator, ESP32-Firmware (Motion, Homing, Index, Stall, Heartbeat) mit UART-Protokoll.
  - `vending.core`-Motion-Service + Servicemodus-CLI („nächster Sektor“, „gehe zu n“, „referenzieren“).
  - BOM M1 und Aufbauanleitung M1.
- Hardware (du): ESP32-DevKit, TMC2209, NEMA17/23, Schneckengetriebe, 2 Hall-Sensoren, 24-V-Netzteil, Holz-/HDPE-Prototyp einer Ebene.
- **Abnahme:**
  - 500 zufällige Positionierungen ohne Fehlposition.
  - Blockade wird in unter 2 s erkannt, inklusive Retry und FAULT.
  - Nach Stromtrennung startet der Automat mit Referenzfahrt neu.
  - Von Hand lässt sich das Karussell nicht verdrehen (Selbsthemmung).

**M2 – Zahlung in der PayPal-Sandbox**
- Orders/Capture/Refund-Client, Zustandsmaschine nach Abschnitt 6, Journal und Recovery, Display-UI mit QR und Countdown, Grundpreis-Anzeige.
- **Abnahme:** Alle Sonderfälle aus Abschnitt 6 laufen als automatisierte Sim-Tests und manuell in der Sandbox. Dazu ein Stromausfall-Test mit Stecker ziehen in jedem Zustand.

**M3 – Einbau in den Kühlschrank**
- Ersatztür mit Klappen, Schlössern und Reed-Kontakten. Verkleidung mit Verflüssiger-Lüftung. Elektronikfach mit Heizung. 230-V-Verteiler (Abnahme Elektrofachkraft). Temperaturregelung 10–15 °C und Eier-Sperren. Web-UI für die Belegung.
- **Abnahme:** 72 h Temperaturlog innerhalb des Fensters, alle Klappen bestehen den Fail-secure-Test.

**M4 – Feldtest**
- Voraussetzungen: PayPal-Geschäftskonto, Registrierung und Auskunft der Lebensmittelüberwachung, Etiketten.
- 4 Wochen Betrieb mit Benachrichtigungen. Auswertung: Fehlkäufe, Rückerstattungen, Temperatur, Kondensat.

---

## Verifikation
- `pytest` in `software/` für Geometrie, Zustandsmaschine, Recovery und Klimasperren. Hardware läuft dabei vollständig simuliert, `ruff` für den Stil.
- `cad/lib/geometry.py` als CLI mit `params.json` ergibt die Sektor-Tabelle.
- FreeCAD-Makros headless über `freecadcmd`. ⚠️ FreeCAD ist auf diesem Rechner nicht installiert. Ohne Installation (`apt install freecad`, vorher fragen) prüfe ich die Makros nur syntaktisch.
- ESP32-Firmware: Logik-Tests mit CPython-Mock, Hardwaretest durch dich nach der Aufbauanleitung M1.
