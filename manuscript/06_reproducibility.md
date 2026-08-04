# Reproducibility

The package is deterministic by construction:

- **Fixed seed**: all synthetic data (the enrolled biometric population) is
  drawn with a fixed seed, so the mission outcome is byte-reproducible across
  runs (`src/die_another_day/mission.py`).
- **No wall-clock in artifacts**: provenance records a `wall_time_s` of `0.0`;
  only `{{GENERATION_TIMESTAMP}}` (a manuscript token) records when variables
  were hydrated.
- **Zero mocks**: `tests/` uses real computation and real data only.
- **Coverage gate**: `uv run pytest tests/ --cov=src --cov-fail-under=90`
  enforces >= 90% line-and-branch coverage.
- **Type and style gates**: `uv run ruff check src/ scripts/` and
  `uv run mypy src/ scripts/` are clean.
- **Token hygiene**: the live cross-reference test (`tests/test_manuscript_variables.py`)
  guarantees every mission `TOKEN` in `manuscript/[0-9]*.md` is produced by
  `generate_variables()`; strict generation fails on any unresolved token.

Python version: {{PYTHON_VERSION}}.
