"""Figure generator tests (real data, deterministic, temp output).

Every renderer here is checked for *input sensitivity*, not just for producing
a file. ``out.is_file()`` and ``st_size > 0`` are true of any PNG whatsoever,
including one that silently ignored its arguments — which is exactly how a
figure of the wrong experiment survived review. Because the saver is
byte-reproducible (see ``test_rendered_pngs_are_byte_reproducible``), "render
twice with different inputs and require different bytes" is a real oracle: a
renderer that drops an argument makes the two renders identical and the test
goes red.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from die_another_day import identity_detection as idmod
from die_another_day import manuscript_variables as mv
from die_another_day import mission_results as mr
from die_another_day import orbital_mirror as om
from die_another_day import hypothermia as hyp
from die_another_day import sequence_identity as si
from die_another_day.figures import (
    hypothermia_window_s,
    render_hypothermia_curve,
    render_identity_drift,
    render_pass_profile,
    render_sequence_mismatches,
)

SMA = 7200e3
MA = 320.0
RAAN = 0.0
JD = 2461300.5

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _plan(**overrides: float) -> om.PassPlan:
    kwargs: dict[str, float] = {
        "semi_major_axis_m": SMA,
        "inclination_deg": 65.0,
        "raan_deg": RAAN,
        "mean_anomaly_deg": MA,
        "target_lat_deg": 60.0,
        "target_lon_deg": 15.0,
        "jd_start": JD,
        "duration_s": 1800.0,
        "dt_s": 60.0,
    }
    kwargs.update(overrides)
    return om.plan_pass(**kwargs)


def test_render_pass_profile_tracks_its_plan(tmp_path: Path) -> None:
    """A different pass geometry must produce a different picture."""
    first = render_pass_profile(_plan(), tmp_path / "a.png")
    second = render_pass_profile(_plan(inclination_deg=40.0), tmp_path / "b.png")
    assert first.read_bytes()[:8] == PNG_MAGIC
    assert first.read_bytes() != second.read_bytes()


def test_render_identity_drift_plots_the_probes_it_is_given(tmp_path: Path) -> None:
    """Both z-vectors must reach the canvas.

    The genuine and replaced series are rendered as separate bar groups; moving
    either one alone must change the image. A renderer that plotted only the
    replaced probe (or, as the published figure once did, a genuine probe of
    ``profile.mean`` whose bars are identically zero) fails the first case.
    """
    results = mr.run_all_concepts(mv.load_manuscript_config())
    genuine = results.identity_genuine_z
    replaced = results.identity_replaced_z
    verdict = results.identity_replaced

    base = render_identity_drift(genuine, replaced, verdict, tmp_path / "base.png", std_threshold=3.0)
    moved_genuine = tuple(v + 1.0 for v in genuine)
    moved_replaced = tuple(v + 1.0 for v in replaced)
    only_genuine = render_identity_drift(moved_genuine, replaced, verdict, tmp_path / "g.png", std_threshold=3.0)
    only_replaced = render_identity_drift(genuine, moved_replaced, verdict, tmp_path / "r.png", std_threshold=3.0)
    other_threshold = render_identity_drift(genuine, replaced, verdict, tmp_path / "t.png", std_threshold=2.0)

    assert base.read_bytes()[:8] == PNG_MAGIC
    assert base.read_bytes() != only_genuine.read_bytes()
    assert base.read_bytes() != only_replaced.read_bytes()
    assert base.read_bytes() != other_threshold.read_bytes()


def test_identity_drift_genuine_series_is_not_degenerate() -> None:
    """The runner's genuine probe has visible, non-zero drift on every marker.

    ``profile.mean`` would give an all-zero vector, drawing an invisible bar
    group and depicting a negative control that cannot fail.
    """
    results = mr.run_all_concepts(mv.load_manuscript_config())
    assert all(abs(v) > 1e-6 for v in results.identity_genuine_z)


def test_render_hypothermia_curve_tracks_its_inputs(tmp_path: Path) -> None:
    """Colder water and a lighter operative must each change the curve."""
    base = render_hypothermia_curve(10.0, 75.0, 0.9, 1800.0, tmp_path / "a.png")
    colder = render_hypothermia_curve(4.0, 75.0, 0.9, 1800.0, tmp_path / "b.png")
    lighter = render_hypothermia_curve(10.0, 55.0, 0.9, 1800.0, tmp_path / "c.png")
    assert base.read_bytes()[:8] == PNG_MAGIC
    assert base.read_bytes() != colder.read_bytes()
    assert base.read_bytes() != lighter.read_bytes()


def test_render_sequence_mismatches_tracks_its_probe(tmp_path: Path) -> None:
    """The mismatch map must depend on the probe, including its edit block."""
    reference = si.generate_genome(1500, seed=7)
    scattered = si.mutate_genome(reference, seed=7, n_substitutions=5)
    blocked = si.mutate_genome(reference, seed=7, n_substitutions=5, cluster_length=12)
    a = render_sequence_mismatches(reference, scattered, tmp_path / "a.png")
    b = render_sequence_mismatches(reference, blocked, tmp_path / "b.png")
    assert a.read_bytes()[:8] == PNG_MAGIC
    assert a.read_bytes() != b.read_bytes()


def test_identity_drift_accepts_plain_sequences_and_arrays(tmp_path: Path) -> None:
    """Tuples (as carried on ``ConceptResults``) and arrays must render alike."""
    baseline = idmod.generate_identity_samples(rng_seed=7, n_samples=200, marker_count=6)
    profile = idmod.estimate_profile(baseline)
    replaced = profile.mean + 4.5 * profile.per_marker_std
    replaced_z = idmod.per_marker_z_scores(profile, replaced)
    genuine_z = idmod.per_marker_z_scores(profile, profile.mean + 0.5 * profile.per_marker_std)
    verdict = idmod.detect_drift(profile, replaced)
    as_arrays = render_identity_drift(genuine_z, replaced_z, verdict, tmp_path / "arr.png", std_threshold=3.0)
    as_tuples = render_identity_drift(
        tuple(float(v) for v in genuine_z),
        tuple(float(v) for v in replaced_z),
        verdict,
        tmp_path / "tup.png",
        std_threshold=3.0,
    )
    assert as_arrays.read_bytes() == as_tuples.read_bytes()
    assert not np.allclose(np.asarray(genuine_z), 0.0)


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
    plan = _plan(duration_s=600.0, min_elevation_deg=89.9)
    assert plan.n_feasible == 0 and plan.best_index is None
    out = render_pass_profile(plan, tmp_path / "empty.png")
    assert out.read_bytes()[:8] == PNG_MAGIC


def test_sequence_mismatch_map_is_reproducible(tmp_path: Path) -> None:
    reference = si.generate_genome(400, seed=7)
    probe = si.mutate_genome(reference, seed=7, n_substitutions=4, cluster_length=12)
    a = render_sequence_mismatches(reference, probe, tmp_path / "s1.png")
    b = render_sequence_mismatches(reference, probe, tmp_path / "s2.png")
    assert a.read_bytes() == b.read_bytes()


def test_hypothermia_figure_default_window_crosses_the_severe_stage(tmp_path: Path) -> None:
    """The figure's default window extends past the severe (28 C) crossing.

    The published curve used to stop ~2 s short of the severe stage it labels,
    on a hardcoded 1800 s window (TODO C1). The default window is derived from
    the physics — time-to-severe times a margin — so the final plotted
    temperature sits at or below the severe threshold, and the renderer used by
    the production script produces that window.
    """
    water_c, mass_kg, insulation = 10.0, 75.0, 0.9
    window = hypothermia_window_s(water_c, mass_kg, insulation)
    k = hyp.cooling_rate_water(mass_kg, insulation)
    t_severe = hyp.time_to_core_temp(37.0, hyp.SEVERE_THRESHOLD_C, water_c, k)
    last_temp = hyp.immersion_core_temp(37.0, water_c, k, window)
    assert window > t_severe
    assert last_temp <= hyp.SEVERE_THRESHOLD_C

    out = render_hypothermia_curve(water_c, mass_kg, insulation, window, tmp_path / "h.png")
    assert out.read_bytes()[:8] == PNG_MAGIC
    with pytest.raises(ValueError):
        hypothermia_window_s(water_c, mass_kg, insulation, margin=1.0)
