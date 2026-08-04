"""Manuscript variable hydration tests + live token cross-reference gate."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from die_another_day import manuscript_variables as mv

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
    assert variables["NUM_CONCEPTS"] == "3"
    assert variables["NUM_BIOMARKERS"] == "6"
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
