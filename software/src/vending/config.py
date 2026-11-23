"""Machine configuration derived from cad/params/params.json (single source of truth)."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PARAMS = Path(os.environ.get("VENDING_PARAMS", REPO_ROOT / "cad" / "params" / "params.json"))

try:  # cad/lib/geometry.py is shared with the FreeCAD macros
    import geometry  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - depends on PYTHONPATH
    sys.path.insert(0, str(REPO_ROOT / "cad" / "lib"))
    import geometry  # type: ignore[import-not-found,no-redef]


@dataclass(frozen=True)
class MachineConfig:
    levels: int
    sectors_per_level: int
    steps_per_rev: int
    max_speed_sps: int
    accel_sps2: int
    home_speed_sps: int
    backoff_steps: int
    retries: int
    home_offset_steps: int
    unlock_max_s: int
    hb_timeout_s: int
    keepalive_s: float
    tmc_irun: int
    tmc_sgthrs: int

    @property
    def positions(self) -> int:
        return self.levels * self.sectors_per_level

    def position_to_level_sector(self, position: int) -> tuple[int, int]:
        if not 0 <= position < self.positions:
            raise ValueError(f"position {position} out of range 0..{self.positions - 1}")
        return divmod(position, self.sectors_per_level)

    def esp32_settings(self) -> dict[str, int]:
        """Key/values sent to the ESP32 via `CFG key value`."""
        return {
            "steps_per_rev": self.steps_per_rev,
            "sectors": self.sectors_per_level,
            "levels": self.levels,
            "max_speed": self.max_speed_sps,
            "accel": self.accel_sps2,
            "home_speed": self.home_speed_sps,
            "home_offset": self.home_offset_steps,
            "backoff": self.backoff_steps,
            "retries": self.retries,
            "unlock_max_s": self.unlock_max_s,
            "hb_timeout_s": self.hb_timeout_s,
            "irun": self.tmc_irun,
            "sgthrs": self.tmc_sgthrs,
        }

    def move_timeout_s(self, steps: int, speed: int | None = None) -> float:
        speed = speed or self.max_speed_sps
        return abs(steps) / speed * 1.5 + 5.0


def load(path: str | Path = DEFAULT_PARAMS) -> MachineConfig:
    with open(path, encoding="utf-8") as fh:
        p = json.load(fh)
    lay = geometry.layout(p)
    d = p["drive"]
    esp32 = p.get("esp32", {})
    return MachineConfig(
        levels=lay.levels,
        sectors_per_level=lay.sectors_per_level,
        steps_per_rev=d["motor_full_steps"] * d["microsteps"] * d["gear_ratio"],
        max_speed_sps=d["max_speed_sps"],
        accel_sps2=d["accel_sps2"],
        home_speed_sps=d["home_speed_sps"],
        backoff_steps=d["backoff_steps"],
        retries=d["retries"],
        home_offset_steps=d.get("home_offset_steps", 0),
        unlock_max_s=esp32.get("unlock_max_s", 60),
        hb_timeout_s=esp32.get("hb_timeout_s", 10),
        keepalive_s=esp32.get("keepalive_s", 2),
        tmc_irun=d["tmc_irun"],
        tmc_sgthrs=d["tmc_sgthrs"],
    )
