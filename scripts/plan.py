#!/usr/bin/env python3
"""Thin orchestrator: ICARUS mission plan phase.

Usage:
    uv run python scripts/plan.py
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
    """Load the provider by slug and print the planned mission steps."""
    provider = load_provider("die_another_day", search_paths=[SRC])
    brief = provider.brief()
    plan = provider.plan(brief)
    print(f"Plan steps ({len(plan.steps)}):")
    for step in plan.steps:
        print(f"  - {step.name}: {step.action} {step.params}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
