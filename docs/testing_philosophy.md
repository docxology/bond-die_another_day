# Testing Philosophy — die_another_day (ICARUS)

## Zero-mock policy

All tests use **real data and real computation** — no `unittest.mock`,
`MagicMock`, `@patch`, or `create_autospec`. The policy exists because mock
tests can pass while the underlying science is wrong: this package's value is
the numerical correctness of its three concepts, so every metric a test asserts
is a genuinely computed value.

## What is tested and why

| Test file | Exercises |
| --- | --- |
| `test_identity_detection.py` | Baseline estimation, Mahalanobis scoring, per-marker z-scores, drift verdicts (replaced vs. genuine), validation branches, deterministic synthetic data. |
| `test_ice_ops.py` | Newton-cooling closed form (`seconds_to_critical`), temperature prediction, rotation roster feasibility, thermal load, heating energy, briefing assembly, validation branches. |
| `test_orbital_mirror.py` | GMST, ECEF/ECI frames, orbit propagation, elevation, shadow test, reflection-law pointing, delivered power/flux, pass planning windows, validation branches. |
| `test_mission.py` | Full `MissionProvider` lifecycle (brief→recon→plan→execute→debrief), gadget registration, deterministic outcome, protocol discovery by slug. |
| `test_manuscript_variables.py` | Config loading, `{{TOKEN}}` map, strict resolution, and the live cross-reference gate over `manuscript/[0-9]*.md`. |
| `test_scripts_smoke.py` | Thin CLIs run end-to-end via subprocess (`sys.executable`, cwd=project root); artifact + exit-code assertions. |

## Determinism

Synthetic data (the enrolled biometric population) uses a fixed seed (`7`).
No untracked random draws; no wall-clock in persisted artifacts
(provenance `wall_time_s = 0.0`). A determinism test reruns the mission and
byte-compares the outcome.

## Coverage gate

```bash
cd projects/working/bond/die_another_day
uv run pytest tests/ --cov=src --cov-fail-under=90
```

`--cov-fail-under=90` enforces ≥90% line **and** branch on `src/`. Cover error
paths (validation `ValueError` branches), container edge cases, and the
feature-detect/no-feature branches of each concept.
