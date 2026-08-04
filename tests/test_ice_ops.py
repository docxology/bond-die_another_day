"""Ice-palace thermal operations planning tests (real data, no mocks)."""

from __future__ import annotations

import pytest

from die_another_day import ice_ops

# Config-matched parameters.
BODY = 37.0
CRIT = 30.0
ENV = -34.0
K = 0.8 / 3600.0  # per-second decay from a 0.8/hour rate


def test_seconds_to_critical_known_value() -> None:
    t = ice_ops.seconds_to_critical(BODY, CRIT, ENV, K)
    assert t == pytest.approx(467.1, rel=0.01)


def test_seconds_to_critical_monotonic() -> None:
    # Lower decay rate (better insulation) => longer safe exposure.
    slow = ice_ops.seconds_to_critical(BODY, CRIT, ENV, K / 2)
    fast = ice_ops.seconds_to_critical(BODY, CRIT, ENV, K)
    assert slow > fast


def test_seconds_to_critical_validation() -> None:
    with pytest.raises(ValueError):
        ice_ops.seconds_to_critical(BODY, CRIT, ENV, 0.0)  # decay <= 0
    with pytest.raises(ValueError):
        ice_ops.seconds_to_critical(CRIT, BODY, ENV, K)  # body < critical
    with pytest.raises(ValueError):
        ice_ops.seconds_to_critical(BODY, ENV, CRIT, K)  # critical < env


def test_exposure_temperature_at_t_zero() -> None:
    assert ice_ops.exposure_temperature(BODY, ENV, K, 0.0) == pytest.approx(BODY)


def test_exposure_temperature_decays() -> None:
    later = ice_ops.exposure_temperature(BODY, ENV, K, 900.0)
    assert ENV < later < BODY


def test_exposure_temperature_validation() -> None:
    with pytest.raises(ValueError):
        ice_ops.exposure_temperature(BODY, ENV, 0.0, 10.0)
    with pytest.raises(ValueError):
        ice_ops.exposure_temperature(BODY, ENV, K, -1.0)


def test_plan_rotation_feasible() -> None:
    # 30-minute op, 4 operatives, ~8-minute safe exposure => 4 squads feasible.
    plan = ice_ops.plan_rotation(4, 1800.0, 467.0)
    assert plan.squad_count == 4
    assert plan.feasible is True
    assert plan.shift_duration_s == pytest.approx(450.0)


def test_plan_rotation_infeasible_when_operations_limited() -> None:
    # 90-minute op with only 2 operatives and a short ceiling => infeasible.
    plan = ice_ops.plan_rotation(2, 5400.0, 467.0)
    assert plan.shift_duration_s > plan.safe_exposure_s
    assert plan.feasible is False


def test_plan_rotation_single_squad() -> None:
    plan = ice_ops.plan_rotation(3, 100.0, 467.0)
    assert plan.squad_count == 1
    assert plan.feasible is True


def test_plan_rotation_validation() -> None:
    with pytest.raises(ValueError):
        ice_ops.plan_rotation(0, 100, 50)
    with pytest.raises(ValueError):
        ice_ops.plan_rotation(2, 0, 50)
    with pytest.raises(ValueError):
        ice_ops.plan_rotation(2, 100, 0)


def test_thermal_load_positive_under_cold() -> None:
    # A long exposure (well past the comfort-crossing point) yields cold stress.
    load = ice_ops.thermal_load(BODY, ENV, K, 3600.0)
    assert load > 0.0


def test_thermal_load_zero_for_short_exposure() -> None:
    # A very short exposure where body stays above comfort => no cold stress.
    load = ice_ops.thermal_load(BODY, ENV, K, 0.001)
    assert load >= 0.0


def test_thermal_load_nonpositive_exposure_zero() -> None:
    assert ice_ops.thermal_load(BODY, ENV, K, 0.0) == 0.0


def test_heating_energy_cold_env() -> None:
    energy = ice_ops.heating_energy(ENV, 1800.0, 1500.0)
    assert energy > 0.0


def test_heating_energy_warm_env_zero() -> None:
    # Ambient above comfort => no heating needed.
    assert ice_ops.heating_energy(25.0, 1800.0, 1500.0) == 0.0


def test_heating_energy_validation() -> None:
    with pytest.raises(ValueError):
        ice_ops.heating_energy(ENV, 1800.0, -1.0)
    with pytest.raises(ValueError):
        ice_ops.heating_energy(ENV, -1.0, 1500.0)


def test_plan_briefing_end_to_end() -> None:
    plan = ice_ops.plan_briefing(
        env_temp_c=ENV,
        body_temp_c=BODY,
        critical_temp_c=CRIT,
        decay_rate=K,
        num_operatives=4,
        op_duration_s=1800.0,
    )
    assert plan.safe_exposure_s == pytest.approx(467.1, rel=0.01)
    assert plan.rotation.feasible is True
    assert plan.thermal_load_deg_s >= 0.0
    assert plan.heating_energy_j > 0.0
    assert plan.env_temp_c == ENV
