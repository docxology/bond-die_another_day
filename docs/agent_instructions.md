# Agent Instructions — ICARUS (die_another_day)

Read-first operational rules for AI agents working inside this package.

## The seven rules

1. **Zero mocks.** No `unittest.mock`, `MagicMock`, `@patch`, or
   `create_autospec` anywhere in `tests/`. Tests use real computation and real
   data. A mock-based test can pass while the science is wrong — that defeats
   the point of a mission-software package.
2. **Infrastructure-free domain core.** `identity_detection.py`, `ice_ops.py`,
   and `orbital_mirror.py` must not import `infrastructure.*` or `bond_api`.
   They are the importable-standalone mathematical core.
3. **Thin orchestrators.** `scripts/` does argv + sys.path bootstrap + a single
   call into `src/`. No business logic or math in scripts.
4. **Deterministic.** Fixed seed (`7`). No unseeded random draws, no wall-clock
   in persisted artifacts. Provenance `wall_time_s` is `0.0`.
5. **Tokens from code.** Manuscript numeric facts use `{{TOKEN}}`s hydrated by
   `scripts/z_generate_manuscript_variables.py` from
   `manuscript/config.yaml` — never hand-author metrics in prose.
6. **Type hints + docstrings.** Every public function is annotated and
   documented.
7. **Real protocol.** `mission.py` is the only module that imports `bond_api`;
   it implements the frozen `MissionProvider` exactly and registers its gadgets.

## Contribution / editing workflow

1. Read `docs/architecture.md` before touching module boundaries.
2. Read `docs/testing_philosophy.md` before writing or editing tests.
3. After editing Python: `uv run ruff check`, `uv run ruff format`,
   `uv run mypy`, then `uv run pytest tests/ --cov=src --cov-fail-under=90`.
4. If you changed a public surface or a config parameter, update the relevant
   manuscript section and re-run the variable hydration + cross-reference test.

## Verification checklist (before done)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . || echo Clean
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
git status --short   # clean after the path-scoped commit
```
