#!/usr/bin/env python3
"""Thin orchestrator: ICARUS mission execute phase.

Usage:
    uv run python scripts/execute.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_api.discovery import load_provider  # noqa: E402
from bond_api.serialization import to_json  # noqa: E402


def main() -> int:
    """Execute the mission plan and print the outcome as round-trip JSON."""
    provider = load_provider("die_another_day", search_paths=[SRC])
    brief = provider.brief()
    plan = provider.plan(brief)
    outcome = provider.execute(plan)
    print(f"Outcome success: {outcome.success}")
    print(to_json(outcome))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
