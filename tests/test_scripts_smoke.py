"""Smoke tests: thin orchestrator scripts run end-to-end (subprocess, real run)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

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
    assert (ROOT / "output" / "figures" / "icarus_pass_profile.png").is_file()
    assert (ROOT / "output" / "figures" / "icarus_identity_drift.png").is_file()


@pytest.mark.parametrize(
    "script",
    [
        "00_preflight.py",
        "run_mission.py",
        "brief.py",
        "recon.py",
        "plan.py",
        "execute.py",
        "debrief.py",
        "generate_figures.py",
        "z_generate_manuscript_variables.py",
    ],
)
def test_scripts_are_python_files(script: str) -> None:
    source = (ROOT / "scripts" / script).read_text(encoding="utf-8")
    assert "def main()" in source
