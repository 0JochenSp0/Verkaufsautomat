# Protokoll Pi ↔ ESP32 (v1)

UART 115200 8N1, ASCII, eine Zeile pro Nachricht, Ende `\n`. Der Pi fragt, der ESP32 antwortet mit genau **einer** Zeile `OK …` oder `ERR <code> …`. Asynchrone Ereignisse kommen jederzeit als `EVT …`, auch zwischen Anfrage und Antwort.

Implementierung: `software/firmware/esp32/carousel_fw/protocol.py` (ESP32), `software/src/vending/hal/esp32.py` (Pi).

## Transport und Update (ADR 0007, 0012)
- Pi `/dev/esp32` (USB, udev-Symlink) ↔ CP2102 auf dem DevKit ↔ ESP32 **UART0** (GPIO3/1). Dieselbe Leitung dient dem ROM-Bootloader und der MicroPython-REPL. DTR und RTS bleiben beim Öffnen gemeinsam gesetzt (Linux-Default). Werden sie einzeln umgeschaltet, setzt die Auto-Reset-Schaltung den ESP32 zurück.
- Nach jedem Reset sendet der ESP32 Bootmeldungen. Der Pi verwirft alle Zeilen, die nicht mit `OK`, `ERR` oder `EVT` beginnen.
- Die Firmware liest über `sys.stdin`, Ctrl-C (0x03) ist abgeschaltet. Ein Absturz landet in der REPL, der WDT resettet dann nach 3 s.
- **Update:** `software/firmware/esp32/flash.sh`. esptool versetzt den ESP32 über DTR/RTS (Auto-Reset-Schaltung des DevKits) in den Bootloader, das Skript flasht das MicroPython-Image komplett neu und kopiert die Dateien mit `mpremote`. Die Konfiguration schickt der Pi danach wie bei jedem Connect als `CFG`.

## Befehle
| Befehl | Antwort | Bemerkung |
|---|---|---|
| `PING` | `OK PONG <proto>` | dient auch als Heartbeat. Jede Zeile zählt, gerechnet ab dem **Ende** des Befehls (eine Fahrt kann länger als `hb_timeout_s` dauern) |
| `CFG <key> <value>` | `OK CFG <key>` | keys: `steps_per_rev sectors levels max_speed accel home_speed home_offset backoff retries unlock_max_s hb_timeout_s home_max_factor irun sgthrs`. `levels` ≤ 3 (Pins). `irun`/`sgthrs` gehen sofort und vor jedem `HOME`/`JOG` an den TMC2209. Eine Änderung von `steps_per_rev`, `sectors` oder `home_offset` hebt die Referenz auf |
| `HOME` | `OK AT 0` | Referenzfahrt, danach auf Sektor 0 mit Index-Prüfung |
| `GOTO <s>` | `OK AT <s>` | kürzester Weg, Stall → Fault (`retries` = 0), Index-Prüfung |
| `JOG <steps>` | `OK POS <pos>` | Service/Kalibrierung: fährt rohe Schritte (\|steps\| ≤ `steps_per_rev`), Referenz bleibt, Sektor wird −1 (kein `UNLOCK` bis zum nächsten `GOTO`). Stall → Fault |
| `UNLOCK <level> <s>` | `OK UNLOCKING <level> <s_eff>` | nur positioniert, nur 1 Klappe gleichzeitig, `s` ≤ `unlock_max_s` |
| `LOCK <level>` | `OK LOCKED <level>` | Solenoid stromlos |
| `STATUS` | `OK STATUS homed=0/1 sector=<s> pos=<steps> fault=<F> flaps=111 locks=000 door=1` | zusätzlich `cfg=0/1`. flaps/door: 1 = geschlossen. `cfg=0`: seit dem Reset kein `CFG`, der Pi konfiguriert neu (`MotionService.ensure_homed`). Geplant (M1): `v24=<mV>` (GPIO35) |
| `CLEAR` | `OK CLEARED` | Fehler quittieren (danach `HOME`) |
| `DISABLE` | `OK DISABLED` | Motor stromlos, Schlösser stromlos, unreferenziert |

## Fehlercodes
`NOT_HOMED`, `HOME_FAIL`, `STALL`, `INDEX` (Position nicht bestätigt), `HEARTBEAT`, `FAULT_ACTIVE`, `FLAP_OPEN` (drehen oder entriegeln bei offener Klappe), `LOCK_ACTIVE`, `NOT_READY`, `BAD_SECTOR`, `BAD_LEVEL`, `BAD_KEY`, `BAD_VALUE`, `BAD_ARGS`, `UNKNOWN`, `EMPTY`.

## Ereignisse
| Ereignis | Bedeutung |
|---|---|
| `EVT FLAP <n> OPEN\|CLOSED` | Reed-Kontakt Klappe n |
| `EVT LOCK <n> RELEASED OPENED\|TIMEOUT` | Solenoid abgeschaltet: Klappe wurde geöffnet bzw. Zeit abgelaufen |
| `EVT ALARM FLAP_FORCED <n>` | Klappe offen ohne Freigabe (Aufbruch/Defekt) |
| `EVT DOOR OPEN\|CLOSED` | Haupttür (Befüllung) |
| `EVT SAFE HEARTBEAT` | Pi still für `hb_timeout_s` → Motor aus, Schlösser zu, Fault `HEARTBEAT` |

## Sicherheitsinvarianten (ESP32 erzwingt sie, unabhängig vom Pi)
1. Keine Bewegung bei offener Klappe oder aktivem Schloss.
2. Maximal ein Schloss aktiv, zeitbegrenzt.
3. Bei Stall (nach `retries` Wiederholungen, Default 0) oder bei fehlendem Index-Signal: Fault, unreferenziert. Erst `CLEAR` + `HOME` macht wieder fahrbereit.
4. Bei Heartbeat-Verlust, ESP32-Reset (Hardware-WDT, Brownout, EN), im Bootloader und beim Flashen sind alle Ausgänge low bzw. hochohmig mit Pull-down/Pull-up: Schlösser zu (fail-secure), Motor aus.

Nach jedem Reset meldet sich der ESP32 mit Defaults und `cfg=0`. Der Pi sendet nach jedem (Re)Connect alle `CFG` (`MotionService.connect()`) und erneut, sobald `STATUS` `cfg=0` meldet.

## Zuordnung der Antworten (Pi)
`Esp32Carousel.request()` prüft das Schlüsselwort nach `OK` gegen den Befehl (`GOTO` → `AT`, `UNLOCK` → `UNLOCKING` …, sonst `PROTO`), `goto()` zusätzlich den Sektor (`POSITION`). Nach einem `TIMEOUT` oder `PROTO` schickt der Pi vor dem nächsten Befehl `PING` und verwirft alles bis zum `PONG`. So wird eine verspätete Antwort nie dem nächsten Befehl zugeordnet.
