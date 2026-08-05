# Scope and Related Work

**Scope.** This package models three decision problems relevant to a
special-agent operation — identity-replacement screening, cold-environment
exposure planning, and orbital-mirror targeting. Each model is deliberately
self-contained and deterministic; it is not a general biometrics, heat-transfer,
or astrodynamics library. Assumptions are stated explicitly in §02 (Gaussian
markers, Newton cooling, circular Keplerian orbit, low-precision solar
ephemeris).

**Related work.** The Mahalanobis-distance screen (Mahalanobis, 1936) is a
classic multivariate outlier tool; here it is specialized to a coherent-marker
replacement hypothesis with a chi-square calibration. Sequence comparison uses
Levenshtein edit distance (Levenshtein, 1966) together with k-mer set
similarity, the fingerprinting idea that underpins alignment-free genome
comparison (Ondov et al., 2016). Newton's law of cooling (Newton, 1701)
underlies standard cold-stress exposure limits. The immersion module borrows
the *clinical staging* used in the cold-water survival literature (Tipton,
1989; Golden and Tipton, 2002) — the mild/moderate/severe core-temperature
bands — but **not** its cooling rates: `K_REF_PER_S` is a scenario constant,
not a calibration against that literature (see Limitations). Ice load capacity
uses the published bearing-capacity rule for floating
ice covers (Gold, 1971; Sodhi, 1995) with mechanical and thermal constants from
ice physics (Hobbs, 1974). Orbital-targeting geometry follows standard two-body
propagation (Battin, 1999; Vallado, 2013) and the mirror reflection law used by
space-solar-power and orbital-reflector studies (Glaser, 1968). The
contribution here is not any single model but their *integration* into one
deterministic mission provider under the frozen BOND-API contract, with every
reported number injected from the run rather than transcribed.

**Limitations.** These are properties of the models, not of the
implementation, and each is visible in the code:

- Biomarker distribution is assumed Gaussian and markers are drawn
  independently; heavy-tailed or correlated traits would need robust covariance
  estimation, and the chi-square calibration would shift accordingly.
- Sequence verification requires equal-length reads. Edit distance tolerates
  indels, but the contiguous-block rule and the Hamming statistic are
  position-aligned, so an unaligned read must be aligned first.
- The orbital pass is a single circular orbit with a low-precision solar
  ephemeris and a cylindrical (not conical) shadow model; it answers a
  feasibility question, not a constellation-design or pointing-error one.
- Beam spread is a simple angular model: the half-angle is a configured
  constant plus the mirror's apparent angular radius. Diffraction, figure
  error, and atmospheric scattering are folded into one lumped transmission
  factor rather than modelled.
- Cold-exposure planning uses a single Newton decay rate for all operatives
  (no per-suit or per-individual variation), and the rotation planner assumes
  squads can hand over instantaneously.
- **The immersion cooling rate is not physiologically calibrated.**
  `hypothermia.K_REF_PER_S` is fixed so a 75 kg operative in 10 C water reaches
  a 30 C core in 20 minutes: an initial cooling rate of about 24 C/hour, which
  is roughly an order of magnitude faster than measured immersion cooling at
  that water temperature. It is a film-scenario constant chosen to put the
  rescue on a dramatic clock. Consequently §03's immersion times
  (`HYP_TIME_TO_SEVERE_S`, `HYP_CORE_AT_REACH_C`, `HYP_MARGIN_S`) are correct
  *for this model* and are not survival-time predictions; the module
  demonstrates the rescue-versus-timeline decision structure, not the timeline
  itself. Only the clinical staging thresholds (35 / 32 / 28 C) are taken from
  the literature. `test_hypothermia.py` pins the constant to its stated
  20-minute definition so the number and the sentence cannot drift apart.
- The ice-structure model is a static bearing-capacity plus thermal-stress
  check; it does not model creep, crack propagation, or repeated loading.
