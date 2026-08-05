# Methodology

The mission's concepts rest on a set of mathematical cores, each pure and
deterministic. All {{NUM_CONCEPTS}} of them ({{CONCEPT_MODULES}}) are driven
from one place, `mission_results.run_all_concepts`, described in §*Execution
and control structure* below.

## Positive and negative controls

Each identity model is exercised with a matched pair, not a single case. The
positive control is a constructed replacement; the negative control is a
genuine subject. The negative control is chosen so that clearing the screen is
a measurement rather than an identity: for the biometric model it is a fresh
out-of-sample draw from the enrolled population (which carries real, non-zero
drift), not the profile mean (which would score exactly zero by construction).
For the sequence model it is a read carrying scattered single-base sequencing
noise, so the discriminating power of the contiguous-block rule is what is
actually being tested.

## Biometric identity-replacement detection (`identity_detection.py`)

A biometric profile is modelled as a Gaussian over $k$ markers
($k = $ {{NUM_BIOMARKERS}}). From an enrolled sample population we estimate
the mean $\boldsymbol{\mu}$, the covariance $\Sigma$, and its inverse
$\Sigma^{-1}$. A probe $\boldsymbol{x}$ is scored by the squared Mahalanobis
distance $D^2 = (\boldsymbol{x}-\boldsymbol{\mu})^\top \Sigma^{-1}(\boldsymbol{x}-\boldsymbol{\mu})$,
which under the Gaussian assumption is $\chi^2$ with $k$ degrees of freedom.
The verdict compares the tail probability against a size $\alpha = $
{{IDENTITY_ALPHA}}, and additionally requires at least {{IDENTITY_MIN_MARKERS}}
markers with standardized deviation $|z_i| > $ {{IDENTITY_STD_THRESHOLD}} — the
coherent, multi-marker signature of gene-therapy-grade trait drift.

## DNA sequence identity verification (`sequence_identity.py`)

Identity is also checked at the sequence level over the {A,C,G,T} alphabet. A
{{SEQ_GENOME_LENGTH}}-base reference genome is enrolled, and a probe is scored
three ways:

* `hamming_distance` — per-base substitutions;
* `edit_distance` — the Levenshtein edit distance (insertions, deletions,
  substitutions) via O(mn) dynamic programming;
* `kmer_jaccard` — Jaccard similarity of the probe's k-mer fingerprints
  (k = {{SEQ_KMER_K}}), robust to isolated single-base noise.

A probe is a suspected replacement when it carries a *contiguous* run of at
least {{SEQ_CLUSTER_MIN}} mismatching bases (`mismatch_clusters`) — a coherent
gene-therapy edit rewrites a block of loci at once, whereas sequencing noise
produces only scattered single-base errors. It is *matched* only when its
k-mer similarity clears {{SEQ_MATCH_JACCARD}} AND no such block is present.

## Ice-palace air operations (`ice_ops.py`)

An operative's core temperature decays toward the ambient environment by
Newton's law of cooling, $T(t) = T_e + (T_0 - T_e)e^{-kt}$, giving a closed-form
safe exposure $t_{\text{crit}} = \frac{1}{k}\ln\frac{T_0 - T_e}{T_{\text{crit}} - T_e}$.
With ambient $T_e = $ {{ICE_ENV_TEMP_C}} C, the planner partitions an
{{ICE_OP_DURATION_S}}-second operation into rotating squads of
{{ICE_NUM_OPERATIVES}} operatives so no squad exceeds the ceiling.

Two further quantities size the resource, and they use *different* references
on purpose. Cold strain is
$\int_0^{E}\max(0,\, T_0 - T(t))\,\mathrm{d}t$ in degree-seconds, referenced to
normothermia ($T_0 =$ {{ICE_BODY_TEMP_C}} C) — referencing it to room comfort
(20 C) would return exactly zero for every survivable shift, since a shift ends
at the {{ICE_CRITICAL_TEMP_C}} C critical core temperature, well above comfort,
and the metric could then never discriminate one plan from another. Space
heating, by contrast, genuinely is comfort-referenced: it is the conductance
times the room-to-ambient deficit times the operation duration.

## Cold-water hypothermia risk (`hypothermia.py`)

Water conducts heat far faster than air, so an immersed operative follows the
same Newton cooling law with a much larger decay rate, scaled by body mass and
insulation. The core temperature then crosses the standard clinical stages:
mild hypothermia at 35 C, moderate at 32 C, and severe (unconsciousness) at
28 C. `plan_cold_water_rescue` computes whether a rescue party sweeping
{{HYP_DISTANCE_M}} m at {{HYP_SWEEP_SPEED_M_S}} m/s can reach the operative
before the core reaches the severe stage, reporting the margin and the core
temperature at reach (immersion in {{HYP_WATER_TEMP_C}} C water, {{HYP_MASS_KG}}
kg operative, insulation factor {{HYP_INSULATION}}).

The reference decay rate `K_REF_PER_S` is a *scenario* constant, not a
physiological calibration. It is fixed so that a {{HYP_MASS_KG}} kg operative in
{{HYP_WATER_TEMP_C}} C water reaches a 30 C core in 20 minutes — an initial
cooling rate near 24 C/hour, which is roughly an order of magnitude faster than
measured immersion cooling in water at this temperature. Every hypothermia
number in §03 is therefore internally consistent with that constant and should
not be read as a survival-time prediction; see §07.

## Ice-structure integrity (`ice_structure.py`)

The ice palace must carry its load and survive thermal gradients. Load capacity
follows the standard ice-engineering rule $P = h^2 / C$ (P tons, h cm); the
thermal gradient stress is $\sigma = E\,\alpha\,\Delta T / (1-\nu)$, and the
critical temperature difference that drives ice to its tensile limit is
$\Delta T_{\text{crit}} = \sigma_{\text{allow}}(1-\nu)/(E\alpha)$. At the
configured thickness ({{STRUCT_THICKNESS_CM}} cm), load
({{STRUCT_LOAD_TONS}} t), and gradient ({{STRUCT_DELTA_T_C}} C, tensile strength
{{STRUCT_ICE_STRENGTH_MPA}} MPa), the plan reports the safety factor and whether
the gradient risks cracking.

## Orbital-mirror targeting (`orbital_mirror.py`)

The mirror is placed on a circular orbit (semi-major axis {{ORBIT_SMA_KM}} km,
inclination {{ORBIT_INCLINATION_DEG}} deg) and propagated by its mean anomaly.
The ground target ({{ORBIT_TARGET_LAT_DEG}} N, {{ORBIT_TARGET_LON_DEG}} E) is
located in the same inertial frame via Greenwich mean sidereal time. At each
instant the mirror normal $\hat{n}$ satisfies the reflection law -- it bisects
the incoming solar ray $\hat{s}$ and the ground re-point $\hat{r}$:
$\hat{n} \propto \hat{s} + \hat{r}$, so the incidence angle
$\arccos(\hat{n}\cdot\hat{s})$ is exactly half the Sun-mirror-target angle.

The incoming ray uses the *parallel-ray* approximation: at 1 au the Sun's
direction from the mirror is the solar unit vector itself, and the ~7e6 m orbit
radius shifts it by well under an arcsecond. Forming that ray by subtracting
the satellite position from a unit solar vector would instead yield the nadir
direction, and the resulting incidence angle would be wrong by tens of degrees;
`tests/test_orbital_mirror.py` pins the incidence angle to the analytic
half-angle to keep that failure mode from returning.

When the target direction is anti-parallel to the solar ray the bisector
degenerates — no orientation folds a 180-degree turn — and the instant is
reported infeasible with zero delivered power rather than raising. Targeting is
otherwise feasible when the mirror is sunlit (outside Earth's cylindrical
shadow) and above the {{MIRROR_MIN_ELEVATION_DEG}}-degree horizon. Delivered
power is the solar constant times mirror area ({{MIRROR_AREA_M2}} m^2) times
reflectivity ({{MIRROR_REFLECTIVITY}}) times the cosine of incidence times a
lumped one-way transmission factor ({{MIRROR_ATMOSPHERE_TRANSMISSION}}) that
stands in for atmospheric attenuation, figure error, and scattering — it is a
configured constant, not a modelled quantity, and it scales every reported
flux. Flux at the target follows from the beam spread, whose half-angle is the
configured {{MIRROR_BEAM_HALF_ANGLE_DEG}} deg plus the mirror's own apparent
angular radius at range.

## Execution and control structure

The six models are not invoked ad hoc. `mission_results.run_all_concepts` reads
the `concepts:` block of `manuscript/config.yaml`, runs every model once under
seed {{MISSION_SEED}}, and returns a frozen `ConceptResults` record. Two
consumers read that record and only that record: `mission.py`, which serialises
it into the frozen BOND-API `MissionOutcome`, and `manuscript_variables.py`,
which formats it into the measured manuscript tokens this paper cites. A number
printed here is therefore the same value the mission reported, not a
transcription of it.
