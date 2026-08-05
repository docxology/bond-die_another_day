#!/usr/bin/env python3
"""Thin orchestrator: render the ICARUS mission concept figures.

Usage:
    uv run python scripts/generate_figures.py

Runs the mission's deterministic models once, then writes the concept figures
(elevation pass, identity drift, hypothermia curve, sequence mismatch map) into
``output/figures/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from die_another_day import identity_detection as idmod  # noqa: E402
from die_another_day import orbital_mirror as om  # noqa: E402
from die_another_day import sequence_identity as si  # noqa: E402
from die_another_day.figures import (  # noqa: E402
    render_hypothermia_curve,
    render_identity_drift,
    render_pass_profile,
    render_sequence_mismatches,
)
from die_another_day.manuscript_variables import load_manuscript_config  # noqa: E402


def main() -> int:
    """Render the four ICARUS concept figures into ``output/figures/``."""
    config = load_manuscript_config()
    concepts = config["concepts"]
    out_dir = ROOT / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Orbital pass profile
    orb = concepts["orbital_mirror"]
    pass_plan = om.plan_pass(
        semi_major_axis_m=float(orb["semi_major_axis_km"]) * 1000.0,
        inclination_deg=float(orb["inclination_deg"]),
        raan_deg=float(orb["raan_deg"]),
        mean_anomaly_deg=float(orb["mean_anomaly_deg"]),
        target_lat_deg=float(orb["target_lat_deg"]),
        target_lon_deg=float(orb["target_lon_deg"]),
        jd_start=float(orb["jd_start"]),
        duration_s=float(orb["duration_s"]),
        dt_s=float(orb["dt_s"]),
        mirror_area_m2=float(orb["mirror_area_m2"]),
        reflectivity=float(orb["reflectivity"]),
        beam_half_angle_deg=float(orb["beam_half_angle_deg"]),
        min_elevation_deg=float(orb["min_elevation_deg"]),
    )
    pass_path = render_pass_profile(pass_plan, out_dir / "icarus_pass_profile.png")

    # Identity trait drift
    idc = concepts["identity"]
    marker_count = int(idc["num_biomarkers"])
    baseline = idmod.generate_identity_samples(rng_seed=int(idc["seed"]), n_samples=200, marker_count=marker_count)
    profile = idmod.estimate_profile(baseline)
    replaced_z = idmod.per_marker_z_scores(
        profile, profile.mean + 1.5 * float(idc["std_threshold"]) * profile.per_marker_std
    )
    genuine_z = idmod.per_marker_z_scores(profile, profile.mean)
    verdict = idmod.detect_drift(
        profile,
        profile.mean + 1.5 * float(idc["std_threshold"]) * profile.per_marker_std,
        alpha=float(idc["alpha"]),
        std_threshold=float(idc["std_threshold"]),
        min_markers=int(idc["min_markers"]),
    )
    drift_path = render_identity_drift(
        genuine_z,
        replaced_z,
        verdict,
        out_dir / "icarus_identity_drift.png",
        std_threshold=float(idc["std_threshold"]),
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

    # DNA sequence mismatch map (replaced probe)
    seq = concepts["sequence_identity"]
    reference = si.generate_genome(int(seq["genome_length"]), seed=int(seq["seed"]))
    replaced_seq = si.mutate_genome(
        reference,
        seed=int(seq["seed"]),
        n_substitutions=int(seq["scattered_errors"]),
        cluster_length=int(seq["cluster_min"]),
    )
    seq_path = render_sequence_mismatches(reference, replaced_seq, out_dir / "icarus_sequence_mismatch.png")

    print(f"Wrote {pass_path}")
    print(f"Wrote {drift_path}")
    print(f"Wrote {hyp_path}")
    print(f"Wrote {seq_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
