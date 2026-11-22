# ADR 0011 – Drei Taster mit Status-LED und kleines Display

**Status:** angenommen (2026-11-22). Löst den Bedienteil von ADR 0006 ab (4 Taster ◀ ▶ OK Abbruch, Display 7–10″).

## Kontext
Es gibt nur zwei Produkte: Wachteleier und Honig. Ein Menü mit Pfeiltasten ist dafür unnötig. Kunden sollen schon von Weitem sehen, ob etwas zu haben ist.

## Entscheidung
- **Taster A = Eier, Taster B = Honig, Taster Abbruch.** Edelstahl, vandalensicher. A und B haben einen Zweifarb-LED-Ring (rot/grün, 24 V).
- **LED:** grün = kaufbar. Rot = nicht kaufbar, also leer oder gesperrt (Temperatur, 28-Tage-Grenze, Fühler, Störung, Haupttür offen, Uhr nicht synchron). Grün blinkend = Kauf läuft bzw. Klappe frei. Aus = außer Betrieb.
- **Kleines Display (ca. 3,5–5″)** hinter Polycarbonat. Es zeigt das gewählte Produkt, den Preis (bei Honig mit Grundpreis €/kg), den PayPal-QR und den Countdown. Bei Rot zeigt ein Druck auf den Taster kurz den Grund.
- **Ablauf:** A oder B drücken → QR mit Countdown 3 min. Der andere Produkttaster wechselt das Produkt (alte Order verfällt), Abbruch beendet den Kauf. In beiden Fällen keine Capture.
- **Sektorwahl durch den Pi:** Eier mit dem ältesten Legedatum zuerst (weniger Verfall vor Tag 28), Honig über den kürzesten Fahrweg. Ein Preis je Produkt.
- **Anschluss am Pi** (der ESP32 hat keine freien Ausgänge): Taster an GPIO5/6/13, LEDs an GPIO12/16/20/21 über Low-Side-MOSFETs mit 10 kΩ Pull-down. Ohne laufenden Pi sind die LEDs aus.

## Alternativen
- **4 Taster + großes Display (ADR 0006):** mehr Möglichkeiten, aber unnötig bei zwei Produkten und mehr Strom.
- **2 Taster ohne Abbruch, nur Timeout:** einfacher, aber der nächste Kunde muss bis zu 3 min warten.
- **E-Paper:** gut bei Sonne, aber zu langsam für einen Countdown und träge im Frost.
- **Kein Display, statischer QR:** keine Zuordnung zum Fach und keine automatische Freigabe (ADR 0003).

## Folgen
- UI und Belegung werden einfacher: Ein Sektor ist nur „Eier“ (mit Legedatum) oder „Honig“ (mit MHD), der Preis hängt am Produkt.
- Display-Leistung sinkt von ca. 6 W auf ca. 2–3 W.
- ⚠️ Kleine Displays für −20…+70 °C sind selten. Typ und Kabel über die Scharnierschleife (HDMI-Kleindisplay oder DSI) bei der Auswahl prüfen.
- ⚠️ Bei den LED-Ringen auf gemeinsame Anode und 24-V-Typ achten, sonst passt der Low-Side-Treiber nicht.
- Pi-GPIO19 und 27 bleiben frei.
