# TODO — die_another_day (ICARUS)

`die_another_day` is the PROJECT BOND film package for *Die Another Day* (2002),
mission codename **ICARUS**. It implements six concepts from the film as pure,
deterministic algorithms — biometric identity-replacement screening, DNA
sequence identity verification, ice-palace thermal operations, cold-water
immersion risk, ice-structure integrity, and orbital-mirror targeting — plus one
runner (`mission_results.run_all_concepts`) that executes all six under seed 7
and one thin adapter (`mission.py`) exposing them as a frozen BOND-API
`MissionProvider`.

**Verified state, measured 2026-08-05 at commit `4de2137`:** `uv run pytest
tests/ --cov=src --cov-fail-under=90` reports **194 passed, 100.00% coverage
(873 statements, 206 branches, 0 missed)**. `ruff check`, `ruff format --check`,
`mypy src/ scripts/`, and `scripts/z_generate_manuscript_variables.py` (90
tokens resolved, strict) all pass. That reading is a dated measurement record
with its command and commit attached, not a standing claim — the package's own
doctrine (`docs/agent_instructions.md`) forbids transcribing it into prose
elsewhere. Re-run the command rather than trusting this line.

All ten findings in `output/verify/die_another_day.json` were closed by commit
`4de2137` except the two recorded in
`output/verify/die_another_day.unresolved.json`; both appear below (V2, and E6 /
Known limitation 1).

---

## Open work

### Correctness

**C1 — The published hypothermia figure stops 2.07 s short of the severe
crossing it illustrates, on a magic number.**

`scripts/generate_figures.py:66` passes a hardcoded `1800.0`-second window to
`render_hypothermia_curve`. That literal is not in `manuscript/config.yaml`, is
not registered in `manuscript_variables.CONFIG_INPUT_TOKENS`, and has no
manuscript token. Measured this session: at 1800 s the core is **28.0084 C**,
while `HYP_TIME_TO_SEVERE_S` is **1802.07 s**. The plotted curve therefore never
crosses the severe (28 C) dashed line the caption draws attention to, and the
window is the one figure parameter not derived from the reported run. It is also
a numeric parameter living in a thin orchestrator, which the `AGENTS.md` layer
contract puts in `mission_results.py` or `config.yaml`.

- Files: `scripts/generate_figures.py:62-68`;
  `src/die_another_day/figures/plots.py:103-130`;
  `manuscript/03_results.md:96-97`.
- Done: the window comes from the run, or from a registered and §05-cited config
  key set comfortably past `time_to_severe`, and a test asserts the last plotted
  temperature is at or below `hypothermia.SEVERE_THRESHOLD_C`.
- Demonstrate: `uv run python scripts/generate_figures.py && uv run pytest
  tests/test_figures.py tests/test_scripts_smoke.py -v`

### Verification

**V1 — `icarus_hypothermia_curve.png` is the only published figure not bound to
the reported run.**

`tests/test_scripts_smoke.py:111-145`
(`test_published_figures_depict_the_reported_run`) byte-compares three of the
four published PNGs — drift, sequence, pass profile — against independent
renders from `run_all_concepts`. The hypothermia curve is absent from that list.
`tests/test_scripts_smoke.py:104-108` only asserts two of the four exist.
`tests/test_figures.py:99-106` proves the *renderer* is input-sensitive, which
is not the same as proving the *published file* depicts the reported
configuration. This is the same class of defect as the SEVERE audit finding on
the identity-drift figure, surviving in the one figure the remediation did not
cover.

- Files: `tests/test_scripts_smoke.py:104-108` and `:111-145`.
- Done: the byte-comparison covers all four published PNGs and all four are
  existence-checked.
- Demonstrate: `uv run pytest
  tests/test_scripts_smoke.py::test_published_figures_depict_the_reported_run -v`,
  then falsify it — change the water temperature at
  `scripts/generate_figures.py:63` and confirm the test goes red before
  reverting.

**V2 — One assertion in the sequence-control test is not independently
falsified.** *(carried from `die_another_day.unresolved.json`)*

`tests/test_mission_results.py:111` asserts `genuine_positions !=
replaced_scattered`. When the test was falsified against a rewrite giving both
reads shared scattered positions, the red came from the count assertions on
lines 109-110, not from line 111. The test as a whole is proven falsifiable in
the direction that matters; that single line is not.

- Files: `tests/test_mission_results.py:87-112`.
- Done: a mutation exists that leaves lines 109-110 green and turns line 111
  red — e.g. a `mutate_genome` variant drawing the same count of scattered
  errors at the same loci for both probes — and the assertion is either proven
  against it or folded into one that is.
- Demonstrate: apply that mutation locally, run `uv run pytest
  tests/test_mission_results.py::test_the_two_reads_are_matched_on_count_not_on_position -v`,
  confirm the failure names line 111, revert.

**V3 — No test binds `plan_rotation`'s operative-limited infeasible branch to
the mission record.**

`src/die_another_day/ice_ops.py:153-154` caps `squad_count` at
`num_operatives`, which is the only way `feasible` can return `False`. The
concept runner surfaces that flag, but nothing asserts that an operative-starved
configuration propagates an infeasible roster all the way into `ConceptResults`
and §03's ice-ops paragraph. Coverage is 100% because the branch executes in a
unit test; that is line reachability, not a bound claim
(`docs/testing_philosophy.md`: coverage is a floor, not a goal).

- Files: `src/die_another_day/ice_ops.py:133-165`;
  `src/die_another_day/mission_results.py:231-241`;
  `tests/test_mission_results.py`.
- Done: a test runs `run_all_concepts` over a config with too few operatives for
  the configured duration and asserts the record reports an infeasible roster.
- Demonstrate: `uv run pytest tests/test_mission_results.py -k rotation -v`

### Documentation

**D1 — `docs/testing_philosophy.md` states the figure-provenance oracle as
universal; it holds for three figures of four.**

The "Content assertions on binary artifacts" section presents *provenance —
compare the published PNG against a render built from `run_all_concepts`
output* as this suite's practice, with no hypothermia exception noted. Once V1
closes, the sentence is true as written and needs no edit; until then it
overstates by one figure.

- Files: `docs/testing_philosophy.md`, section "Content assertions on binary
  artifacts".
- Done: V1 is closed (preferred), **or** the section names the hypothermia curve
  as the uncovered case.
- Demonstrate: `grep -n "hypothermia" docs/testing_philosophy.md` returns the
  exception, or V1's command passes with four figures compared.

### Extension

Genuine future work. None of these is a defect; each is a fidelity or reach
increase the current model deliberately does not attempt.

**E1 — Robust covariance for heavy-tailed biomarkers.**
`src/die_another_day/identity_detection.py:98-128` fits a plain sample
covariance plus a `1e-6` ridge, so one extreme enrolment sample inflates the
covariance and desensitises the screen. Add an optional robust estimator (MCD or
a trimmed estimate) behind a keyword argument, default unchanged so every
reported number holds. Done: a test shows the plain estimator missing a
replacement the robust one catches. Demonstrate: `uv run pytest
tests/test_identity_detection.py -k robust -v`.

**E2 — Unaligned sequence reads.**
`src/die_another_day/sequence_identity.py:229-230` rejects unequal-length input.
Real reads are not pre-aligned; Levenshtein tolerates indels but the
contiguous-block detector and Hamming are position-aligned. Either add a
lightweight alignment step ahead of the block test, or keep the precondition and
raise an error naming alignment as the fix. Done: an unaligned probe either
verifies correctly or fails with an actionable message. Demonstrate: `uv run
pytest tests/test_sequence_identity.py -k align -v`.

**E3 — Conical eclipse and finite solar disc.**
`src/die_another_day/orbital_mirror.py:182-188` uses a cylindrical shadow, so
penumbra reads as full sunlight; the Sun is also a point source, which
understates achievable spot size. Adequate for feasibility, inadequate for
illumination engineering — the largest single fidelity gain available in this
module. Done: an umbra/penumbra case the cylindrical model gets wrong is
asserted. Demonstrate: `uv run pytest tests/test_orbital_mirror.py -k penumbra -v`.

**E4 — Per-operative thermal parameters and handover cost.**
`src/die_another_day/ice_ops.py:216-240` uses one Newton decay rate for the
whole squad; `plan_rotation` (`:133-165`) assumes instantaneous handover. A
per-operative rate (suit, body composition) plus a handover cost turns the
roster from a division into a scheduling problem. Done: differing per-operative
rates change the roster. Demonstrate: `uv run pytest tests/test_ice_ops.py -v`.

**E5 — Ice-structure dynamics.**
`src/die_another_day/ice_structure.py:122+` is a single-instant check: bearing
capacity plus thermal stress. No creep under sustained load, no crack
propagation past the tensile limit, no repeated loading. A time-dependent model
turns today's pass/fail into a time-to-failure. Done: the plan reports a
time-to-failure rather than a boolean. Demonstrate: `uv run pytest
tests/test_ice_structure.py -v`.

**E6 — Recalibrate `K_REF_PER_S` to the survival literature.** *(the standing
option behind unresolved audit finding 1 — see Known limitation 1)*
`src/die_another_day/hypothermia.py:54-66`. This is a scientific redesign, not a
remediation: it moves every immersion number in §03 and can flip the rescue
verdict. Done, if attempted: the constant sits in the few-degrees-per-hour
range, `tests/test_hypothermia.py:176-186` (which asserts the 24.3 C/h gap) is
rewritten rather than deleted, and §07's limitation paragraph is replaced by a
calibration statement with its citation. Demonstrate: `uv run pytest
tests/test_hypothermia.py -v && uv run python
scripts/z_generate_manuscript_variables.py`.

**E7 — Adopt `bond-utilities` for outcome persistence.**
`bond-utilities` now ships `mission_io.record_provenance_outcome`
(`bond-utilities/src/bond_utilities/mission_io.py:153`), which earlier versions
of this file listed as hypothetical. `pyproject.toml:17-26` still depends on
`bond-api` only. If adopted, the import belongs in `mission.py` alone — the six
concept modules stay infrastructure-free and standalone-importable. Done:
outcome persistence is delegated and the standalone-import path still works with
both `bond_api` and `bond_utilities` absent. Demonstrate: `uv run pytest
tests/test_mission.py -v && uv run python scripts/00_preflight.py`.

---

## Known limitations (not bugs)

Accepted scope, recorded so nobody re-opens them as findings.

1. **The immersion cooling rate is not physiologically calibrated.**
   *(unresolved audit finding 1, resolved as a stated limitation rather than
   made true)* `hypothermia.K_REF_PER_S = 2.5e-4` is defined by a film-scenario
   identity — a 75 kg adult in 10 C water reaches a 30 C core in exactly 20
   minutes — implying an initial rate near **24.3 C/hour**. The cold-water
   survival literature (Tipton 1989; Golden & Tipton 2002) reports a few degrees
   per hour at that water temperature, so the model runs roughly an order of
   magnitude fast. Honest scope: §03's immersion times are correct *for this
   model* and are **not** survival-time predictions; only the 35/32/28 C clinical
   staging bands come from the literature. The audit forced this softening — the
   earlier claim that the timeline matched the literature is gone from both the
   docstring and §07. The gap is quantified in three places
   (`src/die_another_day/hypothermia.py:54-66`,
   `manuscript/07_scope_and_related_work.md` Limitations,
   `tests/test_hypothermia.py:176-186`) and two tests pin it, so it cannot go
   stale. Recalibrating is E6, not a bug fix.

2. **Seed is `7` and is a code constant, not a config key.** `config.yaml`
   deliberately carries no seed, and
   `test_no_configuration_seed_can_diverge_from_the_reported_one` enforces that.
   Changing the seed changes every reported number.

3. **`mission_results.run_all_concepts` is the single execution path.** A second
   path is how the manuscript starts disagreeing with the code. Do not add one.

4. **The `MissionProvider` public shape and `ICARUS_GADGETS` are frozen.**
   bond-cli, the coordinator reconcile, and the orchestrator all consume them.
   Discovery is by slug (`load_provider("die_another_day")`); no sibling reaches
   into film internals.

5. **Three §03 tokens are structurally determined by config, by design.**
   `SEQ_GENUINE_HAMMING`, `SEQ_LONGEST_BLOCK`, and `ID_REPLACED_SHIFT_SIGMA` are
   generator/construction checks rather than free measurements.
   `manuscript/05_experimental_setup.md:96-113` names all three. This is
   disclosure, not a defect.

6. **Beam spread is a lumped model.** Diffraction, figure error, and atmospheric
   scattering are folded into the single `atmosphere_transmission = 0.85` factor
   rather than modelled. Stated in §02 and §07.

7. **The measured coverage percentage is not quoted in package prose.**
   `docs/agent_instructions.md` forbids it — the number goes stale and nobody
   re-derives it. The dated reading at the head of this file is a measurement
   record carrying its command and commit, and is the only place it appears.

---

## Verification

Run every command; read every result. All are expected to pass on a clean tree.

```bash
cd /Users/4d/Documents/GitHub/template/projects/working/bond/die_another_day

uv sync --all-extras                                       # bond-api is a path dependency

uv run pytest tests/ --cov=src --cov-fail-under=90         # 194 passed; non-zero exit below the 90% line+branch floor
uv run ruff check src/ scripts/ tests/                     # "All checks passed!"
uv run ruff format --check src/ scripts/ tests/            # "36 files already formatted"
uv run mypy src/ scripts/                                  # "Success: no issues found in 22 source files"

uv run python scripts/00_preflight.py                      # identity + protocol surface
uv run python scripts/run_mission.py                       # five-stage mission + outcome JSON
uv run python scripts/generate_figures.py                  # four PNGs into output/figures/
uv run python scripts/z_generate_manuscript_variables.py   # strict: an unresolved token exits non-zero

git status --short                                         # empty; output/ is git-ignored
```

Two greps that must stay clean:

```bash
grep -rn "unittest.mock\|MagicMock\|mocker.patch\|create_autospec" tests/ || echo "no mocks"
grep -rn "template_code_project" --include='*.py' --include='*.md' . || echo "no exemplar leftovers"
```

A `uv` failure reading `Failed to initialize cache at ~/.cache/uv` or
`Operation not permitted` is a sandbox restriction, not a package failure —
re-run the same command with the sandbox disabled. Do not change the package in
response to it.
