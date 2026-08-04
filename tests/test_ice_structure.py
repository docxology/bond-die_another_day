"""Ice-structure integrity model tests (real data, no mocks)."""

from __future__ import annotations

import math

import pytest

from die_another_day import ice_structure as istruct


def test_safe_load_tons_known_values() -> None:
    assert istruct.safe_load_tons(30.0) == pytest.approx(900.0 / 256.0)
    assert istruct.safe_load_tons(20.0) == pytest.approx(400.0 / 256.0)


def test_safe_load_tons_validation() -> None:
    with pytest.raises(ValueError):
        istruct.safe_load_tons(0.0)
    with pytest.raises(ValueError):
        istruct.safe_load_tons(30.0, coefficient=0.0)


def test_required_thickness_cm() -> None:
    assert istruct.required_thickness_cm(3.0) == pytest.approx(math.sqrt(768.0))
    assert istruct.required_thickness_cm(0.0) == 0.0


def test_required_thickness_validation() -> None:
    with pytest.raises(ValueError):
        istruct.required_thickness_cm(-1.0)
    with pytest.raises(ValueError):
        istruct.required_thickness_cm(3.0, coefficient=0.0)


def test_load_safety_factor() -> None:
    assert istruct.load_safety_factor(30.0, 3.0) == pytest.approx(3.515625 / 3.0)
    assert istruct.load_safety_factor(30.0, 0.0) == float("inf")


def test_thermal_stress_pa_known_value() -> None:
    stress = istruct.thermal_stress_pa(9e9, 5.1e-5, 15.0, 0.33)
    assert stress == pytest.approx(1.0276e7, rel=1e-3)


def test_thermal_stress_validation() -> None:
    with pytest.raises(ValueError):
        istruct.thermal_stress_pa(0.0, 5.1e-5, 1.0, 0.33)
    with pytest.raises(ValueError):
        istruct.thermal_stress_pa(9e9, 0.0, 1.0, 0.33)
    with pytest.raises(ValueError):
        istruct.thermal_stress_pa(9e9, 5.1e-5, -1.0, 0.33)
    with pytest.raises(ValueError):
        istruct.thermal_stress_pa(9e9, 5.1e-5, 1.0, 1.0)


def test_critical_delta_t_c() -> None:
    crit = istruct.critical_delta_t_c(9e9, 5.1e-5, 1.5e6, 0.33)
    assert crit == pytest.approx(2.19, rel=1e-2)


def test_critical_delta_t_validation() -> None:
    with pytest.raises(ValueError):
        istruct.critical_delta_t_c(9e9, 5.1e-5, 0.0, 0.33)
    with pytest.raises(ValueError):
        istruct.critical_delta_t_c(0.0, 5.1e-5, 1.5e6, 0.33)


def test_ice_structure_plan_crack_risk() -> None:
    plan = istruct.ice_structure_plan(thickness_cm=30.0, load_tons=3.0, delta_t_c=15.0)
    assert plan.capacity_tons == pytest.approx(3.515625)
    assert plan.load_ok is True
    assert plan.crack_risk is True
    assert plan.structurally_safe is False
    assert plan.thermal_stress_mpa == pytest.approx(10.28, rel=1e-2)
    assert plan.recommended_thickness_cm == pytest.approx(30.0)


def test_ice_structure_plan_safe() -> None:
    plan = istruct.ice_structure_plan(thickness_cm=30.0, load_tons=3.0, delta_t_c=1.0)
    assert plan.crack_risk is False
    assert plan.structurally_safe is True


def test_ice_structure_plan_load_failure() -> None:
    plan = istruct.ice_structure_plan(thickness_cm=8.0, load_tons=3.0, delta_t_c=1.0)
    assert plan.load_ok is False
    assert plan.recommended_thickness_cm > 8.0


def test_ice_structure_plan_validation() -> None:
    with pytest.raises(ValueError):
        istruct.ice_structure_plan(thickness_cm=30.0, load_tons=3.0, delta_t_c=1.0, ice_strength_mpa=0.0)
    with pytest.raises(ValueError):
        istruct.ice_structure_plan(thickness_cm=30.0, load_tons=3.0, delta_t_c=1.0, elastic_modulus_gpa=0.0)
