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
from die_another_day.mission_results import MISSION_SEED as _MISSION_SEED
from die_another_day.mission_results import run_all_concepts

__all__ = ["MissionProvider"]

#: Package version stamped into provenance (kept in step with ``pyproject.toml``).
_PACKAGE_VERSION = "0.1.0"
_FILM = "die_another_day"
_CODENAME = "ICARUS"


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
        """Run the plan against the deterministic domain core and report results.

        All six concept models run through
        :func:`die_another_day.mission_results.run_all_concepts`, the same
        entry point the manuscript variables use, so the outcome reported here
        and the numbers printed in the paper cannot diverge.
        """
        concept_results = run_all_concepts(self._config, seed=_MISSION_SEED)
        replaced = concept_results.identity_replaced
        genuine = concept_results.identity_genuine
        seq_replaced = concept_results.sequence_replaced
        seq_genuine = concept_results.sequence_genuine
        ice = concept_results.ice
        rescue = concept_results.rescue
        structure = concept_results.structure
        pass_plan = concept_results.mirror

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
                "longest_cluster": concept_results.longest_edit_block,
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
