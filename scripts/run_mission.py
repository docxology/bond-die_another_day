#!/usr/bin/env python3
"""Thin orchestrator: run the full ICARUS mission lifecycle.

Usage:
    uv run python scripts/run_mission.py

Discovers the film by slug, executes the five-stage flow (brief / recon /
plan / execute / debrief), and prints the deterministic debrief plus the
outcome as round-trip JSON.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for _path in (SRC,):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from bond_api.discovery import load_provider  # noqa: E402
from bond_api.protocol import ReconRequest  # noqa: E402
from bond_api.serialization import to_json  # noqa: E402


def main() -> int:
    """Run the full five-stage ICARUS mission and print the outcome JSON."""
    provider = load_provider("die_another_day", search_paths=[SRC])
    brief = provider.brief()
    report = provider.recon(ReconRequest(goal="survey available assets and constraints"))
    plan = provider.plan(brief)
    outcome = provider.execute(plan)
    debrief = provider.debrief(outcome)

    print(f"Film: {brief.film} ({brief.codename})")
    print(f"Objectives: {', '.join(brief.objectives)}")
    print(f"Recon findings: {len(report.findings)}")
    print(f"Plan steps: {len(plan.steps)}")
    print(f"Outcome success: {outcome.success}")
    print(f"Lessons: {len(debrief.lessons)}")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    print("Outcome JSON:")
    print(to_json(outcome))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
