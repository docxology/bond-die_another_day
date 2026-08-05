# die_another_day — ICARUS

**Die Another Day (2002)** · mission codename **ICARUS** · PROJECT BOND film package

Special-agent mission software. The film's two central technical ideas —
**identity replacement** (Gustav Graves is Colonel Moon, rebuilt by gene
therapy) and **extreme-environment operations** (the Icelandic ice palace, the
cold-water escape, and the orbital solar mirror *Icarus*) — are implemented as
real, deterministic algorithms rather than named stubs.

## Film concept → software payload

| Film idea | Module | What it actually computes |
| --- | --- | --- |
| Gene-therapy identity replacement | `src/die_another_day/identity_detection.py` | Enrols a Gaussian biometric baseline; scores a probe by squared Mahalanobis distance against a chi-square threshold and requires a coherent cluster of per-marker z-flags before declaring a substitution. |
| DNA-level identity forensics | `src/die_another_day/sequence_identity.py` | Verifies a DNA read by Hamming distance, Levenshtein edit distance, k-mer Jaccard fingerprinting, and contiguous mismatch-block detection — the block is what separates a therapeutic edit from sequencing noise. |
| Ice-palace operations | `src/die_another_day/ice_ops.py` | Solves Newton's cooling law for a safe-exposure ceiling, builds a rotating squad roster, integrates cold strain below normothermia, and sizes space heating against the ambient. |
| Cold-water escape | `src/die_another_day/hypothermia.py` | Models immersion core-temperature decay scaled by mass and insulation, maps it to the clinical mild/moderate/severe stages, and decides whether a sweeping rescue arrives before the severe stage. |
| Ice-palace structural failure | `src/die_another_day/ice_structure.py` | Bearing capacity of floating ice ($P = h^2/C$) plus thermal-gradient tensile stress ($\sigma = E\alpha\Delta T/(1-\nu)$) and the cracking threshold — two independent verdicts, reported separately. |
| The Icarus orbital mirror | `src/die_another_day/orbital_mirror.py` | Propagates a circular orbit into ECI, places the ground target via sidereal time, solves the mirror reflection law under the parallel-ray approximation, and reports feasible targeting windows with delivered power and focused flux. |

Three support modules complete `src/`:

| Module | Role |
| --- | --- |
| `mission_results.py` | The single deterministic runner. Reads `manuscript/config.yaml`, executes all six models once under seed 7, returns a frozen `ConceptResults` — including the positive and negative controls for both identity models. |
| `manuscript_variables.py` | Turns config into input tokens and the runner's record into measured tokens, then substitutes them into the manuscript (strict: an unresolved token fails the run). |
| `figures/plots.py` | Four byte-reproducible matplotlib figures: orbital pass profile, identity trait drift, immersion curve, DNA mismatch map. |

## MissionProvider surface

`src/die_another_day/mission.py` is the thin adapter implementing the frozen
BOND-API protocol. It is the only module that imports `bond_api`, and its
public shape is consumed by bond-cli, the coordinator, and the orchestrator:

| Member | Returns |
| --- | --- |
| `MissionProvider.film` | `"die_another_day"` (the discovery slug) |
| `brief()` | `MissionBrief` — 3 objectives, the `icarus-suite` asset, a determinism constraint |
| `recon(request)` | `ReconReport` — 6 findings |
| `plan(brief)` | `MissionPlan` — 7 steps (one per concept plus a compile step) |
| `execute(plan)` | `MissionOutcome` — all six concept results, provenance with seed 7 and `wall_time_s = 0.0` |
| `debrief(outcome)` | `Debrief` — 6 lessons rendered from the measured results |
| `ICARUS_GADGETS` | module-level `GadgetRegistry` mapping the slug to its six concept callables |

Discovery is by slug on `sys.path`:
`bond_api.discovery.load_provider("die_another_day", search_paths=[src])`.
The six domain modules remain importable with `bond_api` absent entirely.

## Quick start

```bash
uv sync --extra dev

uv run python scripts/00_preflight.py       # identity + protocol surface
uv run python scripts/run_mission.py        # full five-stage mission + outcome JSON
uv run python scripts/brief.py              # per-phase CLIs
uv run python scripts/recon.py "survey the ice palace"
uv run python scripts/plan.py
uv run python scripts/execute.py
uv run python scripts/debrief.py

uv run python scripts/generate_figures.py                 # output/figures/*.png
uv run python scripts/z_generate_manuscript_variables.py  # output/manuscript/*.md
```

## Verification gates

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90   # fails below the floor
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

The coverage floor is 90% line **and** branch on `src/`. The current measured
percentage is deliberately not quoted in prose anywhere in this package — run
the command; it prints the reading and exits non-zero if it is below the floor.

If a `uv` command fails with `Failed to initialize cache` or
`Operation not permitted`, that is a sandbox restriction rather than a package
failure; re-run it with the sandbox disabled.

## Layer contract

- **Pure domain core** — the six concept modules: stdlib + numpy + scipy only,
  no `infrastructure.*`, no `bond_api`, importable standalone.
- **`mission.py`** — the only module importing `bond_api`; frozen public shape.
- **`mission_results.py`** — the one execution path; both the mission outcome
  and the manuscript's numbers are formatted from its output, so they cannot
  drift apart.
- **`scripts/`** — thin orchestrators (argv + `sys.path` + one call into
  `src/`). A test parses each and rejects a second top-level function, a class,
  or a direct numerical import.
- **`tests/`** — zero mocks; real data, real computation, oracles rather than
  shape checks.

## Documentation

| Where | What |
| --- | --- |
| [`docs/agent_instructions.md`](docs/agent_instructions.md) | Operating rules and the verification checklist |
| [`docs/architecture.md`](docs/architecture.md) | Module-by-module map and the frozen protocol contract |
| [`docs/testing_philosophy.md`](docs/testing_philosophy.md) | No-mock doctrine and the nothing-true-by-construction rule |
| [`manuscript/README.md`](manuscript/README.md) | The paper source and how tokens are hydrated |
| [`AGENTS.md`](AGENTS.md) | Build/test/verify instructions for agents |
| [`TODO.md`](TODO.md) | Remaining work |

This package was forked from the `template_code_project` exemplar; that lineage
is the only reason the exemplar's name appears in documentation.

Local-only working tree: this package has no remote and is never pushed.
