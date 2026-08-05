"""Manuscript variable hydration tests + live token cross-reference gate."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from die_another_day import manuscript_variables as mv
from die_another_day.mission_results import run_all_concepts

ROOT = Path(__file__).resolve().parents[1]


def test_load_default_config() -> None:
    config = mv.load_manuscript_config()
    assert isinstance(config, dict)
    assert config["paper"]["title"].startswith("Die Another Day")
    assert "concepts" in config


def test_load_missing_config_raises() -> None:
    with pytest.raises(FileNotFoundError):
        mv.load_manuscript_config(ROOT / "manuscript" / "does_not_exist.yaml")


def test_load_non_mapping_config_raises(tmp_path: Path) -> None:
    p = tmp_path / "c.yaml"
    p.write_text("- just\n- a\n- list", encoding="utf-8")
    with pytest.raises(ValueError):
        mv.load_manuscript_config(p)


def test_generate_variables_identity(tmp_path: Path) -> None:
    variables = mv.generate_variables()
    assert variables["MISSION_IDENTITY"] == "die_another_day"
    assert variables["MISSION_CODENAME"] == "ICARUS"
    assert variables["NUM_CONCEPTS"] == "6"
    assert variables["NUM_BIOMARKERS"] == "6"
    assert variables["SEQ_GENOME_LENGTH"] == "1500"
    assert variables["HYP_WATER_TEMP_C"] == "10"
    assert variables["STRUCT_THICKNESS_CM"] == "30"
    assert variables["ICE_ENV_TEMP_C"] == "-34"
    assert variables["ORBIT_SMA_KM"] == "7200"


def test_generate_variables_empty_concepts_gate(tmp_path: Path) -> None:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(yaml.safe_dump({"paper": {"title": "t"}, "concepts": {}}), encoding="utf-8")
    with pytest.raises(ValueError):
        mv.generate_variables(config_path=cfg)
    # --allow-draft equivalent: require_outputs=False proceeds.
    variables = mv.generate_variables(config_path=cfg, require_outputs=False)
    assert variables["MISSION_TITLE"] == "t"


def test_generate_variables_bad_paper(tmp_path: Path) -> None:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(yaml.safe_dump({"paper": [1, 2], "concepts": {"x": 1}}), encoding="utf-8")
    with pytest.raises(ValueError):
        mv.generate_variables(config_path=cfg)


def test_resolve_manuscript_tree(tmp_path: Path) -> None:
    ms = tmp_path / "ms"
    ms.mkdir()
    (ms / "00_abstract.md").write_text("Codename {{MISSION_CODENAME}}", encoding="utf-8")
    (ms / "SYNTAX.md").write_text("{{NOT_A_SECTION_TOKEN}}", encoding="utf-8")
    variables = {"MISSION_CODENAME": "ICARUS"}
    out, resolved = mv.resolve_manuscript_tree(variables, manuscript_dir=ms, output_dir=tmp_path / "out")
    assert resolved == ["00_abstract.md"]
    assert (out / "00_abstract.md").read_text(encoding="utf-8") == "Codename ICARUS"
    assert not (out / "SYNTAX.md").exists()


def test_resolve_manuscript_tree_strict_rejects_unresolved(tmp_path: Path) -> None:
    ms = tmp_path / "ms"
    ms.mkdir()
    (ms / "01_x.md").write_text("{{UNKNOWN_TOKEN}}", encoding="utf-8")
    with pytest.raises(ValueError):
        mv.resolve_manuscript_tree({}, manuscript_dir=ms, output_dir=tmp_path / "out", strict=True)
    # Draft mode writes anyway.
    out, _ = mv.resolve_manuscript_tree({}, manuscript_dir=ms, output_dir=tmp_path / "out", strict=False)
    assert (out / "01_x.md").is_file()


_TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def test_live_cross_reference_all_section_tokens_generated() -> None:
    """Every {{TOKEN}} in manuscript/[0-9]*.md must be produced by generate_variables."""
    variables = mv.generate_variables()
    missing: list[str] = []
    for source in sorted((ROOT / "manuscript").glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token in _TOKEN_RE.findall(text):
            if token not in variables:
                missing.append(f"{source.name}:{token}")
    assert missing == []


def test_measured_tokens_are_the_mission_numbers() -> None:
    """Every measured token must equal the value the concept runner produced."""
    config = mv.load_manuscript_config()
    results = run_all_concepts(config)
    variables = mv.generate_variables()

    assert variables["ID_REPLACED_SCORE"] == f"{results.identity_replaced.score:.2f}"
    assert variables["ID_CHI2_THRESHOLD"] == f"{results.identity_replaced.threshold:.2f}"
    assert variables["ID_GENUINE_SCORE"] == f"{results.identity_genuine.score:.2f}"
    assert variables["SEQ_LONGEST_BLOCK"] == str(results.longest_edit_block)
    assert variables["SEQ_REPLACED_EDIT_DISTANCE"] == str(results.sequence_replaced.edit_distance)
    assert variables["ICE_SAFE_EXPOSURE_S"] == f"{results.ice.safe_exposure_s:.1f}"
    assert variables["ICE_SQUADS"] == str(results.ice.rotation.squad_count)
    assert variables["HYP_MARGIN_S"] == f"{results.rescue.margin_s:.1f}"
    assert variables["STRUCT_SAFETY_FACTOR"] == f"{results.structure.safety_factor:.2f}"
    assert variables["MIRROR_N_FEASIBLE"] == str(results.mirror.n_feasible)
    assert variables["MIRROR_BEST_FLUX_W_M2"] == f"{results.mirror.best_flux_w_m2:.2f}"


def test_measured_tokens_track_the_configuration(tmp_path: Path) -> None:
    """A configuration change must move the measured token, not just the input one.

    This is what stops a measured token from silently freezing into a constant.
    """
    config = mv.load_manuscript_config()
    thicker = dict(config)
    thicker["concepts"] = {
        **config["concepts"],
        "ice_structure": {**config["concepts"]["ice_structure"], "thickness_cm": 60.0},
    }
    cfg_path = tmp_path / "thicker.yaml"
    cfg_path.write_text(yaml.safe_dump(thicker), encoding="utf-8")

    baseline = mv.generate_variables()
    changed = mv.generate_variables(config_path=cfg_path)
    assert changed["STRUCT_THICKNESS_CM"] == "60"
    assert float(changed["STRUCT_CAPACITY_TONS"]) > float(baseline["STRUCT_CAPACITY_TONS"])
    assert float(changed["STRUCT_SAFETY_FACTOR"]) > float(baseline["STRUCT_SAFETY_FACTOR"])


def test_include_measured_false_is_config_only() -> None:
    config_only = mv.generate_variables(include_measured=False)
    assert "NUM_BIOMARKERS" in config_only
    assert "ID_REPLACED_SCORE" not in config_only


def test_every_generated_token_is_used_by_the_manuscript() -> None:
    """No orphan tokens: a generated token nobody cites is dead weight.

    ``PYTHON_VERSION`` / ``GENERATION_TIMESTAMP`` are environment stamps and are
    exempt only if a section actually cites them, which it does.
    """
    variables = mv.generate_variables()
    corpus = "\n".join(
        source.read_text(encoding="utf-8") for source in sorted((ROOT / "manuscript").glob("[0-9][0-9]_*.md"))
    )
    unused = sorted(token for token in variables if "{{" + token + "}}" not in corpus)
    assert unused == [], f"tokens generated but never cited: {unused}"
