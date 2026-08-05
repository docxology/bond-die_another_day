"""Figure generator tests (real data, deterministic, temp output)."""

from __future__ import annotations

from pathlib import Path

from die_another_day import identity_detection as idmod
from die_another_day import orbital_mirror as om
from die_another_day import sequence_identity as si
from die_another_day.figures import (
    render_hypothermia_curve,
    render_identity_drift,
    render_pass_profile,
    render_sequence_mismatches,
)

SMA = 7200e3
MA = 320.0
RAAN = 0.0
JD = 2461300.5


def test_render_pass_profile(tmp_path: Path) -> None:
    plan = om.plan_pass(
        semi_major_axis_m=SMA,
        inclination_deg=65.0,
        raan_deg=RAAN,
        mean_anomaly_deg=MA,
        target_lat_deg=60.0,
        target_lon_deg=15.0,
        jd_start=JD,
        duration_s=1800.0,
        dt_s=60.0,
    )
    out = render_pass_profile(plan, tmp_path / "pass.png")
    assert out.is_file()
    assert out.stat().st_size > 0


def test_render_identity_drift(tmp_path: Path) -> None:
    baseline = idmod.generate_identity_samples(rng_seed=7, n_samples=200, marker_count=6)
    profile = idmod.estimate_profile(baseline)
    replaced = profile.mean + 4.5 * profile.per_marker_std
    genuine_z = idmod.per_marker_z_scores(profile, profile.mean)
    replaced_z = idmod.per_marker_z_scores(profile, replaced)
    verdict = idmod.detect_drift(profile, replaced)
    out = render_identity_drift(genuine_z, replaced_z, verdict, tmp_path / "drift.png", std_threshold=3.0)
    assert out.is_file()
    assert out.stat().st_size > 0


def test_render_hypothermia_curve(tmp_path: Path) -> None:
    out = render_hypothermia_curve(10.0, 75.0, 0.9, 1800.0, tmp_path / "hyp.png")
    assert out.is_file()
    assert out.stat().st_size > 0


def test_render_sequence_mismatches(tmp_path: Path) -> None:
    reference = si.generate_genome(1500, seed=7)
    probe = si.mutate_genome(reference, seed=7, n_substitutions=5)
    out = render_sequence_mismatches(reference, probe, tmp_path / "seq.png")
    assert out.is_file()
    assert out.stat().st_size > 0


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def test_rendered_pngs_are_byte_reproducible(tmp_path: Path) -> None:
    """Two identical renders must produce identical bytes, not just a file.

    Matplotlib stamps a creation `Date` into PNG metadata by default; the
    figure saver suppresses it, and this test is what proves the suppression
    actually holds.
    """
    first = render_hypothermia_curve(10.0, 75.0, 0.9, 1800.0, tmp_path / "a.png")
    second = render_hypothermia_curve(10.0, 75.0, 0.9, 1800.0, tmp_path / "b.png")
    assert first.read_bytes()[:8] == PNG_MAGIC
    assert first.read_bytes() == second.read_bytes()


def test_pass_profile_without_a_feasible_window(tmp_path: Path) -> None:
    """A pass with no feasible instant still renders (no shading, no peak marker)."""
    plan = om.plan_pass(
        semi_major_axis_m=SMA,
        inclination_deg=65.0,
        raan_deg=RAAN,
        mean_anomaly_deg=MA,
        target_lat_deg=60.0,
        target_lon_deg=15.0,
        jd_start=JD,
        duration_s=600.0,
        dt_s=60.0,
        min_elevation_deg=89.9,
    )
    assert plan.n_feasible == 0 and plan.best_index is None
    out = render_pass_profile(plan, tmp_path / "empty.png")
    assert out.read_bytes()[:8] == PNG_MAGIC


def test_sequence_mismatch_map_is_reproducible(tmp_path: Path) -> None:
    reference = si.generate_genome(400, seed=7)
    probe = si.mutate_genome(reference, seed=7, n_substitutions=4, cluster_length=12)
    a = render_sequence_mismatches(reference, probe, tmp_path / "s1.png")
    b = render_sequence_mismatches(reference, probe, tmp_path / "s2.png")
    assert a.read_bytes() == b.read_bytes()
