"""Pytest configuration for die_another_day (ICARUS).

Adds ``src/`` to ``sys.path`` (discovery contract) and pins matplotlib's Agg
backend so figure tests never open a display.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parents[1]
for _relative in ("src",):
    _path = str(ROOT / _relative)
    if _path not in sys.path:
        sys.path.insert(0, _path)
