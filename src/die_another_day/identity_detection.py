"""Biometric identity-replacement detection (gene-therapy-grade trait drift).

ICARUS / *Die Another Day* (2002) concept. A subject's biometric signature is a
vector of gene-expression / biomarker levels. When an operative is replaced by
a gene-therapy-grade impostor, many markers shift *coherently* — a large,
multivariate drift. This module enrols a baseline profile from real reference
samples and then scores a probe against it:

* :func:`estimate_profile` fits a Gaussian baseline: mean, covariance,
  precision (inverse covariance), and per-marker standard deviations.
* :func:`mahalanobis_sq` computes the squared Mahalanobis distance of a probe
  from the baseline — the natural scalar drift statistic.
* Under the Gaussian assumption the distance is chi-square distributed, so
  :func:`detect_drift` converts it to a *p*-value and compares it to a
  size ``alpha`` threshold (chi-square quantile), then requires a coherent
  cluster of individually-flagged markers (per-marker ``z``-scores past
  ``std_threshold``, at least ``min_markers``) before declaring replacement.

The module is pure and deterministic: every public function operates on real
data and reproduces identical results for identical inputs (fixed seed when
synthetic data is generated).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

__all__ = [
    "BiometricProfile",
    "DriftVerdict",
    "DEFAULT_SEED",
    "detect_drift",
    "estimate_profile",
    "generate_identity_samples",
    "mahalanobis_sq",
    "per_marker_z_scores",
]

#: Fixed deterministic seed used whenever this module synthesizes data.
DEFAULT_SEED = 7


@dataclass(frozen=True)
class BiometricProfile:
    """Enrolled Gaussian baseline over a set of biometric markers.

    ``mean`` is the reference marker vector, ``covariance`` the (regularized)
    sample covariance, ``precision`` its inverse, and ``per_marker_std`` the
    marginal standard deviation of each marker.
    """

    mean: np.ndarray
    covariance: np.ndarray
    precision: np.ndarray
    marker_count: int
    n_samples: int
    per_marker_std: np.ndarray

    def __post_init__(self) -> None:
        if self.mean.ndim != 1:
            raise ValueError("BiometricProfile.mean must be a 1-D vector")
        if self.marker_count != self.mean.shape[0]:
            raise ValueError("marker_count does not match mean vector length")
        if self.covariance.shape != (self.marker_count, self.marker_count):
            raise ValueError("covariance must be (marker_count, marker_count)")


@dataclass(frozen=True)
class DriftVerdict:
    """Outcome of a replacement-detection pass.

    ``replaced`` is True only when the probe exceeds the chi-square threshold
    *and* a coherent cluster of markers is individually flagged.
    """

    replaced: bool
    score: float
    p_value: float
    threshold: float
    flagged_markers: tuple[int, ...]
    n_flagged: int
    marker_count: int
    method: str


def _as_vector(probe: np.ndarray, marker_count: int, label: str) -> np.ndarray:
    arr = np.asarray(probe, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{label} must be a 1-D vector")
    if arr.shape[0] != marker_count:
        raise ValueError(f"{label} length {arr.shape[0]} != marker count {marker_count}")
    return arr


def estimate_profile(
    samples: np.ndarray,
    *,
    ridge: float = 1e-6,
) -> BiometricProfile:
    """Estimate a Gaussian biometric baseline from a real sample matrix.

    Args:
        samples: ``(n_samples, n_markers)`` array of enrolled reference reads.
        ridge: Diagonal regularization added to the covariance before inversion
            to keep it invertible with few samples.

    Returns:
        A frozen :class:`BiometricProfile`.
    """
    arr = np.asarray(samples, dtype=float)
    if arr.ndim != 2:
        raise ValueError("samples must be a 2-D array of shape (n_samples, n_markers)")
    if arr.shape[1] < 1:
        raise ValueError("samples must contain at least one marker")
    if arr.shape[0] < 2:
        raise ValueError("need at least two baseline samples to estimate a profile")
    n_samples, marker_count = arr.shape
    mean = arr.mean(axis=0)
    centered = arr - mean
    cov = (centered.T @ centered) / (n_samples - 1)
    cov = cov + ridge * np.eye(marker_count)
    try:
        precision = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        precision = np.linalg.pinv(cov)
    per_marker_std = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    return BiometricProfile(
        mean=mean,
        covariance=cov,
        precision=precision,
        marker_count=marker_count,
        n_samples=n_samples,
        per_marker_std=per_marker_std,
    )


def mahalanobis_sq(profile: BiometricProfile, probe: np.ndarray) -> float:
    """Squared Mahalanobis distance of a probe from the baseline profile."""
    x = _as_vector(probe, profile.marker_count, "probe")
    delta = x - profile.mean
    return float(delta @ (profile.precision @ delta))


def per_marker_z_scores(profile: BiometricProfile, probe: np.ndarray) -> np.ndarray:
    """Standardized deviation of each marker: ``(probe - mean) / std``.

    Markers with zero variance contribute ``0.0`` (no evidence of drift).
    """
    x = _as_vector(probe, profile.marker_count, "probe")
    std = profile.per_marker_std
    z = np.zeros_like(x)
    positive = std > 0
    z[positive] = (x[positive] - profile.mean[positive]) / std[positive]
    return z


def detect_drift(
    profile: BiometricProfile,
    probe: np.ndarray,
    *,
    alpha: float = 1e-3,
    std_threshold: float = 3.0,
    min_markers: int = 2,
) -> DriftVerdict:
    """Decide whether a probe is a gene-therapy-grade identity replacement.

    The aggregate statistic is the squared Mahalanobis distance; its *p*-value
    is ``chi2.sf(score, k)`` and it is compared against the ``1 - alpha``
    quantile. Replacement additionally requires at least ``min_markers``
    markers whose standardized deviation exceeds ``std_threshold`` — a single
    noisy marker is not enough to declare a coherent substitution.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    if std_threshold <= 0.0:
        raise ValueError("std_threshold must be positive")
    if min_markers < 1:
        raise ValueError("min_markers must be >= 1")

    k = profile.marker_count
    score = mahalanobis_sq(profile, probe)
    p_value = float(stats.chi2.sf(score, k))
    threshold = float(stats.chi2.ppf(1.0 - alpha, k))
    z = per_marker_z_scores(profile, probe)
    flagged = np.flatnonzero(np.abs(z) > std_threshold)
    n_flagged = int(flagged.size)
    replaced = bool(score > threshold and n_flagged >= min_markers)
    return DriftVerdict(
        replaced=replaced,
        score=score,
        p_value=p_value,
        threshold=threshold,
        flagged_markers=tuple(int(i) for i in flagged),
        n_flagged=n_flagged,
        marker_count=k,
        method="gene-therapy-grade-mahalanobis",
    )


def generate_identity_samples(
    *,
    rng_seed: int = DEFAULT_SEED,
    n_samples: int = 200,
    marker_count: int = 6,
    mean: np.ndarray | None = None,
    std: float = 1.0,
) -> np.ndarray:
    """Deterministically synthesize an enrolled biomarker population.

    Returns an ``(n_samples, marker_count)`` array drawn from independent
    Gaussian markers around ``mean`` (default zeros) with shared ``std``.
    """
    if n_samples < 2:
        raise ValueError("n_samples must be >= 2")
    if marker_count < 1:
        raise ValueError("marker_count must be >= 1")
    rng = np.random.default_rng(rng_seed)
    mu = np.zeros(marker_count) if mean is None else np.asarray(mean, dtype=float)
    return mu + std * rng.standard_normal((n_samples, marker_count))
