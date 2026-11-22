# ADR 0003 – PayPal Orders v2: Polling, Capture erst nach Positionierung

**Status:** angenommen (2026-11-21)

## Kontext
Der Pi steht hinter NAT. Mit intent=CAPTURE fließt Geld erst bei der Capture. Mechanische Fehler (Blockade) sollen den Kunden nichts kosten.

## Entscheidung
- Pro Kauf wird eine Order erzeugt, der approve-Link erscheint als QR.
- Der Order-Status wird per **Polling** abgefragt, nur ausgehend über HTTPS und ohne Tunnel.
- Bei APPROVED: Karussell fahren, Index prüfen, **dann** Capture, dann entriegeln.
- Rückerstattung automatisch, wenn die Klappe nicht geöffnet wird oder ein Fehler nach der Capture auftritt.
- Alle Schritte stehen idempotent im SQLite-Journal: PayPal-Request-Id je Schritt, Recovery beim Boot.

## Alternativen
- Webhooks: brauchen einen öffentlichen Endpunkt (Tunnel). Eventuell später als Ergänzung.
- Statischer PayPal-QR: keine Zuordnung zum Sektor und keine automatische Freigabe.

## Folgen
- Zwischen Zahlung und Entriegelung liegen ein paar Sekunden für die Fahrt. Die UI zeigt dabei „Ihr Produkt wird bereitgestellt“.
- ⚠️ Live-Betrieb nur mit Geschäftskonto (`legal.md`).
