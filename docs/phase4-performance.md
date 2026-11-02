# AION Phase 4 performance report

No independently verified improvement qualifies for a preset. Records/LTO has a repeated regression under the unchanged per-comparison gates: paired gain -15.16% in discovery and -14.16% in held-out confirmation. This is a scoped WSL2 result, not a native Linux or universal production claim. The separate measurement-quality assessment still marks this environment **not yet validated**.

Both ten-workload sessions completed all 50 baseline/O2/LTO/PGO/PGO+LTO configurations. All **1760 measured executions**, **320 warmups**, and **600 discarded calibration pilots** pass correctness. All 100 configuration verification groups pass; all measured processes verify requested guest CPU 0. Independent final binary hashes match for all 50 configurations. Each run freshly generates 20 program-specific PGO builds. Source/compiler/host/placement/constraint compatibility passes across the two distinct recorded sessions, without pooling samples.

**1749/1760 measured samples (99.4%)** fall inside 250–500 ms. All eleven outside the band remain. Every configuration median meets the minimum physical-duration gate: discovery range 277.0–384.4 ms, confirmation 282.5–374.4 ms. Duration coverage alone does not validate quality. Overall noisy summaries are 35/50 in discovery and 17/50 in confirmation; paired-subset CV/drift determines each candidate's gates. Session-to-session variability is not evidence that pinning or another unrecorded intervention fixed the host.

Discovery has 33 inconclusive, six no-clear-change and one regression classification. Confirmation has 18 inconclusive, 15 no-clear-change, five regressions and two improvements. Sorting/LTO (+10.68% / +10.41%) and records/O2 (+2.85% / +2.65%) improve only in the quality-valid confirmation classification; discovery remains inconclusive. Logs/PGO (+10.75% / +9.53%) remains inconclusive in both. A favorable interval or point estimate never overrides failed variability/drift/MAD gates.

The new image application passes correctness in all configurations. O2 has -18.76% / -18.91% paired gains and PGO+LTO -11.27% / -10.91%; both are regressions in confirmation only, with inconclusive discovery. Image LTO/PGO provide no independently verified improvement. The new key/value application has no independently verified gain; its small or noisy signals remain visible below. Matrix LTO/PGO+LTO regress in confirmation, with inconclusive discovery. These are not promoted or described as independently verified regressions across both runs.

The separate [measurement-quality report](phase4-quality.md) covers **1056 measured control executions** across eight runs, two explicit sessions, three workloads and pinned/unpinned modes. There are no false A/A improvement signals in 24 comparisons; 14 A/A results are consistent with no clear change and ten are inconclusive. Eighteen of 24 known slowdowns are detected, with six inconclusive. All quality-valid negative controls are detected. These descriptive counts do not establish a universal false-positive rate.

Pinned and unpinned evidence remain separate compatible strata. Each has 0/12 A/A false gains (approximate 95% Wilson interval 0–24.2%) and 9/12 detected slowdowns (46.8–91.1%). Quality-valid negative-control sensitivity is 9/9 per stratum (70.1–100%); outcomes within sessions/workloads are dependent. Pinned has nine inconclusive control outcomes out of 24, unpinned seven out of 24. This small study does not demonstrate that pinning improves stability. Both operational quality assessments fail, while ten-workload differential/ASan/UBSan validation passes. Native Linux evidence is unavailable and native performance validation remains pending.

[The compiler investigation](phase4-investigation.md) separately records 72 correct equal-work counter executions, 648 unmultiplexed event observations and 24 complete sampled traces on matching preserved Phase 3 binaries. Matrix LTO has nearly unchanged instruction counts but higher cycle counts; SIMD multiplication remains present. Logs/PGO has fewer instructions/cycles in those whole-process observations. These are diagnostic facts and hypotheses, not proof of the cause of a primary timing effect. Counter/sampling/sanitizer data never enter promotion comparisons.

[Discovery details](phase4-discovery.md) and [confirmation details](phase4-confirmation.md) retain calibration, CV/drift, intervals, RSS, build/training cost and failed gates. [The evidence audit](../.aion/validation/phase4-evidence-audit.json) links counts to immutable raw result hashes; [the proposal audit](../.aion/validation/phase4-gate-audit.json) recomputes eligibility from raw timing samples. All four candidate recipes fail proposal eligibility in both runs; PGO also remains ineligible for generic flag-only presets. No preset was created.

The environment is Ubuntu 24.04 / WSL2, Clang 18.1.3, GNU ld 2.42 and Intel Core i7-8665U guest-visible hardware. Logical affinity is not physical isolation. Sysfs frequency/governor and thermal data remain unavailable; power observations are partial. No privileged tuning, AI optimizer or cloud dependency was introduced. See [validation and changed files](phase4-validation.md), [methodology](phase4-methodology.md), and [native replication](native-linux-benchmarking.md). Phase 5 should first obtain native evidence and stronger controls, then test targeted compiler hypotheses before AI-generated proposals.


Discovery: `20261031T025701-07d35075c3`; confirmation: `20261031T032139-5ccfa44eff`.

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1). Machine: Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz.
Scheduling/bootstrap seeds: 64300 and 64400.

Inputs differ between runs; each configuration is compared only against its matched -O3 measurement within that run. A workload-level repeatable improvement does not by itself qualify a configuration for a suite-wide preset.

Each candidate has 11 measured pairs per workload and 10000 circular moving-block bootstrap resamples. Intervals use nominal 95% family confidence across 40 declared comparisons (99.88% per interval). Coverage is approximate, especially for short or nonstationary series.

A confidence interval away from zero does not override the unchanged CV, drift, duration, 2%/combined-MAD improvement floor, or 5% regression checks. All measured samples are retained. PGO profiles remain program-specific research evidence, not reusable flag-only presets.

| Workload | Candidate | Discovery paired gain % | Confirmation paired gain % | Discovery interval % | Confirmation interval % | Outcome |
|---|---|---:|---:|---|---|---|
| array | o2 | -1.020 | 1.101 | [-3.310, 1.096] | [-8.276, 1.821] | no_clear_change / inconclusive |
| array | lto | -0.708 | 0.640 | [-3.444, 3.340] | [-1.154, 1.635] | no_clear_change / no_clear_change |
| array | pgo | -0.113 | 0.394 | [-3.381, 4.266] | [-1.825, 2.923] | inconclusive / no_clear_change |
| array | pgo-lto | -0.049 | 1.046 | [-1.226, 0.951] | [-0.042, 4.475] | inconclusive / inconclusive |
| sorting | o2 | 7.919 | 8.213 | [5.440, 9.553] | [7.649, 10.045] | inconclusive / inconclusive |
| sorting | lto | 10.681 | 10.407 | [8.397, 12.984] | [9.923, 10.620] | inconclusive / improvement |
| sorting | pgo | -2.281 | -1.667 | [-3.699, -0.198] | [-2.494, -1.170] | inconclusive / inconclusive |
| sorting | pgo-lto | 2.980 | 2.924 | [0.280, 4.794] | [1.669, 4.679] | inconclusive / inconclusive |
| hashmap | o2 | 1.287 | 1.185 | [-0.306, 3.611] | [0.996, 2.208] | inconclusive / no_clear_change |
| hashmap | lto | -2.685 | -1.577 | [-14.395, 15.024] | [-19.303, -0.779] | inconclusive / inconclusive |
| hashmap | pgo | -1.437 | 0.960 | [-2.634, 3.281] | [-3.092, 1.539] | inconclusive / inconclusive |
| hashmap | pgo-lto | 1.685 | 0.718 | [1.188, 6.569] | [-0.060, 1.874] | inconclusive / no_clear_change |
| matrix | o2 | -1.144 | -1.014 | [-2.755, 0.598] | [-1.639, 0.033] | no_clear_change / no_clear_change |
| matrix | lto | -35.579 | -36.932 | [-38.346, -33.057] | [-37.402, -36.377] | inconclusive / regression |
| matrix | pgo | 0.107 | 1.250 | [-0.446, 1.628] | [0.095, 2.027] | inconclusive / no_clear_change |
| matrix | pgo-lto | -34.928 | -35.775 | [-38.514, -32.520] | [-36.184, -34.286] | inconclusive / regression |
| strings | o2 | -0.395 | 0.986 | [-2.281, 1.460] | [-0.756, 9.813] | no_clear_change / inconclusive |
| strings | lto | -3.962 | -1.558 | [-5.246, 1.320] | [-4.072, 10.932] | inconclusive / inconclusive |
| strings | pgo | 0.017 | -0.442 | [-0.662, 1.184] | [-4.024, 0.356] | inconclusive / inconclusive |
| strings | pgo-lto | -3.429 | -2.125 | [-4.665, -2.430] | [-3.065, -0.413] | inconclusive / inconclusive |
| records | o2 | 2.846 | 2.649 | [2.335, 3.290] | [2.236, 3.862] | inconclusive / improvement |
| records | lto | -15.163 | -14.156 | [-16.030, -12.816] | [-14.359, -13.851] | verified regression on this workload |
| records | pgo | 0.079 | -1.267 | [-1.194, 0.874] | [-2.450, -0.126] | no_clear_change / no_clear_change |
| records | pgo-lto | -3.826 | -4.930 | [-6.085, -2.827] | [-6.049, -3.956] | inconclusive / no_clear_change |
| graph | o2 | 1.043 | 2.399 | [-3.660, 4.443] | [0.966, 4.258] | inconclusive / no_clear_change |
| graph | lto | -3.104 | -2.881 | [-5.905, -1.758] | [-4.987, -1.992] | inconclusive / no_clear_change |
| graph | pgo | 1.593 | 1.677 | [-2.033, 3.255] | [0.386, 1.992] | inconclusive / no_clear_change |
| graph | pgo-lto | 0.514 | 0.621 | [-3.771, 3.839] | [-0.111, 1.550] | inconclusive / no_clear_change |
| logs | o2 | 0.014 | 1.374 | [-0.431, 1.225] | [-0.909, 8.366] | no_clear_change / inconclusive |
| logs | lto | 4.856 | 5.056 | [1.666, 12.660] | [2.201, 9.685] | inconclusive / inconclusive |
| logs | pgo | 10.753 | 9.534 | [7.717, 12.708] | [7.979, 23.363] | inconclusive / inconclusive |
| logs | pgo-lto | 4.331 | 4.782 | [1.673, 5.944] | [4.162, 5.145] | inconclusive / inconclusive |
| image | o2 | -18.755 | -18.908 | [-19.743, -15.779] | [-20.442, -14.100] | inconclusive / regression |
| image | lto | -4.700 | -4.953 | [-6.636, -2.191] | [-5.723, -4.766] | inconclusive / no_clear_change |
| image | pgo | -0.704 | -0.483 | [-4.391, 0.496] | [-0.835, -0.149] | inconclusive / no_clear_change |
| image | pgo-lto | -11.274 | -10.907 | [-14.669, -8.899] | [-11.347, -8.407] | inconclusive / regression |
| kv | o2 | -2.238 | -0.674 | [-4.221, 3.915] | [-2.475, 0.698] | inconclusive / inconclusive |
| kv | lto | 2.102 | 0.534 | [-2.089, 2.932] | [-1.462, 1.982] | inconclusive / no_clear_change |
| kv | pgo | 3.585 | 0.451 | [-0.726, 10.139] | [-0.695, 0.781] | inconclusive / inconclusive |
| kv | pgo-lto | -0.505 | -0.416 | [-1.808, 0.165] | [-2.743, 0.395] | inconclusive / inconclusive |

## Duration and correctness audit

| Run | Verified configurations | Median compute sample range ms | Measured samples inside 250–500 ms |
|---|---:|---:|---:|
| benchmark | 50/50 | 277.0–384.4 | 871/880 |
| independent_confirmation | 50/50 | 282.5–374.4 | 878/880 |

Full raw samples, calibration pilots, physical durations, paired intervals, drift, resources, correctness checks, and PGO provenance remain in each experiment's JSON and detailed Markdown report.

**Evidence scope:** wsl2; CPU affinity verifies guest/logical placement, not physical-host isolation. Native Linux replications require their own host identity; incompatible samples are not pooled.

Discovery host:

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Environment classification: `wsl2`; session: `a407629a605c4cbd88e960d19ca09b87`. Session IDs alone do not establish independent host conditions.
Measurement environment readiness is assessed separately by `aion quality`; compile/affinity validation alone is insufficient.
Requested affinity: `[0]`; verified pinned samples: 880/880. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Recorded verification methods: `['actual executable sched_getaffinity before/after compute']`. Verification is a snapshot, not exclusive CPU ownership.
Different CPU endpoints observed: 0/880; equal endpoints do not prove no intermediate migration.
Noisy configuration summaries: 35/50; drifting: 2/50.
Load average at start/end: `[1.1455078125, 0.966796875, 0.71484375]` / `[1.123046875, 1.099609375, 0.98095703125]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

Confirmation host:

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Environment classification: `wsl2`; session: `8ebc2d20d2d44e1aab1f49b496c4e39e`. Session IDs alone do not establish independent host conditions.
Measurement environment readiness is assessed separately by `aion quality`; compile/affinity validation alone is insufficient.
Requested affinity: `[0]`; verified pinned samples: 880/880. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Recorded verification methods: `['actual executable sched_getaffinity before/after compute']`. Verification is a snapshot, not exclusive CPU ownership.
Different CPU endpoints observed: 0/880; equal endpoints do not prove no intermediate migration.
Noisy configuration summaries: 17/50; drifting: 1/50.
Load average at start/end: `[1.09130859375, 1.0732421875, 1.01171875]` / `[1.13671875, 1.0751953125, 1.01318359375]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

## Exact promotion-gate failures

Regression classifications correctly fail the promotion regression/improvement requirements. Correctness, complete samples, minimum sample count, warmups and effective affinity pass throughout. The table shows all remaining failed gates; none are omitted for an attractive point estimate.

| Workload | Candidate | Discovery failed gates | Confirmation failed gates |
|---|---|---|---|
| array | o2 | improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| array | lto | improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| array | pgo | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| array | pgo-lto | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| sorting | o2 | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| sorting | lto | variability, improvement_floor_and_uncertainty | none |
| sorting | pgo | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| sorting | pgo-lto | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| hashmap | o2 | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| hashmap | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| hashmap | pgo | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| hashmap | pgo-lto | variability, drift, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| matrix | o2 | improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| matrix | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| matrix | pgo | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| matrix | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | o2 | improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| strings | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| strings | pgo | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| strings | pgo-lto | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| records | o2 | variability, improvement_floor_and_uncertainty | none |
| records | lto | acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| records | pgo | improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| records | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | o2 | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| graph | lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| graph | pgo | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| graph | pgo-lto | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| logs | o2 | improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| logs | lto | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| logs | pgo | variability, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty |
| logs | pgo-lto | variability, drift, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| image | o2 | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| image | lto | acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| image | pgo | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| image | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty |
| kv | o2 | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty |
| kv | lto | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty |
| kv | pgo | variability, drift, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty |
| kv | pgo-lto | variability, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty |

`variability` uses the unchanged 5% default CV gate; `drift` uses paired-series drift; `acceptable_regression_bound` includes point/interval bounds; `improvement_floor_and_uncertainty` requires improvement under the unchanged MAD/floor and uncertainty checks. Raw samples and detailed booleans remain in JSON.
