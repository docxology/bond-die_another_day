# die_another_day TODO

Forward-only backlog for the ICARUS film package (*Die Another Day*, 2002) in
the PROJECT BOND suite. Completed work is not listed here — the code, the
manuscript, and `docs/` describe what exists. This file is only what is *not*
done.

## Open work

### 1. Robust covariance for heavy-tailed biomarkers

`identity_detection.estimate_profile` fits a plain sample covariance with a
ridge term. A single extreme enrolment sample therefore inflates the covariance
and desensitises the screen. Add an optional robust estimator (minimum
covariance determinant, or a simple trimmed estimate) behind a keyword
argument, and a test that shows the plain estimator missing a replacement that
the robust one catches. Keep the default unchanged so existing numbers hold.

### 2. Unaligned sequence reads

`verify_identity` requires equal-length reference and probe. Real reads are not
pre-aligned. Either add a lightweight alignment step before the contiguous-block
test, or document the precondition as a hard interface requirement and reject
unaligned input with a clearer error than the current length check. The
Levenshtein distance already tolerates indels; the block detector does not.

### 3. Conical eclipse and finite solar disc

`orbital_mirror.in_shadow` uses a cylindrical shadow, so penumbra is treated as
full sunlight. The solar disc is also treated as a point source, which
understates the achievable spot size. Both are acceptable for feasibility
questions and inadequate for illumination engineering. Upgrading these is the
single largest fidelity gain available in this module.

### 4. Per-operative thermal parameters

`ice_ops.plan_briefing` uses one Newton decay rate for the whole squad, and
`plan_rotation` assumes instantaneous handover. A per-operative rate (suit,
body composition) and a handover cost would make the roster a scheduling
problem rather than a division.

### 5. Ice-structure dynamics

`ice_structure` is a static check: bearing capacity plus thermal stress at one
instant. It does not model creep under sustained load, crack propagation once
the tensile limit is passed, or repeated loading. A time-dependent model would
turn the current pass/fail into a time-to-failure.

## Integration points

- **bond-api** (frozen dependency) — implemented via a path dependency. The
  `MissionProvider` shape and the module-level `ICARUS_GADGETS` registry are
  unchanged and must stay that way; bond-cli, the coordinator reconcile, and the
  orchestrator all consume them.
- **bond-utilities** — not yet adopted here. If and when it provides
  `mission_io.record_provenance_outcome`, delegate outcome persistence to it.
  The pure core stays infrastructure-free either way.
- **bond-orchestrator / bond-cli** — consume this film through slug discovery
  (`load_provider("die_another_day")`); they never reach into film internals.

## Standing constraints (not tasks — do not "resolve" these)

- Seed stays `7`; changing it changes every reported number.
- `mission_results.run_all_concepts` stays the single execution path. A second
  path is how the manuscript starts disagreeing with the code.
- Coverage floor is 90% line and branch; do not quote the measured percentage in
  prose anywhere in this package.
