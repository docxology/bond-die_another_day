# Architecture — die_another_day (ICARUS)

## Layers (dependency direction: `scripts/` → `src/`)

```
scripts/  (thin orchestrators: argv + sys.path bootstrap + one call into src/)
   |
   v
src/die_another_day/
   mission.py          <- the ONLY module importing bond_api (frozen MissionProvider)
   manuscript_variables.py  <- reads manuscript/config.yaml -> {{TOKEN}} map
   figures/plots.py    <- deterministic matplotlib figure generators
   identity_detection.py|ice_ops.py|orbital_mirror.py   <- pure domain core
```

The pure domain modules depend only on `numpy` / `scipy` and are importable
even if `bond_api` is absent. `mission.py` is the thin protocol adapter between
the domain core and the frozen BOND-API contract: it implements
`MissionProvider` (brief / recon / plan / execute / debrief) and registers the
three concept functions as gadgets in the BOND-API `GadgetRegistry`.

## Module responsibilities

| Module | Responsibility |
| --- | --- |
| `identity_detection.py` | `estimate_profile`, `mahalanobis_sq`, `per_marker_z_scores`, `detect_drift`, `generate_identity_samples` |
| `ice_ops.py` | `seconds_to_critical`, `exposure_temperature`, `plan_rotation`, `thermal_load`, `heating_energy`, `plan_briefing` |
| `orbital_mirror.py` | `gmst_radians`, `lwlatlon_to_ecef`, `ecef_to_eci`, `propagate_circular`, `sun_unit_eci`, `elevation_deg`, `in_shadow`, `point_mirror`, `plan_pass` |
| `mission.py` | `MissionProvider` protocol adapter + gadget registration |
| `manuscript_variables.py` | `load_manuscript_config`, `generate_variables`, `resolve_manuscript_tree` |

## Forbidden patterns

- No `infrastructure.*` import in the pure domain modules.
- No `bond_api` import in the pure domain modules (only `mission.py`).
- No business logic in `scripts/`.
- No mocks in `tests/`.

## Adding a new concept (or figure)

1. Add a pure module `src/die_another_day/<concept>.py` (stdlib + numpy/scipy
   only) with typed, deterministic functions.
2. Wire it into `mission.py` `execute()` results and add matching `{{TOKEN}}`s
   in `manuscript_variables.py` if the manuscript should cite its metrics.
3. Add a `tests/test_<concept>.py` (real data, no mocks) and update the token
   cross-reference test if you added tokens.
4. If it needs a figure, add a generator in `figures/plots.py` and a thin
   entry in `scripts/generate_figures.py`.
