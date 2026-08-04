# die_another_day — ICARUS

**Die Another Day (2002)** · mission codename **ICARUS**

Special-agent mission software for the PROJECT BOND film suite. This package is
a `MissionProvider` (per the frozen BOND-API protocol) backed by six pure,
deterministic domain modules:

| Concept | Module | What it does |
| --- | --- | --- |
| Biometric identity-replacement detection | `src/die_another_day/identity_detection.py` | Enrols a Gaussian biometric baseline and screens a probe for gene-therapy-grade trait drift (Mahalanobis distance vs. chi-square threshold, plus a coherent cluster of per-marker `z` flags). |
| DNA sequence identity verification | `src/die_another_day/sequence_identity.py` | Verifies a DNA read by Levenshtein edit distance, k-mer fingerprint similarity, and contiguous edit-block detection — a coherent genome edit is unmistakable. |
| Ice-palace thermal operations | `src/die_another_day/ice_ops.py` | Solves Newton's cooling law to set cold-exposure ceilings and builds a rotating operations roster with cold-stress and heating-energy metrics. |
| Cold-water hypothermia risk | `src/die_another_day/hypothermia.py` | Models cold-water immersion core-temperature decay and sizes a rescue against the mild/moderate/severe hypothermia timeline. |
| Ice-structure integrity | `src/die_another_day/ice_structure.py` | Checks the ice palace under load (Gold's load-capacity rule) and thermal-gradient stress (cracking threshold). |
| Orbital-mirror (ICARUS) targeting | `src/die_another_day/orbital_mirror.py` | Propagates a circular orbit, solves the mirror reflection law, and reports feasible targeting windows and delivered solar flux over a ground target. |

`src/die_another_day/mission.py` is the thin adapter implementing the frozen
BOND-API `MissionProvider` (brief / recon / plan / execute / debrief) and
registers the six concept functions as gadgets with the BOND-API
`GadgetRegistry`. The domain modules are importable without `bond_api`.

## Quick start

```bash
uv sync --extra dev
uv run python scripts/00_preflight.py        # identity + protocol surface
uv run python scripts/run_mission.py         # full five-stage mission
uv run python scripts/brief.py               # per-phase CLIs
uv run python scripts/recon.py
uv run python scripts/plan.py
uv run python scripts/execute.py
uv run python scripts/debrief.py
uv run python scripts/generate_figures.py    # writes output/figures/*.png
uv run python scripts/z_generate_manuscript_variables.py   # hydrate {{TOKEN}}s
```

## Verification gates

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Layer contract

- Pure domain core (`identity_detection.py`, `ice_ops.py`,
  `orbital_mirror.py`): stdlib + numpy + scipy only — no `infrastructure.*`,
  importable without `bond_api`.
- `mission.py`: the only module that imports `bond_api` (the frozen protocol).
- `scripts/`: thin orchestrators (argv + sys.path bootstrap + a call into
  `src/`).
- `tests/`: zero mocks, real data and computation.

Local-only working tree: this package has no remote and is never pushed.
