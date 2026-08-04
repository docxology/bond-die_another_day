"""ICARUS — special-agent mission software (PROJECT BOND film package).

*Die Another Day* (2002), mission codename ICARUS. This package implements the
three mission concepts as a pure, deterministic domain core plus a thin
:class:`~die_another_day.mission.MissionProvider` adapter against the frozen
BOND-API protocol:

* :mod:`die_another_day.identity_detection` — gene-therapy-grade biometric
  identity-replacement detection (Mahalanobis trait drift).
* :mod:`die_another_day.ice_ops` — ice-palace thermal/cold-environment
  operations planning (Newton-cooling exposure ceilings and rotation).
* :mod:`die_another_day.orbital_mirror` — orbital-mirror (ICARUS) targeting
  geometry (orbit propagation, reflection-law pointing, solar flux delivery).

The domain modules are infrastructure-free and importable without ``bond_api``;
only :mod:`die_another_day.mission` adapts them to the protocol.
"""

from __future__ import annotations

from . import ice_ops, identity_detection, orbital_mirror
from .identity_detection import DriftVerdict, estimate_profile
from .ice_ops import IceOpsPlan, plan_briefing
from .orbital_mirror import PassPlan, plan_pass

__version__ = "0.1.0"

#: Manuscript identity and mission codename (single source of truth).
IDENTITY = "die_another_day"
CODENAME = "ICARUS"
CONCEPT_MODULES = ("identity_detection", "ice_ops", "orbital_mirror")

__all__ = [
    # Identity
    "IDENTITY",
    "CODENAME",
    "CONCEPT_MODULES",
    "__version__",
    # Concept modules
    "ice_ops",
    "identity_detection",
    "orbital_mirror",
    # Re-exported helpers
    "DriftVerdict",
    "IceOpsPlan",
    "PassPlan",
    "estimate_profile",
    "plan_briefing",
    "plan_pass",
]
