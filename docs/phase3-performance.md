# AION Phase 3 performance report

No trustworthy improvement was found and no preset was promoted. All eight workloads completed discovery and held-out confirmation under O3, O2, LTO, PGO, and PGO+LTO. All 80 workload/configuration combinations, 1408 measured executions, 256 warmups, and 483 discarded calibration pilots pass correctness. All measured processes verify requested guest CPU 0. Fresh final binary hashes match across runs for all 40 configurations; each run independently builds 16 fresh program-specific PGO profiles.

Of 1408 measured samples, 1352 (96.0%) fall within 250–500 ms. All 56 outside the band remain. At least one configuration median in each run is below the strict 250 ms gate, despite successful prior calibration. There are 34 noisy overall configuration summaries out of 40 in each run; classification uses the candidate's matched baseline subset, whose CV/drift can differ from the overall summary. Pinning verifies logical placement and does not guarantee stable host conditions.

Across 32 comparisons per run, discovery has 28 inconclusive and four no-clear-change classifications; confirmation has 28 inconclusive, three no-clear-change, and one regression. There is no independently verified improvement or regression across both main runs. The single quality-valid confirmation regression is records/LTO, whose discovery result is inconclusive. "No clear change" is not a proof of equivalence or non-inferiority; the separate regression-bound gate can still fail.

Examples of the retained signals, all relative to each run's own adjacent O3 baseline:

- Records/LTO paired gain is -15.76% / -14.60%; only confirmation has sufficient quality for a regression classification. Records/O2 is +2.75% / +2.32%, with noise preventing an improvement claim.
- Graph/PGO is +3.47% / +0.93%, with noise and a discovery duration failure. No graph candidate yields a verified improvement.
- Logs/PGO is +12.15% / +9.08%, but both runs fail variability. These promising point estimates are not trusted gains.
- Current-harness sorting/O2 is +7.41% / +8.61% and sorting/LTO +9.32% / +11.50%, but variability/drift blocks claims. Current matrix/LTO is -34.26% / -38.24% and PGO+LTO -35.02% / -38.21%; both remain inconclusive. The current common harness has a different source fingerprint from the frozen Phase 2 harness, so these are separate experiments, not pooled estimates or a reproduction of identical old binaries.

[Discovery details](phase3-discovery.md) and [confirmation details](phase3-confirmation.md) show CV, intervals, batch calibration, durations, RSS, build/training cost, binary size, and individual failed gates. Raw JSON is preserved under `.aion/phase3/results/`; the [evidence audit](../.aion/validation/phase3-evidence-audit.json) links counts and classifications to source JSON hashes. The [proposal-gate audit](../.aion/validation/phase3-gate-audit.json) independently recomputes per-run eligibility and still requires registry confirmation.

The [A/A and known-slowdown controls](phase3-controls.md) retain another 352 measured executions: zero A/A false-positive gains in eight comparisons, three quality-valid detected slowdowns, and five inconclusive slowdowns. [Pinned/unpinned comparison](phase3-placement-comparison.md) is explicitly incompatible for confirmation because placement differs; its samples are not pooled. The [frozen Phase 2 investigation](phase3-investigation.md) retains another 264 measured executions and codegen/profile evidence, distinguishing verified artifact differences from causal hypotheses.

All evidence here is **WSL2 virtualized-host evidence**. Sysfs frequency/governor and thermal metrics are unavailable; guest power observations are partial. No governor, turbo, power, or scheduling configuration was silently changed. The existing statistics and thresholds remain intact. The [validation record](phase3-validation.md) contains tests, package checks, changed files, limitations, and Phase 4 priorities; [methodology](phase3-methodology.md) contains exact reproduction commands.


Discovery: `20261030T234834-de3eb6de82`; confirmation: `20261031T000202-01808fcd04`.

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1). Machine: Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz.
Scheduling/bootstrap seeds: 53300 and 53301.

Inputs differ between runs; each configuration is compared only against its matched -O3 measurement within that run. A workload-level repeatable improvement does not by itself qualify a configuration for a suite-wide preset.

Each candidate has 11 measured pairs per workload and 10000 circular moving-block bootstrap resamples. Intervals use nominal 95% family confidence across 32 declared comparisons (99.84% per interval). Coverage is approximate, especially for short or nonstationary series.

A confidence interval away from zero does not override the unchanged CV, drift, duration, 2%/combined-MAD improvement floor, or 5% regression checks. All measured samples are retained. PGO profiles remain program-specific research evidence, not reusable flag-only presets.

| Workload | Candidate | Discovery paired gain % | Confirmation paired gain % | Discovery interval % | Confirmation interval % | Outcome |
|---|---|---:|---:|---|---|---|
| array | o2 | 0.951 | 0.522 | [-12.295, 4.639] | [-6.810, 4.050] | inconclusive / inconclusive |
| array | lto | 0.388 | -0.342 | [-3.046, 1.981] | [-3.093, 6.089] | no_clear_change / inconclusive |
| array | pgo | -0.174 | 0.175 | [-8.829, 3.057] | [-2.111, 10.153] | inconclusive / inconclusive |
| array | pgo-lto | -0.002 | 2.012 | [-0.791, 5.573] | [-1.569, 7.116] | inconclusive / inconclusive |
| sorting | o2 | 7.409 | 8.605 | [5.987, 11.116] | [7.202, 10.342] | inconclusive / inconclusive |
| sorting | lto | 9.318 | 11.500 | [-3.228, 11.505] | [8.147, 22.195] | inconclusive / inconclusive |
| sorting | pgo | -1.653 | -1.037 | [-1.977, 0.183] | [-1.430, 2.343] | inconclusive / inconclusive |
| sorting | pgo-lto | 2.580 | 4.194 | [0.128, 2.992] | [-5.390, 5.304] | inconclusive / inconclusive |
| hashmap | o2 | 1.444 | 1.283 | [-21.957, 4.568] | [-1.106, 22.519] | inconclusive / inconclusive |
| hashmap | lto | 0.029 | -1.414 | [-3.977, 7.468] | [-3.021, 2.673] | inconclusive / inconclusive |
| hashmap | pgo | 0.877 | -0.936 | [-3.698, 23.861] | [-9.337, 1.514] | inconclusive / inconclusive |
| hashmap | pgo-lto | -0.140 | 2.245 | [-26.736, 3.353] | [-0.887, 3.037] | inconclusive / inconclusive |
| matrix | o2 | -0.679 | -0.735 | [-7.297, 6.083] | [-3.691, 0.237] | inconclusive / inconclusive |
| matrix | lto | -34.264 | -38.245 | [-38.689, -31.487] | [-45.019, -35.967] | inconclusive / inconclusive |
| matrix | pgo | 4.020 | 2.068 | [-0.858, 5.289] | [-0.361, 4.243] | inconclusive / inconclusive |
| matrix | pgo-lto | -35.016 | -38.208 | [-39.977, -29.662] | [-39.285, -35.439] | inconclusive / inconclusive |
| strings | o2 | 0.503 | -1.900 | [-0.426, 1.267] | [-8.938, -0.733] | no_clear_change / no_clear_change |
| strings | lto | -2.700 | -3.551 | [-5.275, -0.972] | [-4.549, -2.843] | inconclusive / inconclusive |
| strings | pgo | -0.251 | -0.377 | [-4.163, 1.952] | [-2.344, 0.800] | no_clear_change / no_clear_change |
| strings | pgo-lto | -3.951 | -1.801 | [-5.251, 0.790] | [-4.091, -0.028] | no_clear_change / inconclusive |
| records | o2 | 2.749 | 2.325 | [-2.701, 8.210] | [0.930, 10.653] | inconclusive / inconclusive |
| records | lto | -15.758 | -14.596 | [-19.024, -10.646] | [-17.878, -11.417] | inconclusive / regression |
| records | pgo | -1.602 | 0.106 | [-3.227, 0.789] | [-3.803, 0.672] | inconclusive / no_clear_change |
| records | pgo-lto | -6.372 | -3.760 | [-8.918, -1.619] | [-5.845, -1.173] | inconclusive / inconclusive |
| graph | o2 | 1.298 | 2.867 | [0.902, 2.368] | [0.956, 4.286] | inconclusive / inconclusive |
| graph | lto | -3.234 | -2.812 | [-6.872, 4.483] | [-5.250, 1.876] | inconclusive / inconclusive |
| graph | pgo | 3.466 | 0.927 | [1.761, 9.879] | [-1.984, 2.574] | inconclusive / inconclusive |
| graph | pgo-lto | 0.157 | -0.562 | [-3.726, 1.161] | [-1.765, 3.358] | inconclusive / inconclusive |
| logs | o2 | -0.610 | 1.312 | [-19.555, 1.911] | [-1.135, 5.827] | inconclusive / inconclusive |
| logs | lto | 4.958 | 3.627 | [-3.584, 5.480] | [2.599, 7.884] | inconclusive / inconclusive |
| logs | pgo | 12.153 | 9.076 | [8.903, 16.007] | [7.358, 9.849] | inconclusive / inconclusive |
| logs | pgo-lto | 4.754 | 2.787 | [2.552, 5.323] | [0.002, 5.591] | inconclusive / inconclusive |

## Duration and correctness audit

| Run | Verified configurations | Median compute sample range ms | Measured samples inside 250–500 ms |
|---|---:|---:|---:|
| optimize | 40/40 | 238.0–466.9 | 667/704 |
| independent_confirmation | 40/40 | 240.6–404.9 | 685/704 |

Full raw samples, calibration pilots, physical durations, paired intervals, drift, resources, correctness checks, and PGO provenance remain in each experiment's JSON and detailed Markdown report.

**Evidence scope:** wsl2; CPU affinity verifies guest/logical placement, not physical-host isolation. Native Linux replications require their own host identity; incompatible samples are not pooled.

Discovery host:

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Requested affinity: `[0]`; verified pinned samples: 704/704. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Recorded verification methods: `['actual executable sched_getaffinity before/after compute']`. Verification is a snapshot, not exclusive CPU ownership.
Different CPU endpoints observed: 0/704; equal endpoints do not prove no intermediate migration.
Noisy configuration summaries: 34/40; drifting: 6/40.
Load average at start/end: `[0.29833984375, 0.4306640625, 0.3720703125]` / `[1.00390625, 1.0, 0.7763671875]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

Confirmation host:

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Requested affinity: `[0]`; verified pinned samples: 704/704. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Recorded verification methods: `['actual executable sched_getaffinity before/after compute']`. Verification is a snapshot, not exclusive CPU ownership.
Different CPU endpoints observed: 0/704; equal endpoints do not prove no intermediate migration.
Noisy configuration summaries: 34/40; drifting: 4/40.
Load average at start/end: `[1.00390625, 1.0, 0.7763671875]` / `[1.01806640625, 1.04541015625, 0.96337890625]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

## Candidate promotion-gate failures

These are proposal/promotion requirements. A negative effect is expected to fail the regression bound and improvement requirement. All candidates pass correctness, sample completeness, minimum count, warmups, and effective-affinity gates. PGO also remains ineligible for generic flag-only presets, regardless of performance.

| Workload | Candidate | Discovery failed gates | Confirmation failed gates |
|---|---|---|---|
| array | o2 | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | duration, variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| array | lto | improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| array | pgo | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| array | pgo-lto | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| sorting | o2 | variability, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty |
| sorting | lto | variability, drift, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| sorting | pgo | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| sorting | pgo-lto | variability, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| hashmap | o2 | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty |
| hashmap | lto | variability, drift, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| hashmap | pgo | variability, drift, improvement_floor_and_uncertainty | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| hashmap | pgo-lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| matrix | o2 | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| matrix | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| matrix | pgo | variability, drift, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| matrix | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | o2 | improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| strings | pgo | improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| strings | pgo-lto | acceptable_regression_bound, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| records | o2 | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| records | lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| records | pgo | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| records | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | o2 | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| graph | lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | pgo | duration, variability, drift, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| graph | pgo-lto | variability, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty |
| logs | o2 | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| logs | lto | variability, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty |
| logs | pgo | variability, drift, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| logs | pgo-lto | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |

`variability` is the unchanged CV gate; `duration` the physical minimum; `drift` the paired-series drift gate; `acceptable_regression_bound` includes the point/interval regression limit; `improvement_floor_and_uncertainty` requires an improvement classification under all unchanged statistical quality checks. Exact booleans and source samples remain in JSON.
