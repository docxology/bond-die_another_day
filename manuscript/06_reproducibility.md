# Reproducibility

The package is deterministic by construction:

- **Fixed seed**: all synthetic data (the enrolled biometric population and the
  reference genome) is drawn with seed {{MISSION_SEED}}, so the mission outcome
  is reproducible across runs
  (`src/die_another_day/mission_results.py`). A test re-runs the concept runner
  and compares the whole `ConceptResults` record; a second test changes the
  seed and asserts the stochastic outputs move while the pure-physics ones do
  not, so the seed is demonstrably load-bearing rather than decorative.
- **No wall-clock in artifacts**: provenance records a `wall_time_s` of `0.0`;
  only `{{GENERATION_TIMESTAMP}}` (a manuscript token) records when variables
  were hydrated.
- **Byte-reproducible figures**: the figure saver suppresses matplotlib's PNG
  `Date` metadata chunk, and `tests/test_figures.py` renders each figure twice
  and compares the bytes.
- **Zero mocks**: `tests/` uses real computation and real data only — no
  `unittest.mock`, `MagicMock`, or `mocker.patch` anywhere in the suite.
- **Coverage gate**: `uv run pytest tests/ --cov=src --cov-fail-under=90`
  fails the run below the line-and-branch floor. The measured figure is not
  quoted here; run the command to obtain the current number.
- **Type and style gates**: `uv run ruff check src/ scripts/`,
  `uv run ruff format --check src/ scripts/`, and `uv run mypy src/` are clean.
- **Token hygiene**: two live gates in `tests/test_manuscript_variables.py` —
  every mission token cited in `manuscript/[0-9]*.md` must be produced by
  `generate_variables()`, and every token `generate_variables()` produces must
  be cited by some section (no orphan tokens). Strict generation additionally
  fails on any unresolved token left in a rendered section.
- **Thin-orchestrator gate**: `tests/test_scripts_smoke.py` parses every script
  in `scripts/` and fails if one grows a second top-level function, a class, or
  a direct numpy/scipy/matplotlib import — the mechanical form of the
  layer contract.

Python version: {{PYTHON_VERSION}}.
