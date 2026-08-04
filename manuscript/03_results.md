# Results

Running the deterministic mission (`uv run python scripts/run_mission.py`)
exercises all three concepts and reports measured outcomes.

## Identity-replacement detection

The enrolled baseline is synthesized deterministically (seed). A
gene-therapy-grade probe — a coherent shift on the first
{{IDENTITY_MIN_MARKERS}} markers by {{IDENTITY_STD_THRESHOLD}}-standard-deviation
magnitude — is flagged with a Mahalanobis statistic well past the
$\chi^2_{1-{{IDENTITY_ALPHA}}}$ threshold computed from the $k =$
{{NUM_BIOMARKERS}}-marker profile. The genuine profile (the enrolled mean)
clears the same test, demonstrating a controlled false-rejection rate.

![Per-marker standardized trait drift for the genuine and replaced probes.
The dashed lines mark the $\pm${{IDENTITY_STD_THRESHOLD}} flagging
threshold.](output/figures/icarus_identity_drift.png){#fig:icarus_drift}

## Ice-palace operations

From the configured physics (ambient {{ICE_ENV_TEMP_C}} C,
{{ICE_OP_DURATION_S}}-second operation, {{ICE_NUM_OPERATIVES}} operatives), the
planner derives the safe-exposure ceiling and partitions the operation into a
rotating roster. The plan is feasible exactly when the per-squad shift stays
under the ceiling, and reports the integrated cold stress and heating energy.

## Orbital-mirror targeting

Propagating the {{ORBIT_SMA_KM}}-km circular orbit over the configured window
produces a pass whose elevation and feasible-targeting state are shown below.
The best-illumination moment (peak focused flux) is marked. The pass yields a
contiguous window during which the mirror is sunlit and above the
{{MIRROR_MIN_ELEVATION_DEG}}-degree horizon.

![ICARUS orbital-mirror elevation vs. time over the ground target. The shaded
band marks the feasible targeting window and the red point the peak-flux
instant.](output/figures/icarus_pass_profile.png){#fig:icarus_pass}
