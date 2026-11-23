"""HAL interfaces (typing.Protocol). Implementations: vending.hal.esp32 (real), vending.hal.sim."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class HalError(Exception):
    """Error reported by the hardware layer. `code` mirrors the ESP32 error codes."""

    def __init__(self, code: str, msg: str = ""):
        super().__init__(f"{code} {msg}".strip())
        self.code = code
        self.msg = msg


@dataclass(frozen=True)
class CarouselStatus:
    homed: bool
    sector: int            # -1 = unknown / not positioned
    pos: int
    fault: str             # "NONE" or fault code
    flaps_closed: tuple[bool, ...]
    locks_active: tuple[bool, ...]
    door_closed: bool
    configured: bool           # False = ESP32 was reset and runs on defaults, send CFG again

    @property
    def ready(self) -> bool:
        return self.homed and self.fault == "NONE" and all(self.flaps_closed) and self.door_closed


@dataclass(frozen=True)
class Event:
    """Asynchronous event from the co-processor, e.g. ('FLAP', ('0', 'OPEN'))."""
    kind: str
    args: tuple[str, ...]

    @classmethod
    def parse(cls, line: str) -> Event:
        parts = line.split()
        if len(parts) < 2 or parts[0] != "EVT":
            raise ValueError(line)
        return cls(parts[1], tuple(parts[2:]))


class CarouselDriver(Protocol):
    """Carousel motion + flap locks (both live on the ESP32)."""

    def ping(self) -> int: ...
    def configure(self, settings: dict[str, int]) -> None: ...
    def home(self) -> int: ...
    def goto(self, sector: int) -> int: ...
    def jog(self, steps: int) -> int: ...
    def unlock(self, level: int, seconds: int) -> int: ...
    def lock(self, level: int) -> None: ...
    def clear(self) -> None: ...
    def disable(self) -> None: ...
    def status(self) -> CarouselStatus: ...
    def poll_events(self) -> list[Event]: ...
    def keepalive(self) -> None: ...


class Thermometer(Protocol):  # M3: DS18B20 via 1-Wire
    def read_c(self) -> float: ...


class Relay(Protocol):  # M3: fridge compressor, heaters
    def set(self, on: bool) -> None: ...
    @property
    def is_on(self) -> bool: ...
