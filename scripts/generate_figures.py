#!/usr/bin/env python3
"""Thin orchestrator: render the ICARUS mission concept figures.

Usage:
    uv run python scripts/generate_figures.py

Runs the mission's deterministic models once through
``mission_results.run_all_concepts`` — the same call the ``MissionProvider``
and the manuscript tokens use — then writes the concept figures (elevation
pass, identity drift, hypothermia curve, sequence mismatch map) into
``output/figures/``.

Every figure is drawn from that one record. This script must never build its
own probes: doing so previously published an identity-drift figure of a
*different* experiment than the results table it illustrates (a genuine probe
of ``profile.mean``, whose bars are identically zero). ``test_scripts_smoke``
pins the rendered PNGs to a render of the runner's own arrays.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from die_another_day.figures import (  # noqa: E402
    render_hypothermia_curve,
    render_identity_drift,
    render_pass_profile,
    render_sequence_mismatches,
)
from die_another_day.manuscript_variables import load_manuscript_config  # noqa: E402
from die_another_day.mission_results import run_all_concepts  # noqa: E402


def main() -> int:
    """Render the four ICARUS concept figures into ``output/figures/``."""
    config = load_manuscript_config()
    concepts = config["concepts"]
    results = run_all_concepts(config)
    out_dir = ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Orbital pass profile — the same PassPlan the results table reports.
    pass_path = render_pass_profile(results.mirror, out_dir / "icarus_pass_profile.png")

    # Identity trait drift — the same two probes the verdicts were scored on.
    drift_path = render_identity_drift(
        results.identity_genuine_z,
        results.identity_replaced_z,
        results.identity_replaced,
        out_dir / "icarus_identity_drift.png",
        std_threshold=float(concepts["identity"]["std_threshold"]),
    )

    # Cold-water hypothermia curve
    hypc = concepts["hypothermia"]
    hyp_path = render_hypothermia_curve(
        float(hypc["water_temp_c"]),
        float(hypc["body_mass_kg"]),
        float(hypc["insulation_factor"]),
        1800.0,
        out_dir / "icarus_hypothermia_curve.png",
    )

    # DNA sequence mismatch map — the same replaced read the table reports.
    seq_path = render_sequence_mismatches(
        results.sequence_reference,
        results.sequence_replaced_read,
        out_dir / "icarus_sequence_mismatch.png",
    )

    print(f"Wrote {pass_path}")
    print(f"Wrote {drift_path}")
    print(f"Wrote {hyp_path}")
    print(f"Wrote {seq_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
