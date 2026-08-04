"""Mission lifecycle tests: MissionProvider adapter + protocol integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from bond_api.discovery import load_provider
from bond_api.protocol import MissionProvider as ProtocolProvider, ReconRequest
from die_another_day.mission import ICARUS_GADGETS, MissionProvider

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


@pytest.fixture(scope="module")
def provider() -> MissionProvider:
    return MissionProvider()


def test_provider_satisfies_protocol(provider: MissionProvider) -> None:
    assert isinstance(provider, ProtocolProvider)
    assert provider.film == "die_another_day"


def test_brief(provider: MissionProvider) -> None:
    brief = provider.brief()
    assert brief.film == "die_another_day"
    assert brief.codename == "ICARUS"
    assert len(brief.objectives) == 3
    assert len(brief.assets) == 1
    assert len(brief.constraints) == 1


def test_recon(provider: MissionProvider) -> None:
    report = provider.recon(ReconRequest(goal="survey assets"))
    assert len(report.findings) == 4
    assert report.findings[0].label == "goal"


def test_plan(provider: MissionProvider) -> None:
    plan = provider.plan(provider.brief())
    assert len(plan.steps) == 4
    assert [s.name for s in plan.steps] == ["identity", "ice_ops", "orbital", "verify"]


def test_execute(provider: MissionProvider) -> None:
    outcome = provider.execute(provider.plan(provider.brief()))
    assert outcome.success is True
    results = outcome.results
    assert results["identity"]["replacement_detected"] is True
    assert results["identity"]["genuine_cleared"] is True
    assert results["ice_ops"]["rotation_feasible"] is True
    assert results["orbital_mirror"]["feasible_seconds"] > 0.0
    assert outcome.provenance.seed == 7
    assert outcome.provenance.wall_time_s == 0.0


def test_debrief(provider: MissionProvider) -> None:
    outcome = provider.execute(provider.plan(provider.brief()))
    debrief = provider.debrief(outcome)
    assert len(debrief.lessons) == 3
    assert all(isinstance(lesson, str) and lesson for lesson in debrief.lessons)


def test_mission_deterministic(provider: MissionProvider) -> None:
    plan = provider.plan(provider.brief())
    first = provider.execute(plan)
    second = provider.execute(plan)
    assert first.results == second.results


def test_gadgets_registered() -> None:
    assert "die_another_day" in ICARUS_GADGETS
    assert ICARUS_GADGETS.gadgets_for("die_another_day") == (
        "identity_detection",
        "ice_ops",
        "orbital_mirror",
    )
    assert callable(ICARUS_GADGETS.lookup("die_another_day", "ice_ops"))


def test_discovery_by_slug() -> None:
    discovered = load_provider("die_another_day", search_paths=[SRC])
    assert isinstance(discovered, ProtocolProvider)
    assert discovered.film == "die_another_day"
    assert discovered.brief().codename == "ICARUS"
