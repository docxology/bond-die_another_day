"""Smoke tests: thin orchestrator scripts run end-to-end (subprocess, real run)."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from die_another_day import manuscript_variables as mv
from die_another_day.figures import (
    hypothermia_window_s,
    render_hypothermia_curve,
    render_identity_drift,
    render_pass_profile,
    render_sequence_mismatches,
)
from die_another_day.mission_results import run_all_concepts

ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def test_preflight_reports_identity() -> None:
    result = _run("scripts/00_preflight.py")
    assert result.returncode == 0, result.stderr
    assert "die_another_day" in result.stdout
    assert "ICARUS" in result.stdout
    assert "orbital_mirror" in result.stdout


def test_run_mission_succeeds() -> None:
    result = _run("scripts/run_mission.py")
    assert result.returncode == 0, result.stderr
    assert "Film: die_another_day (ICARUS)" in result.stdout
    assert "Outcome success: True" in result.stdout
    assert "Outcome JSON:" in result.stdout


def test_run_mission_outcome_json() -> None:
    result = _run("scripts/run_mission.py")
    block = result.stdout.split("Outcome JSON:\n", 1)[1]
    outcome = json.loads(block)
    assert outcome["__bond_type__"] == "MissionOutcome"
    assert outcome["success"] is True
    assert outcome["provenance"]["seed"] == 7


@pytest.mark.parametrize(
    "script,marker",
    [
        ("brief.py", "Objectives:"),
        ("recon.py", "Recon findings"),
        ("plan.py", "Plan steps"),
        ("execute.py", "Outcome success: True"),
        ("debrief.py", "Lessons"),
    ],
)
def test_phase_clis(script: str, marker: str) -> None:
    result = _run(f"scripts/{script}")
    assert result.returncode == 0, result.stderr
    assert marker in result.stdout


def test_generate_manuscript_variables_writes_artifacts(tmp_path: Path) -> None:
    result = _run("scripts/z_generate_manuscript_variables.py", "--output-dir", str(tmp_path / "out"))
    assert result.returncode == 0, result.stderr
    variables_path = tmp_path / "out" / "data" / "manuscript_variables.json"
    assert variables_path.is_file()
    variables = json.loads(variables_path.read_text(encoding="utf-8"))
    assert variables["MISSION_CODENAME"] == "ICARUS"
    abstract = tmp_path / "out" / "manuscript" / "00_abstract.md"
    text = abstract.read_text(encoding="utf-8")
    assert "{{" not in text
    assert "ICARUS" in text


def test_regeneration_is_byte_identical(tmp_path: Path) -> None:
    """§06's byte-identical regeneration claim, run against the real generator.

    Two full runs of the production entry point into two output roots, compared
    file-by-file on raw bytes. Nothing is injected: the script reads the same
    clock it would read in anger.

    The ``sleep`` is deliberate, not overhead. The defect this gate exists to
    catch was a ``GENERATION_TIMESTAMP`` hydrated from
    ``datetime.now(...).isoformat(timespec="seconds")`` and rendered into §05
    and the variables JSON. A second-resolution stamp only differs across two
    runs that straddle a second boundary. Without the sleep the crossing is
    incidental — it happens today only because each subprocess costs more than
    a second to start and compute, which is a property of this machine, not of
    the test. Sleeping strictly longer than one second makes the crossing
    guaranteed on any machine, so a second-resolution stamp must differ; a
    finer-resolution stamp differs regardless.

    Verified failable: reinstating the ``GENERATION_TIMESTAMP`` token turns
    this test red on both ``data/manuscript_variables.json`` and
    ``manuscript/05_experimental_setup.md``.
    """
    first = tmp_path / "first"
    second = tmp_path / "second"

    result = _run("scripts/z_generate_manuscript_variables.py", "--output-dir", str(first))
    assert result.returncode == 0, result.stderr
    time.sleep(1.05)
    result = _run("scripts/z_generate_manuscript_variables.py", "--output-dir", str(second))
    assert result.returncode == 0, result.stderr

    def _tree(root: Path) -> dict[str, bytes]:
        return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}

    left, right = _tree(first), _tree(second)
    assert sorted(left) == sorted(right), "the two runs wrote different file sets"
    assert left, "the generator wrote no files — the comparison would be vacuous"
    assert "data/manuscript_variables.json" in left
    assert "manuscript/05_experimental_setup.md" in left

    differing = sorted(name for name in left if left[name] != right[name])
    assert differing == [], f"regeneration is not byte-identical; wall-clock or other nondeterminism in: {differing}"


def test_generate_manuscript_variables_strict_rejects_unresolved(tmp_path: Path) -> None:
    ms = tmp_path / "ms"
    ms.mkdir()
    (ms / "00_abstract.md").write_text("{{MISSION_CODENAME}} {{UNKNOWN}}", encoding="utf-8")
    result = _run(
        "scripts/z_generate_manuscript_variables.py",
        "--manuscript-dir",
        str(ms),
        "--output-dir",
        str(tmp_path / "out"),
    )
    assert result.returncode != 0
    assert "unresolved manuscript tokens" in result.stderr


def test_generate_figures_writes_pngs() -> None:
    result = _run("scripts/generate_figures.py")
    assert result.returncode == 0, result.stderr
    for name in (
        "icarus_pass_profile.png",
        "icarus_identity_drift.png",
        "icarus_hypothermia_curve.png",
        "icarus_sequence_mismatch.png",
    ):
        assert (ROOT / "output" / "figures" / name).is_file(), name


def test_published_figures_depict_the_reported_run(tmp_path: Path) -> None:
    """The PNGs on disk must be renders of the runner's own arrays.

    This is the gate that catches a figure script rebuilding its own probes.
    The published identity-drift figure once plotted a *different* experiment
    from the results table it illustrates (a genuine probe of ``profile.mean``,
    all-zero and invisible) and no test noticed, because the figure tests
    checked only that a file existed. Renders are byte-reproducible, so
    comparing bytes against an independent render from
    ``run_all_concepts`` is exact: change either the script's probes or the
    runner's and this fails.
    """
    result = _run("scripts/generate_figures.py")
    assert result.returncode == 0, result.stderr

    config = mv.load_manuscript_config()
    results = run_all_concepts(config)
    expected_drift = render_identity_drift(
        results.identity_genuine_z,
        results.identity_replaced_z,
        results.identity_replaced,
        tmp_path / "drift.png",
        std_threshold=float(config["concepts"]["identity"]["std_threshold"]),
    )
    expected_seq = render_sequence_mismatches(
        results.sequence_reference,
        results.sequence_replaced_read,
        tmp_path / "seq.png",
    )
    expected_pass = render_pass_profile(results.mirror, tmp_path / "pass.png")
    hyp_cfg = config["concepts"]["hypothermia"]
    expected_hyp = render_hypothermia_curve(
        float(hyp_cfg["water_temp_c"]),
        float(hyp_cfg["body_mass_kg"]),
        float(hyp_cfg["insulation_factor"]),
        hypothermia_window_s(
            float(hyp_cfg["water_temp_c"]), float(hyp_cfg["body_mass_kg"]), float(hyp_cfg["insulation_factor"])
        ),
        tmp_path / "hyp.png",
    )

    figures = ROOT / "output" / "figures"
    assert (figures / "icarus_identity_drift.png").read_bytes() == expected_drift.read_bytes()
    assert (figures / "icarus_sequence_mismatch.png").read_bytes() == expected_seq.read_bytes()
    assert (figures / "icarus_pass_profile.png").read_bytes() == expected_pass.read_bytes()
    assert (figures / "icarus_hypothermia_curve.png").read_bytes() == expected_hyp.read_bytes()


SCRIPTS = [
    "00_preflight.py",
    "run_mission.py",
    "brief.py",
    "recon.py",
    "plan.py",
    "execute.py",
    "debrief.py",
    "generate_figures.py",
    "z_generate_manuscript_variables.py",
]


@pytest.mark.parametrize("script", SCRIPTS)
def test_scripts_are_thin_orchestrators(script: str) -> None:
    """Every script must be a documented, single-entry-point thin orchestrator.

    This is an architectural gate, not a shape check: it parses the script and
    fails if anyone adds a second top-level function or a class, which is how
    business logic starts leaking out of ``src/`` into ``scripts/``.
    """
    source = (ROOT / "scripts" / script).read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert ast.get_docstring(tree), f"{script} has no module docstring"

    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    assert functions == ["main"], f"{script} defines top-level functions {functions}; logic belongs in src/"
    assert classes == [], f"{script} defines classes {classes}; logic belongs in src/"

    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    assert ast.get_docstring(main) is not None, f"{script}: main() needs a docstring"
    assert isinstance(main.returns, ast.Name) and main.returns.id == "int", f"{script}: main must return int"
    assert "raise SystemExit(main())" in source, f"{script} has no SystemExit entry guard"


@pytest.mark.parametrize("script", SCRIPTS)
def test_scripts_do_not_compute(script: str) -> None:
    """Thin orchestrators must not import the numerical stack directly."""
    source = (ROOT / "scripts" / script).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "numpy" not in imported, f"{script} imports numpy; computation belongs in src/"
    assert "scipy" not in imported, f"{script} imports scipy; computation belongs in src/"
    assert "matplotlib" not in imported, f"{script} imports matplotlib; plotting belongs in src/figures/"
