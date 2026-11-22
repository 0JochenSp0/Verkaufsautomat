# ADR 0005 – Fail-secure-Hubmagnetschlösser statt Haftmagnet

**Status:** angenommen (2026-11-21) ⚠️ Präzisierung von „Magnetschloss“ im Konzept

## Kontext
Haftmagnete („Maglock“) sind **fail-safe**: Ohne Strom sind sie offen. Bei Stromausfall wäre der Automat damit frei zugänglich.

## Entscheidung
Wir verwenden **fail-secure-Hubmagnetschlösser mit Schnappfalle** (24 V):
- Ohne Strom verriegelt, beim Zufallen rastet die Klappe selbst ein.
- Die Ansteuerung ist zeitlich begrenzt (Coprozessor, heute ESP32 nach ADR 0007, max. `unlock_max_s`) und passt zur Einschaltdauer des Schlosses.
- Eine Ausstoßfeder öffnet die Klappe beim Entriegeln ca. 5 mm.
- Ein Reed-Kontakt meldet „Klappe zu“. Einen Rückmeldekontakt im Schloss gibt es nicht (Verschlankung 2026-11-22). ⚠️ Der Reed weist nur „Klappe zu“ nach, nicht „Falle eingerastet“. Nachrüsten, wenn der Feldtest zeigt, dass Klappen zu, aber nicht verriegelt sind.

## Folgen
- Die Schlosstypen werden nach Einschaltdauer (ED) ausgewählt (BOM M3).
- Die Software unterstellt nie „stromlos = offen“.
