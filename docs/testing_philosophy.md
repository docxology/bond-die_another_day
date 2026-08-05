# Testing philosophy — `die_another_day` (ICARUS)

## Why no mocks

No `unittest.mock`, `MagicMock`, `mocker.patch`, `@patch`, or
`create_autospec` appears anywhere in `tests/`. The reason is specific to this
package rather than stylistic: everything of value here is a *number*. A mock
lets a test pass while the physics is wrong, which is precisely the failure this
suite exists to catch. Every assertion in this suite is made against a value
that was actually computed from real inputs.

Environment isolation (`tmp_path`, `monkeypatch` for env vars) is not
dependency replacement and is permitted. Subprocess execution of the real
scripts is preferred over importing and stubbing them.

## The stronger rule: nothing may be true by construction

A green test that could not have failed is worse than no test — it converts an
unexamined assumption into apparent evidence. The suite carries explicit guards
against four ways that happens, each of which had actually occurred in this
package before being fixed:

| Failure mode | Where it bit | How it is pinned now |
| --- | --- | --- |
| **Degenerate negative control.** The "genuine" biometric probe was `profile.mean`, whose Mahalanobis distance is exactly 0. "The genuine operative clears" was arithmetic, not measurement. | `mission.execute` | `mission_results.genuine_probe` draws a fresh out-of-sample operative; `test_negative_control_is_a_real_draw_not_the_profile_mean` asserts the score is strictly positive *and* below threshold. |
| **Metric that is zero by construction.** Cold strain was integrated below room comfort (20 C), but a survivable shift ends at the 30 C critical core temperature, so the integral was identically zero for every valid plan. | `ice_ops.thermal_load` | The integral is referenced to normothermia; `test_thermal_load_is_strictly_positive_for_the_operational_shift` asserts the new value is positive *and* that the old comfort-referenced form returns exactly zero. |
| **Assertion that cannot fail.** `assert load >= 0.0` on a non-negative integral; `assert threshold > 0` on a chi-square quantile. | `test_ice_ops.py`, `test_identity_detection.py` | Both replaced with analytic oracles — the closed-form cold-strain integral, and a probe placed exactly on the $\alpha$ quantile whose reported *p*-value must equal $\alpha$. |
| **Shape test standing in for a behaviour test.** `assert "def main()" in source`. | `test_scripts_smoke.py` | Replaced by an AST gate that fails on a second top-level function, a class, a missing docstring, a wrong return annotation, or a direct numpy/scipy/matplotlib import. |

When adding a test, ask what input would make it fail. If you cannot name one,
the test is decoration.

## Unreachable-looking gates: prove them, do not delete them

Two validation branches look like dead code — the `ratio >= 1.0` guards in
`ice_ops.seconds_to_critical` and `hypothermia.time_to_core_temp`, both of
which sit behind an ordering check that seems to make them impossible. They are
not dead: with an extreme ambient the floating-point division rounds to exactly
1.0 while the ordering still holds, and without the guard the function would
silently return a zero time. Each has a test that reaches it
(`test_fp_degenerate_ratio_guard_is_reachable`).

One branch genuinely was dead — the empty-union check in
`sequence_identity.kmer_jaccard`, unreachable because the length precondition
guarantees non-empty k-mer sets. That one was removed, with a comment recording
why. Prove or delete; do not leave an untested branch to imply robustness it
does not provide.

## What each test file binds

| Test file | What it exercises |
| --- | --- |
| `test_identity_detection.py` | Baseline estimation and its singular-covariance pseudo-inverse fallback, Mahalanobis scoring, per-marker z-scores, chi-square calibration against an exact quantile probe, threshold crossing from both sides, validation branches, deterministic synthesis. |
| `test_sequence_identity.py` | Genome synthesis and GC content, deterministic mutation, Hamming/Levenshtein/Jaccard scoring, contiguous-cluster detection, matched-versus-replacement verdicts, validation branches. |
| `test_ice_ops.py` | Newton closed form against a known value and for monotonicity, rotation feasibility including the operative-limited case, cold strain against its analytic integral, heating energy, briefing assembly, the fp-degenerate guard. |
| `test_hypothermia.py` | Mass and insulation scaling of the cooling rate, forward/backward cooling solutions, exact clinical stage boundaries, rescue feasibility on both sides, the fp-degenerate guard, validation branches. |
| `test_ice_structure.py` | Bearing capacity and its inverse, safety factor including the unloaded infinity case, thermal stress and critical gradient, the combined verdict, validation branches. |
| `test_orbital_mirror.py` | Sidereal time, ECEF/ECI frames, orbit propagation and radius invariance, elevation above/below horizon, eclipse test, the solar-ray regression, the reflection-law bisector identity, degenerate-bisector infeasibility, delivered power against its closed form, feasible and empty pass windows. |
| `test_mission_results.py` | Determinism of the whole run, positive and negative controls, seed sensitivity (stochastic outputs move, physics outputs do not), config consumption (a changed parameter must move the output), and graceful degradation on absent or malformed config sections. |
| `test_mission.py` | The full `MissionProvider` lifecycle, protocol conformance, gadget registration and ordering, deterministic outcome equality, discovery by slug. |
| `test_manuscript_variables.py` | Config loading and its error paths, strict token resolution, the measured-token equality check against the runner, config-sensitivity of measured tokens, and both directions of the token/section cross-reference. |
| `test_figures.py` | Real rendering to temp paths, PNG magic bytes, byte-identical re-renders, and the no-feasible-window branch. |
| `test_scripts_smoke.py` | Every script executed as a real subprocess with output and exit-code assertions, plus the AST-level thin-orchestrator gate. |

## Determinism

Seed `7` throughout. Synthetic populations, reference genomes, and probe
construction all derive from it. Two tests make the seed falsifiable: one
re-runs the concept runner and compares the entire result record, another
changes the seed and asserts the stochastic outputs move while the pure-physics
outputs stay identical. Figures are byte-reproducible because the saver
suppresses matplotlib's PNG `Date` chunk, and a test compares two renders
byte-for-byte. Persisted provenance carries `wall_time_s = 0.0` — no wall clock
enters an artifact.

## Coverage

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

The floor is 90% line **and** branch on `src/`; the command prints the current
measurement. Do not transcribe that number into any document — it goes stale
and nobody re-derives it. Quote the gate, not the reading.

Coverage is a floor, not a goal. A hundred percent of lines executed with weak
assertions is worth less than eighty percent with oracles. Prefer adding an
assertion that can fail over adding a line that merely runs.
