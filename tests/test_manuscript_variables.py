"""Manuscript variable hydration tests + live token cross-reference gate."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from die_another_day import manuscript_variables as mv
from die_another_day import mission_results as mr
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
    assert variables["SEQ_REPLACED_HAMMING"] == str(results.sequence_replaced.hamming)
    assert variables["SEQ_GENUINE_EDIT_DISTANCE"] == str(results.sequence_genuine.edit_distance)
    assert variables["SEQ_GENUINE_HAMMING"] == str(results.sequence_genuine.hamming)
    assert variables["ICE_SAFE_EXPOSURE_S"] == f"{results.ice.safe_exposure_s:.1f}"
    assert variables["ICE_SQUADS"] == str(results.ice.rotation.squad_count)
    assert variables["HYP_MARGIN_S"] == f"{results.rescue.margin_s:.1f}"
    assert variables["STRUCT_SAFETY_FACTOR"] == f"{results.structure.safety_factor:.2f}"
    assert variables["MIRROR_N_FEASIBLE"] == str(results.mirror.n_feasible)
    assert variables["MIRROR_BEST_FLUX_W_M2"] == f"{results.mirror.best_flux_w_m2:.2f}"
    assert variables["ICE_ROTATION_FEASIBLE"] == ("yes" if results.ice.rotation.feasible else "no")


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


def test_hamming_and_edit_distance_tokens_are_not_interchangeable() -> None:
    """The two statistics must be reported by their own tokens.

    The genuine row happens to have Hamming == edit distance; the replaced row
    proves they are different quantities. Printing the Hamming token under an
    "edit distance" heading was only invisible because of that coincidence.
    """
    variables = mv.generate_variables()
    assert variables["SEQ_GENUINE_HAMMING"] == variables["SEQ_GENUINE_EDIT_DISTANCE"]
    assert variables["SEQ_REPLACED_HAMMING"] != variables["SEQ_REPLACED_EDIT_DISTANCE"]


def test_shift_sigma_token_is_the_probe_magnitude_not_the_threshold() -> None:
    """§03 must cite the probe's real shift, which is not the flagging bar."""
    variables = mv.generate_variables()
    threshold = float(variables["IDENTITY_STD_THRESHOLD"])
    shift = float(variables["ID_REPLACED_SHIFT_SIGMA"])
    assert shift == pytest.approx(mr.REPLACEMENT_SHIFT_FACTOR * threshold)
    assert shift != threshold
    results_text = (ROOT / "manuscript" / "03_results.md").read_text(encoding="utf-8")
    assert "{{ID_REPLACED_SHIFT_SIGMA}}-sigma shift" in results_text


def test_include_measured_false_is_config_only() -> None:
    config_only = mv.generate_variables(include_measured=False)
    assert "NUM_BIOMARKERS" in config_only
    assert "ID_REPLACED_SCORE" not in config_only


def test_every_configured_input_is_registered_and_cited() -> None:
    """§05's "every configured input" billing must be true of the file on disk.

    Two directions, both able to fail:

    * every ``concepts.<section>.<key>`` in ``config.yaml`` appears in
      ``CONFIG_INPUT_TOKENS`` (adding a config key without registering it —
      how ``raan_deg``, ``mean_anomaly_deg``, ``jd_start``,
      ``thermal_conductance`` and ``scattered_errors`` went unlisted — fails);
    * every registered token is cited in ``05_experimental_setup.md``
      (registering without documenting fails).
    """
    config = mv.load_manuscript_config()
    on_disk = {(section, key) for section, block in config["concepts"].items() for key in block}
    registered = {(section, key) for section, key, _, _ in mv.CONFIG_INPUT_TOKENS}
    assert on_disk == registered, f"unregistered: {sorted(on_disk - registered)}; stale: {sorted(registered - on_disk)}"

    setup = (ROOT / "manuscript" / "05_experimental_setup.md").read_text(encoding="utf-8")
    uncited = [token for _, _, token, _ in mv.CONFIG_INPUT_TOKENS if "{{" + token + "}}" not in setup]
    assert uncited == [], f"configured inputs never listed in §05: {uncited}"


def test_no_configuration_seed_can_diverge_from_the_reported_one() -> None:
    """``config.yaml`` must carry no seed key of its own.

    Per-concept ``seed:`` keys used to sit in the config: three were read by
    nothing, and two were read only by the figure script, which is how the
    published figures came to be able to drift away from the reported run. The
    seed is ``mission_results.MISSION_SEED`` and nothing else.
    """
    config = mv.load_manuscript_config()
    stray = [f"{section}.{key}" for section, block in config["concepts"].items() for key in block if "seed" in key]
    assert stray == [], f"config seed keys can diverge from MISSION_SEED: {stray}"


def test_atmospheric_transmission_is_consumed_not_just_declared() -> None:
    """Halving the transmission factor must halve the reported flux."""
    config = mv.load_manuscript_config()
    baseline = run_all_concepts(config)
    dimmed = {
        **config,
        "concepts": {
            **config["concepts"],
            "orbital_mirror": {**config["concepts"]["orbital_mirror"], "atmosphere_transmission": 0.425},
        },
    }
    changed = run_all_concepts(dimmed)
    assert changed.mirror.best_flux_w_m2 == pytest.approx(baseline.mirror.best_flux_w_m2 / 2.0, rel=1e-9)


def test_every_generated_token_is_used_by_the_manuscript() -> None:
    """No orphan tokens: a generated token nobody cites is dead weight.

    ``PYTHON_VERSION`` is an environment stamp and is exempt only if a section
    actually cites it, which §05 and §06 do.
    """
    variables = mv.generate_variables()
    corpus = "\n".join(
        source.read_text(encoding="utf-8") for source in sorted((ROOT / "manuscript").glob("[0-9][0-9]_*.md"))
    )
    unused = sorted(token for token in variables if "{{" + token + "}}" not in corpus)
    assert unused == [], f"tokens generated but never cited: {unused}"
