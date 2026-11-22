# ADR 0006 – Display ohne Touch und Edelstahltaster, UI mit pygame/KMS

**Status:** angenommen (2026-11-21). Der Bedienteil (4 Taster, Display 7–10″) ist abgelöst durch ADR 0011 (2026-11-22). pygame/KMS, segno und „kein Touch“ gelten weiter.

## Kontext
Der Automat steht außen: Nässe, Kälte und Handschuhe. Capacitive Touch ist dabei unzuverlässig. Der Pi 3B hat 1 GB RAM, ein Chromium-Kiosk wäre schwer und anfällig.

## Entscheidung
- Industriedisplay (−20…+70 °C) hinter Polycarbonat, ohne Touch.
- Edelstahl-Vandalismustaster: ◀ ▶ (Auswahl), OK, Abbruch.
- Die UI läuft in Python mit pygame/SDL direkt auf KMS/DRM, ohne X und ohne Browser. Den QR erzeugt segno.
- Der Betreiber arbeitet über die Kommandozeile (`service_cli`). Eine Web-UI im LAN ist zurückgestellt (optional nach M4, Verschlankung 2026-11-22).

## Folgen
- Die Bedienführung ist bewusst einfach: Produkt wählen, Preis und QR, Klappe leuchtet bzw. öffnet.
