"""Single deterministic runner for all six ICARUS concepts.

ICARUS / *Die Another Day* (2002). This module is the one place that turns the
``concepts:`` block of ``manuscript/config.yaml`` into concrete model outputs.
Both consumers use it, so they can never disagree:

* :mod:`die_another_day.mission` — the frozen ``MissionProvider`` adapter,
  which serialises these results into a ``MissionOutcome``;
* :mod:`die_another_day.manuscript_variables` — which turns the same results
  into the manuscript's ``{{TOKEN}}`` values, so every measured number printed
  in the paper is literally the number the mission computed.

Two probes are run against each identity model, a positive and a negative
control:

* the **replaced** biometric probe is a coherent multi-marker shift, and the
  **genuine** probe is a fresh out-of-sample draw from the *same* enrolled
  population (seed ``seed + 1``) — not the profile mean, which would score
  exactly zero and make the negative control unfalsifiable;
* the **replaced** genome carries a contiguous edit block, and the **genuine**
  genome carries only scattered single-base sequencing noise. The two reads
  draw their scattered errors from *independent* position sets (the block
  consumes RNG draws before the scattered positions, and it also removes its
  own loci from the available pool), so the probes are matched on the *number*
  of scattered errors, not on their positions.

:class:`ConceptResults` also carries the exact probe arrays and reads that were
scored, so ``scripts/generate_figures.py`` can plot the very experiment the
results table reports instead of rebuilding its own probes.

Every function is pure and deterministic: the same config and seed reproduce
identical results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from die_another_day import (
    hypothermia,
    ice_ops,
    ice_structure,
    identity_detection,
    orbital_mirror,
    sequence_identity,
)

__all__ = [
    "BASELINE_SAMPLES",
    "ConceptResults",
    "MISSION_SEED",
    "REPLACEMENT_SHIFT_FACTOR",
    "genuine_probe",
    "replacement_probe",
    "run_all_concepts",
]

#: Deterministic seed for every synthetic population this package generates.
MISSION_SEED = 7

#: Enrolled baseline population size for the biometric profile.
BASELINE_SAMPLES = 200

#: Multiple of the per-marker flagging threshold used to build the positive
#: control. The replaced probe is shifted by ``REPLACEMENT_SHIFT_FACTOR *
#: std_threshold`` sigma so it lands clearly *past* the flagging bar rather
#: than exactly on it — the manuscript cites the product, never the threshold
#: alone, via the ``ID_REPLACED_SHIFT_SIGMA`` token.
REPLACEMENT_SHIFT_FACTOR = 1.5


@dataclass(frozen=True)
class ConceptResults:
    """The six concept outputs for one deterministic mission run."""

    identity_replaced: identity_detection.DriftVerdict
    identity_genuine: identity_detection.DriftVerdict
    sequence_replaced: sequence_identity.SequenceVerdict
    sequence_genuine: sequence_identity.SequenceVerdict
    ice: ice_ops.IceOpsPlan
    rescue: hypothermia.ColdWaterRescuePlan
    structure: ice_structure.IceStructurePlan
    mirror: orbital_mirror.PassPlan
    seed: int
    #: Per-marker standardized drift of the two biometric probes that were
    #: actually scored above. Carried so the published figure plots the same
    #: experiment the results table reports.
    identity_genuine_z: tuple[float, ...]
    identity_replaced_z: tuple[float, ...]
    #: Magnitude (in sigma) of the coherent shift applied to the positive
    #: control's leading markers — ``REPLACEMENT_SHIFT_FACTOR * std_threshold``.
    identity_shift_sigma: float
    #: The exact reads that were scored, for the same reason.
    sequence_reference: str
    sequence_genuine_read: str
    sequence_replaced_read: str

    @property
    def longest_edit_block(self) -> int:
        """Longest contiguous mismatch run in the replaced genome (bases)."""
        return _longest_run(self.sequence_replaced)

    @property
    def genuine_longest_run(self) -> int:
        """Longest contiguous mismatch run in the genuine genome (bases).

        Reported so the manuscript can state the negative control's block
        length as a measurement rather than asserting it is zero.
        """
        return _longest_run(self.sequence_genuine)


def _longest_run(verdict: sequence_identity.SequenceVerdict) -> int:
    """Longest contiguous mismatch run in a sequence verdict (0 when none)."""
    return max((end - start for start, end in verdict.clusters), default=0)


def _section(config: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    """Read one ``concepts.<name>`` sub-mapping, defaulting to empty."""
    concepts = config.get("concepts", {})
    section = concepts.get(name, {}) if isinstance(concepts, Mapping) else {}
    return section if isinstance(section, Mapping) else {}


def replacement_probe(
    profile: identity_detection.BiometricProfile,
    *,
    seed: int,
    std_threshold: float,
    min_markers: int,
) -> np.ndarray:
    """Synthesize a gene-therapy-grade replaced operative (positive control).

    Shifts the first ``min_markers`` markers by
    ``REPLACEMENT_SHIFT_FACTOR * std_threshold`` standard deviations — a
    coherent, multi-marker drift — plus small noise so the probe is not an
    exact algebraic construction. The remaining markers are left at the
    population mean, so the probe is a *coherent partial* replacement rather
    than a uniform offset of every marker.
    """
    rng = np.random.default_rng(seed)
    probe = profile.mean.copy()
    n_shift = min(min_markers, profile.marker_count)
    shift = REPLACEMENT_SHIFT_FACTOR * std_threshold
    probe[:n_shift] = probe[:n_shift] + shift * profile.per_marker_std[:n_shift]
    return probe + 0.1 * rng.standard_normal(profile.marker_count)


def genuine_probe(profile: identity_detection.BiometricProfile, *, seed: int) -> np.ndarray:
    """Draw a fresh out-of-sample operative from the enrolled population.

    This is the negative control. It is deliberately *not* ``profile.mean``:
    the mean scores a Mahalanobis distance of exactly zero, so clearing the
    screen would be true by construction rather than measured.
    """
    rng = np.random.default_rng(seed + 1)
    return profile.mean + profile.per_marker_std * rng.standard_normal(profile.marker_count)


def run_all_concepts(config: Mapping[str, Any], *, seed: int = MISSION_SEED) -> ConceptResults:
    """Run all six ICARUS concept models against a manuscript config.

    Args:
        config: Parsed ``manuscript/config.yaml`` mapping (its ``concepts:``
            block supplies every physical parameter).
        seed: Deterministic seed for all synthetic populations.

    Returns:
        A frozen :class:`ConceptResults` holding one output per concept.
    """
    id_cfg = _section(config, "identity")
    seq_cfg = _section(config, "sequence_identity")
    ice_cfg = _section(config, "ice_ops")
    hyp_cfg = _section(config, "hypothermia")
    struct_cfg = _section(config, "ice_structure")
    orb_cfg = _section(config, "orbital_mirror")

    # --- Concept 1: biometric identity-replacement detection ---------------
    marker_count = int(id_cfg.get("num_biomarkers", 6))
    alpha = float(id_cfg.get("alpha", 1e-3))
    std_threshold = float(id_cfg.get("std_threshold", 3.0))
    min_markers = int(id_cfg.get("min_markers", 2))
    baseline = identity_detection.generate_identity_samples(
        rng_seed=seed,
        n_samples=BASELINE_SAMPLES,
        marker_count=marker_count,
    )
    profile = identity_detection.estimate_profile(baseline)
    replaced_vector = replacement_probe(profile, seed=seed, std_threshold=std_threshold, min_markers=min_markers)
    genuine_vector = genuine_probe(profile, seed=seed)
    identity_replaced = identity_detection.detect_drift(
        profile,
        replaced_vector,
        alpha=alpha,
        std_threshold=std_threshold,
        min_markers=min_markers,
    )
    identity_genuine = identity_detection.detect_drift(
        profile,
        genuine_vector,
        alpha=alpha,
        std_threshold=std_threshold,
        min_markers=min_markers,
    )
    replaced_z = tuple(float(v) for v in identity_detection.per_marker_z_scores(profile, replaced_vector))
    genuine_z = tuple(float(v) for v in identity_detection.per_marker_z_scores(profile, genuine_vector))

    # --- Concept 2: DNA sequence identity verification ---------------------
    genome_length = int(seq_cfg.get("genome_length", 1500))
    scattered = int(seq_cfg.get("scattered_errors", 5))
    cluster_min = int(seq_cfg.get("cluster_min", 12))
    kmer_k = int(seq_cfg.get("kmer_k", 9))
    match_jaccard = float(seq_cfg.get("match_jaccard", 0.90))
    reference = sequence_identity.generate_genome(genome_length, seed=seed)
    genuine_seq = sequence_identity.mutate_genome(reference, seed=seed, n_substitutions=scattered)
    replaced_seq = sequence_identity.mutate_genome(
        reference,
        seed=seed,
        n_substitutions=scattered,
        cluster_length=cluster_min,
    )
    sequence_genuine = sequence_identity.verify_identity(
        reference, genuine_seq, k=kmer_k, match_jaccard=match_jaccard, cluster_min=cluster_min
    )
    sequence_replaced = sequence_identity.verify_identity(
        reference, replaced_seq, k=kmer_k, match_jaccard=match_jaccard, cluster_min=cluster_min
    )

    # --- Concept 3: ice-palace air operations ------------------------------
    ice = ice_ops.plan_briefing(
        env_temp_c=float(ice_cfg.get("env_temp_c", -34.0)),
        body_temp_c=float(ice_cfg.get("body_temp_c", 37.0)),
        critical_temp_c=float(ice_cfg.get("critical_temp_c", 30.0)),
        decay_rate=float(ice_cfg.get("decay_rate_h", 0.8)) / 3600.0,
        num_operatives=int(ice_cfg.get("num_operatives", 4)),
        op_duration_s=float(ice_cfg.get("op_duration_s", 1800)),
        thermal_conductance=float(ice_cfg.get("thermal_conductance", 1500.0)),
    )

    # --- Concept 4: cold-water hypothermia / rescue ------------------------
    rescue = hypothermia.plan_cold_water_rescue(
        water_c=float(hyp_cfg.get("water_temp_c", 10.0)),
        mass_kg=float(hyp_cfg.get("body_mass_kg", 75.0)),
        insulation_factor=float(hyp_cfg.get("insulation_factor", 0.9)),
        distance_m=float(hyp_cfg.get("distance_m", 400.0)),
        sweep_speed_m_s=float(hyp_cfg.get("sweep_speed_m_s", 2.0)),
    )

    # --- Concept 5: ice-palace structural integrity ------------------------
    structure = ice_structure.ice_structure_plan(
        thickness_cm=float(struct_cfg.get("thickness_cm", 30.0)),
        load_tons=float(struct_cfg.get("load_tons", 3.0)),
        delta_t_c=float(struct_cfg.get("delta_t_c", 15.0)),
        ice_strength_mpa=float(struct_cfg.get("ice_strength_mpa", 1.5)),
    )

    # --- Concept 6: orbital-mirror targeting -------------------------------
    mirror = orbital_mirror.plan_pass(
        semi_major_axis_m=float(orb_cfg.get("semi_major_axis_km", 6878.0)) * 1000.0,
        inclination_deg=float(orb_cfg.get("inclination_deg", 45.0)),
        raan_deg=float(orb_cfg.get("raan_deg", 120.0)),
        mean_anomaly_deg=float(orb_cfg.get("mean_anomaly_deg", 30.0)),
        target_lat_deg=float(orb_cfg.get("target_lat_deg", 60.0)),
        target_lon_deg=float(orb_cfg.get("target_lon_deg", 15.0)),
        jd_start=float(orb_cfg.get("jd_start", 2461000.5)),
        duration_s=float(orb_cfg.get("duration_s", 1800.0)),
        dt_s=float(orb_cfg.get("dt_s", 30.0)),
        mirror_area_m2=float(orb_cfg.get("mirror_area_m2", 1e4)),
        reflectivity=float(orb_cfg.get("reflectivity", 0.90)),
        beam_half_angle_deg=float(orb_cfg.get("beam_half_angle_deg", 0.02)),
        atmosphere_rl=float(orb_cfg.get("atmosphere_transmission", 0.85)),
        min_elevation_deg=float(orb_cfg.get("min_elevation_deg", 10.0)),
    )

    return ConceptResults(
        identity_replaced=identity_replaced,
        identity_genuine=identity_genuine,
        sequence_replaced=sequence_replaced,
        sequence_genuine=sequence_genuine,
        ice=ice,
        rescue=rescue,
        structure=structure,
        mirror=mirror,
        seed=seed,
        identity_genuine_z=genuine_z,
        identity_replaced_z=replaced_z,
        identity_shift_sigma=REPLACEMENT_SHIFT_FACTOR * std_threshold,
        sequence_reference=reference,
        sequence_genuine_read=genuine_seq,
        sequence_replaced_read=replaced_seq,
    )
