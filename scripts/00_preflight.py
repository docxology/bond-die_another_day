#!/usr/bin/env python3
"""Thin orchestrator: ICARUS mission preflight and identity report.

Usage:
    uv run python scripts/00_preflight.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_api.protocol import protocol_surface  # noqa: E402
from die_another_day import CODENAME, CONCEPT_MODULES, IDENTITY, __version__  # noqa: E402


def main() -> int:
    """Print the package identity and the frozen protocol surface."""
    surface = protocol_surface()
    print(f"Mission identity: {IDENTITY}")
    print(f"Mission codename: {CODENAME}")
    print(f"Package version: {__version__}")
    print(f"Concept modules ({len(CONCEPT_MODULES)}): {', '.join(CONCEPT_MODULES)}")
    print(f"Protocol dataclasses ({len(surface['dataclasses'])}): {', '.join(surface['dataclasses'])}")
    print(f"Provider methods: {', '.join(surface['provider_methods'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
