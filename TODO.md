# die_another_day TODO

Forward-only backlog for the ICARUS film package (Die Another Day, 2002),
mission codename **ICARUS**, in the PROJECT BOND suite.

## Status — Phase 4 (deep improvement)

Six pure deterministic domain modules behind a frozen-protocol
`MissionProvider`, plus per-phase thin CLIs, token-hydrated manuscript, four
concept figures, and a zero-mock test suite.

- `identity_detection.py` — gene-therapy-grade biometric identity-replacement
  detection (Mahalanobis trait drift + coherent per-marker z-flags).
- `sequence_identity.py` — DNA sequence identity verification (Levenshtein
  edit distance + k-mer Jaccard + contiguous edit-block detection).
- `ice_ops.py` — ice-palace cold-environment air operations planning
  (Newton-cooling exposure ceilings + rotation roster + thermal/heating
  metrics).
- `hypothermia.py` — cold-water immersion core-temperature model and rescue
  feasibility against the clinical hypothermia timeline.
- `ice_structure.py` — ice-palace structural integrity (Gold load-capacity
  rule + thermal-gradient stress / cracking threshold).
- `orbital_mirror.py` — orbital-mirror (ICARUS) targeting geometry
  (circular-orbit propagation, reflection-law pointing, solar-flux delivery).
- `mission.py` — implements the frozen BOND-API `MissionProvider`; registers
  all six concept functions as gadgets in the BOND-API `GadgetRegistry`.

## Current validation evidence

- Tests + coverage gate: `uv run pytest tests/ --cov=src --cov-fail-under=90`
  (>98% line + branch on `src/`; live numbers ->
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md))
- Code quality: `uv run ruff check src/ scripts/ tests/` and
  `uv run mypy src/ scripts/` both pass clean.
- No mocks: `grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/`
- Manuscript token gate: `uv run python scripts/z_generate_manuscript_variables.py`
  (strict; unresolved `{{TOKEN}}` fails) + live cross-reference in
  `tests/test_manuscript_variables.py`.
- Determinism: fixed seed `7`; provenance `wall_time_s = 0.0`; mission outcome
  byte-reproducible.

## Integration points (declared)

- **bond-api** (frozen, dependency) — implemented via path dependency in
  `pyproject.toml`; the mission adapter imports `bond_api.protocol` /
  `bond_api.registry` / `bond_api.serialization`. Public `MissionProvider`
  shape and the module-level `ICARUS_GADGETS` GadgetRegistry are unchanged, so
  bond-cli / coordinator / orchestrator discovery is stable.
- **bond-utilities** — not yet converted to a real utilities package; if/when
  it lands, delegate provenance persistence (`mission_io.record_provenance_outcome`).
  Pure core stays infrastructure-free either way.
- **bond-orchestrator / bond-cli** — consume this film via slug discovery
  (`load_provider("die_another_day")` on `sys.path`); no film internals.

## Known gaps / constraints

- Orbital solar ephemeris is low-precision (coarse unit vector); adequate for
  feasibility modelling, not precise illumination engineering.
- Biomarker distribution assumed Gaussian; heavy-tailed traits would need
  robust covariance estimation.
- DNA sequence model assumes equal-length reads (indel-tolerant via edit
  distance, but verification requires aligned length).
- Single circular orbit per pass; no constellation or propagation-error model.

## Ordered improvement ladder

1. Keep all six pure concepts deterministic and standalone; any math change
   must keep the test suite green.
2. When bond-utilities ships, adopt `mission_io.record_provenance_outcome` for
   outcome persistence.
3. Optionally add a robust-covariance layer to identity detection.
4. Refresh generated docs / figures after any public-surface change.
