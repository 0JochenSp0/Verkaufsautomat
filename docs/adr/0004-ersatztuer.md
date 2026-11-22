# ADR 0004 – Eigene Ersatztür statt Ausschnitten in der Originaltür

**Status:** angenommen (2026-11-21) 🔶 Abweichung vom Ausgangskonzept

## Kontext
Die Originaltür ist ein verklebtes PU-Schaum-Sandwich mit geformten Innenfächern. Ausschnitte schwächen die Tür, die Lage von Kabeln ist unbekannt, und saubere Klappenrahmen sind schwer einzubauen.

## Entscheidung
Wir bauen eine neue Tür:
- Multiplex-Rahmen, 50–60 mm XPS, innen HDPE- oder Alu-Verbundplatte
- Original-Scharniere und Magnetdichtung (gefräste Nut) oder Universaldichtung
- 3 Klappen aus dem CAD (`door.py`, `flap.py`), thermisch getrennte Rahmen, Hohlprofildichtung
- Ein gebogener Kragen innen folgt dem Karussellradius (Spalt < 8 mm)

## Folgen
- Mehr Bauaufwand, dafür voll parametrisch und reparierbar.
- Kabel laufen als Schleife über die Scharnierseite.
- Die Originaltür wird aufbewahrt, so bleibt der Umbau rückbaubar.
