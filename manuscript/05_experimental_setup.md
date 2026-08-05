# Experimental Setup

All mission parameters are declared once in `manuscript/config.yaml` under the
`concepts:` block and consumed by the code via
`src/die_another_day/mission_results.py`. They are reproduced here as mission
tokens so the manuscript cannot drift from the configuration. Package identity:
`{{MISSION_IDENTITY}}` (codename {{MISSION_CODENAME}}), deterministic seed
{{MISSION_SEED}}.

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

## Ice-palace operations

- Ambient temperature: {{ICE_ENV_TEMP_C}} C
- Body/core temperature: {{ICE_BODY_TEMP_C}} C
- Critical (minimum safe) core temperature: {{ICE_CRITICAL_TEMP_C}} C
- Cooling decay rate: {{ICE_DECAY_RATE_H}} /hour
- Operatives available: {{ICE_NUM_OPERATIVES}}
- Operation duration: {{ICE_OP_DURATION_S}} s

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
- Ground target: {{ORBIT_TARGET_LAT_DEG}} N, {{ORBIT_TARGET_LON_DEG}} E
- Pass window: {{ORBIT_DURATION_S}} s sampled every {{ORBIT_DT_S}} s
  ({{MIRROR_PASS_SAMPLES}} instants)
- Mirror area: {{MIRROR_AREA_M2}} m^2
- Mirror reflectivity: {{MIRROR_REFLECTIVITY}}
- Beam half-angle: {{MIRROR_BEAM_HALF_ANGLE_DEG}} deg
- Minimum targeting elevation: {{MIRROR_MIN_ELEVATION_DEG}} deg

## Software environment

- Python: {{PYTHON_VERSION}}
- Concept modules ({{NUM_CONCEPTS}}): {{CONCEPT_MODULES}}
- Variables generated: {{GENERATION_TIMESTAMP}} (UTC)

## What is configured versus what is measured

The lists above are *inputs*: every one is a literal in
`manuscript/config.yaml`. Everything in §03 is an *output*: it comes from
running the models on these inputs. The two families are formatted by different
code paths (`generate_variables` for inputs, `measured_variables` for outputs)
and a test asserts that each measured token equals the value the concept runner
produced, so an input can never be quietly presented as a result.
