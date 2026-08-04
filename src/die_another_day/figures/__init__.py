"""Figure-generation package for ICARUS.

Deterministic matplotlib visualizations for the mission's three concepts,
written only from explicit orchestration paths (scripts / tests) into
``output/figures/``.
"""

from __future__ import annotations

from .plots import render_identity_drift, render_pass_profile

__all__ = ["render_identity_drift", "render_pass_profile"]
