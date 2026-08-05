# Experimental Setup

All mission parameters are declared once in `manuscript/config.yaml` under the
`concepts:` block and consumed by the code via
`src/die_another_day/mission_results.py`. They are reproduced here as mission
tokens so the manuscript cannot drift from the configuration. Package identity:
`{{MISSION_IDENTITY}}` (codename {{MISSION_CODENAME}}), deterministic seed
{{MISSION_SEED}}.

The seed is the single module constant `mission_results.MISSION_SEED`, not a
configuration key: `config.yaml` carries no seed of its own, so no consumer can
be reading a different one from the run this paper reports.

The list below is complete by construction rather than by inspection. Every
`concepts.<section>.<key>` in `manuscript/config.yaml` is registered in
`manuscript_variables.CONFIG_INPUT_TOKENS`, and
`test_every_configured_input_is_registered_and_cited` fails if the registry and
the file disagree, or if a registered token is not cited in this section.

## Identity detection

- Biomarker markers: {{NUM_BIOMARKERS}}
- Test size $\alpha$: {{IDENTITY_ALPHA}}
- Per-marker $z$ threshold: {{IDENTITY_STD_THRESHOLD}}
- Minimum flagged markers: {{IDENTITY_MIN_MARKERS}}

## DNA sequence identity

- Genome length: {{SEQ_GENOME_LENGTH}} bases
- k-mer size: {{SEQ_KMER_K}}
- Match Jaccard threshold: {{SEQ_MATCH_JACCARD}}
- Edit-cluster minimum: {{SEQ_CLUSTER_MIN}} bases
- Scattered single-base errors per read: {{SEQ_SCATTERED_ERRORS}}

## Ice-palace operations

- Ambient temperature: {{ICE_ENV_TEMP_C}} C
- Body/core temperature: {{ICE_BODY_TEMP_C}} C
- Critical (minimum safe) core temperature: {{ICE_CRITICAL_TEMP_C}} C
- Cooling decay rate: {{ICE_DECAY_RATE_H}} /hour
- Operatives available: {{ICE_NUM_OPERATIVES}}
- Operation duration: {{ICE_OP_DURATION_S}} s
- Envelope thermal conductance: {{ICE_THERMAL_CONDUCTANCE_W_K}} W/K

## Cold-water hypothermia risk

- Water temperature: {{HYP_WATER_TEMP_C}} C
- Operative mass: {{HYP_MASS_KG}} kg
- Insulation factor: {{HYP_INSULATION}}
- Rescue distance: {{HYP_DISTANCE_M}} m
- Sweep speed: {{HYP_SWEEP_SPEED_M_S}} m/s

## Ice-structure integrity

- Ice thickness: {{STRUCT_THICKNESS_CM}} cm
- Applied load: {{STRUCT_LOAD_TONS}} t
- Thermal gradient: {{STRUCT_DELTA_T_C}} C
- Tensile strength: {{STRUCT_ICE_STRENGTH_MPA}} MPa

## Orbital-mirror targeting

- Orbit semi-major axis: {{ORBIT_SMA_KM}} km
- Orbit inclination: {{ORBIT_INCLINATION_DEG}} deg
- Right ascension of the ascending node: {{ORBIT_RAAN_DEG}} deg
- Mean anomaly at epoch: {{ORBIT_MEAN_ANOMALY_DEG}} deg
- Epoch (Julian date): {{ORBIT_JD_START}}
- Ground target: {{ORBIT_TARGET_LAT_DEG}} N, {{ORBIT_TARGET_LON_DEG}} E
- Pass window: {{ORBIT_DURATION_S}} s sampled every {{ORBIT_DT_S}} s
  ({{MIRROR_PASS_SAMPLES}} instants)
- Mirror area: {{MIRROR_AREA_M2}} m^2
- Mirror reflectivity: {{MIRROR_REFLECTIVITY}}
- Beam half-angle: {{MIRROR_BEAM_HALF_ANGLE_DEG}} deg
- Lumped one-way transmission factor: {{MIRROR_ATMOSPHERE_TRANSMISSION}}
- Minimum targeting elevation: {{MIRROR_MIN_ELEVATION_DEG}} deg

The epoch, RAAN, and mean anomaly are not incidental: together with the
inclination they select *which* pass the {{ORBIT_DURATION_S}}-second window
lands on, and hence every number in §03's orbital-mirror row. They were chosen
so that a pass occurs over the target inside the window — a hand-tuned
geometry, stated here rather than buried in a default.

## Software environment

- Python: {{PYTHON_VERSION}}
- Concept modules ({{NUM_CONCEPTS}}): {{CONCEPT_MODULES}}
- Package version: {{MISSION_VERSION}} (`manuscript/config.yaml`, `paper.version`)

There is deliberately no generation timestamp in this list. An earlier draft
hydrated one from the wall clock, which made every regeneration of the
manuscript differ in bytes while §00 and §06 claimed determinism; §06 states the
property that replaced it, and a test enforces it.

## What is configured versus what is measured

The lists above are *inputs*: every one is a literal in
`manuscript/config.yaml`. Everything in §03 is an *output*: it comes from
running the models on these inputs. The two families are formatted by different
code paths (`generate_variables` for inputs, `measured_variables` for outputs)
and a test asserts that each measured token equals the value the concept runner
produced.

That test binds provenance, not independence: it proves a §03 number came out
of the runner, not that the runner had any freedom in producing it. Three
tokens are worth naming because they are *structurally determined* by inputs
and would look like findings otherwise:

- `SEQ_GENUINE_HAMMING` equals `scattered_errors` whenever the mutation
  generator behaves — it applies exactly that many substitutions at distinct
  loci, each guaranteed to change the base. Read it as a check on the
  generator, not as a measurement of sequencing noise.
- `SEQ_LONGEST_BLOCK` is bounded below by `cluster_min` for the same reason;
  it can only exceed it if a scattered error happens to abut the block. The
  informative comparison is against `SEQ_GENUINE_LONGEST_RUN`, which is free to
  be anything and is what makes the separation a result.
- `ID_REPLACED_SHIFT_SIGMA` is a construction parameter of the positive
  control (`REPLACEMENT_SHIFT_FACTOR` times the configured threshold), reported
  so §03 states the probe's actual magnitude instead of reusing the threshold
  token.

Everything else in §03 — every score, verdict, time, flux, and safety factor —
is free to move with the inputs, and
`test_measured_tokens_track_the_configuration` demonstrates that it does.
