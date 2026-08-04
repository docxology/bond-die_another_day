"""Manuscript variable hydration for ICARUS.

Every ``{{TOKEN}}`` in ``manuscript/[0-9]*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
frozen protocol identity. Metrics are never hand-authored in prose — they flow
through this module so the manuscript cannot drift from the code or the
configured mission parameters.

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

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

CONCEPT_NAMES = (
    "Biometric Identity-Replacement Detection",
    "Ice-Palace Thermal Operations",
    "Orbital Mirror Targeting",
)


def _num(value: Any) -> str:
    """Format a configured number tersely (int-like as int, else %g)."""
    f = float(value)
    return str(int(f)) if f.is_integer() else f"{f:g}"


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
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), verify the ``concepts`` block is
            present and non-empty — the strict-mode gate.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")
    concepts = config.get("concepts", {})
    if require_outputs and not concepts:
        raise ValueError("manuscript config 'concepts' section is empty — nothing to report")
    identity = concepts.get("identity", {})
    ice = concepts.get("ice_ops", {})
    mirror = concepts.get("orbital_mirror", {})

    return {
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
        "ICE_ENV_TEMP_C": _num(ice.get("env_temp_c", -34.0)),
        "ICE_CRITICAL_TEMP_C": _num(ice.get("critical_temp_c", 30.0)),
        "ICE_BODY_TEMP_C": _num(ice.get("body_temp_c", 37.0)),
        "ICE_DECAY_RATE_H": _num(ice.get("decay_rate_h", 0.8)),
        "ICE_NUM_OPERATIVES": _num(ice.get("num_operatives", 4)),
        "ICE_OP_DURATION_S": _num(ice.get("op_duration_s", 5400)),
        "ORBIT_SMA_KM": _num(mirror.get("semi_major_axis_km", 6878.0)),
        "ORBIT_INCLINATION_DEG": _num(mirror.get("inclination_deg", 45.0)),
        "MIRROR_AREA_M2": _num(mirror.get("mirror_area_m2", 1e4)),
        "MIRROR_REFLECTIVITY": _num(mirror.get("reflectivity", 0.90)),
        "MIRROR_BEAM_HALF_ANGLE_DEG": _num(mirror.get("beam_half_angle_deg", 0.02)),
        "MIRROR_MIN_ELEVATION_DEG": _num(mirror.get("min_elevation_deg", 10.0)),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


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
