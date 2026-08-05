"""Shared concept-runner tests (real data, real computation, no mocks).

``mission_results.run_all_concepts`` is the single place where the six ICARUS
models are executed, so both the ``MissionOutcome`` and the manuscript tokens
are derived from it. These tests pin its determinism, its positive/negative
controls, and its config sensitivity.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from die_another_day import identity_detection as idm
from die_another_day import manuscript_variables as mv
from die_another_day import mission_results as mr


@pytest.fixture(scope="module")
def config() -> dict[str, Any]:
    return mv.load_manuscript_config()


@pytest.fixture(scope="module")
def results(config: dict[str, Any]) -> mr.ConceptResults:
    return mr.run_all_concepts(config)


def test_all_six_concepts_are_populated(results: mr.ConceptResults) -> None:
    assert results.seed == mr.MISSION_SEED
    assert results.identity_replaced.marker_count == 6
    assert results.sequence_replaced.genome_length == 1500
    assert results.ice.rotation.squad_count >= 1
    assert results.rescue.time_to_severe_s > 0.0
    assert results.structure.capacity_tons > 0.0
    assert len(results.mirror.points) == 51


def test_positive_control_is_flagged(results: mr.ConceptResults) -> None:
    """The replaced probe must clear the chi-square bar *and* the marker bar."""
    replaced = results.identity_replaced
    assert replaced.replaced is True
    assert replaced.score > replaced.threshold
    assert replaced.n_flagged >= 2


def test_negative_control_is_a_real_draw_not_the_profile_mean(results: mr.ConceptResults) -> None:
    """The genuine probe must clear the screen with a non-zero, measured score.

    Scoring the profile mean would give a Mahalanobis distance of exactly zero,
    making "the genuine operative clears" true by construction. The negative
    control is a fresh out-of-sample draw instead, so clearing is a measurement.
    """
    genuine = results.identity_genuine
    assert genuine.replaced is False
    assert genuine.score > 0.0
    assert genuine.score < genuine.threshold
    assert 0.0 < genuine.p_value < 1.0


def test_genuine_probe_differs_from_the_profile_mean(config: dict[str, Any]) -> None:
    baseline = idm.generate_identity_samples(rng_seed=mr.MISSION_SEED, n_samples=50, marker_count=6)
    profile = idm.estimate_profile(baseline)
    probe = mr.genuine_probe(profile, seed=mr.MISSION_SEED)
    assert not np.allclose(probe, profile.mean)
    assert probe.shape == profile.mean.shape


def test_replacement_probe_shifts_only_the_configured_markers() -> None:
    baseline = idm.generate_identity_samples(rng_seed=mr.MISSION_SEED, n_samples=200, marker_count=6)
    profile = idm.estimate_profile(baseline)
    probe = mr.replacement_probe(profile, seed=mr.MISSION_SEED, std_threshold=3.0, min_markers=2)
    z = idm.per_marker_z_scores(profile, probe)
    assert (np.abs(z[:2]) > 3.0).all()
    assert (np.abs(z[2:]) < 3.0).all()


def test_sequence_controls_separate(results: mr.ConceptResults) -> None:
    assert results.sequence_genuine.matched is True
    assert results.sequence_genuine.replacement_suspected is False
    assert results.sequence_replaced.replacement_suspected is True
    assert results.longest_edit_block >= 12


def test_the_two_reads_are_matched_on_count_not_on_position(results: mr.ConceptResults) -> None:
    """Pin what the sequence controls actually share, and what they do not.

    §03 used to claim the replaced read carried "the same scattered errors" as
    the genuine one. It does not: the edit block consumes RNG draws first and
    removes its own loci from the available pool, so the two scattered sets are
    independent. What *is* matched is their size, and that is the property the
    manuscript now states.
    """
    config = mv.load_manuscript_config()["concepts"]["sequence_identity"]
    scattered = int(config["scattered_errors"])
    cluster_min = int(config["cluster_min"])
    reference = results.sequence_reference

    def positions(read: str) -> set[int]:
        return {i for i, (a, b) in enumerate(zip(reference, read, strict=True)) if a != b}

    genuine_positions = positions(results.sequence_genuine_read)
    replaced_positions = positions(results.sequence_replaced_read)
    block = next(c for c in results.sequence_replaced.clusters if c[1] - c[0] >= cluster_min)
    replaced_scattered = replaced_positions - set(range(block[0], block[1]))

    assert len(genuine_positions) == scattered
    assert len(replaced_scattered) == scattered
    assert genuine_positions != replaced_scattered
    assert results.sequence_replaced.hamming == scattered + (block[1] - block[0])


def test_generator_places_exactly_the_configured_number_of_scattered_errors(
    results: mr.ConceptResults,
) -> None:
    """``SEQ_GENUINE_HAMMING`` is a generator check, not an independent finding.

    ``mutate_genome`` must substitute at ``scattered_errors`` *distinct* loci
    and must actually change the base at each — a collision or a no-op
    substitution would break this equality. §05 names this token as
    structurally determined for exactly this reason.
    """
    scattered = int(mv.load_manuscript_config()["concepts"]["sequence_identity"]["scattered_errors"])
    assert results.sequence_genuine.hamming == scattered
    assert results.genuine_longest_run == 1


def test_replacement_shift_is_clear_of_the_flagging_threshold() -> None:
    """The positive control's shift magnitude is a multiple of the threshold."""
    baseline = idm.generate_identity_samples(rng_seed=mr.MISSION_SEED, n_samples=200, marker_count=6)
    profile = idm.estimate_profile(baseline)
    probe = mr.replacement_probe(profile, seed=mr.MISSION_SEED, std_threshold=3.0, min_markers=2)
    z = idm.per_marker_z_scores(profile, probe)
    expected = mr.REPLACEMENT_SHIFT_FACTOR * 3.0
    assert np.allclose(z[:2], expected, atol=0.2)
    assert expected != 3.0


def test_carried_probe_arrays_are_the_ones_that_were_scored(results: mr.ConceptResults) -> None:
    """The z-vectors on the record must reproduce the reported flag counts.

    They are what the published figure plots, so if they were stale the figure
    would illustrate a different experiment than the table.
    """
    threshold = float(mv.load_manuscript_config()["concepts"]["identity"]["std_threshold"])
    assert sum(1 for v in results.identity_replaced_z if abs(v) > threshold) == results.identity_replaced.n_flagged
    assert sum(1 for v in results.identity_genuine_z if abs(v) > threshold) == results.identity_genuine.n_flagged
    assert all(abs(v) > 0.0 for v in results.identity_genuine_z)


def test_run_is_deterministic(config: dict[str, Any]) -> None:
    first = mr.run_all_concepts(config)
    second = mr.run_all_concepts(config)
    assert first == second


def test_seed_changes_the_synthetic_populations(config: dict[str, Any]) -> None:
    """A different seed must move the measured numbers — the seed is real."""
    baseline = mr.run_all_concepts(config, seed=mr.MISSION_SEED)
    other = mr.run_all_concepts(config, seed=mr.MISSION_SEED + 1)
    assert other.identity_replaced.score != baseline.identity_replaced.score
    # Physics-only concepts are seed-independent by construction.
    assert other.ice == baseline.ice
    assert other.structure == baseline.structure


def test_config_parameters_are_actually_consumed(config: dict[str, Any]) -> None:
    """Flipping a configured value must move the corresponding output."""
    warmer = {
        **config,
        "concepts": {
            **config["concepts"],
            "ice_ops": {**config["concepts"]["ice_ops"], "env_temp_c": -5.0},
        },
    }
    baseline = mr.run_all_concepts(config)
    changed = mr.run_all_concepts(warmer)
    assert changed.ice.safe_exposure_s > baseline.ice.safe_exposure_s


def test_missing_sections_fall_back_to_documented_defaults() -> None:
    """An empty config still runs: every parameter has a coded default."""
    results = mr.run_all_concepts({})
    assert results.identity_replaced.marker_count == 6
    assert results.sequence_replaced.genome_length == 1500
    assert results.ice.safe_exposure_s > 0.0


def test_malformed_sections_are_ignored_rather_than_crashing() -> None:
    """A non-mapping ``concepts`` block degrades to defaults, not a TypeError."""
    results = mr.run_all_concepts({"concepts": ["not", "a", "mapping"]})
    assert results.identity_replaced.marker_count == 6
    other = mr.run_all_concepts({"concepts": {"identity": "not-a-mapping"}})
    assert other.identity_replaced.marker_count == 6


def test_the_discriminating_statistic_actually_discriminates(results: mr.ConceptResults) -> None:
    """The block-length rule, not fingerprint similarity, separates the probes.

    Both probes clear the configured k-mer match threshold, so a Jaccard-only
    screen would pass the replaced genome. Only the contiguous-run length
    separates them, and the genuine control's longest run must sit strictly
    below the cluster minimum for that claim to hold.
    """
    threshold = float(mv.load_manuscript_config()["concepts"]["sequence_identity"]["match_jaccard"])
    cluster_min = int(mv.load_manuscript_config()["concepts"]["sequence_identity"]["cluster_min"])
    assert results.sequence_genuine.jaccard >= threshold
    assert results.sequence_replaced.jaccard >= threshold
    assert results.genuine_longest_run < cluster_min <= results.longest_edit_block
