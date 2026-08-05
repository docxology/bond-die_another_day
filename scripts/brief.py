#!/usr/bin/env python3
"""Thin orchestrator: ICARUS mission brief phase.

Usage:
    uv run python scripts/brief.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_api.discovery import load_provider  # noqa: E402


def main() -> int:
    """Load the provider by slug and print the mission brief."""
    provider = load_provider("die_another_day", search_paths=[SRC])
    brief = provider.brief()
    print(f"Film: {brief.film} ({brief.codename})")
    print("Objectives:")
    for obj in brief.objectives:
        print(f"  - {obj}")
    print("Assets:")
    for asset in brief.assets:
        print(f"  - {asset.kind}: {asset.name}")
    print("Constraints:")
    for constraint in brief.constraints:
        print(f"  - {constraint.kind}: {constraint.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
