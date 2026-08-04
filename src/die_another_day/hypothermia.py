"""Cold-water immersion and hypothermia risk planning.

ICARUS / *Die Another Day* (2002) concept extension of
:mod:`die_another_day.ice_ops`. Where ice_ops plans around *air* exposure, this
module models the far more aggressive case: an operative immersed in near-freezing
water. Water conducts heat roughly twenty-five times faster than air, so core
temperature follows Newton's cooling law with a much larger decay rate, and the
physiological timeline is measured in minutes:

* :func:`cooling_rate_water` scales a calibrated reference decay rate by body
  mass (heat capacity grows with mass, so larger operatives cool more slowly)
  and by an insulation factor.
* :func:`immersion_core_temp` / :func:`time_to_core_temp` solve Newton's law
  for predicted core temperature and time-to-threshold.
* :func:`hypothermia_stage` maps core temperature to the standard clinical
  stages (mild / moderate / severe).
* :func:`plan_cold_water_rescue` computes whether a rescue party sweeping the
  water can reach the operative before the core reaches the severe stage, and
  reports the margin.

All functions are pure and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "COLD_SHOCK_WINDOW_S",
    "ColdWaterRescuePlan",
    "ImmersionRisk",
    "K_REF_PER_S",
    "REF_MASS_KG",
    "cooling_rate_water",
    "hypothermia_stage",
    "immersion_core_temp",
    "immersion_risk",
    "plan_cold_water_rescue",
    "rescue_reach_time",
    "time_to_core_temp",
]

#: Reference adult mass (kg) for the cooling-rate scaling.
REF_MASS_KG = 75.0

#: Calibrated cooling rate (1/s): a 75 kg adult in 10 C water reaches a 30 C
#: core in ~20 minutes, matching the cold-water survival literature.
K_REF_PER_S = 2.5e-4

#: Cold-shock window (s): the first three minutes carry gasp/aspiration risk.
COLD_SHOCK_WINDOW_S = 180.0

#: Core-temperature thresholds (C) for clinical hypothermia staging.
MILD_THRESHOLD_C = 35.0
MODERATE_THRESHOLD_C = 32.0
SEVERE_THRESHOLD_C = 28.0


@dataclass(frozen=True)
class ImmersionRisk:
    """Risk snapshot after a given immersion duration."""

    core_temp_after_c: float
    stage: str
    time_to_mild_s: float
    time_to_moderate_s: float
    time_to_severe_s: float
    cold_shock_active: bool
    survival_budget_s: float
    duration_s: float


@dataclass(frozen=True)
class ColdWaterRescuePlan:
    """Rescue feasibility against the hypothermia timeline."""

    feasible: bool
    reach_time_s: float
    time_to_severe_s: float
    margin_s: float
    core_temp_at_reach_c: float
    water_temp_c: float
    mass_kg: float


def _validate_mass_insulation(mass_kg: float, insulation_factor: float) -> None:
    if mass_kg <= 0.0:
        raise ValueError("mass_kg must be positive")
    if not 0.0 < insulation_factor <= 1.0:
        raise ValueError("insulation_factor must lie in (0, 1]")


def cooling_rate_water(mass_kg: float, insulation_factor: float) -> float:
    """Effective cooling decay rate (1/s) for an immersed operative."""
    _validate_mass_insulation(mass_kg, insulation_factor)
    rate: float = float(K_REF_PER_S * (mass_kg / REF_MASS_KG) ** (-1.0 / 3.0) * insulation_factor)
    return rate


def immersion_core_temp(initial_c: float, water_c: float, k: float, duration_s: float) -> float:
    """Predicted core temperature after ``duration_s`` of immersion."""
    if water_c >= initial_c:
        raise ValueError("water_c must be colder than initial_c")
    if k <= 0.0:
        raise ValueError("k must be positive")
    if duration_s < 0.0:
        raise ValueError("duration_s must be non-negative")
    temp: float = float(water_c + (initial_c - water_c) * np.exp(-k * duration_s))
    return temp


def time_to_core_temp(initial_c: float, target_c: float, water_c: float, k: float) -> float:
    """Seconds to cool from ``initial_c`` to ``target_c`` (closed form)."""
    if not water_c < target_c < initial_c:
        raise ValueError("expected water_c < target_c < initial_c")
    if k <= 0.0:
        raise ValueError("k must be positive")
    ratio = (target_c - water_c) / (initial_c - water_c)
    if ratio <= 0.0 or ratio >= 1.0:
        raise ValueError("target_c must lie strictly between water_c and initial_c")
    time: float = float(-np.log(ratio) / k)
    return time


def hypothermia_stage(core_temp_c: float) -> str:
    """Clinical hypothermia stage for a core temperature in Celsius.

    Hypothermia begins below 35 C; staging follows the standard mild (32-35),
    moderate (28-32), severe (<28) bands.
    """
    if core_temp_c >= MILD_THRESHOLD_C:
        return "normal"
    if core_temp_c >= MODERATE_THRESHOLD_C:
        return "mild"
    if core_temp_c >= SEVERE_THRESHOLD_C:
        return "moderate"
    return "severe"


def immersion_risk(
    initial_c: float,
    water_c: float,
    mass_kg: float,
    insulation_factor: float,
    duration_s: float,
) -> ImmersionRisk:
    """Assess the hypothermia timeline at a given immersion duration."""
    k = cooling_rate_water(mass_kg, insulation_factor)
    core = immersion_core_temp(initial_c, water_c, k, duration_s)
    t_mild = time_to_core_temp(initial_c, MILD_THRESHOLD_C, water_c, k)
    t_moderate = time_to_core_temp(initial_c, MODERATE_THRESHOLD_C, water_c, k)
    t_severe = time_to_core_temp(initial_c, SEVERE_THRESHOLD_C, water_c, k)
    return ImmersionRisk(
        core_temp_after_c=core,
        stage=hypothermia_stage(core),
        time_to_mild_s=t_mild,
        time_to_moderate_s=t_moderate,
        time_to_severe_s=t_severe,
        cold_shock_active=duration_s < COLD_SHOCK_WINDOW_S,
        survival_budget_s=t_severe,
        duration_s=duration_s,
    )


def rescue_reach_time(distance_m: float, sweep_speed_m_s: float) -> float:
    """Time for a rescue party to cover ``distance_m`` at ``sweep_speed_m_s``."""
    if distance_m < 0.0:
        raise ValueError("distance_m must be non-negative")
    if sweep_speed_m_s <= 0.0:
        raise ValueError("sweep_speed_m_s must be positive")
    return float(distance_m / sweep_speed_m_s)


def plan_cold_water_rescue(
    *,
    initial_c: float = 37.0,
    water_c: float,
    mass_kg: float,
    insulation_factor: float,
    distance_m: float,
    sweep_speed_m_s: float,
) -> ColdWaterRescuePlan:
    """Plan a rescue against the immersion hypothermia timeline.

    Feasible when the rescue party can reach the operative before the core
    reaches the severe stage (28 C).
    """
    k = cooling_rate_water(mass_kg, insulation_factor)
    t_severe = time_to_core_temp(initial_c, SEVERE_THRESHOLD_C, water_c, k)
    reach = rescue_reach_time(distance_m, sweep_speed_m_s)
    core_at_reach = immersion_core_temp(initial_c, water_c, k, reach)
    return ColdWaterRescuePlan(
        feasible=reach <= t_severe,
        reach_time_s=reach,
        time_to_severe_s=t_severe,
        margin_s=t_severe - reach,
        core_temp_at_reach_c=core_at_reach,
        water_temp_c=water_c,
        mass_kg=mass_kg,
    )
