# Methodology

The three mission concepts rest on three mathematical cores, each pure and
deterministic.

## Identity-replacement detection (`identity_detection.py`)

A biometric profile is modelled as a Gaussian over $k$ markers
($k = $ {{NUM_BIOMARKERS}}). From an enrolled sample population we estimate
the mean $\boldsymbol{\mu}$, the covariance $\Sigma$, and its inverse
$\Sigma^{-1}$. A probe $\boldsymbol{x}$ is scored by the squared Mahalanobis
distance

$$
D^2 = (\boldsymbol{x}-\boldsymbol{\mu})^\top \Sigma^{-1} (\boldsymbol{x}-\boldsymbol{\mu}),
$$

which, under the Gaussian assumption, is $\chi^2$ with $k$ degrees of freedom.
The verdict compares the tail probability against a size
$\alpha = $ {{IDENTITY_ALPHA}}: a probe is a candidate replacement when
$D^2$ exceeds the $1-\alpha$ quantile. To reject single-marker noise, the
verdict additionally requires at least {{IDENTITY_MIN_MARKERS}} markers whose
standardized deviation $|z_i| > $ {{IDENTITY_STD_THRESHOLD}} — the signature of
a coherent, gene-therapy-grade trait drift.

## Ice-palace operations (`ice_ops.py`)

An operative's core temperature decays toward the ambient environment by
Newton's law of cooling, $T(t) = T_e + (T_0 - T_e)e^{-kt}$. Solving for the
moment the core reaches a critical temperature gives the closed-form safe
exposure

$$
t_{\text{crit}} = \frac{1}{k}\ln\frac{T_0 - T_e}{T_{\text{crit}} - T_e}.
$$

With ambient $T_e = $ {{ICE_ENV_TEMP_C}} C, core $T_0 = $ {{ICE_BODY_TEMP_C}} C,
critical $T_{\text{crit}} = $ {{ICE_CRITICAL_TEMP_C}} C, and a decay rate
$k = $ {{ICE_DECAY_RATE_H}} /hour, the planner partitions an
{{ICE_OP_DURATION_S}}-second operation into rotating squads of
{{ICE_NUM_OPERATIVES}} operatives so no squad exceeds the ceiling. Cold stress
is quantified as degree-seconds below comfort, and heating energy sizes the
power to hold a space at comfort.

## Orbital-mirror targeting (`orbital_mirror.py`)

The mirror is placed on a circular orbit (semi-major axis
{{ORBIT_SMA_KM}} km, inclination {{ORBIT_INCLINATION_DEG}} deg) and propagated
by its mean anomaly. The ground target is located in the same inertial frame
via sidereal time. At each instant the mirror normal $\hat{n}$ satisfies the
reflection law — it bisects the incoming solar ray $\hat{s}$ and the ground
re-point $\hat{r}$:

$$
\hat{n} \propto \hat{s} + \hat{r}.
$$

Targeting is feasible when the mirror is sunlit, above the
{{MIRROR_MIN_ELEVATION_DEG}}-degree horizon, and the incidence angle is
positive. Delivered power is the project solar constant times mirror area
({{MIRROR_AREA_M2}} m^2) times reflectivity ({{MIRROR_REFLECTIVITY}}) times
the cosine of incidence; flux at the target follows from the focused beam
spread ({{MIRROR_BEAM_HALF_ANGLE_DEG}} deg half-angle).
