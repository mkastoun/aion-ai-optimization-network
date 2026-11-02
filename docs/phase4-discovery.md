# AION Phase 4 performance comparison

Run: `20261031T025701-07d35075c3` (benchmark); status: **completed**

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1) — x86_64-pc-linux-gnu
Machine: Linux — Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz
Measured pairs per candidate: 11; warmups: 2; schedule/bootstrap seed: 64300.

Target compute time: 250–500 ms per sample. Input generation, allocation of input buffers, and reset/copy work are excluded from compute time.

A unit is one execution of the workload's fixed input/rounds. Each configuration calibrates its batch count separately; comparisons normalize by batches and use its adjacent -O3 partner. Insertion/rehash costs in hash maps and checksum scans remain timed.

Positive paired improvement means faster. Both the reported gain and interval describe the median of paired effects. The raw JSON also retains the ratio of marginal medians used by the unchanged screening floor. Intervals use a Bonferroni adjustment across 40 declared comparisons (nominal family confidence 95%).

| Workload | Config | Batches | Unit ms | Sample ms | CV % | Paired gain % | Adjusted interval % | Outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| array | baseline | 11 | 25.294 | 278.238 | 5.388 | baseline | n/a | measured (noisy) |
| array | o2 | 15 | 25.624 | 384.364 | 1.857 | -1.020 | [-3.310, 1.096] | no_clear_change |
| array | lto | 14 | 25.504 | 357.054 | 1.652 | -0.708 | [-3.444, 3.340] | no_clear_change |
| array | pgo | 15 | 25.224 | 378.365 | 3.490 | -0.113 | [-3.381, 4.266] | inconclusive (noisy) |
| array | pgo-lto | 14 | 25.228 | 353.198 | 7.938 | -0.049 | [-1.226, 0.951] | inconclusive (noisy) |
| sorting | baseline | 6 | 63.113 | 378.678 | 5.404 | baseline | n/a | measured (noisy) |
| sorting | o2 | 6 | 57.834 | 347.003 | 6.260 | 7.919 | [5.440, 9.553] | inconclusive (noisy) |
| sorting | lto | 6 | 57.058 | 342.349 | 5.221 | 10.681 | [8.397, 12.984] | inconclusive (noisy) |
| sorting | pgo | 5 | 64.678 | 323.388 | 2.806 | -2.281 | [-3.699, -0.198] | inconclusive (noisy) |
| sorting | pgo-lto | 6 | 61.784 | 370.706 | 8.781 | 2.980 | [0.280, 4.794] | inconclusive (noisy) |
| hashmap | baseline | 5 | 68.010 | 340.048 | 10.177 | baseline | n/a | measured (noisy) |
| hashmap | o2 | 5 | 67.536 | 337.678 | 14.255 | 1.287 | [-0.306, 3.611] | inconclusive (noisy) |
| hashmap | lto | 5 | 68.760 | 343.801 | 12.541 | -2.685 | [-14.395, 15.024] | inconclusive (noisy) |
| hashmap | pgo | 5 | 67.666 | 338.329 | 2.567 | -1.437 | [-2.634, 3.281] | inconclusive (noisy) |
| hashmap | pgo-lto | 5 | 67.365 | 336.825 | 8.182 | 1.685 | [1.188, 6.569] | inconclusive (noisy, drift) |
| matrix | baseline | 39 | 8.950 | 349.052 | 10.748 | baseline | n/a | measured (noisy) |
| matrix | o2 | 38 | 9.001 | 342.048 | 3.240 | -1.144 | [-2.755, 0.598] | no_clear_change |
| matrix | lto | 29 | 12.374 | 358.845 | 9.146 | -35.579 | [-38.346, -33.057] | inconclusive (noisy) |
| matrix | pgo | 38 | 8.971 | 340.888 | 2.701 | 0.107 | [-0.446, 1.628] | inconclusive (noisy) |
| matrix | pgo-lto | 29 | 12.172 | 352.999 | 10.992 | -34.928 | [-38.514, -32.520] | inconclusive (noisy) |
| strings | baseline | 14 | 26.336 | 368.706 | 7.582 | baseline | n/a | measured (noisy) |
| strings | o2 | 13 | 26.166 | 340.162 | 4.419 | -0.395 | [-2.281, 1.460] | no_clear_change |
| strings | lto | 13 | 27.471 | 357.127 | 7.906 | -3.962 | [-5.246, 1.320] | inconclusive (noisy) |
| strings | pgo | 14 | 26.381 | 369.328 | 8.792 | 0.017 | [-0.662, 1.184] | inconclusive (noisy) |
| strings | pgo-lto | 13 | 27.254 | 354.306 | 8.870 | -3.429 | [-4.665, -2.430] | inconclusive (noisy) |
| records | baseline | 45 | 7.711 | 346.997 | 5.007 | baseline | n/a | measured (noisy) |
| records | o2 | 45 | 7.518 | 338.314 | 4.112 | 2.846 | [2.335, 3.290] | inconclusive (noisy) |
| records | lto | 40 | 8.809 | 352.372 | 2.284 | -15.163 | [-16.030, -12.816] | regression |
| records | pgo | 46 | 7.731 | 355.610 | 2.760 | 0.079 | [-1.194, 0.874] | no_clear_change |
| records | pgo-lto | 45 | 8.076 | 363.430 | 8.856 | -3.826 | [-6.085, -2.827] | inconclusive (noisy) |
| graph | baseline | 24 | 14.223 | 341.348 | 9.709 | baseline | n/a | measured (noisy) |
| graph | o2 | 21 | 13.947 | 292.881 | 6.758 | 1.043 | [-3.660, 4.443] | inconclusive (noisy) |
| graph | lto | 23 | 15.122 | 347.814 | 12.138 | -3.104 | [-5.905, -1.758] | inconclusive (noisy, drift) |
| graph | pgo | 25 | 13.844 | 346.105 | 9.882 | 1.593 | [-2.033, 3.255] | inconclusive (noisy) |
| graph | pgo-lto | 25 | 13.947 | 348.675 | 12.162 | 0.514 | [-3.771, 3.839] | inconclusive (noisy) |
| logs | baseline | 21 | 15.626 | 328.141 | 8.834 | baseline | n/a | measured (noisy) |
| logs | o2 | 23 | 15.589 | 358.557 | 1.993 | 0.014 | [-0.431, 1.225] | no_clear_change |
| logs | lto | 22 | 14.991 | 329.795 | 2.628 | 4.856 | [1.666, 12.660] | inconclusive (noisy) |
| logs | pgo | 27 | 14.167 | 382.499 | 13.328 | 10.753 | [7.717, 12.708] | inconclusive (noisy) |
| logs | pgo-lto | 24 | 14.954 | 358.900 | 12.257 | 4.331 | [1.673, 5.944] | inconclusive (noisy, drift) |
| image | baseline | 165 | 1.952 | 322.084 | 8.395 | baseline | n/a | measured (noisy) |
| image | o2 | 146 | 2.313 | 337.722 | 5.484 | -18.755 | [-19.743, -15.779] | inconclusive (noisy) |
| image | lto | 159 | 2.046 | 325.389 | 2.664 | -4.700 | [-6.636, -2.191] | inconclusive |
| image | pgo | 171 | 2.005 | 342.934 | 15.572 | -0.704 | [-4.391, 0.496] | inconclusive (noisy) |
| image | pgo-lto | 153 | 2.170 | 331.970 | 2.889 | -11.274 | [-14.669, -8.899] | inconclusive (noisy) |
| kv | baseline | 28 | 12.164 | 340.603 | 18.326 | baseline | n/a | measured (noisy) |
| kv | o2 | 29 | 12.217 | 354.301 | 10.569 | -2.238 | [-4.221, 3.915] | inconclusive (noisy) |
| kv | lto | 29 | 11.872 | 344.275 | 7.427 | 2.102 | [-2.089, 2.932] | inconclusive (noisy) |
| kv | pgo | 30 | 12.111 | 363.325 | 10.375 | 3.585 | [-0.726, 10.139] | inconclusive (noisy, drift) |
| kv | pgo-lto | 23 | 12.045 | 277.039 | 38.954 | -0.505 | [-1.808, 0.165] | inconclusive (noisy) |

## Calibration and inputs

Pilots are discarded from statistics; all pilot outputs must pass correctness. Measured samples are retained even when noisy or outside the target band.

| Workload | Input seed | Config | Pilots | Batches | Pilot median ms | Samples in target band |
|---|---:|---|---:|---:|---:|---:|
| array | 42 | baseline | 6 | 11 | 288.866 | 44/44 |
| array | 42 | o2 | 6 | 15 | 381.943 | 11/11 |
| array | 42 | lto | 6 | 14 | 353.229 | 11/11 |
| array | 42 | pgo | 6 | 15 | 377.588 | 11/11 |
| array | 42 | pgo-lto | 6 | 14 | 354.121 | 11/11 |
| sorting | 42 | baseline | 6 | 6 | 385.105 | 44/44 |
| sorting | 42 | o2 | 6 | 6 | 350.668 | 11/11 |
| sorting | 42 | lto | 6 | 6 | 338.512 | 11/11 |
| sorting | 42 | pgo | 6 | 5 | 333.043 | 11/11 |
| sorting | 42 | pgo-lto | 6 | 6 | 372.157 | 11/11 |
| hashmap | 42 | baseline | 6 | 5 | 346.480 | 44/44 |
| hashmap | 42 | o2 | 6 | 5 | 338.775 | 11/11 |
| hashmap | 42 | lto | 6 | 5 | 338.050 | 11/11 |
| hashmap | 42 | pgo | 6 | 5 | 343.008 | 11/11 |
| hashmap | 42 | pgo-lto | 6 | 5 | 355.550 | 11/11 |
| matrix | 42 | baseline | 6 | 39 | 355.326 | 43/44 |
| matrix | 42 | o2 | 6 | 38 | 345.081 | 11/11 |
| matrix | 42 | lto | 6 | 29 | 354.779 | 11/11 |
| matrix | 42 | pgo | 6 | 38 | 341.047 | 11/11 |
| matrix | 42 | pgo-lto | 6 | 29 | 353.522 | 11/11 |
| strings | 42 | baseline | 6 | 14 | 368.273 | 44/44 |
| strings | 42 | o2 | 6 | 13 | 437.729 | 11/11 |
| strings | 42 | lto | 6 | 13 | 455.539 | 11/11 |
| strings | 42 | pgo | 6 | 14 | 370.590 | 11/11 |
| strings | 42 | pgo-lto | 6 | 13 | 352.272 | 11/11 |
| records | 42 | baseline | 6 | 45 | 347.539 | 44/44 |
| records | 42 | o2 | 6 | 45 | 346.744 | 11/11 |
| records | 42 | lto | 6 | 40 | 351.435 | 11/11 |
| records | 42 | pgo | 6 | 46 | 361.250 | 11/11 |
| records | 42 | pgo-lto | 6 | 45 | 362.814 | 11/11 |
| graph | 42 | baseline | 6 | 24 | 331.662 | 44/44 |
| graph | 42 | o2 | 6 | 21 | 304.257 | 11/11 |
| graph | 42 | lto | 6 | 23 | 336.553 | 11/11 |
| graph | 42 | pgo | 6 | 25 | 350.010 | 11/11 |
| graph | 42 | pgo-lto | 6 | 25 | 343.594 | 11/11 |
| logs | 42 | baseline | 6 | 21 | 325.532 | 44/44 |
| logs | 42 | o2 | 6 | 23 | 368.152 | 11/11 |
| logs | 42 | lto | 6 | 22 | 325.627 | 11/11 |
| logs | 42 | pgo | 6 | 27 | 384.026 | 10/11 |
| logs | 42 | pgo-lto | 6 | 24 | 362.957 | 11/11 |
| image | 42 | baseline | 6 | 165 | 325.337 | 44/44 |
| image | 42 | o2 | 6 | 146 | 337.973 | 11/11 |
| image | 42 | lto | 6 | 159 | 335.972 | 11/11 |
| image | 42 | pgo | 6 | 171 | 339.548 | 10/11 |
| image | 42 | pgo-lto | 6 | 153 | 338.268 | 11/11 |
| kv | 42 | baseline | 6 | 28 | 341.101 | 41/44 |
| kv | 42 | o2 | 6 | 29 | 355.767 | 11/11 |
| kv | 42 | lto | 6 | 29 | 350.512 | 11/11 |
| kv | 42 | pgo | 6 | 30 | 368.136 | 11/11 |
| kv | 42 | pgo-lto | 6 | 23 | 331.160 | 8/11 |

## Resource comparison

Peak RSS covers the whole process, including prepared input buffers. Setup is not part of compute time. Build time is one observation; PGO includes instrumented build, profile merge, and final build. Training time is reported separately.

| Workload | Config | Peak RSS MiB | Setup ms/sample | Build ms | PGO training ms | Binary KiB |
|---|---|---:|---:|---:|---:|---:|
| array | baseline | 125.508 | 158.059 | 1127.401 | n/a | 27.281 |
| array | o2 | 125.508 | 182.148 | 1029.439 | n/a | 27.281 |
| array | lto | 125.508 | 179.831 | 1177.396 | n/a | 30.523 |
| array | pgo | 125.512 | 184.041 | 2102.038 | 30.770 | 28.953 |
| array | pgo-lto | 125.508 | 177.582 | 2522.672 | 30.612 | 28.391 |
| sorting | baseline | 11.023 | 7.298 | 1121.214 | n/a | 31.547 |
| sorting | o2 | 11.023 | 7.273 | 1121.601 | n/a | 31.562 |
| sorting | lto | 11.023 | 7.480 | 1257.061 | n/a | 30.664 |
| sorting | pgo | 11.023 | 6.834 | 2400.256 | 23.738 | 37.898 |
| sorting | pgo-lto | 11.023 | 7.287 | 2732.906 | 24.892 | 29.070 |
| hashmap | baseline | 23.246 | 47.820 | 1183.075 | n/a | 30.867 |
| hashmap | o2 | 23.250 | 48.323 | 1177.352 | n/a | 27.719 |
| hashmap | lto | 23.250 | 47.145 | 1340.719 | n/a | 30.414 |
| hashmap | pgo | 23.250 | 48.670 | 2473.471 | 30.369 | 29.047 |
| hashmap | pgo-lto | 23.246 | 48.291 | 2916.722 | 28.662 | 28.039 |
| matrix | baseline | 8.498 | 4.259 | 1070.361 | n/a | 30.938 |
| matrix | o2 | 8.379 | 4.190 | 1051.866 | n/a | 26.938 |
| matrix | lto | 8.504 | 3.796 | 1216.049 | n/a | 30.414 |
| matrix | pgo | 8.418 | 4.215 | 2215.665 | 16.796 | 28.906 |
| matrix | pgo-lto | 8.426 | 3.815 | 2756.343 | 16.065 | 28.211 |
| strings | baseline | 34.008 | 66.502 | 1009.881 | n/a | 27.742 |
| strings | o2 | 34.008 | 64.234 | 1390.228 | n/a | 27.742 |
| strings | lto | 34.008 | 64.816 | 1325.949 | n/a | 26.891 |
| strings | pgo | 34.008 | 66.994 | 2085.996 | 21.201 | 29.375 |
| strings | pgo-lto | 34.008 | 65.210 | 2532.597 | 20.624 | 29.031 |
| records | baseline | 8.504 | 19.895 | 2153.034 | n/a | 39.039 |
| records | o2 | 8.410 | 19.911 | 2204.382 | n/a | 35.055 |
| records | lto | 8.379 | 19.703 | 2505.893 | n/a | 38.438 |
| records | pgo | 8.500 | 20.314 | 4520.233 | 35.324 | 40.922 |
| records | pgo-lto | 8.504 | 20.324 | 4980.713 | 35.881 | 40.336 |
| graph | baseline | 8.410 | 1.028 | 2437.780 | n/a | 39.305 |
| graph | o2 | 8.379 | 1.008 | 2415.001 | n/a | 35.328 |
| graph | lto | 8.410 | 1.052 | 2696.286 | n/a | 38.344 |
| graph | pgo | 8.504 | 1.043 | 5230.711 | 19.933 | 40.953 |
| graph | pgo-lto | 8.500 | 1.031 | 5850.721 | 18.993 | 39.969 |
| logs | baseline | 9.625 | 45.173 | 2371.102 | n/a | 43.148 |
| logs | o2 | 9.625 | 44.544 | 2126.266 | n/a | 39.148 |
| logs | lto | 9.625 | 46.269 | 2448.175 | n/a | 42.594 |
| logs | pgo | 9.625 | 43.596 | 4375.055 | 77.594 | 49.281 |
| logs | pgo-lto | 9.625 | 44.347 | 4995.629 | 71.944 | 44.422 |
| image | baseline | 8.410 | 0.486 | 2107.927 | n/a | 35.086 |
| image | o2 | 8.410 | 0.537 | 2086.786 | n/a | 35.086 |
| image | lto | 8.426 | 0.470 | 2211.463 | n/a | 34.422 |
| image | pgo | 8.426 | 0.471 | 4464.895 | 13.324 | 36.945 |
| image | pgo-lto | 8.379 | 0.473 | 4953.131 | 10.252 | 36.422 |
| kv | baseline | 14.145 | 17.824 | 2625.194 | n/a | 42.109 |
| kv | o2 | 14.148 | 17.716 | 2637.978 | n/a | 42.289 |
| kv | lto | 14.148 | 17.310 | 2920.796 | n/a | 39.180 |
| kv | pgo | 14.145 | 16.529 | 5256.189 | 39.932 | 48.320 |
| kv | pgo-lto | 14.145 | 18.835 | 6677.898 | 42.572 | 46.141 |

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
Environment classification: `wsl2`; session: `a407629a605c4cbd88e960d19ca09b87`. Session IDs alone do not establish independent host conditions.
Measurement environment readiness is assessed separately by `aion quality`; compile/affinity validation alone is insufficient.
Requested affinity: `[0]`; verified pinned samples: 880/880. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Recorded verification methods: `['actual executable sched_getaffinity before/after compute']`. Verification is a snapshot, not exclusive CPU ownership.
Different CPU endpoints observed: 0/880; equal endpoints do not prove no intermediate migration.
Noisy configuration summaries: 35/50; drifting: 2/50.
Load average at start/end: `[1.1455078125, 0.966796875, 0.71484375]` / `[1.123046875, 1.099609375, 0.98095703125]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

## Gate audit

| Workload | Candidate | Failed gates |
|---|---|---|
| array | o2 | improvement_floor_and_uncertainty |
| array | lto | improvement_floor_and_uncertainty |
| array | pgo | variability, improvement_floor_and_uncertainty |
| array | pgo-lto | variability, improvement_floor_and_uncertainty |
| sorting | o2 | variability, improvement_floor_and_uncertainty |
| sorting | lto | variability, improvement_floor_and_uncertainty |
| sorting | pgo | variability, improvement_floor_and_uncertainty |
| sorting | pgo-lto | variability, improvement_floor_and_uncertainty |
| hashmap | o2 | variability, improvement_floor_and_uncertainty |
| hashmap | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| hashmap | pgo | variability, improvement_floor_and_uncertainty |
| hashmap | pgo-lto | variability, drift, improvement_floor_and_uncertainty |
| matrix | o2 | improvement_floor_and_uncertainty |
| matrix | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| matrix | pgo | variability, improvement_floor_and_uncertainty |
| matrix | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | o2 | improvement_floor_and_uncertainty |
| strings | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | pgo | variability, improvement_floor_and_uncertainty |
| strings | pgo-lto | variability, improvement_floor_and_uncertainty |
| records | o2 | variability, improvement_floor_and_uncertainty |
| records | lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| records | pgo | improvement_floor_and_uncertainty |
| records | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | o2 | variability, improvement_floor_and_uncertainty |
| graph | lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | pgo | variability, improvement_floor_and_uncertainty |
| graph | pgo-lto | variability, improvement_floor_and_uncertainty |
| logs | o2 | improvement_floor_and_uncertainty |
| logs | lto | variability, improvement_floor_and_uncertainty |
| logs | pgo | variability, improvement_floor_and_uncertainty |
| logs | pgo-lto | variability, drift, improvement_floor_and_uncertainty |
| image | o2 | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| image | lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| image | pgo | variability, improvement_floor_and_uncertainty |
| image | pgo-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| kv | o2 | variability, improvement_floor_and_uncertainty |
| kv | lto | variability, improvement_floor_and_uncertainty |
| kv | pgo | variability, drift, improvement_floor_and_uncertainty |
| kv | pgo-lto | variability, improvement_floor_and_uncertainty |
