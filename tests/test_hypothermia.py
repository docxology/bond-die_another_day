"""Cold-water immersion / hypothermia model tests (real data, no mocks)."""

from __future__ import annotations

import pytest

from die_another_day import hypothermia as hyp


def test_cooling_rate_water_units() -> None:
    k = hyp.cooling_rate_water(75.0, 1.0)
    assert 1e-5 < k < 1e-3


def test_cooling_rate_heavier_is_slower() -> None:
    small = hyp.cooling_rate_water(50.0, 1.0)
    large = hyp.cooling_rate_water(100.0, 1.0)
    assert large < small


def test_cooling_rate_more_insulation_slower() -> None:
    bare = hyp.cooling_rate_water(75.0, 1.0)
    insulated = hyp.cooling_rate_water(75.0, 0.5)
    assert insulated < bare


def test_cooling_rate_validation() -> None:
    with pytest.raises(ValueError):
        hyp.cooling_rate_water(0.0, 1.0)
    with pytest.raises(ValueError):
        hyp.cooling_rate_water(75.0, 0.0)
    with pytest.raises(ValueError):
        hyp.cooling_rate_water(75.0, 1.5)


def test_immersion_core_temp_at_zero() -> None:
    assert hyp.immersion_core_temp(37.0, 10.0, 2.5e-4, 0.0) == pytest.approx(37.0)


def test_immersion_core_temp_decays() -> None:
    temp = hyp.immersion_core_temp(37.0, 10.0, 2.5e-4, 900.0)
    assert 10.0 < temp < 37.0


def test_immersion_core_temp_validation() -> None:
    with pytest.raises(ValueError):
        hyp.immersion_core_temp(37.0, 40.0, 2.5e-4, 10.0)
    with pytest.raises(ValueError):
        hyp.immersion_core_temp(37.0, 10.0, 0.0, 10.0)
    with pytest.raises(ValueError):
        hyp.immersion_core_temp(37.0, 10.0, 2.5e-4, -1.0)


def test_time_to_core_temp_closed_form() -> None:
    t = hyp.time_to_core_temp(37.0, 28.0, 10.0, 2.5e-4)
    assert t == pytest.approx(1622.0, rel=0.02)


def test_time_to_core_temp_validation() -> None:
    with pytest.raises(ValueError):
        hyp.time_to_core_temp(37.0, 30.0, 10.0, 0.0)
    with pytest.raises(ValueError):
        hyp.time_to_core_temp(37.0, 10.0, 15.0, 2.5e-4)
    with pytest.raises(ValueError):
        hyp.time_to_core_temp(37.0, 40.0, 10.0, 2.5e-4)


def test_hypothermia_stage_thresholds() -> None:
    assert hyp.hypothermia_stage(36.0) == "normal"
    assert hyp.hypothermia_stage(35.0) == "normal"
    assert hyp.hypothermia_stage(33.0) == "mild"
    assert hyp.hypothermia_stage(30.0) == "moderate"
    assert hyp.hypothermia_stage(28.0) == "moderate"
    assert hyp.hypothermia_stage(25.0) == "severe"


def test_immersion_risk_fields() -> None:
    risk = hyp.immersion_risk(37.0, 10.0, 75.0, 0.9, 600.0)
    assert risk.time_to_mild_s < risk.time_to_moderate_s < risk.time_to_severe_s
    assert risk.survival_budget_s == risk.time_to_severe_s
    assert risk.cold_shock_active is False
    early = hyp.immersion_risk(37.0, 10.0, 75.0, 0.9, 60.0)
    assert early.cold_shock_active is True


def test_rescue_reach_time() -> None:
    assert hyp.rescue_reach_time(400.0, 2.0) == pytest.approx(200.0)


def test_rescue_reach_time_validation() -> None:
    with pytest.raises(ValueError):
        hyp.rescue_reach_time(-1.0, 2.0)
    with pytest.raises(ValueError):
        hyp.rescue_reach_time(400.0, 0.0)


def test_plan_cold_water_rescue_feasible() -> None:
    plan = hyp.plan_cold_water_rescue(
        water_c=10.0,
        mass_kg=75.0,
        insulation_factor=0.9,
        distance_m=400.0,
        sweep_speed_m_s=2.0,
    )
    assert plan.feasible is True
    assert plan.reach_time_s == pytest.approx(200.0)
    assert plan.margin_s > 0.0
    assert plan.core_temp_at_reach_c < 37.0


def test_plan_cold_water_rescue_infeasible_when_far() -> None:
    plan = hyp.plan_cold_water_rescue(
        water_c=10.0,
        mass_kg=75.0,
        insulation_factor=0.9,
        distance_m=9000.0,
        sweep_speed_m_s=2.0,
    )
    assert plan.feasible is False
    assert plan.margin_s < 0.0


def test_plan_cold_water_rescue_warm_water_raises() -> None:
    with pytest.raises(ValueError):
        hyp.plan_cold_water_rescue(
            water_c=40.0,
            mass_kg=75.0,
            insulation_factor=0.9,
            distance_m=400.0,
            sweep_speed_m_s=2.0,
        )


def test_fp_degenerate_ratio_guard_is_reachable() -> None:
    """The `ratio >= 1.0` guard in `time_to_core_temp` is a live gate.

    `water_c < target_c < initial_c` holds, yet the float division rounds to
    exactly 1.0 for an extreme water temperature — without the second guard the
    function would silently return a zero cooling time.
    """
    with pytest.raises(ValueError, match="strictly between"):
        hyp.time_to_core_temp(1.0, 0.0, -1e16, 1e-3)


def test_stage_boundaries_are_exact() -> None:
    """Staging is closed on the lower bound of each band, so 35/32/28 map down."""
    assert hyp.hypothermia_stage(hyp.MILD_THRESHOLD_C) == "normal"
    assert hyp.hypothermia_stage(hyp.MILD_THRESHOLD_C - 1e-9) == "mild"
    assert hyp.hypothermia_stage(hyp.MODERATE_THRESHOLD_C) == "mild"
    assert hyp.hypothermia_stage(hyp.MODERATE_THRESHOLD_C - 1e-9) == "moderate"
    assert hyp.hypothermia_stage(hyp.SEVERE_THRESHOLD_C) == "moderate"
    assert hyp.hypothermia_stage(hyp.SEVERE_THRESHOLD_C - 1e-9) == "severe"


def test_cooling_rate_scales_inversely_with_mass() -> None:
    """Heat capacity grows with mass, so a heavier operative cools more slowly."""
    light = hyp.cooling_rate_water(50.0, 1.0)
    reference = hyp.cooling_rate_water(hyp.REF_MASS_KG, 1.0)
    heavy = hyp.cooling_rate_water(120.0, 1.0)
    assert light > reference > heavy
    assert reference == pytest.approx(hyp.K_REF_PER_S)


def test_reference_rate_matches_its_documented_definition() -> None:
    """``K_REF_PER_S`` is defined by a 20-minute identity; pin it to that.

    The constant's docstring states exactly one calibration: a 75 kg adult in
    10 C water reaches a 30 C core in 20 minutes. That sentence is now a test.
    Changing the constant without changing the sentence (or vice versa) fails.
    """
    k = hyp.cooling_rate_water(hyp.REF_MASS_KG, 1.0)
    assert hyp.time_to_core_temp(37.0, 30.0, 10.0, k) == pytest.approx(1200.0, abs=1.0)


def test_reference_rate_is_far_faster_than_measured_immersion_cooling() -> None:
    """The scenario constant is an order of magnitude off the literature.

    This is asserted, not hidden: manuscript §07 states the model is not
    physiologically calibrated, and this test is what keeps that statement
    true. Measured core cooling in ~10 C water is a few degrees per hour; if
    someone ever recalibrates ``K_REF_PER_S`` down to that range, this test
    goes red and the §07 limitation must be rewritten rather than left stale.
    """
    k = hyp.cooling_rate_water(hyp.REF_MASS_KG, 1.0)
    initial_rate_c_per_hour = k * (37.0 - 10.0) * 3600.0
    assert initial_rate_c_per_hour == pytest.approx(24.3, abs=0.1)
    assert initial_rate_c_per_hour > 10.0
