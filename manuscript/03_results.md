# Results

Running the deterministic mission (`uv run python scripts/run_mission.py`)
exercises all {{NUM_CONCEPTS}} concepts and reports measured outcomes.

## Identity-replacement detection (biometric)

The enrolled baseline is synthesized deterministically. A gene-therapy-grade
probe — a coherent shift of {{IDENTITY_STD_THRESHOLD}}-standard-deviation
magnitude on the first {{IDENTITY_MIN_MARKERS}} markers — is flagged with a
Mahalanobis statistic well past the $\chi^2_{1-{{IDENTITY_ALPHA}}}$ threshold
for the $k =$ {{NUM_BIOMARKERS}}-marker profile; the genuine profile clears the
same test.

![Per-marker standardized trait drift for the genuine and replaced probes. The
dashed lines mark the $\pm${{IDENTITY_STD_THRESHOLD}} flagging
threshold.](output/figures/icarus_identity_drift.png){#fig:icarus_drift}

## Identity-replacement detection (sequence)

The {{SEQ_GENOME_LENGTH}}-base reference genome is enrolled, then probed with a
genuine read ({{SEQ_KMER_K}}-mer Jaccard above the {{SEQ_MATCH_JACCARD}} match
threshold, no edit block) and with a replaced read carrying a coherent
{{SEQ_CLUSTER_MIN}}-base substitution block. The replaced probe is flagged: its
contiguous edit block is unmistakable, whereas the genuine read — even with
isolated sequencing noise — matches. The mismatch map shows the replaced
probe's single contiguous cluster against the genuine probe's isolated errors.

![DNA mismatch map for the replaced probe: the contiguous edit cluster is
shaded against isolated single-base errors.](output/figures/icarus_sequence_mismatch.png){#fig:icarus_sequence}

## Ice-palace operations

From the configured physics (ambient {{ICE_ENV_TEMP_C}} C, one
{{ICE_OP_DURATION_S}}-second op, {{ICE_NUM_OPERATIVES}} operatives), the planner
derives the safe-exposure ceiling and a rotating roster. The air plan is
feasible exactly when the per-squad shift stays under the ceiling, and reports
integrated cold stress and heating energy.

## Cold-water hypothermia risk

In {{HYP_WATER_TEMP_C}} C water, a {{HYP_MASS_KG}} kg operative cools through
the mild/moderate/severe clinical thresholds on a minutes-timescale. The rescue
plan — a {{HYP_DISTANCE_M}} m sweep at {{HYP_SWEEP_SPEED_M_S}} m/s — reaches
the operative before the severe (28 C) stage, reporting a positive margin and a
core temperature still in the safe range. The immersion curve below shows the
core-temperature decay and the stage thresholds.

![Cold-water immersion core-temperature decay with mild/moderate/severe stage
thresholds.](output/figures/icarus_hypothermia_curve.png){#fig:icarus_hypothermia}

## Ice-structure integrity

The palace ice at {{STRUCT_THICKNESS_CM}} cm carries the {{STRUCT_LOAD_TONS}} t
load with a safety factor above one, but a {{STRUCT_DELTA_T_C}} C thermal
gradient produces a tensile stress above the {{STRUCT_ICE_STRENGTH_MPA}} MPa
strength — the structure is at thermal-cracking risk even though it holds its
load.

## Orbital-mirror targeting

Propagating the {{ORBIT_SMA_KM}}-km circular orbit over the configured window
produces a pass with a feasible window during which the mirror is sunlit and
above the {{MIRROR_MIN_ELEVATION_DEG}}-degree horizon; the best-illumination
moment (peak focused flux) is marked.

![ICARUS orbital-mirror elevation vs. time over the ground target. The shaded
band marks the feasible targeting window and the red point the peak-flux
instant.](output/figures/icarus_pass_profile.png){#fig:icarus_pass}
