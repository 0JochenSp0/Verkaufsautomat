# ADR 0001 – Gebrauchter Kühlschrank mit eigener Regelung auf 10–15 °C

**Status:** angenommen (2026-11-21)

## Kontext
Für Wachteleier wurde keine gesetzliche Kühlpflicht gefunden. Verlangt ist eine „möglichst konstante Temperatur“ (Tier-LMHV Anl. 2/5), siehe `docs/legal.md`. Ein reines Holzgehäuse außen schwankt im Sommer stark. Der Kühlschrank begrenzt dafür den Karusselldurchmesser auf ca. 400 mm (Rechner mit den aktuellen Maßen: 403 mm) und damit auf ca. 12 Sektoren statt 18–27.

## Entscheidung
Wir bauen einen gebrauchten Kühlschrank ein, der Kältekreis bleibt unangetastet. Der Pi schaltet ihn über ein Relais und regelt mit Hysterese auf **10–15 °C**:
- Mindest-Aus-Zeit, Mindest-Ein-Zeit, Anlaufsperre nach Stromausfall. Die Werte stehen in konzept.md §4 (Stand 2026-11-22: 6 min aus, 5 min ein).
- Das Originalthermostat steht auf „kalt“ und dient als Sicherheits-Backstop.

## Alternativen
- Holzgehäuse ohne Kühlung: mehr Sektoren, aber im Sommer keine konstante Temperatur.
- Originalthermostat allein (ca. 4–8 °C): Bei Entnahme bildet sich Kondensat auf den Eiern, außerdem mehr Energie.

## Folgen
- ⚠️ Der Verflüssiger muss in der Verkleidung belüftet bleiben (Q1).
- ⚠️ Unter +10 °C Umgebung läuft der Kompressor außerhalb der Klimaklasse. Im Winter ist die Kühlung deshalb aus.
- Die Software braucht Temperaturfühler, Regler und Verkaufssperren (`vending.climate`).
