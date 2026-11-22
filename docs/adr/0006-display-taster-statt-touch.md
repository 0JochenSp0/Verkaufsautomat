# ADR 0006 – Display ohne Touch und Edelstahltaster, UI mit pygame/KMS

**Status:** angenommen (2026-11-21)

## Kontext
Der Automat steht außen: Nässe, Kälte und Handschuhe. Capacitive Touch ist dabei unzuverlässig. Der Pi 3B hat 1 GB RAM, ein Chromium-Kiosk wäre schwer und anfällig.

## Entscheidung
- Industriedisplay (−20…+70 °C) hinter Polycarbonat, ohne Touch.
- Edelstahl-Vandalismustaster: ◀ ▶ (Auswahl), OK, Abbruch.
- Die UI läuft in Python mit pygame/SDL direkt auf KMS/DRM, ohne X und ohne Browser. Den QR erzeugt segno.
- Die Admin-Oberfläche ist eine eigene Web-UI im LAN (FastAPI).

## Folgen
- Die Bedienführung ist bewusst einfach: Produkt wählen, Preis und QR, Klappe leuchtet bzw. öffnet.
