# Leistungsbilanz Kleinspannung (24 V SELV)

| Verbraucher | Typ. | Spitze | Bemerkung |
|---|---|---|---|
| Pi 3B (5 V) | 4 W | 7 W | über DC/DC 24→5,1 V 3 A (η≈90 %) |
| Display 3,5–5″ (ADR 0011) | 1,5 W | 3 W | Industrietyp, Hintergrundbeleuchtung dimmbar, zwischen Käufen gedimmt |
| Taster-LEDs A/B (24 V) | 0,5 W | 1 W | je Taster eine Farbe an |
| ESP32 (ohne Funk) + Sensoren | 0,4 W | 0,8 W | WLAN/BT aus |
| Schrittmotor + TMC2209 | 1 W (Halten reduziert) | 25 W | nur während der Fahrt |
| Schloss (1 gleichzeitig) | 0 W | 12 W | max. `unlock_max_s` |
| Heizung Elektronikfach | 0 W | 20 W | nur falls nachgerüstet (ADR 0009), bei < +5 °C |
| **Summe** | **≈ 9 W** | **≈ 70 W** | |

→ **24-V-Netzteil 100 W** (z. B. Hutschiene, Klasse II). 🔶 Das ist mehr als die 60 W aus dem Konzept: Reserve für Kälte (Motorstrom) und Alterung.
Absicherung je Zweig: Motor 3 A, Schlösser 2 A, Heizung 2 A, DC/DC 2 A (Flachsicherung oder PTC).

Die 230-V-Seite (Kühlschrank ca. 80–150 W, Anlauf deutlich höher) läuft separat über den Verteiler, siehe Konzept §8.
