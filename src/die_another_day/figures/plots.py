"""Deterministic figure generators for the ICARUS mission concepts."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from die_another_day import hypothermia as hyp  # noqa: E402
from die_another_day import sequence_identity as si  # noqa: E402
from die_another_day.identity_detection import DriftVerdict  # noqa: E402
from die_another_day.orbital_mirror import PassPlan  # noqa: E402

__all__ = ["render_hypothermia_curve", "render_identity_drift", "render_pass_profile", "render_sequence_mismatches"]


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


def render_hypothermia_curve(
    water_c: float,
    mass_kg: float,
    insulation_factor: float,
    duration_s: float,
    out_path: Path,
) -> Path:
    """Render the cold-water immersion core-temperature decay with stage bands."""
    times = np.linspace(0.0, duration_s, 512)
    k = hyp.cooling_rate_water(mass_kg, insulation_factor)
    temps = np.array([hyp.immersion_core_temp(37.0, water_c, k, float(t)) for t in times])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(times, temps, color="#1f4e79", label="core temperature")
    for threshold, label, color in [
        (35.0, "mild (35C)", "#7d7d7d"),
        (32.0, "moderate (32C)", "#7d7d7d"),
        (28.0, "severe (28C)", "#7d7d7d"),
    ]:
        ax.axhline(threshold, color=color, linestyle="--", linewidth=0.9)
        ax.text(times[-1] * 0.02, threshold + 0.3, label, fontsize=8, color=color)
    ax.set_xlabel("immersion time (s)")
    ax.set_ylabel("core temperature (C)")
    ax.set_title(f"cold-water immersion ({water_c:g} C, {mass_kg:g} kg)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return _save(fig, out_path)


def render_sequence_mismatches(reference: str, probe: str, out_path: Path) -> Path:
    """Render DNA mismatch positions, shading the contiguous edit clusters."""
    mismatch = np.array([int(a != b) for a, b in zip(reference, probe, strict=True)])
    positions = np.arange(len(reference))
    clusters = si.mismatch_clusters(reference, probe, min_run=1)

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.fill_between(positions, mismatch, step="mid", color="#c0392b", alpha=0.6, label="mismatch")
    for start, end in clusters:
        ax.axvspan(
            start - 0.5,
            end - 0.5,
            color="#c9a227",
            alpha=0.3,
            label="contiguous edit" if start == clusters[0][0] else None,
        )
    ax.set_xlabel("genome position")
    ax.set_ylabel("mismatch (0/1)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("DNA sequence identity verification — mismatch map")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return _save(fig, out_path)
