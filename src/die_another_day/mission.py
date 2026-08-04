"""ICARUS — the ``MissionProvider`` adapter between BOND-API and the domain core.

*Die Another Day* (2002), mission codename ICARUS. This is the thin adapter that
implements the frozen :class:`bond_api.protocol.MissionProvider` contract. It
keeps all real science in the pure domain modules
(:mod:`~die_another_day.identity_detection`,
:mod:`~die_another_day.sequence_identity`, :mod:`~die_another_day.ice_ops`,
:mod:`~die_another_day.hypothermia`, :mod:`~die_another_day.ice_structure`,
:mod:`~die_another_day.orbital_mirror`) and here only wires their outputs into
the protocol's five lifecycle stages (brief / recon / plan / execute / debrief).

The domain modules are importable without ``bond_api``; this module is the only
place the protocol is imported, and it registers the mission's gadgets with the
BOND-API :class:`bond_api.registry.GadgetRegistry`. Discovery loads this module
as ``die_another_day.mission`` on ``sys.path`` and binds the top-level
``MissionProvider`` class (see :mod:`bond_api.discovery`).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

from die_another_day import (
    hypothermia,
    ice_ops,
    ice_structure,
    identity_detection,
    orbital_mirror,
    sequence_identity,
)
from die_another_day.manuscript_variables import load_manuscript_config

__all__ = ["MissionProvider"]

#: Package version stamped into provenance (kept in step with ``pyproject.toml``).
_PACKAGE_VERSION = "0.1.0"
_FILM = "die_another_day"
_CODENAME = "ICARUS"

#: Deterministic seed for all synthetic data this provider generates.
_MISSION_SEED = 7


def _replacement_probe(profile: identity_detection.BiometricProfile, seed: int, cfg: dict) -> np.ndarray:
    """Deterministically synthesize a gene-therapy-grade replaced operative.

    Shifts the first ``min_markers`` markers by ``1.5 * std_threshold``
    standard deviations (a coherent, multi-marker drift) plus small noise.
    """
    rng = np.random.default_rng(seed)
    std_threshold = float(cfg.get("std_threshold", 3.0))
    shift = 1.5 * std_threshold
    probe = profile.mean.copy()
    n_shift = min(int(cfg.get("min_markers", 2)), profile.marker_count)
    probe[:n_shift] = probe[:n_shift] + shift * profile.per_marker_std[:n_shift]
    return probe + 0.1 * rng.standard_normal(profile.marker_count)


class MissionProvider:  # noqa: N801 — class name is fixed by the discovery contract
    """Deterministic ICARUS mission provider implementing the BOND-API protocol.

    ``execute`` runs all six concepts on real, deterministic data and returns
    the measured outcomes — replacement verdicts (biometric and sequence), the
    ice-palace operations and structure plan, the cold-water rescue plan, and
    the orbital-mirror pass analysis — in the outcome ``results``.
    """

    film = _FILM

    def __init__(self) -> None:
        self._config = load_manuscript_config()

    def brief(self) -> MissionBrief:
        """Declare the ICARUS mission: three theatres, deterministic execution."""
        return MissionBrief(
            film=self.film,
            codename=_CODENAME,
            objectives=(
                "detect gene-therapy-grade identity replacement",
                "plan ice-palace cold-environment operations",
                "verify orbital-mirror (ICARUS) targeting geometry",
            ),
            assets=(
                Asset(
                    kind="software",
                    name="icarus-suite",
                    payload={
                        "concepts": [
                            "identity_detection",
                            "sequence_identity",
                            "ice_ops",
                            "hypothermia",
                            "ice_structure",
                            "orbital_mirror",
                        ],
                        "seed": _MISSION_SEED,
                        "version": _PACKAGE_VERSION,
                    },
                ),
            ),
            constraints=(Constraint(kind="determinism", detail="fixed seed, no wall-clock, no external calls"),),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request plus the available concept assets and constraints."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(label="concepts", detail="6 mission concepts available to execute"),
                Finding(
                    label="models",
                    detail="drift screen, sequence screen, thermal ops, rescue plan, structure plan, mirror pass",
                ),
                Finding(label="assets", detail="icarus-suite software payload enrolled"),
                Finding(label="constraints", detail="deterministic execution required"),
                Finding(label="gadgets", detail="6 concept functions registered with the BOND-API GadgetRegistry"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the six deterministic execution steps, one per concept."""
        return MissionPlan(
            steps=(
                Step(name="identity", action="detect_replacement", params={"objective": brief.objectives[0]}),
                Step(name="sequence", action="verify_sequence", params={"objective": brief.objectives[0]}),
                Step(name="ice_ops", action="plan_operations", params={"objective": brief.objectives[1]}),
                Step(name="hypothermia", action="plan_rescue", params={"objective": brief.objectives[1]}),
                Step(name="structure", action="assess_integrity", params={"objective": brief.objectives[1]}),
                Step(name="orbital", action="target_orbit", params={"objective": brief.objectives[2]}),
                Step(name="verify", action="compile_outcome", params={"success": True}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the plan against the deterministic domain core and report results."""
        concepts = self._config.get("concepts", {})
        id_cfg = concepts.get("identity", {})
        seq_cfg = concepts.get("sequence_identity", {})
        ice_cfg = concepts.get("ice_ops", {})
        hyp_cfg = concepts.get("hypothermia", {})
        struct_cfg = concepts.get("ice_structure", {})
        orb_cfg = concepts.get("orbital_mirror", {})

        # --- Concept 1: biometric identity-replacement detection -----------
        marker_count = int(id_cfg.get("num_biomarkers", 6))
        baseline = identity_detection.generate_identity_samples(
            rng_seed=_MISSION_SEED,
            n_samples=200,
            marker_count=marker_count,
        )
        profile = identity_detection.estimate_profile(baseline)
        replaced = identity_detection.detect_drift(
            profile,
            _replacement_probe(profile, _MISSION_SEED, id_cfg),
            alpha=float(id_cfg.get("alpha", 1e-3)),
            std_threshold=float(id_cfg.get("std_threshold", 3.0)),
            min_markers=int(id_cfg.get("min_markers", 2)),
        )
        genuine = identity_detection.detect_drift(
            profile,
            profile.mean,
            alpha=float(id_cfg.get("alpha", 1e-3)),
            std_threshold=float(id_cfg.get("std_threshold", 3.0)),
            min_markers=int(id_cfg.get("min_markers", 2)),
        )

        # --- Concept 2: DNA sequence identity verification -----------------
        genome_length = int(seq_cfg.get("genome_length", 1500))
        reference = sequence_identity.generate_genome(genome_length, seed=_MISSION_SEED)
        scattered = int(seq_cfg.get("scattered_errors", 5))
        cluster_len = int(seq_cfg.get("cluster_min", 12))
        genuine_seq = sequence_identity.mutate_genome(reference, seed=_MISSION_SEED, n_substitutions=scattered)
        replaced_seq = sequence_identity.mutate_genome(
            reference,
            seed=_MISSION_SEED,
            n_substitutions=scattered,
            cluster_length=cluster_len,
        )
        seq_genuine = sequence_identity.verify_identity(
            reference,
            genuine_seq,
            k=int(seq_cfg.get("kmer_k", 9)),
            match_jaccard=float(seq_cfg.get("match_jaccard", 0.90)),
            cluster_min=cluster_len,
        )
        seq_replaced = sequence_identity.verify_identity(
            reference,
            replaced_seq,
            k=int(seq_cfg.get("kmer_k", 9)),
            match_jaccard=float(seq_cfg.get("match_jaccard", 0.90)),
            cluster_min=cluster_len,
        )

        # --- Concept 3: ice-palace air operations ---------------------------
        decay_rate = float(ice_cfg.get("decay_rate_h", 0.8)) / 3600.0
        ice = ice_ops.plan_briefing(
            env_temp_c=float(ice_cfg.get("env_temp_c", -34.0)),
            body_temp_c=float(ice_cfg.get("body_temp_c", 37.0)),
            critical_temp_c=float(ice_cfg.get("critical_temp_c", 30.0)),
            decay_rate=decay_rate,
            num_operatives=int(ice_cfg.get("num_operatives", 4)),
            op_duration_s=float(ice_cfg.get("op_duration_s", 1800)),
            thermal_conductance=float(ice_cfg.get("thermal_conductance", 1500.0)),
        )

        # --- Concept 4: cold-water hypothermia / rescue ---------------------
        rescue = hypothermia.plan_cold_water_rescue(
            water_c=float(hyp_cfg.get("water_temp_c", 10.0)),
            mass_kg=float(hyp_cfg.get("body_mass_kg", 75.0)),
            insulation_factor=float(hyp_cfg.get("insulation_factor", 0.9)),
            distance_m=float(hyp_cfg.get("distance_m", 400.0)),
            sweep_speed_m_s=float(hyp_cfg.get("sweep_speed_m_s", 2.0)),
        )

        # --- Concept 5: ice-palace structural integrity ---------------------
        structure = ice_structure.ice_structure_plan(
            thickness_cm=float(struct_cfg.get("thickness_cm", 30.0)),
            load_tons=float(struct_cfg.get("load_tons", 3.0)),
            delta_t_c=float(struct_cfg.get("delta_t_c", 15.0)),
            ice_strength_mpa=float(struct_cfg.get("ice_strength_mpa", 1.5)),
        )

        # --- Concept 6: orbital-mirror targeting ----------------------------
        pass_plan = orbital_mirror.plan_pass(
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
            min_elevation_deg=float(orb_cfg.get("min_elevation_deg", 10.0)),
        )

        results: dict[str, Any] = {
            "steps_completed": len(plan.steps),
            "outputs": tuple(step.name for step in plan.steps),
            "identity": {
                "replacement_detected": replaced.replaced,
                "genuine_cleared": not genuine.replaced,
                "score": replaced.score,
                "threshold": replaced.threshold,
                "p_value": replaced.p_value,
                "n_flagged": replaced.n_flagged,
                "method": replaced.method,
            },
            "sequence": {
                "genuine_matched": seq_genuine.matched,
                "replacement_suspected": seq_replaced.replacement_suspected,
                "genuine_jaccard": seq_genuine.jaccard,
                "replaced_jaccard": seq_replaced.jaccard,
                "edit_distance": seq_replaced.edit_distance,
                "longest_cluster": max((c[1] - c[0] for c in seq_replaced.clusters), default=0),
                "genome_length": seq_replaced.genome_length,
                "method": seq_replaced.method,
            },
            "ice_ops": {
                "safe_exposure_s": ice.safe_exposure_s,
                "squads": ice.rotation.squad_count,
                "rotation_feasible": ice.rotation.feasible,
                "thermal_load_deg_s": ice.thermal_load_deg_s,
                "heating_energy_j": ice.heating_energy_j,
            },
            "hypothermia": {
                "feasible": rescue.feasible,
                "reach_time_s": rescue.reach_time_s,
                "time_to_severe_s": rescue.time_to_severe_s,
                "margin_s": rescue.margin_s,
                "core_temp_at_reach_c": rescue.core_temp_at_reach_c,
                "stage": hypothermia.hypothermia_stage(rescue.core_temp_at_reach_c),
            },
            "ice_structure": {
                "capacity_tons": structure.capacity_tons,
                "safety_factor": structure.safety_factor,
                "load_ok": structure.load_ok,
                "thermal_stress_mpa": structure.thermal_stress_mpa,
                "crack_risk": structure.crack_risk,
                "structurally_safe": structure.structurally_safe,
                "recommended_thickness_cm": structure.recommended_thickness_cm,
            },
            "orbital_mirror": {
                "feasible_seconds": pass_plan.feasible_seconds,
                "n_feasible": pass_plan.n_feasible,
                "best_index": pass_plan.best_index,
                "best_flux_w_m2": pass_plan.best_flux_w_m2,
            },
            "seed": _MISSION_SEED,
        }

        success = (
            results["identity"]["replacement_detected"]
            and results["identity"]["genuine_cleared"]
            and results["sequence"]["replacement_suspected"]
            and results["sequence"]["genuine_matched"]
            and results["ice_ops"]["rotation_feasible"]
            and results["hypothermia"]["feasible"]
            and results["orbital_mirror"]["feasible_seconds"] > 0.0
        )
        return MissionOutcome(
            success=success,
            results=results,
            provenance=Provenance(
                package_version=_PACKAGE_VERSION,
                seed=_MISSION_SEED,
                input_hash="icarus-config-v1",
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record the standing lessons learned."""
        identity = outcome.results["identity"]
        sequence = outcome.results["sequence"]
        ice = outcome.results["ice_ops"]
        rescue = outcome.results["hypothermia"]
        structure = outcome.results["ice_structure"]
        mirror = outcome.results["orbital_mirror"]
        return Debrief(
            outcome=outcome,
            lessons=(
                f"a {identity['method']} drift flagged a coherent replacement probe "
                f"(score {identity['score']:.2f} vs threshold {identity['threshold']:.2f})",
                f"a {sequence['longest_cluster']}-base contiguous edit block is the "
                f"sequence-level substitution signature (method {sequence['method']})",
                f"ice-palace ops sustain {ice['squads']} rotating squads under a "
                f"{ice['safe_exposure_s']:.0f}s exposure ceiling",
                f"cold-water rescue reaches the operative in {rescue['reach_time_s']:.0f}s, "
                f"{rescue['margin_s']:.0f}s before the severe stage ({rescue['stage']} at reach)",
                f"the palace ice carries {structure['capacity_tons']:.2f}t but a "
                f"{structure['thermal_stress_mpa']:.1f} MPa thermal gradient "
                f"{'risks' if structure['crack_risk'] else 'stays below'} the cracking threshold",
                f"ICARUS mirror holds {mirror['feasible_seconds']:.0f}s of feasible "
                f"targeting with peak flux {mirror['best_flux_w_m2']:.2e} W/m^2",
            ),
        )


#: Gadgets this film registers with the BOND-API ``GadgetRegistry``.
ICARUS_GADGETS = GadgetRegistry()
ICARUS_GADGETS.register(
    _FILM,
    {
        "identity_detection": identity_detection.detect_drift,
        "sequence_identity": sequence_identity.verify_identity,
        "ice_ops": ice_ops.plan_briefing,
        "hypothermia": hypothermia.plan_cold_water_rescue,
        "ice_structure": ice_structure.ice_structure_plan,
        "orbital_mirror": orbital_mirror.plan_pass,
    },
)
