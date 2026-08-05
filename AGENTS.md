# die_another_day — Agent Guide (ICARUS)

**Die Another Day (2002)** · mission codename **ICARUS** · PROJECT BOND film package.

Build, test, and verify instructions. Deeper rules live in
[`docs/agent_instructions.md`](docs/agent_instructions.md),
[`docs/architecture.md`](docs/architecture.md), and
[`docs/testing_philosophy.md`](docs/testing_philosophy.md).

## Package identity

- Film: *Die Another Day* (2002); mission codename `ICARUS`.
- Discovery slug: `die_another_day`, bound from
  `src/die_another_day/mission.py` on `sys.path`.
- Protocol: the frozen BOND-API `MissionProvider`
  (`brief` / `recon` / `plan` / `execute` / `debrief`) plus the module-level
  `ICARUS_GADGETS` registry. Both are consumed by sibling packages — **do not
  change their public shape.**

## Setup

`bond-api` is a path dependency (`[tool.uv.sources]` in `pyproject.toml`), so
sync before anything else:

```bash
uv sync --extra dev
```

## Layer contract (enforced by tests, not convention)

| Surface | Rule |
| --- | --- |
| `identity_detection.py`, `sequence_identity.py`, `ice_ops.py`, `hypothermia.py`, `ice_structure.py`, `orbital_mirror.py` | Pure domain core. stdlib + numpy + scipy only. No `infrastructure.*`, no `bond_api` — importable standalone. |
| `mission_results.py` | The single deterministic runner over all six concepts. The only place parameter defaults and control construction live. |
| `mission.py` | Thin adapter; the **only** module importing `bond_api`. Frozen public shape. |
| `manuscript_variables.py` | Config → input tokens; runner record → measured tokens; strict substitution into `output/manuscript/`. |
| `figures/plots.py` | Four deterministic, byte-reproducible matplotlib renderers. |
| `scripts/` | Thin orchestrators: docstring, `sys.path` bootstrap, one `main() -> int`, `raise SystemExit(main())`. No second top-level function, no class, no numpy/scipy/matplotlib import. |
| `tests/` | Zero mocks. Real data, real computation, assertions with oracles. |

## Build and run

```bash
uv run python scripts/00_preflight.py                     # identity + protocol surface
uv run python scripts/run_mission.py                      # full mission, outcome JSON
uv run python scripts/generate_figures.py                 # output/figures/*.png
uv run python scripts/z_generate_manuscript_variables.py  # output/manuscript/*.md (strict)
```

`output/` is git-ignored and fully regenerable — never hand-edit anything in it.

## Verify (run all, read every result)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py
git status --short
```

Coverage gate: 90% line **and** branch on `src/`. Do not transcribe the measured
percentage into any document — quote the gate, run the command.

Two greps that should stay clean:

```bash
grep -rn "unittest.mock\|MagicMock\|mocker.patch\|create_autospec" tests/ || echo "no mocks"
grep -rn "template_code_project" --include='*.py' --include='*.md' . || echo "no exemplar leftovers"
```

A `uv` failure reading `Failed to initialize cache` or `Operation not permitted`
is a sandbox restriction, not a package failure — re-run with the sandbox
disabled rather than changing the package.

## Hard guardrails

- Scope is exactly this directory. Never touch a sibling package, the bond root
  files, or the template repo.
- Local-only tree: no remote, never push. Commits are path-scoped to this
  package's own repository.
- Determinism: seed `7`; no wall-clock in persisted artifacts
  (`wall_time_s = 0.0`); PNG `Date` metadata suppressed. Enforced end-to-end by
  `test_regeneration_is_byte_identical`, which regenerates the manuscript
  variables twice a second apart and compares bytes — a `GENERATION_TIMESTAMP`
  token from `datetime.now()` once broke this rule undetected for several
  commits.
- Manuscript metrics are injected tokens. Never hand-author a number in results
  prose — see [`manuscript/AGENTS.md`](manuscript/AGENTS.md).
- Nothing may be green by construction: a new assertion needs an input that
  would make it fail, and a new metric needs a case where it is non-trivial.
