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
    "CONFIG_INPUT_TOKENS",
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


#: The complete registry of configured inputs: ``(concepts section, config key,
#: manuscript token, coded default)``.
#:
#: This tuple is the *only* place configured-input tokens are declared, and it
#: is what makes §05's "every configured input" billing checkable rather than
#: aspirational. ``test_every_configured_input_is_registered_and_cited`` asserts
#: (a) the set of ``(section, key)`` pairs here is exactly the set present in
#: ``manuscript/config.yaml``, and (b) every token here is cited in
#: ``manuscript/05_experimental_setup.md``. Adding a config key without adding a
#: row, or adding a row without citing it, fails that test.
CONFIG_INPUT_TOKENS: tuple[tuple[str, str, str, Any], ...] = (
    ("identity", "num_biomarkers", "NUM_BIOMARKERS", 6),
    ("identity", "alpha", "IDENTITY_ALPHA", 0.001),
    ("identity", "std_threshold", "IDENTITY_STD_THRESHOLD", 3.0),
    ("identity", "min_markers", "IDENTITY_MIN_MARKERS", 2),
    ("sequence_identity", "genome_length", "SEQ_GENOME_LENGTH", 1500),
    ("sequence_identity", "kmer_k", "SEQ_KMER_K", 9),
    ("sequence_identity", "match_jaccard", "SEQ_MATCH_JACCARD", 0.90),
    ("sequence_identity", "cluster_min", "SEQ_CLUSTER_MIN", 12),
    ("sequence_identity", "scattered_errors", "SEQ_SCATTERED_ERRORS", 5),
    ("ice_ops", "env_temp_c", "ICE_ENV_TEMP_C", -34.0),
    ("ice_ops", "critical_temp_c", "ICE_CRITICAL_TEMP_C", 30.0),
    ("ice_ops", "body_temp_c", "ICE_BODY_TEMP_C", 37.0),
    ("ice_ops", "decay_rate_h", "ICE_DECAY_RATE_H", 0.8),
    ("ice_ops", "num_operatives", "ICE_NUM_OPERATIVES", 4),
    ("ice_ops", "op_duration_s", "ICE_OP_DURATION_S", 1800),
    ("ice_ops", "thermal_conductance", "ICE_THERMAL_CONDUCTANCE_W_K", 1500.0),
    ("hypothermia", "water_temp_c", "HYP_WATER_TEMP_C", 10.0),
    ("hypothermia", "body_mass_kg", "HYP_MASS_KG", 75.0),
    ("hypothermia", "insulation_factor", "HYP_INSULATION", 0.9),
    ("hypothermia", "distance_m", "HYP_DISTANCE_M", 400.0),
    ("hypothermia", "sweep_speed_m_s", "HYP_SWEEP_SPEED_M_S", 2.0),
    ("ice_structure", "thickness_cm", "STRUCT_THICKNESS_CM", 30.0),
    ("ice_structure", "load_tons", "STRUCT_LOAD_TONS", 3.0),
    ("ice_structure", "delta_t_c", "STRUCT_DELTA_T_C", 15.0),
    ("ice_structure", "ice_strength_mpa", "STRUCT_ICE_STRENGTH_MPA", 1.5),
    ("orbital_mirror", "semi_major_axis_km", "ORBIT_SMA_KM", 6878.0),
    ("orbital_mirror", "inclination_deg", "ORBIT_INCLINATION_DEG", 45.0),
    ("orbital_mirror", "raan_deg", "ORBIT_RAAN_DEG", 120.0),
    ("orbital_mirror", "mean_anomaly_deg", "ORBIT_MEAN_ANOMALY_DEG", 30.0),
    ("orbital_mirror", "jd_start", "ORBIT_JD_START", 2461000.5),
    ("orbital_mirror", "target_lat_deg", "ORBIT_TARGET_LAT_DEG", 60.0),
    ("orbital_mirror", "target_lon_deg", "ORBIT_TARGET_LON_DEG", 15.0),
    ("orbital_mirror", "duration_s", "ORBIT_DURATION_S", 1800.0),
    ("orbital_mirror", "dt_s", "ORBIT_DT_S", 30.0),
    ("orbital_mirror", "mirror_area_m2", "MIRROR_AREA_M2", 1e4),
    ("orbital_mirror", "reflectivity", "MIRROR_REFLECTIVITY", 0.90),
    ("orbital_mirror", "beam_half_angle_deg", "MIRROR_BEAM_HALF_ANGLE_DEG", 0.02),
    ("orbital_mirror", "atmosphere_transmission", "MIRROR_ATMOSPHERE_TRANSMISSION", 0.85),
    ("orbital_mirror", "min_elevation_deg", "MIRROR_MIN_ELEVATION_DEG", 10.0),
)


def _num(value: Any) -> str:
    """Format a configured number tersely (int-like as int, else 10 sig figs).

    Ten significant figures rather than ``%g``'s six so that a Julian date
    (``2461300.5``) renders in full instead of collapsing to ``2.4613e+06``.
    """
    f = float(value)
    return str(int(f)) if f.is_integer() else f"{f:.10g}"


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
        # Construction parameter of the positive control, not an outcome: the
        # sigma magnitude of the coherent shift applied to its leading markers.
        "ID_REPLACED_SHIFT_SIGMA": _num(results.identity_shift_sigma),
        # --- identity (sequence) --------------------------------------------
        "SEQ_METHOD": seq_replaced.method,
        "SEQ_GENUINE_JACCARD_MEASURED": _fixed(seq_genuine.jaccard, 4),
        "SEQ_GENUINE_HAMMING": str(seq_genuine.hamming),
        "SEQ_GENUINE_EDIT_DISTANCE": str(seq_genuine.edit_distance),
        "SEQ_GENUINE_LONGEST_RUN": str(results.genuine_longest_run),
        "SEQ_REPLACED_JACCARD_MEASURED": _fixed(seq_replaced.jaccard, 4),
        "SEQ_REPLACED_HAMMING": str(seq_replaced.hamming),
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

    variables = {
        "MISSION_IDENTITY": IDENTITY,
        "MISSION_CODENAME": CODENAME,
        "MISSION_VERSION": str(paper.get("version", "")),
        "MISSION_TITLE": str(paper.get("title", "")),
        "MISSION_SUBTITLE": str(paper.get("subtitle", "")),
        "NUM_CONCEPTS": str(len(CONCEPT_MODULES)),
        "CONCEPT_MODULES": ", ".join(CONCEPT_MODULES),
        "CONCEPT_NAMES": ", ".join(CONCEPT_NAMES),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    for section, key, token, default in CONFIG_INPUT_TOKENS:
        block = concepts.get(section, {}) if isinstance(concepts, dict) else {}
        block = block if isinstance(block, dict) else {}
        variables[token] = _num(block.get(key, default))
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
