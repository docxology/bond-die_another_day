# docs/ — agent guide

Index for `die_another_day/docs/`. Each document is a constraint on how this
package may be changed, not a suggestion.

| Before you… | Read |
| --- | --- |
| edit anything | [`agent_instructions.md`](agent_instructions.md) |
| move logic between `scripts/`, `src/`, and `mission.py` | [`architecture.md`](architecture.md) |
| add or change a test | [`testing_philosophy.md`](testing_philosophy.md) |
| touch the paper or a token | [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) |

## Non-negotiables, in one screen

- `mission.py` is the only module that may import `bond_api`. Its public shape
  — the `MissionProvider` class with `brief` / `recon` / `plan` / `execute` /
  `debrief`, and the module-level `ICARUS_GADGETS` registry — is **frozen**:
  bond-cli, the coordinator, and the orchestrator consume it across packages.
  Deepen inside the package; never change that surface.
- The six domain modules must stay importable without `bond_api`.
- `scripts/` holds thin orchestrators only. A test parses each one and fails on
  a second top-level function, a class, or a numpy/scipy/matplotlib import.
- No mock framework anywhere in `tests/`.
- Determinism: seed `7`, no wall-clock in persisted artifacts, PNG `Date`
  metadata suppressed so figures are byte-reproducible.
- Manuscript numbers are injected tokens, never typed prose.

## Test and coverage counts

Do not quote a test count or a coverage percentage in any document here — it
goes stale the moment someone adds a test. Describe the *gate* instead, and let
the reader run it:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

The floor is 90% line **and** branch on `src/`; the command prints the current
measurement and exits non-zero below the floor.
