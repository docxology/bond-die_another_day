"""Figure-generation package for ICARUS.

Deterministic matplotlib visualizations for the mission's concepts, written only
from explicit orchestration paths (scripts / tests) into ``output/figures/``.
"""

from __future__ import annotations

from .plots import (
    hypothermia_window_s,
    render_hypothermia_curve,
    render_identity_drift,
    render_pass_profile,
    render_sequence_mismatches,
)

__all__ = [
    "hypothermia_window_s",
    "render_hypothermia_curve",
    "render_identity_drift",
    "render_pass_profile",
    "render_sequence_mismatches",
]
