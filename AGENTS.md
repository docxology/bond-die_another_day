# die_another_day — Agent Guide (ICARUS)

**Die Another Day (2002)** · mission codename **ICARUS** · PROJECT BOND film package.

## Package identity

- Film: `Die Another Day` (2002)
- Mission codename: `ICARUS`
- Protocol: implements the frozen BOND-API `MissionProvider`
  (`src/die_another_day/mission.py`), discoverable by slug `die_another_day`
  on `sys.path`.

## Layer contract (enforced)

| Surface | Rule |
| --- | --- |
| `src/die_another_day/identity_detection.py`, `sequence_identity.py`, `ice_ops.py`, `hypothermia.py`, `ice_structure.py`, `orbital_mirror.py` | Pure domain core. stdlib + numpy + scipy only. **No** `infrastructure.*`, **no** `bond_api` imports — importable standalone. |
| `src/die_another_day/mission.py` | Thin adapter. The **only** module importing `bond_api`; implements the protocol and registers the six concept gadgets. |
| `src/die_another_day/manuscript_variables.py` | Reads `manuscript/config.yaml` → emits `{{TOKEN}}` map (yaml only). |
| `src/die_another_day/figures/` | Deterministic matplotlib figure generators (4 concept figures). |
| `scripts/` | Thin orchestrators: sys.path bootstrap + one call into `src/`, no business logic. |
| `tests/` | Zero mocks; real data + computation only. |

## Hard guardrails

- Scope = exactly this package directory. Never touch siblings, bond root
  files, or the template repo.
- Local-only tree: no remote, never push.
- Deterministic: fixed seed (`7`), no wall-clock in persisted artifacts
  (provenance `wall_time_s = 0.0`).
- ≥90% line+branch coverage on `src/`:
  `uv run pytest tests/ --cov=src --cov-fail-under=90`.
- No leftover `template[_]code_project` strings (aim zero).
- `output/` is git-ignored (regenerable).

## Protocol integration

- `[tool.uv.sources] bond-api = { path = ".../bond-api" }` (path dependency).
  Run `uv sync --extra dev` before pytest.
- Discovery loads `die_another_day.mission` and binds the top-level
  `MissionProvider` class. The class declares `film = "die_another_day"`.

## Verification checklist (before done)

1. `uv run pytest tests/ --cov=src --cov-fail-under=90`
2. `uv run ruff check src/ scripts/ tests/` and `uv run ruff format --check`
3. `uv run mypy src/ scripts/`
4. `rg -n "template[_]code_project" .` → zero
5. `git status` clean after the path-scoped commit

See `docs/agent_instructions.md`, `docs/architecture.md`,
`docs/testing_philosophy.md`.
