"""Ice-palace cold-environment operations planning (thermal / Newton cooling).

ICARUS / *Die Another Day* (2002) concept. Operations inside an ice palace are
bounded by human cold tolerance: an operative's core temperature decays toward
the ambient environmental temperature according to Newton's law of cooling,
:math:`dT/dt = -k (T - T_\\text{env})`, so the time to reach a critical core
temperature is a closed-form exponential. This module turns that physics into
an operations plan:

* :func:`seconds_to_critical` solves the cooling law for how long an operative
  can remain exposed before their core temperature reaches ``critical_temp``.
* :func:`plan_rotation` divides a total op duration into rotating squads so no
  squad exceeds its safe exposure, and reports the resulting roster.
* :func:`thermal_load` integrates the operative's core-temperature depression
  below normothermia (degree-seconds) as a physiological cold-strain metric.
  The reference is normothermia (37 C), **not** room comfort: a survivable
  plan never lets the core fall below a 20 C room-comfort line, so a
  comfort-referenced integral would report exactly zero for every valid
  operation and could never discriminate one plan from another.
* :func:`heating_energy` sizes the power needed to hold an indoor *space* at a
  room-comfort temperature against the cold ambient — that one genuinely is a
  comfort-referenced quantity.

All functions are pure and deterministic — given the same physical parameters
they return identical plans.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

import numpy as np

__all__ = [
    "DEFAULT_COMFORT_C",
    "IceOpsPlan",
    "NORMOTHERMIA_C",
    "RotationPlan",
    "exposure_temperature",
    "heating_energy",
    "plan_rotation",
    "plan_briefing",
    "seconds_to_critical",
    "thermal_load",
]

#: Room-comfort temperature (Celsius) used to size *space* heating.
DEFAULT_COMFORT_C = 20.0

#: Normothermic human core temperature (Celsius) — the physiological reference
#: for the cold-strain integral.
NORMOTHERMIA_C = 37.0


@dataclass(frozen=True)
class RotationPlan:
    """Roster for a cold-environment operation under an exposure ceiling.

    ``squad_count`` squads rotate so that no squad stays exposed longer than
    ``safe_exposure_s``; each active shift lasts ``shift_duration_s`` and is
    followed by ``rest_duration_s``. ``feasible`` is True when the total op
    can be covered within the safe-exposure ceiling.
    """

    squad_count: int
    shift_duration_s: float
    rest_duration_s: float
    safe_exposure_s: float
    total_duration_s: float
    feasible: bool


@dataclass(frozen=True)
class IceOpsPlan:
    """Complete cold-environment briefing for an ice-palace operation.

    ``thermal_load_deg_s`` is the per-shift core depression below
    ``reference_temp_c`` (normothermia); ``heating_energy_j`` is the space
    heating needed to hold the room at ``comfort_temp_c``.
    """

    safe_exposure_s: float
    rotation: RotationPlan
    thermal_load_deg_s: float
    heating_energy_j: float
    env_temp_c: float
    body_temp_c: float
    critical_temp_c: float
    comfort_temp_c: float
    reference_temp_c: float


def _validate_temps(body_temp: float, critical_temp: float, env_temp: float) -> None:
    if not (env_temp < critical_temp < body_temp):
        raise ValueError("expected env_temp < critical_temp < body_temp (in Celsius)")


def seconds_to_critical(
    body_temp: float,
    critical_temp: float,
    env_temp: float,
    decay_rate: float,
) -> float:
    """Seconds for a body to cool from ``body_temp`` to ``critical_temp``.

    Newton's law gives ``T(t) = env + (body - env) exp(-k t)``; solving for
    ``t`` at ``T = critical_temp`` yields the closed form.
    """
    if decay_rate <= 0.0:
        raise ValueError("decay_rate must be positive")
    _validate_temps(body_temp, critical_temp, env_temp)
    ratio = (critical_temp - env_temp) / (body_temp - env_temp)
    if ratio <= 0.0 or ratio >= 1.0:
        raise ValueError("critical_temp must lie strictly between env and body")
    return float(-np.log(ratio) / decay_rate)


def exposure_temperature(
    body_temp: float,
    env_temp: float,
    decay_rate: float,
    elapsed_s: float,
) -> float:
    """Predicted core temperature after ``elapsed_s`` of continuous exposure."""
    if decay_rate <= 0.0:
        raise ValueError("decay_rate must be positive")
    if elapsed_s < 0.0:
        raise ValueError("elapsed_s must be non-negative")
    return float(env_temp + (body_temp - env_temp) * np.exp(-decay_rate * elapsed_s))


def plan_rotation(
    num_operatives: int,
    op_duration_s: float,
    safe_exposure_s: float,
) -> RotationPlan:
    """Plan a rotating roster under a per-squad cold-exposure ceiling.

    With ``num_operatives`` available, the op is split into enough squads so
    that no squad's continuous exposure exceeds ``safe_exposure_s``; squads
    alternate active/rest so the full ``op_duration_s`` is covered.
    """
    if num_operatives < 1:
        raise ValueError("num_operatives must be >= 1")
    if op_duration_s <= 0.0:
        raise ValueError("op_duration_s must be positive")
    if safe_exposure_s <= 0.0:
        raise ValueError("safe_exposure_s must be positive")

    squad_count = int(ceil(op_duration_s / safe_exposure_s))
    # Cannot have more squads than operatives (each squad needs one operative).
    squad_count = min(squad_count, num_operatives)
    shift_duration_s = op_duration_s / squad_count
    rest_duration_s = max(0.0, (squad_count - 1) * shift_duration_s)
    feasible = shift_duration_s <= safe_exposure_s
    return RotationPlan(
        squad_count=squad_count,
        shift_duration_s=shift_duration_s,
        rest_duration_s=rest_duration_s,
        safe_exposure_s=safe_exposure_s,
        total_duration_s=op_duration_s,
        feasible=feasible,
    )


def thermal_load(
    body_temp: float,
    env_temp: float,
    decay_rate: float,
    exposure_s: float,
    reference_temp: float = NORMOTHERMIA_C,
) -> float:
    """Integrated cold strain: degree-seconds of core depression below normothermia.

    Returns :math:`\\int_0^{E} \\max(0,\\, T_\\text{ref} - T(t))\\, dt` in
    degree-seconds, evaluated on a fine deterministic grid. With the default
    reference (``body_temp`` starting at normothermia) this has the exact
    closed form :math:`(T_0-T_e)\\left[E - (1-e^{-kE})/k\\right]`, which
    ``tests/test_ice_ops.py`` checks the quadrature against.

    Args:
        body_temp: Core temperature at exposure start (C).
        env_temp: Ambient temperature (C).
        decay_rate: Newton cooling constant (1/s).
        exposure_s: Exposure duration (s); non-positive returns ``0.0``.
        reference_temp: Reference the depression is measured from (C).
    """
    if exposure_s <= 0.0:
        return 0.0
    if decay_rate <= 0.0:
        # A non-positive rate silently returns a wrong (zero or growing-gap)
        # integral today; reject it like the sibling cooling functions do.
        raise ValueError("decay_rate must be positive")
    grid = np.linspace(0.0, exposure_s, 2048)
    temps = env_temp + (body_temp - env_temp) * np.exp(-decay_rate * grid)
    deficit = np.maximum(0.0, reference_temp - temps)
    return float(np.trapezoid(deficit, grid))


def heating_energy(
    env_temp: float,
    duration_s: float,
    thermal_conductance: float,
    comfort_temp: float = DEFAULT_COMFORT_C,
) -> float:
    """Energy (joules) to hold a space at comfort temp against the cold.

    Heat input rate equals conductance times the temperature deficit, so the
    total energy over ``duration_s`` is ``conductance * (comfort - env) * time``.
    """
    if thermal_conductance < 0.0:
        raise ValueError("thermal_conductance must be non-negative")
    if duration_s < 0.0:
        raise ValueError("duration_s must be non-negative")
    deficit = max(0.0, comfort_temp - env_temp)
    return float(thermal_conductance * deficit * duration_s)


def plan_briefing(
    *,
    env_temp_c: float,
    body_temp_c: float,
    critical_temp_c: float,
    decay_rate: float,
    num_operatives: int,
    op_duration_s: float,
    thermal_conductance: float = 1500.0,
    comfort_temp_c: float = DEFAULT_COMFORT_C,
) -> IceOpsPlan:
    """Assemble a full ice-palace operations briefing from the physical inputs.

    Cold strain is integrated against the operative's own starting core
    temperature (normothermia), while space heating is sized against the room
    comfort temperature — two different references for two different physical
    questions.
    """
    safe_exposure_s = seconds_to_critical(body_temp_c, critical_temp_c, env_temp_c, decay_rate)
    rotation = plan_rotation(num_operatives, op_duration_s, safe_exposure_s)
    load = thermal_load(body_temp_c, env_temp_c, decay_rate, rotation.shift_duration_s, body_temp_c)
    energy = heating_energy(env_temp_c, op_duration_s, thermal_conductance, comfort_temp_c)
    return IceOpsPlan(
        safe_exposure_s=safe_exposure_s,
        rotation=rotation,
        thermal_load_deg_s=load,
        heating_energy_j=energy,
        env_temp_c=env_temp_c,
        body_temp_c=body_temp_c,
        critical_temp_c=critical_temp_c,
        comfort_temp_c=comfort_temp_c,
        reference_temp_c=body_temp_c,
    )
