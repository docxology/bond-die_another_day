"""Deterministic figure generators for the ICARUS mission concepts."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from die_another_day.identity_detection import DriftVerdict  # noqa: E402
from die_another_day.orbital_mirror import PassPlan  # noqa: E402

__all__ = ["render_pass_profile", "render_identity_drift"]


def _save(fig: plt.Figure, out_path: Path) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def render_pass_profile(pass_plan: PassPlan, out_path: Path) -> Path:
    """Render the orbital-mirror pass: elevation vs time with feasible window."""
    times = np.array([p.time_s for p in pass_plan.points])
    elevations = np.array([p.elevation_deg for p in pass_plan.points])
    feasible = np.array([p.feasible for p in pass_plan.points])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(times, elevations, color="#1f4e79", label="mirror elevation")
    if feasible.any():
        ax.fill_between(
            times,
            0,
            elevations,
            where=feasible.tolist(),
            color="#c9a227",
            alpha=0.35,
            label="feasible targeting window",
        )
    if pass_plan.best_index is not None:
        best = pass_plan.points[pass_plan.best_index]
        ax.scatter([best.time_s], [best.elevation_deg], color="#c0392b", zorder=5, label="peak flux")
    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.set_xlabel("time since epoch (s)")
    ax.set_ylabel("elevation (deg)")
    ax.set_title("ICARUS orbital-mirror pass over target")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _save(fig, out_path)


def render_identity_drift(
    genuine_z: np.ndarray,
    replaced_z: np.ndarray,
    verdict: DriftVerdict,
    out_path: Path,
    *,
    std_threshold: float = 3.0,
) -> Path:
    """Render per-marker standardized trait drift for genuine vs replaced probes."""
    markers = np.arange(1, verdict.marker_count + 1)
    width = 0.38

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(markers - width / 2, np.asarray(genuine_z), width, label="genuine probe", color="#2e86ab")
    ax.bar(markers + width / 2, np.asarray(replaced_z), width, label="replaced probe", color="#c0392b")
    ax.axhline(std_threshold, color="#7d7d7d", linestyle="--")
    ax.axhline(-std_threshold, color="#7d7d7d", linestyle="--")
    ax.set_xlabel("biomarker index")
    ax.set_ylabel("standardized drift (z)")
    ax.set_title(f"identity trait drift — replaced={verdict.replaced}")
    ax.legend(loc="best")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    return _save(fig, out_path)
