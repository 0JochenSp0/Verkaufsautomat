# ADR 0002 – RP2040 Pico (MicroPython) als Motion- und I/O-Coprozessor

**Status:** abgelöst durch ADR 0007 (2026-11-22), vorher angenommen (2026-11-21) 🔶 Erweiterung gegenüber dem Ausgangskonzept („Pi 3B, Python“)

## Kontext
Der Schrittmotor mit Schneckengetriebe (~1:30) und Microstepping braucht Schrittraten im kHz-Bereich mit sauberen Rampen. Python unter Linux erzeugt keine jitterfreien Pulse. Sicherheitsrelevante I/O (Schlösser, Klappen-Reed, Stall) sollen auch dann definiert reagieren, wenn der Pi hängt oder neu startet.

## Entscheidung
Ein Raspberry Pi Pico (RP2040) mit **MicroPython** übernimmt:
- Schrittausgabe (PIO), Homing, Index-Prüfung und StallGuard-DIAG
- Schlossansteuerung mit Zeitbegrenzung und Entprellen der Reed-Kontakte
- Heartbeat-Überwachung: Bleibt der Pi aus, ist der Motor aus und alle Schlösser sind stromlos (fail-secure).

Pi und Pico sind per UART verbunden, das Protokoll ist zeilenbasiert (`docs/protocol-pico.md`). Die gesamte Software bleibt Python.

## Alternativen
- pigpio-DMA-Waves direkt am Pi 3B: weniger Teile, aber kein unabhängiger Sicherheitsrückfall. Bleibt Fallback.
- Getriebemotor mit Encoder am Pi: nicht gewählt. Ohne Schneckengetriebe ist er nicht selbsthemmend, und die Encoder-Auswertung braucht ebenfalls Echtzeit (`konzept.md` §2).

## Folgen
- Zwei Firmware-Stände, die gemeinsam versioniert werden. `PING` meldet die Protokollversion.
- Die Motion-Logik ist ohne `machine` geschrieben und unter CPython testbar (`software/firmware/pico/motion.py`).
