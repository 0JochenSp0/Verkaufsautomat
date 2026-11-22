"""Make src/, firmware/esp32 and cad/lib importable when tests run without PYTHONPATH."""

import sys
from pathlib import Path

_SW = Path(__file__).resolve().parents[1]
for p in (_SW / "src", _SW / "firmware" / "esp32", _SW.parent / "cad" / "lib"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
