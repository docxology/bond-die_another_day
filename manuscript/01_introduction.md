# Introduction

{{MISSION_TITLE}} is the PROJECT BOND film package for *Die Another Day*
(2002), mission codename **{{MISSION_CODENAME}}** (version {{MISSION_VERSION}}).
{{MISSION_SUBTITLE}}.

An ICARUS-class special agent operates across three theatres, each encoded in
{{NUM_CONCEPTS}} dedicated, infrastructure-free domain modules under
`src/die_another_day/`:

1. `identity_detection.py` + `sequence_identity.py` — detect when an operative
   has been replaced by a gene-therapy-grade impostor, both at the biometric
   (marker-vector) level and at the DNA-sequence level;
2. `ice_ops.py` + `hypothermia.py` + `ice_structure.py` — plan operations in
   the extreme cold of an ice palace: air-exposure ceilings and rotation,
   cold-water immersion/rescue risk, and the structural integrity of the ice
   itself;
3. `orbital_mirror.py` — aim an orbiting solar mirror at a ground target,
   solving the line-of-sight and reflection geometry.

Two further modules complete the package without adding domain science.
`mission_results.py` is the single deterministic runner: it reads the
configuration, executes all {{NUM_CONCEPTS}} models once under seed
{{MISSION_SEED}}, and returns one frozen record. `mission.py` is a thin adapter
that turns that record into the frozen BOND-API `MissionProvider` contract, so
the orchestrator can discover and run the film by slug on `sys.path`. The pure
domain modules remain importable without `bond_api`; only the adapter couples
the two layers.

That structure is what lets this manuscript state measured numbers safely: the
results in §03 and the mission's own `MissionOutcome` are formatted from the
same record, so there is no second code path along which they could drift.

The remainder of this manuscript documents the methodology (§02), results
(§03), scope and limitations (§07), experimental setup (§05), and
reproducibility guarantees (§06) of the package.
