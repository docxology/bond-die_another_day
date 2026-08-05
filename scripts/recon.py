#!/usr/bin/env python3
"""Thin orchestrator: ICARUS mission recon phase.

Usage:
    uv run python scripts/recon.py ["goal text"]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_api.discovery import load_provider  # noqa: E402
from bond_api.protocol import ReconRequest  # noqa: E402

DEFAULT_GOAL = "survey available assets and constraints"


def main() -> int:
    """Load the provider by slug and print the recon findings for a goal."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goal", nargs="?", default=DEFAULT_GOAL)
    args = parser.parse_args()
    provider = load_provider("die_another_day", search_paths=[SRC])
    report = provider.recon(ReconRequest(goal=args.goal))
    print(f"Recon findings ({len(report.findings)}):")
    for finding in report.findings:
        print(f"  - {finding.label}: {finding.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
