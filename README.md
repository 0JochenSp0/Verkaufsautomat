# Verkaufsautomat für Wachteleier und Honig

Ein selbst gebauter Automat, an dem Kundinnen und Kunden rund um die Uhr Wachteleier und Honig aus eigener Erzeugung kaufen können. Bezahlt wird mit dem Handy über PayPal. Stand: 22.11.2026.

Diese Seite erklärt das Projekt ohne Fachwissen. Die technischen Einzelheiten stehen in [`docs/technik.md`](docs/technik.md).

---

## So kauft man

1. **Taster drücken:** Links ist der Taster für **Eier**, rechts der für **Honig**, darunter **Abbruch**.
2. **Mit dem Handy bezahlen:** Auf dem kleinen Bildschirm erscheinen Produkt, Preis und ein QR-Code. Den QR-Code mit dem Handy scannen und in PayPal bezahlen. Man hat dafür 3 Minuten.
3. **Ware entnehmen:** Der Automat dreht das richtige Fach vor eine Klappe und gibt nur diese Klappe frei. Klappe öffnen, Ware nehmen, Klappe zufallen lassen.

Wer es sich anders überlegt, drückt **Abbruch** oder den anderen Produkttaster. Dann wird nichts abgebucht.

**Was die Lichter an den Tastern bedeuten:**

| Licht | Bedeutung |
|---|---|
| 🟢 grün | Ware ist da und kann gekauft werden |
| 🔴 rot | Gerade nicht zu haben: ausverkauft, oder Eier sind gesperrt (z. B. zu warm, zu kalt oder zu alt) |
| 🟢 grün blinkend | Kauf läuft, bzw. die Klappe ist frei |
| ⚫ aus | Automat außer Betrieb |

---

## Was drin steckt

- **Ein gebrauchter Kühlschrank** als Gehäuse. Er hält die Ware gleichmäßig bei 10–15 °C. Außen bekommt er eine Holzverkleidung, vorne eine neue, selbst gebaute Tür.
- **Ein Drehteller mit Fächern** im Inneren, auf drei Etagen. Jedes Fach nimmt eine Schachtel Eier oder ein Glas Honig auf. Insgesamt sind es etwa 12 Fächer. Zum Start wird nur eine Etage eingebaut.
- **Drei kleine Klappen** in der Tür, eine pro Etage. Sie sind verschlossen und gehen nur nach dem Bezahlen auf, und immer nur vor dem gekauften Fach.
- **Ein kleiner Computer** (Raspberry Pi) steuert alles: Bezahlung, Bildschirm, Taster, Lichter und Kühlung. Ein **Helfer-Chip** (ESP32) bewegt den Drehteller und öffnet die Schlösser.
- **Ein Motor mit Schneckengetriebe** dreht den Drehteller. Das Getriebe lässt sich von Hand nicht weiterdrehen. So kommt niemand durch die offene Klappe an ein anderes Fach.

---

## Wie Geld und Ware geschützt sind

- **Erst bereitstellen, dann abbuchen:** Das Geld wird erst eingezogen, wenn das Fach nachweislich vor der Klappe steht.
- **Ohne Strom bleibt alles zu:** Die Schlösser sind so gebaut, dass sie ohne Strom verriegelt bleiben.
- **Im Zweifel Geld zurück:** Wenn bezahlt wurde, die Ware aber nicht sicher herausgegeben wurde, bekommt der Kunde sein Geld automatisch zurück. Der Betreiber wird benachrichtigt.
- **Alles wird mitgeschrieben:** Jeder Schritt eines Kaufs wird gespeichert, bevor er passiert. Nach einem Stromausfall weiß der Automat, wo er stehen geblieben ist.
- **Verkauft wird nur, wenn alles stimmt:** Uhrzeit, Strom, Temperatur und Technik müssen in Ordnung sein. Sonst leuchtet rot.

---

## Kühlung und Jahreszeiten

- Der Automat hält die Eier bei 10–15 °C. Ist es wärmer oder kälter, werden die Eier gesperrt (rotes Licht), Honig bleibt verkaufbar.
- Eier werden spätestens am 28. Tag nach dem Legen automatisch gesperrt, so verlangt es das Gesetz.
- **Im Winter** gibt es nur Honig. Die Kühlung bleibt dann aus.

---

## Rechtliches in Kürze

Keine Rechtsberatung. Vor dem Start klärt der Betreiber mit Lebensmittelüberwachung, Veterinäramt und Steuerberatung: Registrierung, Etiketten, Kleinmengenregel für Wachteln und die steuerliche Einordnung. Für den Verkauf braucht es ein PayPal-Geschäftskonto. Einzelheiten: [`docs/legal.md`](docs/legal.md).

Die Arbeiten an der 230-Volt-Seite (Steckdose, Sicherungen, Schalter für den Kühlschrank) macht eine Elektrofachkraft.

---

## Stand und nächste Schritte

| Schritt | Inhalt | Stand |
|---|---|---|
| M0 | Planung, Grundgerüst | ✅ fertig |
| M1 | Drehteller als Probeaufbau auf dem Tisch | läuft: Software fertig, Teile und Aufbau stehen aus |
| M2 | Bezahlen im PayPal-Testmodus, Bildschirm, Taster und Lichter | offen |
| M3 | Einbau in den Kühlschrank, neue Tür, Kühlung | offen |
| M4 | Vier Wochen Probebetrieb | offen |

Genaue Checklisten: [`docs/milestones.md`](docs/milestones.md). Teilelisten: [`docs/bom/`](docs/bom/).

---

## Was noch zu klären ist

- Welcher Kühlschrank, wie groß ist er innen, und wo sitzt sein Wärmetauscher?
- Wie groß sind die Eierschachteln und Honiggläser genau? Davon hängt die Zahl der Fächer ab.
- Gibt es am Standort einen Fehlerstrom-Schutzschalter, und wer ist die Elektrofachkraft?
- Wie soll der Betreiber benachrichtigt werden (E-Mail, App)?
- Preise und PayPal-Gebühren.
- Gilt die Kleinmengenregel auch für Wachteln?
- Sollen leere Honiggläser zurückgenommen werden?

Vollständige Liste: [`docs/requirements.md`](docs/requirements.md).

---

## Kleines Wörterbuch

| Begriff | Bedeutung |
|---|---|
| Fach / Sektor | ein Platz auf dem Drehteller für eine Schachtel oder ein Glas |
| Etage / Ebene | eine der drei Stufen des Drehtellers, jede mit eigener Klappe |
| QR-Code | das Quadratmuster auf dem Bildschirm, das man mit der Handykamera scannt |
| Abbuchen (Capture) | der Moment, in dem PayPal das Geld wirklich einzieht |
| fail-secure | ohne Strom verriegelt |

---

## Für Technikerinnen und Techniker

- Technischer Gesamtplan mit Schaltplänen und Steuerlogik: [`docs/technik.md`](docs/technik.md)
- Entscheidungen und Begründungen: [`docs/adr/`](docs/adr/)
- Arbeitsregeln für die Entwicklung: [`CLAUDE.md`](CLAUDE.md)
- Schnellstart ohne Hardware:
  ```bash
  cd software && export PYTHONPATH=src:firmware/esp32:../cad/lib
  python3 -m unittest discover -s tests -v
  python3 -m vending.core.service_cli --sim
  ```
