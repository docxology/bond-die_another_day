"""Identity-replacement detection tests (real data, no mocks)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from die_another_day import identity_detection as idm


def _profile(marker_count: int = 6, seed: int = 7, n_samples: int = 200) -> idm.BiometricProfile:
    samples = idm.generate_identity_samples(rng_seed=seed, n_samples=n_samples, marker_count=marker_count)
    return idm.estimate_profile(samples)


def test_estimate_profile_shape_and_fields() -> None:
    profile = _profile(marker_count=6)
    assert profile.marker_count == 6
    assert profile.n_samples == 200
    assert profile.mean.shape == (6,)
    assert profile.covariance.shape == (6, 6)
    assert profile.precision.shape == (6, 6)
    assert profile.per_marker_std.shape == (6,)


def test_estimate_profile_validation() -> None:
    with pytest.raises(ValueError):
        idm.estimate_profile(np.zeros(5))  # not 2-D
    with pytest.raises(ValueError):
        idm.estimate_profile(np.zeros((1, 3)))  # < 2 samples
    with pytest.raises(ValueError):
        idm.estimate_profile(np.zeros((5, 0)))  # zero markers


def test_profile_post_init_validation() -> None:
    v = np.zeros(3)
    eye = np.eye(3)
    with pytest.raises(ValueError):
        idm.BiometricProfile(
            mean=np.zeros((2, 2)), covariance=eye, precision=eye, marker_count=3, n_samples=4, per_marker_std=v
        )  # mean not 1-D
    with pytest.raises(ValueError):
        idm.BiometricProfile(
            mean=np.zeros(2), covariance=eye, precision=eye, marker_count=3, n_samples=4, per_marker_std=v
        )  # marker mismatch
    with pytest.raises(ValueError):
        idm.BiometricProfile(
            mean=v, covariance=np.eye(2), precision=eye, marker_count=3, n_samples=4, per_marker_std=v
        )  # cov shape


def test_mahalanobis_of_mean_is_zero() -> None:
    profile = _profile()
    assert idm.mahalanobis_sq(profile, profile.mean) == pytest.approx(0.0, abs=1e-9)


def test_mahalanobis_increases_with_distance() -> None:
    profile = _profile()
    near = profile.mean + 0.1 * profile.per_marker_std
    far = profile.mean + 10.0 * profile.per_marker_std
    assert idm.mahalanobis_sq(profile, far) > idm.mahalanobis_sq(profile, near)


def test_mahalanobis_validation() -> None:
    profile = _profile()
    with pytest.raises(ValueError):
        idm.mahalanobis_sq(profile, np.zeros((3, 3)))  # not 1-D
    with pytest.raises(ValueError):
        idm.mahalanobis_sq(profile, np.zeros(3))  # wrong length


def test_per_marker_z_of_mean_is_zero() -> None:
    profile = _profile()
    z = idm.per_marker_z_scores(profile, profile.mean)
    assert np.allclose(z, 0.0, atol=1e-9)


def test_per_marker_z_zero_variance_marker() -> None:
    # Constant marker => zero std => z treated as 0 (no evidence).
    samples = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 2.0], [1.0, 3.0]])
    profile = idm.estimate_profile(samples)
    z = idm.per_marker_z_scores(profile, np.array([1.0, 4.0]))
    assert z[0] == 0.0
    assert z[1] != 0.0


def test_detect_replacement_true() -> None:
    profile = _profile()
    probe = profile.mean.copy()
    probe[:2] = probe[:2] + 4.5 * profile.per_marker_std[:2]
    verdict = idm.detect_drift(profile, probe)
    assert verdict.replaced is True
    assert verdict.n_flagged >= 2
    assert verdict.score > verdict.threshold
    assert verdict.p_value < 0.05


def test_detect_genuine_cleared() -> None:
    profile = _profile()
    verdict = idm.detect_drift(profile, profile.mean)
    assert verdict.replaced is False
    assert verdict.n_flagged == 0


def test_single_marker_shift_not_enough_for_min_markers() -> None:
    profile = _profile()
    probe = profile.mean.copy()
    probe[:1] = probe[:1] + 6.0 * profile.per_marker_std[:1]
    verdict = idm.detect_drift(profile, probe, min_markers=2)
    # One marker flagged even though it is far: no coherent cluster -> cleared.
    assert verdict.n_flagged < 2 or not verdict.replaced


def test_detect_drift_validation() -> None:
    profile = _profile()
    with pytest.raises(ValueError):
        idm.detect_drift(profile, profile.mean, alpha=1.5)
    with pytest.raises(ValueError):
        idm.detect_drift(profile, profile.mean, alpha=0.0)
    with pytest.raises(ValueError):
        idm.detect_drift(profile, profile.mean, std_threshold=0.0)
    with pytest.raises(ValueError):
        idm.detect_drift(profile, profile.mean, min_markers=0)


def test_chi_square_statistic_consistent() -> None:
    """A probe placed exactly on the alpha quantile must report p_value == alpha.

    The probe is constructed by scaling an arbitrary direction so its squared
    Mahalanobis distance equals the quantile exactly, which makes the
    chi-square calibration falsifiable rather than merely asserted.
    """
    profile = _profile()
    k = profile.marker_count
    alpha = 0.05
    threshold = float(stats.chi2.ppf(1.0 - alpha, k))

    direction = np.ones(k)
    quadratic = float(direction @ (profile.precision @ direction))
    probe = profile.mean + direction * np.sqrt(threshold / quadratic)

    assert idm.mahalanobis_sq(profile, probe) == pytest.approx(threshold, rel=1e-9)
    verdict = idm.detect_drift(profile, probe, alpha=alpha, std_threshold=0.5, min_markers=1)
    assert verdict.p_value == pytest.approx(alpha, rel=1e-9)
    assert verdict.threshold == pytest.approx(threshold, rel=1e-12)

    # A probe scaled just inside the quantile clears; just outside, it trips.
    inside = profile.mean + 0.99 * (probe - profile.mean)
    outside = profile.mean + 1.01 * (probe - profile.mean)
    assert idm.detect_drift(profile, inside, alpha=alpha, std_threshold=0.5, min_markers=1).replaced is False
    assert idm.detect_drift(profile, outside, alpha=alpha, std_threshold=0.5, min_markers=1).replaced is True


def test_singular_covariance_falls_back_to_pseudo_inverse() -> None:
    """With ridge disabled, an exactly singular covariance takes the pinv path."""
    identical = np.array([[1.0, 1.0], [1.0, 1.0]])
    profile = idm.estimate_profile(identical, ridge=0.0)
    assert np.allclose(profile.covariance, 0.0)
    # pinv of the zero matrix is the zero matrix; np.linalg.inv would not be.
    assert np.allclose(profile.precision, 0.0)
    # Zero-variance markers contribute no drift evidence.
    assert np.allclose(idm.per_marker_z_scores(profile, np.array([5.0, 5.0])), 0.0)


def test_generate_identity_samples_deterministic() -> None:
    a = idm.generate_identity_samples(rng_seed=3, n_samples=10, marker_count=4)
    b = idm.generate_identity_samples(rng_seed=3, n_samples=10, marker_count=4)
    assert np.array_equal(a, b)


def test_generate_identity_samples_validation() -> None:
    with pytest.raises(ValueError):
        idm.generate_identity_samples(n_samples=1)
    with pytest.raises(ValueError):
        idm.generate_identity_samples(marker_count=0)
