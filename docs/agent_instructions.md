# Agent instructions — ICARUS (`die_another_day`)

Read-first operational rules for anyone (human or agent) editing this package.

## Scope

Your working scope is exactly this directory. Never modify a sibling BOND
package, the bond root files, or the template repository. This tree is
local-only: it has no git remote and must never be pushed.

## The rules

1. **Zero mocks.** No `unittest.mock`, `MagicMock`, `mocker.patch`, `@patch`,
   or `create_autospec` in `tests/`. Real data, real computation. A mock-based
   test can pass while the physics is wrong, which is the one failure this
   package cannot tolerate. Environment isolation (`tmp_path`, env-var
   monkeypatching) is not dependency replacement and is fine.
2. **Nothing true by construction.** Before you add an assertion, name the input
   that would make it fail. Negative controls must be real draws, not algebraic
   identities; metrics must be capable of taking a non-trivial value; guards
   must be reachable or removed. `testing_philosophy.md` lists the four times
   this package violated the rule and how each is now pinned.
3. **Infrastructure-free domain core.** The six concept modules
   (`identity_detection`, `sequence_identity`, `ice_ops`, `hypothermia`,
   `ice_structure`, `orbital_mirror`) import numpy/scipy and nothing else from
   this ecosystem — no `infrastructure.*`, no `bond_api`. They must stay
   importable standalone.
4. **The protocol surface is frozen.** `mission.py` is the only module that may
   import `bond_api`. Its `MissionProvider` class (`brief` / `recon` / `plan` /
   `execute` / `debrief`, `film` attribute) and the module-level
   `ICARUS_GADGETS` registry are consumed by bond-cli, the coordinator, and the
   orchestrator. Deepen inside the package; never change that shape.
5. **One run, two consumers.** All six models execute through
   `mission_results.run_all_concepts`. `mission.py` and
   `manuscript_variables.py` both read its output. Never add a second execution
   path — that is how a paper drifts from its code.
6. **Thin orchestrators.** A file in `scripts/` does argv parsing, `sys.path`
   bootstrap, and one call into `src/`. A test parses each script and fails on a
   second top-level function, a class, or a numpy/scipy/matplotlib import.
7. **Deterministic.** Seed `7`. No unseeded draws, no wall-clock in a persisted
   artifact (`wall_time_s` stays `0.0`), no PNG creation-date metadata.
8. **Numbers come from code.** Manuscript metrics are tokens hydrated by
   `scripts/z_generate_manuscript_variables.py`. Configured inputs go through
   `generate_variables`; measured outputs go through `measured_variables`,
   reading the runner's record. Never type a result into prose.
9. **Types and docstrings.** Every public function is annotated and documented,
   including `main()` in every script.

## Editing workflow

1. Read [`architecture.md`](architecture.md) before touching module boundaries;
   read [`testing_philosophy.md`](testing_philosophy.md) before touching tests;
   read [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) before touching the
   paper.
2. Make the change in `src/`, not in `scripts/`.
3. If a public surface or a config parameter changed, update the affected
   manuscript section and re-run token hydration.
4. Run the full gate set below and read the output — do not infer success from
   an exit code you did not look at.
5. Commit inside this package only, path-scoped, with a message that says what
   changed and why.

## Verification checklist

Run all of these, in this order, and read each result:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py   # strict token gate
uv run python scripts/generate_figures.py                  # figures still render
uv run python scripts/run_mission.py                       # end-to-end mission
git status --short                                         # clean after commit
```

Two greps worth keeping in the loop:

```bash
grep -rn "unittest.mock\|MagicMock\|mocker.patch\|create_autospec" tests/ || echo "no mocks"
grep -rn "template_code_project" --include='*.py' --include='*.md' . || echo "no exemplar leftovers"
```

## Sandbox note

`uv` cannot write its cache under a restrictive sandbox. A failure reading
`Failed to initialize cache at ~/.cache/uv` or `Operation not permitted` is an
environment restriction, not a package failure — re-run the same command with
the sandbox disabled. Do not "fix" the package in response to it.

## What not to do

- Do not quote a test count or coverage percentage in any document. Describe the
  gate and let the reader run it.
- Do not suppress a failure with `2>/dev/null || true`. If a generator or gate
  fails, let it fail loudly.
- Do not add a parameter to `config.yaml` without a consumer; the concept runner
  is where parameters are read, and an unread key is a lie about
  configurability.
- Do not delete an untested branch to raise coverage. Prove it is reachable or
  establish that it is not, and record which.
