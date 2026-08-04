#!/usr/bin/env python3
"""Thin orchestrator: ICARUS mission debrief phase.

Usage:
    uv run python scripts/debrief.py
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
    provider = load_provider("die_another_day", search_paths=[SRC])
    brief = provider.brief()
    plan = provider.plan(brief)
    outcome = provider.execute(plan)
    debrief = provider.debrief(outcome)
    print(f"Outcome success: {debrief.outcome.success}")
    print(f"Lessons ({len(debrief.lessons)}):")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
