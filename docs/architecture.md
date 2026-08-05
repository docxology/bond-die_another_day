# Architecture — `die_another_day` (ICARUS)

*Die Another Day* (2002), mission codename **ICARUS**. This document is the map
of `src/` and the contract each layer owes the others.

## Layer topology

Dependency direction is strictly downward. Nothing below reaches up.

```
scripts/                     thin orchestrators (argv, sys.path, one call in)
  |
  v
src/die_another_day/
  mission.py                 <- the ONLY module importing bond_api
  mission_results.py         <- the single deterministic concept runner
  manuscript_variables.py    <- config -> tokens; measured tokens via the runner
  figures/plots.py           <- deterministic matplotlib renderers
  |
  v
  identity_detection.py  sequence_identity.py
  ice_ops.py  hypothermia.py  ice_structure.py
  orbital_mirror.py          <- pure domain core: numpy / scipy only
```

`bond_api` is a path dependency declared in `pyproject.toml`. The domain core
does not import it, so `import die_another_day.orbital_mirror` works in an
environment where the protocol package is absent entirely.

## The six domain modules

Each is pure, deterministic, fully typed, and independently testable.

### `identity_detection.py` — biometric replacement screening

Models a subject's biometric signature as a Gaussian over $k$ markers.
`estimate_profile` fits mean, covariance (ridge-regularised), precision, and
per-marker standard deviations from an enrolled sample matrix, falling back to
the pseudo-inverse when the covariance is exactly singular. `mahalanobis_sq`
gives the scalar drift statistic; `per_marker_z_scores` gives the marginal
view. `detect_drift` converts the distance to a chi-square *p*-value, compares
it to the $1-\alpha$ quantile, and **additionally** requires at least
`min_markers` individually flagged markers — one noisy marker is not a
substitution. `generate_identity_samples` synthesises an enrolled population
from a seed.

### `sequence_identity.py` — DNA identity verification

Verifies identity at the sequence level over {A, C, G, T}. `generate_genome`
synthesises a reference at a configured GC content; `mutate_genome` introduces
scattered substitutions and optionally one *contiguous* edit block.
`hamming_distance`, `edit_distance` (Levenshtein, O(mn) DP), and `kmer_jaccard`
score similarity three ways; `mismatch_clusters` finds contiguous mismatch
runs. `verify_identity` combines them: a probe is a suspected replacement when
a contiguous run reaches `cluster_min`, and is matched only when k-mer
similarity clears the threshold *and* no such block exists. The contiguous-run
test is the discriminating one — k-mer similarity alone does not separate a
gene-therapy edit from sequencing noise, which the results section shows
numerically.

### `ice_ops.py` — cold-environment air operations

Newton's law of cooling in closed form. `seconds_to_critical` solves for the
exposure ceiling; `exposure_temperature` predicts core temperature at a time;
`plan_rotation` splits an operation into squads so none exceeds the ceiling;
`thermal_load` integrates core depression below **normothermia** (not room
comfort — see the note below); `heating_energy` sizes space heating against the
ambient. `plan_briefing` assembles the whole `IceOpsPlan`.

Note on the two references: cold strain is physiological and measured from the
operative's normothermic core (37 C). Space heating is architectural and
measured from room comfort (20 C). Using comfort for both makes the strain
integral identically zero for every survivable shift, because a shift ends at
the critical core temperature, which is far above comfort. Keep them separate.

### `hypothermia.py` — cold-water immersion and rescue

The aggressive case: water conducts heat far faster than air.
`cooling_rate_water` scales a calibrated reference rate by mass$^{-1/3}$ (heat
capacity grows with mass) and an insulation factor. `immersion_core_temp` and
`time_to_core_temp` solve the cooling law forward and backward.
`hypothermia_stage` maps a core temperature to the clinical mild / moderate /
severe bands. `immersion_risk` reports the full timeline;
`plan_cold_water_rescue` decides whether a sweeping rescue party reaches the
operative before the severe stage and by what margin.

### `ice_structure.py` — palace structural integrity

Two independent checks. `safe_load_tons` / `required_thickness_cm` /
`load_safety_factor` implement the published bearing-capacity rule for floating
ice ($P = h^2/C$). `thermal_stress_pa` and `critical_delta_t_c` implement
$\sigma = E\alpha\Delta T/(1-\nu)$ and the gradient that reaches the tensile
limit. `ice_structure_plan` returns both verdicts *and* their conjunction —
deliberately, because the configured scenario passes its load case and fails
its thermal case, and a single collapsed verdict would hide that.

### `orbital_mirror.py` — ICARUS targeting geometry

`propagate_circular` propagates a circular orbit by mean anomaly into ECI.
`lwlatlon_to_ecef` plus `ecef_to_eci` and `gmst_radians` place the ground
target in the same frame. `sun_unit_eci` gives a low-precision solar unit
vector; `elevation_deg` and `in_shadow` give visibility and eclipse.
`point_mirror` solves the reflection law — the normal bisects the incoming
solar ray and the ground re-point — and returns incidence, delivered power,
spot radius, and target flux. `plan_pass` marches the orbit and aggregates
feasible windows.

Two subtleties are load-bearing. The incoming ray is the **solar unit vector
itself** (parallel-ray approximation at 1 au); forming it as
`unit(sun_unit - sat)` collapses to the nadir direction and produces incidence
angles wrong by tens of degrees — a defect this module carried until it was
fixed and pinned by
`test_mirror_to_sun_direction_is_the_solar_vector_not_nadir`. And when the
target is anti-parallel to the Sun the bisector degenerates; that instant
returns infeasible with zero power rather than raising.

## The three support modules

| Module | Responsibility |
| --- | --- |
| `mission_results.py` | The single deterministic runner. Reads the `concepts:` block of `manuscript/config.yaml`, runs all six models once under seed 7 (the module constant `MISSION_SEED`; the config carries no seed key of its own), returns a frozen `ConceptResults`. Owns the positive/negative control construction (`replacement_probe`, `genuine_probe`) and every parameter default. `ConceptResults` also carries the probe z-vectors and the reads that were scored, so figures plot the run rather than rebuilding it. |
| `manuscript_variables.py` | `load_manuscript_config`, `generate_variables` (configured-input tokens, declared once in `CONFIG_INPUT_TOKENS`), `measured_variables` (measured-output tokens, read off `ConceptResults`), `resolve_manuscript_tree` (strict token substitution into `output/manuscript/`). |
| `figures/plots.py` | Four deterministic renderers: pass profile, identity drift, hypothermia curve, sequence mismatch map. `_save` suppresses PNG `Date` metadata so output is byte-reproducible — which is what lets `test_scripts_smoke` compare published PNGs byte-for-byte against a render of the runner's own arrays. |

## `mission.py` — the frozen protocol adapter

`mission.py` implements the BOND-API `MissionProvider` contract and nothing
else. Its public shape is consumed by other packages and must not change:

| Member | Contract |
| --- | --- |
| `MissionProvider.film` | `"die_another_day"` — the discovery slug. |
| `brief()` | Returns a `MissionBrief`: three objectives, the `icarus-suite` software asset (concept list, seed, version), and a determinism constraint. |
| `recon(request)` | Returns a `ReconReport` of six findings surveying goal, concepts, models, assets, constraints, and gadgets. |
| `plan(brief)` | Returns a `MissionPlan` of seven `Step`s — one per concept plus a compile step. |
| `execute(plan)` | Calls `run_all_concepts`, packs the six model outputs into `MissionOutcome.results`, and sets `success` from the conjunction of the concept verdicts. Provenance carries the package version, seed 7, and `wall_time_s = 0.0`. |
| `debrief(outcome)` | Returns a `Debrief` with six lessons rendered from the measured results. |
| `ICARUS_GADGETS` | A module-level `GadgetRegistry` mapping the film slug to its six concept callables. |

Discovery loads `die_another_day.mission` from `sys.path` and binds the
top-level `MissionProvider` class (`bond_api.discovery.load_provider`). Adding
a concept means adding a step, a results key, a lesson, and a gadget — never
renaming or removing an existing one.

## Forbidden patterns

- `infrastructure.*` imported anywhere in this package.
- `bond_api` imported by anything other than `mission.py`.
- Business logic, math, or plotting in `scripts/`.
- A second top-level function or a class in a file under `scripts/`.
- Mock frameworks in `tests/`.
- A hand-authored number in manuscript results prose.

## Adding a new concept

1. Write `src/die_another_day/<concept>.py`: pure, typed, documented,
   deterministic, numpy/scipy only.
2. Add it to `CONCEPT_MODULES` and the re-exports in `__init__.py`.
3. Run it inside `mission_results.run_all_concepts` and surface its output on
   `ConceptResults`.
4. Add a `Step`, a `results` key, and a lesson in `mission.py`, and register its
   entry point in `ICARUS_GADGETS`. Do not disturb the existing entries.
5. Add measured tokens in `measured_variables` and cite them in a manuscript
   section — the orphan-token test fails otherwise.
6. Add `tests/test_<concept>.py` with real data and value assertions.
7. If it needs a figure: a renderer in `figures/plots.py`, a call in
   `scripts/generate_figures.py`, and a reference in `03_results.md`. The
   renderer's inputs must come off the `ConceptResults` record — never rebuilt
   in the script — and the figure needs an input-sensitivity test
   (render twice with one input changed, require different bytes). A figure
   that rebuilds its own probes can illustrate a different experiment than the
   table it sits under; that has happened here once already.
8. If it needs a new `concepts:` key: register it in
   `manuscript_variables.CONFIG_INPUT_TOKENS` and list it in
   `05_experimental_setup.md`, or
   `test_every_configured_input_is_registered_and_cited` fails.
