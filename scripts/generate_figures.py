#!/usr/bin/env python3
"""Thin orchestrator: render the ICARUS mission concept figures.

Usage:
    uv run python scripts/generate_figures.py

Runs the deterministic mission once, then writes both concept figures
(elevation pass profile and identity trait-drift) into ``output/figures/``.
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
from die_another_day.figures import render_identity_drift, render_pass_profile  # noqa: E402
from die_another_day.manuscript_variables import load_manuscript_config  # noqa: E402


def main() -> int:
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
    baseline = idmod.generate_identity_samples(
        rng_seed=int(idc["seed"]),
        n_samples=200,
        marker_count=marker_count,
    )
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

    print(f"Wrote {pass_path}")
    print(f"Wrote {drift_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
