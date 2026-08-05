"""Manuscript variable hydration for ICARUS.

Every ``{{TOKEN}}`` in ``manuscript/[0-9]*.md`` resolves through
:func:`generate_variables`. Tokens come in two families and neither is ever
hand-authored in prose:

* **configured inputs** — read straight from ``manuscript/config.yaml``
  (marker count, genome length, ambient temperature, orbital elements, ...);
* **measured outputs** — produced by actually running the six concept models
  through :func:`die_another_day.mission_results.run_all_concepts`, the very
  same entry point :mod:`die_another_day.mission` uses for its
  ``MissionOutcome``. Every measured number in the paper is therefore the
  number the mission computed, not a transcription of it.

The consuming orchestrator is ``scripts/z_generate_manuscript_variables.py``
(thin wrapper); the live cross-reference gate lives in
``tests/test_manuscript_variables.py``.
"""

from __future__ import annotations

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from die_another_day import CODENAME, CONCEPT_MODULES, IDENTITY
from die_another_day.hypothermia import (
    MILD_THRESHOLD_C,
    MODERATE_THRESHOLD_C,
    SEVERE_THRESHOLD_C,
    hypothermia_stage,
)
from die_another_day.mission_results import ConceptResults, run_all_concepts

__all__ = [
    "generate_variables",
    "load_manuscript_config",
    "measured_variables",
    "resolve_manuscript_tree",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

CONCEPT_NAMES = (
    "Biometric Identity-Replacement Detection",
    "DNA Sequence Identity Verification",
    "Ice-Palace Thermal Operations",
    "Cold-Water Hypothermia Risk",
    "Ice-Structure Integrity",
    "Orbital Mirror Targeting",
)


def _num(value: Any) -> str:
    """Format a configured number tersely (int-like as int, else %g)."""
    f = float(value)
    return str(int(f)) if f.is_integer() else f"{f:g}"


def _fixed(value: float, digits: int) -> str:
    """Format a measured number at a fixed number of decimal places."""
    return f"{float(value):.{digits}f}"


def measured_variables(results: ConceptResults) -> dict[str, str]:
    """Turn one deterministic concept run into the manuscript's measured tokens.

    Args:
        results: The output of
            :func:`die_another_day.mission_results.run_all_concepts`.

    Returns:
        A ``{{TOKEN}}`` → formatted-value mapping covering every number the
        results and conclusion sections state.
    """
    replaced = results.identity_replaced
    genuine = results.identity_genuine
    seq_replaced = results.sequence_replaced
    seq_genuine = results.sequence_genuine
    ice = results.ice
    rescue = results.rescue
    structure = results.structure
    mirror = results.mirror
    best_time_s = mirror.points[mirror.best_index].time_s if mirror.best_index is not None else 0.0

    return {
        # --- identity (biometric) -------------------------------------------
        "ID_METHOD": replaced.method,
        "ID_REPLACED_SCORE": _fixed(replaced.score, 2),
        "ID_REPLACED_FLAGGED": str(replaced.n_flagged),
        "ID_CHI2_THRESHOLD": _fixed(replaced.threshold, 2),
        "ID_GENUINE_SCORE": _fixed(genuine.score, 2),
        "ID_GENUINE_P_VALUE": _fixed(genuine.p_value, 3),
        "ID_GENUINE_FLAGGED": str(genuine.n_flagged),
        # --- identity (sequence) --------------------------------------------
        "SEQ_METHOD": seq_replaced.method,
        "SEQ_GENUINE_JACCARD_MEASURED": _fixed(seq_genuine.jaccard, 4),
        "SEQ_GENUINE_HAMMING": str(seq_genuine.hamming),
        "SEQ_GENUINE_LONGEST_RUN": str(results.genuine_longest_run),
        "SEQ_REPLACED_JACCARD_MEASURED": _fixed(seq_replaced.jaccard, 4),
        "SEQ_REPLACED_EDIT_DISTANCE": str(seq_replaced.edit_distance),
        "SEQ_LONGEST_BLOCK": str(results.longest_edit_block),
        # --- ice-palace air operations --------------------------------------
        "ICE_SAFE_EXPOSURE_S": _fixed(ice.safe_exposure_s, 1),
        "ICE_SQUADS": str(ice.rotation.squad_count),
        "ICE_SHIFT_S": _fixed(ice.rotation.shift_duration_s, 1),
        "ICE_THERMAL_LOAD_DEG_S": _fixed(ice.thermal_load_deg_s, 1),
        "ICE_HEATING_ENERGY_MJ": _fixed(ice.heating_energy_j / 1e6, 1),
        # --- cold-water hypothermia -----------------------------------------
        "HYP_MILD_THRESHOLD_C": _num(MILD_THRESHOLD_C),
        "HYP_MODERATE_THRESHOLD_C": _num(MODERATE_THRESHOLD_C),
        "HYP_SEVERE_THRESHOLD_C": _num(SEVERE_THRESHOLD_C),
        "HYP_REACH_TIME_S": _fixed(rescue.reach_time_s, 1),
        "HYP_TIME_TO_SEVERE_S": _fixed(rescue.time_to_severe_s, 1),
        "HYP_MARGIN_S": _fixed(rescue.margin_s, 1),
        "HYP_CORE_AT_REACH_C": _fixed(rescue.core_temp_at_reach_c, 2),
        "HYP_STAGE_AT_REACH": hypothermia_stage(rescue.core_temp_at_reach_c),
        # --- ice-structure integrity ----------------------------------------
        "STRUCT_CAPACITY_TONS": _fixed(structure.capacity_tons, 2),
        "STRUCT_SAFETY_FACTOR": _fixed(structure.safety_factor, 2),
        "STRUCT_THERMAL_STRESS_MPA": _fixed(structure.thermal_stress_mpa, 2),
        "STRUCT_CRITICAL_DELTA_T_C": _fixed(structure.critical_delta_t_c, 2),
        "STRUCT_CRACK_RISK": "yes" if structure.crack_risk else "no",
        # --- orbital-mirror targeting ---------------------------------------
        "MIRROR_PASS_SAMPLES": str(len(mirror.points)),
        "MIRROR_FEASIBLE_S": _fixed(mirror.feasible_seconds, 0),
        "MIRROR_N_FEASIBLE": str(mirror.n_feasible),
        "MIRROR_BEST_TIME_S": _fixed(best_time_s, 0),
        "MIRROR_BEST_FLUX_W_M2": _fixed(mirror.best_flux_w_m2, 2),
        "MISSION_SEED": str(results.seed),
    }


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"manuscript config must be a top-level mapping, got {type(data).__name__}")
    return data


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
    include_measured: bool = True,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), verify the ``concepts`` block is
            present and non-empty — the strict-mode gate.
        include_measured: When True (default), actually run the six concept
            models and merge in the measured-output tokens. Set False only for
            a fast configuration-only inspection; the manuscript itself always
            needs the measured half.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")
    concepts = config.get("concepts", {})
    if require_outputs and not concepts:
        raise ValueError("manuscript config 'concepts' section is empty — nothing to report")
    identity = concepts.get("identity", {})
    sequence = concepts.get("sequence_identity", {})
    ice = concepts.get("ice_ops", {})
    hyp = concepts.get("hypothermia", {})
    structure = concepts.get("ice_structure", {})
    mirror = concepts.get("orbital_mirror", {})

    variables = {
        "MISSION_IDENTITY": IDENTITY,
        "MISSION_CODENAME": CODENAME,
        "MISSION_VERSION": str(paper.get("version", "")),
        "MISSION_TITLE": str(paper.get("title", "")),
        "MISSION_SUBTITLE": str(paper.get("subtitle", "")),
        "NUM_CONCEPTS": str(len(CONCEPT_MODULES)),
        "CONCEPT_MODULES": ", ".join(CONCEPT_MODULES),
        "CONCEPT_NAMES": ", ".join(CONCEPT_NAMES),
        "NUM_BIOMARKERS": _num(identity.get("num_biomarkers", 6)),
        "IDENTITY_ALPHA": _num(identity.get("alpha", 0.001)),
        "IDENTITY_STD_THRESHOLD": _num(identity.get("std_threshold", 3.0)),
        "IDENTITY_MIN_MARKERS": _num(identity.get("min_markers", 2)),
        "SEQ_GENOME_LENGTH": _num(sequence.get("genome_length", 1500)),
        "SEQ_KMER_K": _num(sequence.get("kmer_k", 9)),
        "SEQ_MATCH_JACCARD": _num(sequence.get("match_jaccard", 0.90)),
        "SEQ_CLUSTER_MIN": _num(sequence.get("cluster_min", 12)),
        "ICE_ENV_TEMP_C": _num(ice.get("env_temp_c", -34.0)),
        "ICE_CRITICAL_TEMP_C": _num(ice.get("critical_temp_c", 30.0)),
        "ICE_BODY_TEMP_C": _num(ice.get("body_temp_c", 37.0)),
        "ICE_DECAY_RATE_H": _num(ice.get("decay_rate_h", 0.8)),
        "ICE_NUM_OPERATIVES": _num(ice.get("num_operatives", 4)),
        "ICE_OP_DURATION_S": _num(ice.get("op_duration_s", 1800)),
        "HYP_WATER_TEMP_C": _num(hyp.get("water_temp_c", 10.0)),
        "HYP_MASS_KG": _num(hyp.get("body_mass_kg", 75.0)),
        "HYP_INSULATION": _num(hyp.get("insulation_factor", 0.9)),
        "HYP_DISTANCE_M": _num(hyp.get("distance_m", 400.0)),
        "HYP_SWEEP_SPEED_M_S": _num(hyp.get("sweep_speed_m_s", 2.0)),
        "STRUCT_THICKNESS_CM": _num(structure.get("thickness_cm", 30.0)),
        "STRUCT_LOAD_TONS": _num(structure.get("load_tons", 3.0)),
        "STRUCT_DELTA_T_C": _num(structure.get("delta_t_c", 15.0)),
        "STRUCT_ICE_STRENGTH_MPA": _num(structure.get("ice_strength_mpa", 1.5)),
        "ORBIT_SMA_KM": _num(mirror.get("semi_major_axis_km", 6878.0)),
        "ORBIT_INCLINATION_DEG": _num(mirror.get("inclination_deg", 45.0)),
        "ORBIT_TARGET_LAT_DEG": _num(mirror.get("target_lat_deg", 60.0)),
        "ORBIT_TARGET_LON_DEG": _num(mirror.get("target_lon_deg", 15.0)),
        "ORBIT_DURATION_S": _num(mirror.get("duration_s", 1800.0)),
        "ORBIT_DT_S": _num(mirror.get("dt_s", 30.0)),
        "MIRROR_AREA_M2": _num(mirror.get("mirror_area_m2", 1e4)),
        "MIRROR_REFLECTIVITY": _num(mirror.get("reflectivity", 0.90)),
        "MIRROR_BEAM_HALF_ANGLE_DEG": _num(mirror.get("beam_half_angle_deg", 0.02)),
        "MIRROR_MIN_ELEVATION_DEG": _num(mirror.get("min_elevation_deg", 10.0)),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if include_measured:
        variables.update(measured_variables(run_all_concepts(config)))
    return variables


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each manuscript section to ``output/manuscript/``, substituting tokens.

    Only ``NN_*.md`` section files are copied (not sidecars such as
    ``SYNTAX.md``). In strict mode any leftover ``{{TOKEN}}`` fails the
    resolution so the manuscript can never render with raw braces.

    Returns the output directory and the sorted list of resolved file names.
    """
    manuscript_dir = Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    output_dir = Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
