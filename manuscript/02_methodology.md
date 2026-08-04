# Methodology

The mission's concepts rest on a set of mathematical cores, each pure and
deterministic.

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
{{ICE_NUM_OPERATIVES}} operatives so no squad exceeds the ceiling; cold stress
(degree-seconds below comfort) and heating energy size the resource.

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
The ground target is located in the same inertial frame via sidereal time. At
each instant the mirror normal $\hat{n}$ satisfies the reflection law -- it
bisects the incoming solar ray $\hat{s}$ and the ground re-point $\hat{r}$:
$\hat{n} \propto \hat{s} + \hat{r}$. Targeting is feasible when the mirror is
sunlit, above the {{MIRROR_MIN_ELEVATION_DEG}}-degree horizon, and the
incidence angle is positive. Delivered power is the solar constant times mirror
area ({{MIRROR_AREA_M2}} m^2) times reflectivity ({{MIRROR_REFLECTIVITY}}) times
the cosine of incidence; flux at the target follows from the focused beam
spread.
