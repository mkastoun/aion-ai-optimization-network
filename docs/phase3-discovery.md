# AION Phase 3 performance comparison

Run: `20261030T234834-de3eb6de82` (optimize); status: **completed**

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1) — x86_64-pc-linux-gnu
Machine: Linux — Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz
Measured pairs per candidate: 11; warmups: 2; schedule/bootstrap seed: 53300.

Target compute time: 250–500 ms per sample. Input generation, allocation of input buffers, and reset/copy work are excluded from compute time.

A unit is one execution of the workload's fixed input/rounds. Each configuration calibrates its batch count separately; comparisons normalize by batches and use its adjacent -O3 partner. Insertion/rehash costs in hash maps and checksum scans remain timed.

Positive paired improvement means faster. Both the reported gain and interval describe the median of paired effects. The raw JSON also retains the ratio of marginal medians used by the unchanged screening floor. Intervals use a Bonferroni adjustment across 32 declared comparisons (nominal family confidence 95%).

| Workload | Config | Batches | Unit ms | Sample ms | CV % | Paired gain % | Adjusted interval % | Outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| array | baseline | 18 | 25.941 | 466.938 | 6.557 | baseline | n/a | measured (noisy) |
| array | o2 | 15 | 25.656 | 384.842 | 10.186 | 0.951 | [-12.295, 4.639] | inconclusive (noisy, drift) |
| array | lto | 14 | 26.113 | 365.587 | 4.882 | 0.388 | [-3.046, 1.981] | no_clear_change |
| array | pgo | 15 | 25.969 | 389.530 | 8.459 | -0.174 | [-8.829, 3.057] | inconclusive (noisy) |
| array | pgo-lto | 15 | 26.034 | 390.511 | 8.267 | -0.002 | [-0.791, 5.573] | inconclusive (noisy) |
| sorting | baseline | 6 | 64.201 | 385.205 | 8.510 | baseline | n/a | measured (noisy) |
| sorting | o2 | 6 | 59.687 | 358.124 | 13.304 | 7.409 | [5.987, 11.116] | inconclusive (noisy) |
| sorting | lto | 6 | 57.734 | 346.407 | 9.768 | 9.318 | [-3.228, 11.505] | inconclusive (noisy, drift) |
| sorting | pgo | 6 | 63.220 | 379.322 | 5.512 | -1.653 | [-1.977, 0.183] | inconclusive (noisy) |
| sorting | pgo-lto | 6 | 63.107 | 378.642 | 15.352 | 2.580 | [0.128, 2.992] | inconclusive (noisy) |
| hashmap | baseline | 5 | 71.440 | 357.200 | 70.758 | baseline | n/a | measured (noisy, drift) |
| hashmap | o2 | 5 | 69.058 | 345.289 | 35.159 | 1.444 | [-21.957, 4.568] | inconclusive (noisy, drift) |
| hashmap | lto | 5 | 71.477 | 357.384 | 32.407 | 0.029 | [-3.977, 7.468] | inconclusive (noisy, drift) |
| hashmap | pgo | 5 | 72.688 | 363.440 | 19.215 | 0.877 | [-3.698, 23.861] | inconclusive (noisy, drift) |
| hashmap | pgo-lto | 5 | 71.167 | 355.837 | 17.981 | -0.140 | [-26.736, 3.353] | inconclusive (noisy, drift) |
| matrix | baseline | 32 | 9.339 | 298.837 | 12.011 | baseline | n/a | measured (noisy) |
| matrix | o2 | 40 | 9.353 | 374.102 | 10.767 | -0.679 | [-7.297, 6.083] | inconclusive (noisy) |
| matrix | lto | 28 | 12.543 | 351.199 | 19.035 | -34.264 | [-38.689, -31.487] | inconclusive (noisy) |
| matrix | pgo | 39 | 9.095 | 354.691 | 8.131 | 4.020 | [-0.858, 5.289] | inconclusive (noisy, drift) |
| matrix | pgo-lto | 28 | 12.736 | 356.610 | 12.851 | -35.016 | [-39.977, -29.662] | inconclusive (noisy) |
| strings | baseline | 14 | 26.906 | 376.681 | 3.801 | baseline | n/a | measured |
| strings | o2 | 13 | 26.873 | 349.347 | 1.560 | 0.503 | [-0.426, 1.267] | no_clear_change |
| strings | lto | 12 | 27.715 | 332.578 | 4.059 | -2.700 | [-5.275, -0.972] | inconclusive (noisy) |
| strings | pgo | 11 | 26.992 | 296.914 | 2.456 | -0.251 | [-4.163, 1.952] | no_clear_change |
| strings | pgo-lto | 12 | 27.603 | 331.241 | 2.515 | -3.951 | [-5.251, 0.790] | no_clear_change |
| records | baseline | 45 | 7.891 | 355.091 | 15.900 | baseline | n/a | measured (noisy) |
| records | o2 | 46 | 7.711 | 354.693 | 13.552 | 2.749 | [-2.701, 8.210] | inconclusive (noisy) |
| records | lto | 33 | 9.204 | 303.718 | 10.160 | -15.758 | [-19.024, -10.646] | inconclusive (noisy, drift) |
| records | pgo | 44 | 8.155 | 358.815 | 13.382 | -1.602 | [-3.227, 0.789] | inconclusive (noisy) |
| records | pgo-lto | 42 | 8.233 | 345.800 | 11.809 | -6.372 | [-8.918, -1.619] | inconclusive (noisy) |
| graph | baseline | 21 | 14.362 | 301.604 | 14.978 | baseline | n/a | measured (noisy) |
| graph | o2 | 18 | 13.949 | 251.088 | 8.536 | 1.298 | [0.902, 2.368] | inconclusive (noisy) |
| graph | lto | 21 | 15.073 | 316.541 | 12.733 | -3.234 | [-6.872, 4.483] | inconclusive (noisy, drift) |
| graph | pgo | 17 | 14.000 | 237.995 | 18.653 | 3.466 | [1.761, 9.879] | inconclusive (noisy, drift, short) |
| graph | pgo-lto | 24 | 14.239 | 341.746 | 15.547 | 0.157 | [-3.726, 1.161] | inconclusive (noisy) |
| logs | baseline | 19 | 16.039 | 304.740 | 20.756 | baseline | n/a | measured (noisy) |
| logs | o2 | 22 | 15.813 | 347.885 | 14.786 | -0.610 | [-19.555, 1.911] | inconclusive (noisy, drift) |
| logs | lto | 23 | 15.188 | 349.314 | 16.289 | 4.958 | [-3.584, 5.480] | inconclusive (noisy) |
| logs | pgo | 24 | 14.234 | 341.610 | 8.599 | 12.153 | [8.903, 16.007] | inconclusive (noisy, drift) |
| logs | pgo-lto | 24 | 15.455 | 370.912 | 14.198 | 4.754 | [2.552, 5.323] | inconclusive (noisy) |

## Calibration and inputs

Pilots are discarded from statistics; all pilot outputs must pass correctness. Measured samples are retained even when noisy or outside the target band.

| Workload | Input seed | Config | Pilots | Batches | Pilot median ms | Samples in target band |
|---|---:|---|---:|---:|---:|---:|
| array | 42 | baseline | 6 | 18 | 465.348 | 41/44 |
| array | 42 | o2 | 6 | 15 | 384.556 | 11/11 |
| array | 42 | lto | 6 | 14 | 355.330 | 11/11 |
| array | 42 | pgo | 6 | 15 | 381.621 | 11/11 |
| array | 42 | pgo-lto | 6 | 15 | 358.873 | 11/11 |
| sorting | 42 | baseline | 6 | 6 | 379.546 | 44/44 |
| sorting | 42 | o2 | 6 | 6 | 360.807 | 11/11 |
| sorting | 42 | lto | 6 | 6 | 357.345 | 11/11 |
| sorting | 42 | pgo | 6 | 6 | 398.688 | 11/11 |
| sorting | 42 | pgo-lto | 6 | 6 | 362.938 | 10/11 |
| hashmap | 42 | baseline | 6 | 5 | 360.835 | 38/44 |
| hashmap | 42 | o2 | 6 | 5 | 347.237 | 10/11 |
| hashmap | 42 | lto | 6 | 5 | 356.647 | 10/11 |
| hashmap | 42 | pgo | 6 | 5 | 349.225 | 10/11 |
| hashmap | 42 | pgo-lto | 6 | 5 | 332.044 | 10/11 |
| matrix | 42 | baseline | 6 | 32 | 343.913 | 44/44 |
| matrix | 42 | o2 | 6 | 40 | 361.142 | 10/11 |
| matrix | 42 | lto | 6 | 28 | 342.055 | 9/11 |
| matrix | 42 | pgo | 6 | 39 | 382.648 | 11/11 |
| matrix | 42 | pgo-lto | 6 | 28 | 449.513 | 11/11 |
| strings | 42 | baseline | 6 | 14 | 373.384 | 44/44 |
| strings | 42 | o2 | 6 | 13 | 356.079 | 11/11 |
| strings | 42 | lto | 6 | 12 | 326.728 | 11/11 |
| strings | 42 | pgo | 6 | 11 | 379.026 | 11/11 |
| strings | 42 | pgo-lto | 6 | 12 | 345.272 | 11/11 |
| records | 42 | baseline | 6 | 45 | 416.048 | 42/44 |
| records | 42 | o2 | 6 | 46 | 361.642 | 11/11 |
| records | 42 | lto | 6 | 33 | 381.259 | 11/11 |
| records | 42 | pgo | 6 | 44 | 354.062 | 11/11 |
| records | 42 | pgo-lto | 6 | 42 | 345.384 | 11/11 |
| graph | 42 | baseline | 6 | 21 | 489.005 | 43/44 |
| graph | 42 | o2 | 6 | 18 | 323.899 | 8/11 |
| graph | 42 | lto | 6 | 21 | 337.212 | 11/11 |
| graph | 42 | pgo | 9 | 17 | 291.288 | 3/11 |
| graph | 42 | pgo-lto | 6 | 24 | 461.950 | 10/11 |
| logs | 42 | baseline | 6 | 19 | 374.231 | 42/44 |
| logs | 42 | o2 | 6 | 22 | 407.698 | 10/11 |
| logs | 42 | lto | 6 | 23 | 439.672 | 10/11 |
| logs | 42 | pgo | 6 | 24 | 344.550 | 11/11 |
| logs | 42 | pgo-lto | 6 | 24 | 368.693 | 10/11 |

## Resource comparison

Peak RSS covers the whole process, including prepared input buffers. Setup is not part of compute time. Build time is one observation; PGO includes instrumented build, profile merge, and final build. Training time is reported separately.

| Workload | Config | Peak RSS MiB | Setup ms/sample | Build ms | PGO training ms | Binary KiB |
|---|---|---:|---:|---:|---:|---:|
| array | baseline | 125.508 | 208.774 | 750.865 | n/a | 27.281 |
| array | o2 | 125.508 | 190.317 | 966.830 | n/a | 27.281 |
| array | lto | 125.512 | 183.938 | 1246.697 | n/a | 30.523 |
| array | pgo | 125.508 | 185.712 | 2140.859 | 28.498 | 28.953 |
| array | pgo-lto | 125.508 | 191.492 | 2444.962 | 27.725 | 28.391 |
| sorting | baseline | 11.023 | 7.231 | 1144.193 | n/a | 31.547 |
| sorting | o2 | 11.023 | 7.246 | 1191.629 | n/a | 31.562 |
| sorting | lto | 11.023 | 7.205 | 1243.748 | n/a | 30.664 |
| sorting | pgo | 11.023 | 6.999 | 2390.115 | 24.192 | 37.898 |
| sorting | pgo-lto | 11.023 | 7.459 | 2824.867 | 23.357 | 29.070 |
| hashmap | baseline | 23.246 | 50.021 | 1242.397 | n/a | 30.867 |
| hashmap | o2 | 23.246 | 51.260 | 1180.137 | n/a | 27.719 |
| hashmap | lto | 23.246 | 49.502 | 1340.995 | n/a | 30.414 |
| hashmap | pgo | 23.246 | 50.551 | 2539.515 | 30.302 | 29.047 |
| hashmap | pgo-lto | 23.246 | 51.038 | 3017.560 | 30.979 | 28.039 |
| matrix | baseline | 8.383 | 3.968 | 1336.190 | n/a | 30.938 |
| matrix | o2 | 8.430 | 4.399 | 1152.574 | n/a | 26.938 |
| matrix | lto | 8.414 | 3.921 | 1283.309 | n/a | 30.414 |
| matrix | pgo | 8.383 | 4.283 | 2217.778 | 16.992 | 28.906 |
| matrix | pgo-lto | 8.414 | 3.947 | 2639.953 | 14.848 | 28.211 |
| strings | baseline | 34.008 | 68.200 | 1063.923 | n/a | 27.742 |
| strings | o2 | 34.008 | 65.354 | 986.642 | n/a | 27.742 |
| strings | lto | 34.008 | 64.872 | 1146.746 | n/a | 26.891 |
| strings | pgo | 34.008 | 62.352 | 2129.659 | 21.061 | 29.375 |
| strings | pgo-lto | 34.008 | 64.627 | 2974.294 | 21.148 | 29.031 |
| records | baseline | 8.414 | 20.236 | 2245.300 | n/a | 39.039 |
| records | o2 | 8.414 | 21.428 | 2496.595 | n/a | 35.055 |
| records | lto | 8.383 | 21.074 | 2409.260 | n/a | 38.438 |
| records | pgo | 8.430 | 21.574 | 4549.377 | 36.464 | 40.922 |
| records | pgo-lto | 8.305 | 20.421 | 5020.209 | 36.135 | 40.336 |
| graph | baseline | 8.398 | 1.042 | 4136.046 | n/a | 39.305 |
| graph | o2 | 8.508 | 0.992 | 3250.777 | n/a | 35.328 |
| graph | lto | 8.383 | 1.019 | 3699.557 | n/a | 38.344 |
| graph | pgo | 8.430 | 1.075 | 5421.110 | 20.032 | 40.953 |
| graph | pgo-lto | 8.414 | 1.062 | 6431.476 | 16.959 | 39.969 |
| logs | baseline | 9.625 | 45.901 | 3296.802 | n/a | 43.148 |
| logs | o2 | 9.625 | 47.349 | 2792.442 | n/a | 39.148 |
| logs | lto | 9.625 | 46.130 | 2469.574 | n/a | 42.594 |
| logs | pgo | 9.625 | 46.474 | 4586.542 | 75.515 | 49.281 |
| logs | pgo-lto | 9.625 | 45.334 | 4990.182 | 66.513 | 44.422 |

## Configurations and verification

- `baseline`: `-O3`; build mode `standard`.
- `o2`: `-O2`; build mode `standard`.
- `lto`: `-O3 -flto`; build mode `standard`.
- `pgo`: `-O3`; build mode `pgo`.
- `pgo-lto`: `-O3 -flto`; build mode `pgo`.

## Interpretation limits

- Compute timing excludes input generation and reset/copy work; checksums remain timed.
- Peak RSS is per-process maximum resident memory; null means unsupported.
- Paired moving-block bootstrap intervals are empirical; short series and nonstationarity limit coverage. No outliers are removed.
- Correctness covers supplied deterministic cases, not arbitrary C++ programs.
- Existing promotion floors remain: at least 2% and twice combined relative MAD; maximum 5% regression; CV at most 5% by default.
- Confidence bounds and drift checks add restrictions; they never relax those rules. No samples are dropped.
- Circular moving-block resampling retains adjacent pair dependence; its square-root block length is a heuristic. Coverage remains approximate with few pairs or nonstationarity.
- Fresh confirmation uses a different scheduling/bootstrap seed and a different held-out input seed with equal work per batch.
- PGO profiles are trained on separate inputs and regenerated for each experiment. They cannot become reusable flag-only application presets.
- Resource limits handle accidental runaway trusted local code; they are not a security sandbox.


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

## Gate audit

| Workload | Candidate | Failed gates |
|---|---|---|
| array | o2 | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| array | lto | improvement_floor_and_uncertainty |
| array | pgo | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| array | pgo-lto | variability, improvement_floor_and_uncertainty |
| sorting | o2 | variability, improvement_floor_and_uncertainty |
| sorting | lto | variability, drift, improvement_floor_and_uncertainty |
| sorting | pgo | variability, improvement_floor_and_uncertainty |
| sorting | pgo-lto | variability, improvement_floor_and_uncertainty |
| hashmap | o2 | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| hashmap | lto | variability, drift, improvement_floor_and_uncertainty |
| hashmap | pgo | variability, drift, improvement_floor_and_uncertainty |
| hashmap | pgo-lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| matrix | o2 | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| matrix | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| matrix | pgo | variability, drift, improvement_floor_and_uncertainty |
| matrix | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | o2 | improvement_floor_and_uncertainty |
| strings | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | pgo | improvement_floor_and_uncertainty |
| strings | pgo-lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| records | o2 | variability, improvement_floor_and_uncertainty |
| records | lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| records | pgo | variability, improvement_floor_and_uncertainty |
| records | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | o2 | variability, improvement_floor_and_uncertainty |
| graph | lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | pgo | duration, variability, drift, improvement_floor_and_uncertainty |
| graph | pgo-lto | variability, improvement_floor_and_uncertainty |
| logs | o2 | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| logs | lto | variability, improvement_floor_and_uncertainty |
| logs | pgo | variability, drift, improvement_floor_and_uncertainty |
| logs | pgo-lto | variability, improvement_floor_and_uncertainty |
