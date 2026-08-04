"""Ice-palace structural integrity: load capacity and thermal stress.

ICARUS / *Die Another Day* (2002) concept extension of
:mod:`die_another_day.ice_ops`. Operations inside an ice palace depend on the
structure holding: the load-bearing floor must carry operatives and equipment,
and the palace walls must survive thermal gradients. This module models both
with standard ice-engineering relations:

* :func:`safe_load_tons` — the classic load-capacity rule
  ``P = h^2 / 256`` (P in tons, h in centimetres) for wheeled traffic on an
  ice sheet, matching published engineering rules of thumb (20 cm ≈ 1.5 t,
  30 cm ≈ 3.5 t).
* :func:`thermal_stress_pa` / :func:`critical_delta_t_c` — the thermal
  gradient stress ``σ = E α ΔT / (1 − ν)`` and the temperature difference that
  cracks ice (tensile failure).
* :func:`ice_structure_plan` combines both into a structural verdict with a
  safety factor and a recommended thickness.

All functions are pure and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "GOLD_COEFFICIENT",
    "IceStructurePlan",
    "critical_delta_t_c",
    "ice_structure_plan",
    "load_safety_factor",
    "required_thickness_cm",
    "safe_load_tons",
    "thermal_stress_pa",
]

#: Gold-rule coefficient: tons of safe load per square centimetre of thickness
#: (P_tons = h_cm^2 / 256), the widely published wheeled-traffic rule.
GOLD_COEFFICIENT = 1.0 / 256.0


@dataclass(frozen=True)
class IceStructurePlan:
    """Structural verdict for an ice palace at given thickness, load, and ΔT."""

    capacity_tons: float
    safety_factor: float
    load_ok: bool
    thermal_stress_mpa: float
    critical_delta_t_c: float
    crack_risk: bool
    structurally_safe: bool
    recommended_thickness_cm: float


def safe_load_tons(thickness_cm: float, coefficient: float = GOLD_COEFFICIENT) -> float:
    """Safe load (tons) an ice sheet of ``thickness_cm`` can carry."""
    if thickness_cm <= 0.0:
        raise ValueError("thickness_cm must be positive")
    if coefficient <= 0.0:
        raise ValueError("coefficient must be positive")
    capacity: float = float(coefficient * thickness_cm**2)
    return capacity


def required_thickness_cm(load_tons: float, coefficient: float = GOLD_COEFFICIENT) -> float:
    """Minimum ice thickness (cm) to carry ``load_tons``."""
    if load_tons < 0.0:
        raise ValueError("load_tons must be non-negative")
    if coefficient <= 0.0:
        raise ValueError("coefficient must be positive")
    if load_tons == 0.0:
        return 0.0
    thickness: float = float(np.sqrt(load_tons / coefficient))
    return thickness


def load_safety_factor(thickness_cm: float, load_tons: float, coefficient: float = GOLD_COEFFICIENT) -> float:
    """Ratio of load capacity to applied load (infinite when unloaded)."""
    capacity = safe_load_tons(thickness_cm, coefficient)
    if load_tons <= 0.0:
        return float("inf")
    return float(capacity / load_tons)


def thermal_stress_pa(
    elastic_modulus_pa: float,
    thermal_expansion_1c: float,
    delta_t_c: float,
    poisson: float,
) -> float:
    """Thermal gradient stress ``σ = E α ΔT / (1 − ν)`` (pascals)."""
    if elastic_modulus_pa <= 0.0:
        raise ValueError("elastic_modulus_pa must be positive")
    if thermal_expansion_1c <= 0.0:
        raise ValueError("thermal_expansion_1c must be positive")
    if delta_t_c < 0.0:
        raise ValueError("delta_t_c must be non-negative")
    if not 0.0 <= poisson < 1.0:
        raise ValueError("poisson must lie in [0, 1)")
    stress: float = float(elastic_modulus_pa * thermal_expansion_1c * delta_t_c / (1.0 - poisson))
    return stress


def critical_delta_t_c(
    elastic_modulus_pa: float,
    thermal_expansion_1c: float,
    ice_strength_pa: float,
    poisson: float,
) -> float:
    """Temperature difference (C) that drives ice to its tensile limit."""
    if ice_strength_pa <= 0.0:
        raise ValueError("ice_strength_pa must be positive")
    if elastic_modulus_pa <= 0.0 or thermal_expansion_1c <= 0.0:
        raise ValueError("elastic_modulus_pa and thermal_expansion_1c must be positive")
    delta: float = float(ice_strength_pa * (1.0 - poisson) / (elastic_modulus_pa * thermal_expansion_1c))
    return delta


def ice_structure_plan(
    *,
    thickness_cm: float,
    load_tons: float,
    delta_t_c: float,
    ice_strength_mpa: float = 1.5,
    elastic_modulus_gpa: float = 9.0,
    thermal_expansion_1c: float = 5.1e-5,
    poisson: float = 0.33,
    coefficient: float = GOLD_COEFFICIENT,
) -> IceStructurePlan:
    """Assemble the structural verdict for an ice-palace scenario.

    ``structurally_safe`` requires the load safety factor >= 1 AND no thermal
    crack risk. The recommended thickness covers the applied load.
    """
    if ice_strength_mpa <= 0.0:
        raise ValueError("ice_strength_mpa must be positive")
    if elastic_modulus_gpa <= 0.0:
        raise ValueError("elastic_modulus_gpa must be positive")
    capacity = safe_load_tons(thickness_cm, coefficient)
    safety = load_safety_factor(thickness_cm, load_tons, coefficient)
    load_ok = safety >= 1.0
    stress_pa = thermal_stress_pa(elastic_modulus_gpa * 1e9, thermal_expansion_1c, delta_t_c, poisson)
    crit = critical_delta_t_c(elastic_modulus_gpa * 1e9, thermal_expansion_1c, ice_strength_mpa * 1e6, poisson)
    crack_risk = delta_t_c > crit
    recommended = max(thickness_cm, required_thickness_cm(load_tons, coefficient))
    return IceStructurePlan(
        capacity_tons=capacity,
        safety_factor=safety,
        load_ok=load_ok,
        thermal_stress_mpa=stress_pa / 1e6,
        critical_delta_t_c=crit,
        crack_risk=crack_risk,
        structurally_safe=load_ok and not crack_risk,
        recommended_thickness_cm=recommended,
    )
