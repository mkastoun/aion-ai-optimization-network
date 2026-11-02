# AION Phase 3 performance comparison

Run: `20261031T000202-01808fcd04` (independent_confirmation); status: **completed**

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1) — x86_64-pc-linux-gnu
Machine: Linux — Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz
Measured pairs per candidate: 11; warmups: 2; schedule/bootstrap seed: 53301.

Target compute time: 250–500 ms per sample. Input generation, allocation of input buffers, and reset/copy work are excluded from compute time.

A unit is one execution of the workload's fixed input/rounds. Each configuration calibrates its batch count separately; comparisons normalize by batches and use its adjacent -O3 partner. Insertion/rehash costs in hash maps and checksum scans remain timed.

Positive paired improvement means faster. Both the reported gain and interval describe the median of paired effects. The raw JSON also retains the ratio of marginal medians used by the unchanged screening floor. Intervals use a Bonferroni adjustment across 32 declared comparisons (nominal family confidence 95%).

| Workload | Config | Batches | Unit ms | Sample ms | CV % | Paired gain % | Adjusted interval % | Outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| array | baseline | 11 | 26.446 | 290.902 | 23.491 | baseline | n/a | measured (noisy) |
| array | o2 | 9 | 26.736 | 240.622 | 22.657 | 0.522 | [-6.810, 4.050] | inconclusive (noisy, short) |
| array | lto | 12 | 26.361 | 316.333 | 5.362 | -0.342 | [-3.093, 6.089] | inconclusive (noisy) |
| array | pgo | 15 | 26.993 | 404.896 | 8.573 | 0.175 | [-2.111, 10.153] | inconclusive (noisy) |
| array | pgo-lto | 15 | 25.944 | 389.153 | 8.937 | 2.012 | [-1.569, 7.116] | inconclusive (noisy) |
| sorting | baseline | 4 | 64.877 | 259.507 | 10.632 | baseline | n/a | measured (noisy) |
| sorting | o2 | 5 | 60.097 | 300.486 | 13.166 | 8.605 | [7.202, 10.342] | inconclusive (noisy, drift) |
| sorting | lto | 6 | 58.178 | 349.068 | 11.999 | 11.500 | [8.147, 22.195] | inconclusive (noisy) |
| sorting | pgo | 5 | 65.497 | 327.484 | 6.603 | -1.037 | [-1.430, 2.343] | inconclusive (noisy) |
| sorting | pgo-lto | 5 | 63.341 | 316.704 | 12.088 | 4.194 | [-5.390, 5.304] | inconclusive (noisy) |
| hashmap | baseline | 5 | 69.482 | 347.408 | 15.422 | baseline | n/a | measured (noisy) |
| hashmap | o2 | 5 | 69.653 | 348.266 | 24.621 | 1.283 | [-1.106, 22.519] | inconclusive (noisy, drift) |
| hashmap | lto | 5 | 69.591 | 347.953 | 17.089 | -1.414 | [-3.021, 2.673] | inconclusive (noisy) |
| hashmap | pgo | 5 | 69.183 | 345.914 | 10.683 | -0.936 | [-9.337, 1.514] | inconclusive (noisy, drift) |
| hashmap | pgo-lto | 5 | 67.845 | 339.224 | 13.130 | 2.245 | [-0.887, 3.037] | inconclusive (noisy) |
| matrix | baseline | 41 | 9.030 | 370.238 | 8.585 | baseline | n/a | measured (noisy) |
| matrix | o2 | 41 | 9.140 | 374.760 | 19.067 | -0.735 | [-3.691, 0.237] | inconclusive (noisy) |
| matrix | lto | 30 | 12.450 | 373.503 | 8.410 | -38.245 | [-45.019, -35.967] | inconclusive (noisy) |
| matrix | pgo | 39 | 8.998 | 350.941 | 10.784 | 2.068 | [-0.361, 4.243] | inconclusive (noisy) |
| matrix | pgo-lto | 29 | 12.373 | 358.822 | 11.354 | -38.208 | [-39.285, -35.439] | inconclusive (noisy) |
| strings | baseline | 13 | 26.499 | 344.485 | 5.304 | baseline | n/a | measured (noisy) |
| strings | o2 | 14 | 26.948 | 377.274 | 4.353 | -1.900 | [-8.938, -0.733] | no_clear_change |
| strings | lto | 14 | 27.628 | 386.789 | 6.149 | -3.551 | [-4.549, -2.843] | inconclusive (noisy) |
| strings | pgo | 14 | 26.409 | 369.728 | 1.458 | -0.377 | [-2.344, 0.800] | no_clear_change |
| strings | pgo-lto | 13 | 27.335 | 355.353 | 8.516 | -1.801 | [-4.091, -0.028] | inconclusive (noisy) |
| records | baseline | 45 | 7.744 | 348.495 | 9.269 | baseline | n/a | measured (noisy) |
| records | o2 | 36 | 7.510 | 270.375 | 8.212 | 2.325 | [0.930, 10.653] | inconclusive (noisy) |
| records | lto | 40 | 9.014 | 360.575 | 3.312 | -14.596 | [-17.878, -11.417] | regression |
| records | pgo | 38 | 7.793 | 296.150 | 0.832 | 0.106 | [-3.803, 0.672] | no_clear_change |
| records | pgo-lto | 34 | 8.118 | 276.018 | 11.265 | -3.760 | [-5.845, -1.173] | inconclusive (noisy) |
| graph | baseline | 25 | 14.261 | 356.515 | 11.663 | baseline | n/a | measured (noisy) |
| graph | o2 | 20 | 14.332 | 286.639 | 8.785 | 2.867 | [0.956, 4.286] | inconclusive (noisy) |
| graph | lto | 24 | 14.800 | 355.210 | 13.062 | -2.812 | [-5.250, 1.876] | inconclusive (noisy) |
| graph | pgo | 24 | 14.102 | 338.443 | 12.719 | 0.927 | [-1.984, 2.574] | inconclusive (noisy) |
| graph | pgo-lto | 24 | 14.358 | 344.586 | 12.722 | -0.562 | [-1.765, 3.358] | inconclusive (noisy, drift) |
| logs | baseline | 23 | 15.742 | 362.074 | 9.502 | baseline | n/a | measured (noisy) |
| logs | o2 | 23 | 15.574 | 358.202 | 7.178 | 1.312 | [-1.135, 5.827] | inconclusive (noisy) |
| logs | lto | 24 | 15.228 | 365.460 | 12.662 | 3.627 | [2.599, 7.884] | inconclusive (noisy, drift) |
| logs | pgo | 22 | 14.281 | 314.175 | 3.759 | 9.076 | [7.358, 9.849] | inconclusive (noisy) |
| logs | pgo-lto | 24 | 15.066 | 361.581 | 3.889 | 2.787 | [0.002, 5.591] | inconclusive (noisy) |

## Calibration and inputs

Pilots are discarded from statistics; all pilot outputs must pass correctness. Measured samples are retained even when noisy or outside the target band.

| Workload | Input seed | Config | Pilots | Batches | Pilot median ms | Samples in target band |
|---|---:|---|---:|---:|---:|---:|
| array | 314159 | baseline | 6 | 11 | 296.539 | 42/44 |
| array | 314159 | o2 | 6 | 9 | 279.881 | 2/11 |
| array | 314159 | lto | 6 | 12 | 323.546 | 11/11 |
| array | 314159 | pgo | 6 | 15 | 453.353 | 11/11 |
| array | 314159 | pgo-lto | 6 | 15 | 380.663 | 11/11 |
| sorting | 314159 | baseline | 6 | 4 | 324.439 | 44/44 |
| sorting | 314159 | o2 | 6 | 5 | 300.433 | 11/11 |
| sorting | 314159 | lto | 6 | 6 | 334.634 | 11/11 |
| sorting | 314159 | pgo | 6 | 5 | 330.403 | 11/11 |
| sorting | 314159 | pgo-lto | 6 | 5 | 323.290 | 11/11 |
| hashmap | 314159 | baseline | 6 | 5 | 364.128 | 41/44 |
| hashmap | 314159 | o2 | 6 | 5 | 344.936 | 10/11 |
| hashmap | 314159 | lto | 6 | 5 | 343.783 | 10/11 |
| hashmap | 314159 | pgo | 6 | 5 | 331.233 | 11/11 |
| hashmap | 314159 | pgo-lto | 6 | 5 | 341.247 | 11/11 |
| matrix | 314159 | baseline | 6 | 41 | 378.902 | 43/44 |
| matrix | 314159 | o2 | 6 | 41 | 371.599 | 10/11 |
| matrix | 314159 | lto | 6 | 30 | 496.000 | 11/11 |
| matrix | 314159 | pgo | 6 | 39 | 345.458 | 11/11 |
| matrix | 314159 | pgo-lto | 6 | 29 | 351.825 | 11/11 |
| strings | 314159 | baseline | 6 | 13 | 347.872 | 44/44 |
| strings | 314159 | o2 | 6 | 14 | 366.026 | 11/11 |
| strings | 314159 | lto | 6 | 14 | 485.279 | 11/11 |
| strings | 314159 | pgo | 6 | 14 | 374.561 | 11/11 |
| strings | 314159 | pgo-lto | 6 | 13 | 354.277 | 11/11 |
| records | 314159 | baseline | 6 | 45 | 344.275 | 44/44 |
| records | 314159 | o2 | 6 | 36 | 285.245 | 11/11 |
| records | 314159 | lto | 6 | 40 | 364.854 | 11/11 |
| records | 314159 | pgo | 6 | 38 | 316.914 | 11/11 |
| records | 314159 | pgo-lto | 6 | 34 | 275.265 | 11/11 |
| graph | 314159 | baseline | 6 | 25 | 356.384 | 43/44 |
| graph | 314159 | o2 | 6 | 20 | 304.301 | 11/11 |
| graph | 314159 | lto | 6 | 24 | 351.321 | 11/11 |
| graph | 314159 | pgo | 6 | 24 | 339.371 | 11/11 |
| graph | 314159 | pgo-lto | 6 | 24 | 341.517 | 11/11 |
| logs | 314159 | baseline | 6 | 23 | 371.919 | 44/44 |
| logs | 314159 | o2 | 6 | 23 | 357.662 | 11/11 |
| logs | 314159 | lto | 6 | 24 | 361.582 | 11/11 |
| logs | 314159 | pgo | 6 | 22 | 335.387 | 11/11 |
| logs | 314159 | pgo-lto | 6 | 24 | 359.311 | 11/11 |

## Resource comparison

Peak RSS covers the whole process, including prepared input buffers. Setup is not part of compute time. Build time is one observation; PGO includes instrumented build, profile merge, and final build. Training time is reported separately.

| Workload | Config | Peak RSS MiB | Setup ms/sample | Build ms | PGO training ms | Binary KiB |
|---|---|---:|---:|---:|---:|---:|
| array | baseline | 125.508 | 162.991 | 1015.527 | n/a | 27.281 |
| array | o2 | 125.508 | 151.123 | 1319.452 | n/a | 27.281 |
| array | lto | 125.508 | 175.018 | 1199.488 | n/a | 30.523 |
| array | pgo | 125.508 | 203.626 | 2049.327 | 27.725 | 28.953 |
| array | pgo-lto | 125.508 | 188.403 | 2698.635 | 29.472 | 28.391 |
| sorting | baseline | 11.023 | 6.694 | 1143.128 | n/a | 31.547 |
| sorting | o2 | 11.023 | 6.997 | 1235.699 | n/a | 31.562 |
| sorting | lto | 11.023 | 7.462 | 1281.540 | n/a | 30.664 |
| sorting | pgo | 11.023 | 7.156 | 2401.943 | 23.342 | 37.898 |
| sorting | pgo-lto | 11.023 | 6.893 | 3031.652 | 22.844 | 29.070 |
| hashmap | baseline | 23.195 | 49.184 | 1226.276 | n/a | 30.867 |
| hashmap | o2 | 23.195 | 49.738 | 1557.810 | n/a | 27.719 |
| hashmap | lto | 23.070 | 48.607 | 1318.968 | n/a | 30.414 |
| hashmap | pgo | 23.195 | 50.218 | 2542.402 | 32.170 | 29.047 |
| hashmap | pgo-lto | 23.195 | 48.318 | 2893.696 | 32.303 | 28.039 |
| matrix | baseline | 8.414 | 4.406 | 1068.687 | n/a | 30.938 |
| matrix | o2 | 8.383 | 4.379 | 1067.822 | n/a | 26.938 |
| matrix | lto | 8.379 | 3.923 | 1241.175 | n/a | 30.414 |
| matrix | pgo | 8.379 | 4.249 | 2558.032 | 15.230 | 28.906 |
| matrix | pgo-lto | 8.383 | 3.755 | 3038.762 | 14.823 | 28.211 |
| strings | baseline | 34.008 | 65.093 | 1116.112 | n/a | 27.742 |
| strings | o2 | 34.012 | 67.959 | 1010.960 | n/a | 27.742 |
| strings | lto | 34.008 | 67.843 | 1174.318 | n/a | 26.891 |
| strings | pgo | 34.008 | 67.184 | 2104.677 | 20.757 | 29.375 |
| strings | pgo-lto | 34.008 | 64.753 | 2409.561 | 21.268 | 29.031 |
| records | baseline | 8.414 | 19.822 | 2145.597 | n/a | 39.039 |
| records | o2 | 8.414 | 20.220 | 2576.059 | n/a | 35.055 |
| records | lto | 8.383 | 19.925 | 2532.983 | n/a | 38.438 |
| records | pgo | 8.430 | 20.337 | 4795.907 | 35.718 | 40.922 |
| records | pgo-lto | 8.379 | 20.341 | 6097.002 | 35.933 | 40.336 |
| graph | baseline | 8.414 | 1.043 | 2443.144 | n/a | 39.305 |
| graph | o2 | 8.418 | 1.014 | 2439.044 | n/a | 35.328 |
| graph | lto | 8.379 | 1.022 | 3466.620 | n/a | 38.344 |
| graph | pgo | 8.414 | 1.009 | 5892.676 | 19.440 | 40.953 |
| graph | pgo-lto | 8.383 | 1.062 | 5937.278 | 19.894 | 39.969 |
| logs | baseline | 9.625 | 45.065 | 2132.199 | n/a | 43.148 |
| logs | o2 | 9.625 | 43.740 | 2344.217 | n/a | 39.148 |
| logs | lto | 9.625 | 46.488 | 2403.842 | n/a | 42.594 |
| logs | pgo | 9.625 | 46.252 | 5181.446 | 70.564 | 49.281 |
| logs | pgo-lto | 9.625 | 45.518 | 5057.240 | 72.657 | 44.422 |

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
Noisy configuration summaries: 34/40; drifting: 4/40.
Load average at start/end: `[1.00390625, 1.0, 0.7763671875]` / `[1.01806640625, 1.04541015625, 0.96337890625]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

## Gate audit

| Workload | Candidate | Failed gates |
|---|---|---|
| array | o2 | duration, variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| array | lto | variability, improvement_floor_and_uncertainty |
| array | pgo | variability, improvement_floor_and_uncertainty |
| array | pgo-lto | variability, improvement_floor_and_uncertainty |
| sorting | o2 | variability, drift, improvement_floor_and_uncertainty |
| sorting | lto | variability, improvement_floor_and_uncertainty |
| sorting | pgo | variability, improvement_floor_and_uncertainty |
| sorting | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| hashmap | o2 | variability, drift, improvement_floor_and_uncertainty |
| hashmap | lto | variability, improvement_floor_and_uncertainty |
| hashmap | pgo | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| hashmap | pgo-lto | variability, improvement_floor_and_uncertainty |
| matrix | o2 | variability, improvement_floor_and_uncertainty |
| matrix | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| matrix | pgo | variability, improvement_floor_and_uncertainty |
| matrix | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | o2 | acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | lto | variability, improvement_floor_and_uncertainty |
| strings | pgo | improvement_floor_and_uncertainty |
| strings | pgo-lto | variability, improvement_floor_and_uncertainty |
| records | o2 | variability, improvement_floor_and_uncertainty |
| records | lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| records | pgo | improvement_floor_and_uncertainty |
| records | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | o2 | variability, improvement_floor_and_uncertainty |
| graph | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | pgo | variability, improvement_floor_and_uncertainty |
| graph | pgo-lto | variability, drift, improvement_floor_and_uncertainty |
| logs | o2 | variability, improvement_floor_and_uncertainty |
| logs | lto | variability, drift, improvement_floor_and_uncertainty |
| logs | pgo | variability, improvement_floor_and_uncertainty |
| logs | pgo-lto | variability, improvement_floor_and_uncertainty |
