"""ICARUS — special-agent mission software (PROJECT BOND film package).

*Die Another Day* (2002), mission codename ICARUS. This package implements six
mission concepts as a pure, deterministic domain core plus a thin
:class:`~die_another_day.mission.MissionProvider` adapter against the frozen
BOND-API protocol:

* :mod:`die_another_day.identity_detection` — gene-therapy-grade biometric
  identity-replacement detection (Mahalanobis trait drift).
* :mod:`die_another_day.sequence_identity` — DNA sequence identity verification
  (Levenshtein edit distance, k-mer fingerprints, contiguous edit-block
  detection).
* :mod:`die_another_day.ice_ops` — ice-palace thermal/cold-environment
  operations planning (Newton-cooling exposure ceilings and rotation).
* :mod:`die_another_day.hypothermia` — cold-water immersion and hypothermia
  risk planning (immersion cooling timeline and rescue feasibility).
* :mod:`die_another_day.ice_structure` — ice-palace structural integrity (load
  capacity and thermal-gradient cracking).
* :mod:`die_another_day.orbital_mirror` — orbital-mirror (ICARUS) targeting
  geometry (orbit propagation, reflection-law pointing, solar flux delivery).

The domain modules are infrastructure-free and importable without ``bond_api``;
only :mod:`die_another_day.mission` adapts them to the protocol.
"""

from __future__ import annotations

from . import (
    hypothermia,
    ice_ops,
    ice_structure,
    identity_detection,
    orbital_mirror,
    sequence_identity,
)
from .hypothermia import ColdWaterRescuePlan, plan_cold_water_rescue
from .ice_ops import IceOpsPlan, plan_briefing
from .ice_structure import IceStructurePlan, ice_structure_plan
from .identity_detection import DriftVerdict, estimate_profile
from .orbital_mirror import PassPlan, plan_pass
from .sequence_identity import SequenceVerdict, verify_identity

__version__ = "0.1.0"

#: Manuscript identity and mission codename (single source of truth).
IDENTITY = "die_another_day"
CODENAME = "ICARUS"
CONCEPT_MODULES = (
    "identity_detection",
    "sequence_identity",
    "ice_ops",
    "hypothermia",
    "ice_structure",
    "orbital_mirror",
)

__all__ = [
    # Identity
    "IDENTITY",
    "CODENAME",
    "CONCEPT_MODULES",
    "__version__",
    # Concept modules
    "hypothermia",
    "ice_ops",
    "ice_structure",
    "identity_detection",
    "orbital_mirror",
    "sequence_identity",
    # Re-exported helpers
    "ColdWaterRescuePlan",
    "DriftVerdict",
    "IceOpsPlan",
    "IceStructurePlan",
    "PassPlan",
    "SequenceVerdict",
    "estimate_profile",
    "ice_structure_plan",
    "plan_briefing",
    "plan_cold_water_rescue",
    "plan_pass",
    "verify_identity",
]
