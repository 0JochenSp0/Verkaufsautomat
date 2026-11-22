# Anforderungen

Stand: 2026-11-21. Herleitung und Begründung stehen in [`konzept.md`](konzept.md).

## Funktionale Anforderungen

| ID | Anforderung | Prüfung | Meilenstein |
|---|---|---|---|
| F1 | 3 Ebenen auf einer Welle mit einem Antrieb. Sektoren sind universal und nehmen entweder 1 Eierschachtel oder 1 Glas à 500 g auf. Die Sektorzahl ergibt sich aus den Parametern (Ziel 10–20). | `geometry.py` mit echten Maßen, Probebestückung | M1 |
| F2 | Je Ebene 1 Ausgabeklappe mit fail-secure-Schloss und Zu-Sensor. Pro Kauf wird genau 1 Klappe entriegelt, vor genau 1 Sektor. | Sim-Test, Hardwaretest | M2/M3 |
| F3 | Display mit Tastern zeigt Auswahl, Gesamtpreis, Grundpreis (€/kg bei Honig) und dynamischen PayPal-QR mit Countdown. | Sichtprüfung, Sim | M2 |
| F4 | Ausgabe nur nach bestätigter Zahlung. Capture erst nach verifizierter Positionierung. Automatische Rückerstattung, wenn nicht ausgegeben wird. | Sim-Tests aller Sonderfälle | M2 |
| F5 | Web-UI im LAN mit Login: Belegung (Sektor → Produkt, Preis, Legedatum/MHD), Journal, Servicemodus (Sektor für Sektor weiterdrehen). | Manuell | M3 |
| F6 | Temperaturregelung 10–15 °C. Eier werden gesperrt bei Fenster-Verletzung (Grenze und Verzögerung als Parameter), bei Sensorfehler und ab dem 28. Tag nach dem Legen. | Sim-Test, 72-h-Log | M3 |
| F7 | Saisonmodus Winter: Kühlung aus, nur Honig. Optional eine Innenraumheizung für Eier im Winter (offen). | Konfiguration | M3 |
| F8 | Betreiber-Benachrichtigung bei FAULT, Rückerstattung, leerem Bestand, Temperaturalarm und Neustart. | Sim-Test | M2 |
| F9 | Servicemodus über Schlüsselschalter oder Web-UI. Bei geöffneter Haupttür sind keine Verkäufe möglich. | Hardwaretest | M1/M3 |

## Nicht-funktionale Anforderungen

| ID | Anforderung |
|---|---|
| N1 | Außen, überdacht. Elektronik für −20 … +40 °C Umgebung, Kondenswasser und Insekten. Das Elektronikfach ist beheizt. |
| N2 | Stromausfall in jedem Zustand ohne Verlust von Ware oder Geld. Klappen bleiben stromlos zu, beim Boot läuft eine Recovery. |
| N3 | Die Software läuft vollständig mit simulierter Hardware (Tests, Sandbox, Entwicklung am PC). |
| N4 | Alle Maße sind Parameter (`cad/params/params.json`). |
| N5 | Hardware-Watchdog, Autostart als Docker-Container (ADR 0008). Verkauf erst bei synchronisierter Uhrzeit. Read-only-Root entfällt 🔶 |
| N6 | Netz- und Kleinspannung in getrennten Gehäusen, RCD 30 mA, Außenkomponenten mindestens IP54 (Elektronik) bzw. IP65 (230 V). |
| N7 | Karussell ist selbsthemmend: Bei offener Klappe lässt es sich nicht von Hand verdrehen. Der Spalt zwischen Tür und Karussell ist kleiner als 8 mm. |

## Offene Fragen

| # | Frage | Wer | Blockiert |
|---|---|---|---|
| Q1 | Kühlschrankmodell, Klimaklasse, Verflüssigertyp (hinten offen oder Skin-Condenser in den Seitenwänden), Gefrierfach ja/nein | Betreiber | M3, Verkleidung |
| Q2 | Innenmaße (Breite, Tiefe ohne Verdampferabstand, Höhe) | Betreiber | Endgültige Sektorzahl |
| Q3 | Schachtelmaße (10er/18er) und Glastyp (DIB / TO82) | Betreiber | Endgültige Sektorzahl |
| Q4 | Ist ein RCD 30 mA am Standort vorhanden? Wer ist die Elektrofachkraft? | Betreiber | M3 |
| Q5 | Benachrichtigungskanal (E-Mail, ntfy, Telegram) | Betreiber | M2 |
| Q6 | Preise, Gebühren des PayPal-Geschäftskontos | Betreiber | M4 |
| Q7 | Fallen Wachteln unter die Kleinmengenregel (< 350 Legehennen)? Registrierung? | Veterinäramt / Lebensmittelüberwachung | M4 |
| Q8 | Eier im Winter mit Innenraumheizung anbieten? | Betreiber | M3 |
