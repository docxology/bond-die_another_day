# Results

Running the deterministic mission (`uv run python scripts/run_mission.py`)
exercises all {{NUM_CONCEPTS}} concepts under seed {{MISSION_SEED}} and reports
measured outcomes. Every number below is produced by
`src/die_another_day/mission_results.py` — the same entry point the
`MissionProvider` uses for its `MissionOutcome` — and injected as a manuscript
token, so the paper and the code cannot disagree.

## Identity-replacement detection (biometric)

Two probes are scored against the enrolled Gaussian baseline: a positive
control (a coherent {{ID_REPLACED_SHIFT_SIGMA}}-sigma shift on the first
{{IDENTITY_MIN_MARKERS}} markers, the remaining markers left at the population
mean, plus small noise) and a negative control (a fresh out-of-sample operative
drawn from the same enrolled population). The shift magnitude is
{{ID_REPLACED_SHIFT_SIGMA}} sigma, deliberately clear of — and not equal to —
the {{IDENTITY_STD_THRESHOLD}}-sigma per-marker flagging threshold it must
cross.

| Probe | Mahalanobis $D^2$ | $\chi^2$ threshold | markers flagged | verdict |
| --- | --- | --- | --- | --- |
| replaced (positive control) | {{ID_REPLACED_SCORE}} | {{ID_CHI2_THRESHOLD}} | {{ID_REPLACED_FLAGGED}} | replacement |
| genuine (negative control) | {{ID_GENUINE_SCORE}} | {{ID_CHI2_THRESHOLD}} | {{ID_GENUINE_FLAGGED}} | cleared |

The replaced probe scores {{ID_REPLACED_SCORE}} against a threshold of
{{ID_CHI2_THRESHOLD}} at $\alpha =$ {{IDENTITY_ALPHA}} on
{{NUM_BIOMARKERS}} degrees of freedom, with {{ID_REPLACED_FLAGGED}}
individually flagged markers — both conditions of the {{ID_METHOD}} rule. The
genuine draw scores {{ID_GENUINE_SCORE}} ($p =$ {{ID_GENUINE_P_VALUE}}) with
{{ID_GENUINE_FLAGGED}} flagged markers and is cleared. The negative control is
deliberately not the profile mean, which would score exactly zero and make
clearance true by construction rather than measured.

![Per-marker standardized trait drift for the two probes that produced the
verdicts in the table above — the out-of-sample genuine draw and the
{{ID_REPLACED_SHIFT_SIGMA}}-sigma replaced probe — plotted from the same
`ConceptResults` record. The dashed lines mark the
$\pm${{IDENTITY_STD_THRESHOLD}} flagging
threshold.](output/figures/icarus_identity_drift.png){#fig:icarus_drift}

## Identity-replacement detection (sequence)

The {{SEQ_GENOME_LENGTH}}-base reference genome is probed with a genuine read
carrying {{SEQ_SCATTERED_ERRORS}} scattered single-base errors and with a
replaced read carrying an *independent* draw of {{SEQ_SCATTERED_ERRORS}}
scattered errors plus a coherent {{SEQ_CLUSTER_MIN}}-base substitution block.
The two reads are matched on the number of scattered errors, not on their
positions: the block consumes RNG draws before the scattered positions and
removes its own loci from the available pool, so the scattered sets differ.
What separates the probes is therefore the block alone, which is exactly the
control the contiguous-run rule is being tested against.

| Probe | {{SEQ_KMER_K}}-mer Jaccard | Hamming | edit distance | longest contiguous block | verdict |
| --- | --- | --- | --- | --- | --- |
| genuine | {{SEQ_GENUINE_JACCARD_MEASURED}} | {{SEQ_GENUINE_HAMMING}} | {{SEQ_GENUINE_EDIT_DISTANCE}} | {{SEQ_GENUINE_LONGEST_RUN}} | matched |
| replaced | {{SEQ_REPLACED_JACCARD_MEASURED}} | {{SEQ_REPLACED_HAMMING}} | {{SEQ_REPLACED_EDIT_DISTANCE}} | {{SEQ_LONGEST_BLOCK}} | replacement suspected |

Hamming and edit distance are separate statistics and are reported separately:
they coincide for the genuine read but not for the replaced one, where the
contiguous block admits a cheaper alignment ({{SEQ_REPLACED_HAMMING}} versus
{{SEQ_REPLACED_EDIT_DISTANCE}}).

Fingerprint similarity alone does not separate the two probes — both clear the
{{SEQ_MATCH_JACCARD}} match threshold, at {{SEQ_GENUINE_JACCARD_MEASURED}} and
{{SEQ_REPLACED_JACCARD_MEASURED}} respectively. The discriminating statistic is
the {{SEQ_LONGEST_BLOCK}}-base contiguous mismatch run, which scattered
sequencing noise does not produce; this is what the {{SEQ_METHOD}} rule keys on.

![DNA mismatch map for the replaced probe: the contiguous edit cluster is
shaded against isolated single-base errors.](output/figures/icarus_sequence_mismatch.png){#fig:icarus_sequence}

## Ice-palace operations

From the configured physics (ambient {{ICE_ENV_TEMP_C}} C, core
{{ICE_BODY_TEMP_C}} C, critical {{ICE_CRITICAL_TEMP_C}} C, decay
{{ICE_DECAY_RATE_H}} /hour) the closed-form exposure ceiling is
{{ICE_SAFE_EXPOSURE_S}} s. The {{ICE_OP_DURATION_S}}-second operation is
therefore split across {{ICE_SQUADS}} rotating squads drawn from the
{{ICE_NUM_OPERATIVES}} available operatives, giving a {{ICE_SHIFT_S}}-second
shift — inside the ceiling, so the roster is feasible ({{ICE_ROTATION_FEASIBLE}}).
Each shift accrues
{{ICE_THERMAL_LOAD_DEG_S}} degree-seconds of core depression below
normothermia, and holding the interior at comfort against the ambient costs
{{ICE_HEATING_ENERGY_MJ}} MJ over the operation.

## Cold-water hypothermia risk

In {{HYP_WATER_TEMP_C}} C water a {{HYP_MASS_KG}} kg operative reaches the
severe ({{HYP_SEVERE_THRESHOLD_C}} C) stage after {{HYP_TIME_TO_SEVERE_S}} s.
A rescue sweeping {{HYP_DISTANCE_M}} m at {{HYP_SWEEP_SPEED_M_S}} m/s arrives
at {{HYP_REACH_TIME_S}} s — a margin of {{HYP_MARGIN_S}} s. Core temperature at
reach is {{HYP_CORE_AT_REACH_C}} C, clinical stage *{{HYP_STAGE_AT_REACH}}*
against the mild/moderate/severe bands at {{HYP_MILD_THRESHOLD_C}},
{{HYP_MODERATE_THRESHOLD_C}}, and {{HYP_SEVERE_THRESHOLD_C}} C.

![Cold-water immersion core-temperature decay with mild/moderate/severe stage
thresholds.](output/figures/icarus_hypothermia_curve.png){#fig:icarus_hypothermia}

## Ice-structure integrity

The palace ice at {{STRUCT_THICKNESS_CM}} cm carries {{STRUCT_CAPACITY_TONS}} t
against the applied {{STRUCT_LOAD_TONS}} t — a safety factor of
{{STRUCT_SAFETY_FACTOR}}. The load case therefore passes. The thermal case does
not: a {{STRUCT_DELTA_T_C}} C gradient drives {{STRUCT_THERMAL_STRESS_MPA}} MPa
of tensile stress, far past the {{STRUCT_ICE_STRENGTH_MPA}} MPa strength, whose
critical gradient is only {{STRUCT_CRITICAL_DELTA_T_C}} C. Cracking risk:
**{{STRUCT_CRACK_RISK}}**. The structure holds its load and still fails its
thermal case — the two checks are independent, and the combined verdict
requires both.

## Orbital-mirror targeting

Propagating the {{ORBIT_SMA_KM}}-km circular orbit at
{{ORBIT_INCLINATION_DEG}} deg inclination over an {{ORBIT_DURATION_S}}-second
window sampled every {{ORBIT_DT_S}} s yields {{MIRROR_PASS_SAMPLES}} instants
over the {{ORBIT_TARGET_LAT_DEG}} N, {{ORBIT_TARGET_LON_DEG}} E target. Of
these, {{MIRROR_N_FEASIBLE}} are feasible — mirror sunlit and above the
{{MIRROR_MIN_ELEVATION_DEG}}-degree horizon — for {{MIRROR_FEASIBLE_S}} s of
targeting. Peak focused flux is {{MIRROR_BEST_FLUX_W_M2}} W/m^2 at
{{MIRROR_BEST_TIME_S}} s after epoch. That delivered flux is small next to the
solar constant: a {{MIRROR_AREA_M2}} m^2 mirror at orbital range spreads its
beam over a footprint kilometres across, so at this scale the model describes
an illumination instrument rather than the film's weapon.

![ICARUS orbital-mirror elevation vs. time over the ground target. The shaded
band marks the feasible targeting window and the red point the peak-flux
instant.](output/figures/icarus_pass_profile.png){#fig:icarus_pass}
