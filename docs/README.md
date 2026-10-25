# docs/ — agent-facing documentation for `die_another_day` (ICARUS)

The technical rulebook for working inside this package. It documents the
package as it actually is.

## What lives here

| File | Read it when |
| --- | --- |
| [`agent_instructions.md`](agent_instructions.md) | **First.** The operating rules, the editing workflow, and the verification checklist you must clear before claiming done. |
| [`architecture.md`](architecture.md) | Before touching module boundaries, adding a concept, or changing what `mission.py` exposes. Module-by-module map of `src/`, the dependency direction, and how the frozen `MissionProvider` is implemented. |
| [`testing_philosophy.md`](testing_philosophy.md) | Before writing or editing any test. The no-mock doctrine, what each test file binds, and the specific failure modes this suite is built to catch. |
| [`AGENTS.md`](AGENTS.md) | A short index of the above for an agent scanning the tree. |
| `README.md` | This file. |

Manuscript-specific rules live one directory over, in
[`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) and
[`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md); root-level orientation is
in [`../README.md`](../README.md) and [`../AGENTS.md`](../AGENTS.md).

## The package in one paragraph

`die_another_day` is the PROJECT BOND film package for *Die Another Day* (2002),
mission codename **ICARUS**. It implements six concepts from the film as pure,
deterministic, tested algorithms — biometric identity-replacement detection,
DNA sequence identity verification, ice-palace thermal operations, cold-water
hypothermia risk, ice-structure integrity, and orbital-mirror targeting — plus
one runner that executes them all under a fixed seed and one thin adapter that
exposes them as a frozen BOND-API `MissionProvider`.

## The three invariants everything else serves

1. **The domain core knows nothing about the protocol.** The six concept
   modules import numpy/scipy and nothing else from this ecosystem. Only
   `mission.py` imports `bond_api`.
2. **One run, two consumers.** `mission_results.run_all_concepts` is the single
   execution path. The `MissionOutcome` and the manuscript's measured tokens are
   both formatted from its output, so they cannot diverge.
3. **Nothing is true by construction.** Negative controls are real draws, gates
   are reachable, metrics are non-degenerate, and tests assert values rather
   than shapes. `testing_philosophy.md` records where this was violated before
   and how each violation is now pinned.
