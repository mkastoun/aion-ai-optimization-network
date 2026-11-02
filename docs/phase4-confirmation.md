# AION Phase 4 performance comparison

Run: `20261031T032139-5ccfa44eff` (independent_confirmation); status: **completed**

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1) — x86_64-pc-linux-gnu
Machine: Linux — Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz
Measured pairs per candidate: 11; warmups: 2; schedule/bootstrap seed: 64400.

Target compute time: 250–500 ms per sample. Input generation, allocation of input buffers, and reset/copy work are excluded from compute time.

A unit is one execution of the workload's fixed input/rounds. Each configuration calibrates its batch count separately; comparisons normalize by batches and use its adjacent -O3 partner. Insertion/rehash costs in hash maps and checksum scans remain timed.

Positive paired improvement means faster. Both the reported gain and interval describe the median of paired effects. The raw JSON also retains the ratio of marginal medians used by the unchanged screening floor. Intervals use a Bonferroni adjustment across 40 declared comparisons (nominal family confidence 95%).

| Workload | Config | Batches | Unit ms | Sample ms | CV % | Paired gain % | Adjusted interval % | Outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| array | baseline | 15 | 24.416 | 366.245 | 4.233 | baseline | n/a | measured |
| array | o2 | 15 | 24.259 | 363.879 | 5.213 | 1.101 | [-8.276, 1.821] | inconclusive (noisy) |
| array | lto | 15 | 24.197 | 362.953 | 4.535 | 0.640 | [-1.154, 1.635] | no_clear_change |
| array | pgo | 15 | 24.147 | 362.203 | 1.392 | 0.394 | [-1.825, 2.923] | no_clear_change |
| array | pgo-lto | 15 | 24.047 | 360.701 | 4.092 | 1.046 | [-0.042, 4.475] | inconclusive (noisy) |
| sorting | baseline | 6 | 59.969 | 359.814 | 5.107 | baseline | n/a | measured (noisy) |
| sorting | o2 | 6 | 55.065 | 330.391 | 6.134 | 8.213 | [7.649, 10.045] | inconclusive (noisy) |
| sorting | lto | 6 | 53.797 | 322.784 | 1.432 | 10.407 | [9.923, 10.620] | improvement |
| sorting | pgo | 6 | 60.767 | 364.602 | 7.540 | -1.667 | [-2.494, -1.170] | inconclusive (noisy) |
| sorting | pgo-lto | 6 | 58.584 | 351.506 | 3.331 | 2.924 | [1.669, 4.679] | inconclusive (noisy) |
| hashmap | baseline | 5 | 62.996 | 314.980 | 3.268 | baseline | n/a | measured |
| hashmap | o2 | 5 | 62.009 | 310.047 | 4.846 | 1.185 | [0.996, 2.208] | no_clear_change |
| hashmap | lto | 5 | 64.616 | 323.082 | 10.261 | -1.577 | [-19.303, -0.779] | inconclusive (noisy) |
| hashmap | pgo | 6 | 62.121 | 372.727 | 10.121 | 0.960 | [-3.092, 1.539] | inconclusive (noisy) |
| hashmap | pgo-lto | 5 | 62.042 | 310.209 | 1.524 | 0.718 | [-0.060, 1.874] | no_clear_change |
| matrix | baseline | 42 | 8.445 | 354.697 | 1.368 | baseline | n/a | measured |
| matrix | o2 | 41 | 8.482 | 347.743 | 1.277 | -1.014 | [-1.639, 0.033] | no_clear_change |
| matrix | lto | 30 | 11.540 | 346.200 | 0.785 | -36.932 | [-37.402, -36.377] | regression |
| matrix | pgo | 41 | 8.348 | 342.274 | 1.001 | 1.250 | [0.095, 2.027] | no_clear_change |
| matrix | pgo-lto | 31 | 11.444 | 354.774 | 0.899 | -35.775 | [-36.184, -34.286] | regression |
| strings | baseline | 14 | 25.290 | 354.061 | 8.652 | baseline | n/a | measured (noisy) |
| strings | o2 | 14 | 25.279 | 353.912 | 2.260 | 0.986 | [-0.756, 9.813] | inconclusive (noisy) |
| strings | lto | 12 | 26.175 | 314.104 | 1.678 | -1.558 | [-4.072, 10.932] | inconclusive (noisy) |
| strings | pgo | 14 | 25.588 | 358.235 | 7.965 | -0.442 | [-4.024, 0.356] | inconclusive (noisy) |
| strings | pgo-lto | 14 | 25.695 | 359.725 | 11.000 | -2.125 | [-3.065, -0.413] | inconclusive (noisy) |
| records | baseline | 46 | 7.186 | 330.561 | 1.221 | baseline | n/a | measured |
| records | o2 | 50 | 6.971 | 348.537 | 0.639 | 2.649 | [2.236, 3.862] | improvement |
| records | lto | 41 | 8.247 | 338.111 | 0.648 | -14.156 | [-14.359, -13.851] | regression |
| records | pgo | 46 | 7.254 | 333.672 | 1.977 | -1.267 | [-2.450, -0.126] | no_clear_change |
| records | pgo-lto | 45 | 7.535 | 339.080 | 0.916 | -4.930 | [-6.049, -3.956] | no_clear_change |
| graph | baseline | 25 | 13.387 | 334.686 | 3.067 | baseline | n/a | measured |
| graph | o2 | 26 | 13.292 | 345.594 | 1.752 | 2.399 | [0.966, 4.258] | no_clear_change |
| graph | lto | 24 | 13.857 | 332.568 | 3.397 | -2.881 | [-4.987, -1.992] | no_clear_change |
| graph | pgo | 25 | 13.141 | 328.529 | 1.223 | 1.677 | [0.386, 1.992] | no_clear_change |
| graph | pgo-lto | 26 | 13.237 | 344.175 | 1.295 | 0.621 | [-0.111, 1.550] | no_clear_change |
| logs | baseline | 25 | 14.974 | 374.356 | 10.318 | baseline | n/a | measured (noisy) |
| logs | o2 | 19 | 14.870 | 282.528 | 9.063 | 1.374 | [-0.909, 8.366] | inconclusive (noisy) |
| logs | lto | 25 | 14.140 | 353.490 | 8.730 | 5.056 | [2.201, 9.685] | inconclusive (noisy) |
| logs | pgo | 27 | 13.457 | 363.345 | 6.006 | 9.534 | [7.979, 23.363] | inconclusive (noisy, drift) |
| logs | pgo-lto | 24 | 14.276 | 342.627 | 7.704 | 4.782 | [4.162, 5.145] | inconclusive (noisy) |
| image | baseline | 173 | 1.839 | 318.136 | 2.658 | baseline | n/a | measured |
| image | o2 | 149 | 2.178 | 324.576 | 2.874 | -18.908 | [-20.442, -14.100] | regression |
| image | lto | 174 | 1.929 | 335.572 | 2.781 | -4.953 | [-5.723, -4.766] | no_clear_change |
| image | pgo | 173 | 1.848 | 319.660 | 1.617 | -0.483 | [-0.835, -0.149] | no_clear_change |
| image | pgo-lto | 147 | 2.046 | 300.784 | 2.223 | -10.907 | [-11.347, -8.407] | regression |
| kv | baseline | 31 | 11.305 | 350.441 | 8.801 | baseline | n/a | measured (noisy) |
| kv | o2 | 30 | 11.213 | 336.403 | 2.862 | -0.674 | [-2.475, 0.698] | inconclusive (noisy) |
| kv | lto | 31 | 11.215 | 347.652 | 3.404 | 0.534 | [-1.462, 1.982] | no_clear_change |
| kv | pgo | 30 | 11.204 | 336.126 | 11.809 | 0.451 | [-0.695, 0.781] | inconclusive (noisy, drift) |
| kv | pgo-lto | 30 | 11.429 | 342.885 | 8.735 | -0.416 | [-2.743, 0.395] | inconclusive (noisy, drift) |

## Calibration and inputs

Pilots are discarded from statistics; all pilot outputs must pass correctness. Measured samples are retained even when noisy or outside the target band.

| Workload | Input seed | Config | Pilots | Batches | Pilot median ms | Samples in target band |
|---|---:|---|---:|---:|---:|---:|
| array | 314159 | baseline | 6 | 15 | 363.539 | 44/44 |
| array | 314159 | o2 | 6 | 15 | 361.281 | 11/11 |
| array | 314159 | lto | 6 | 15 | 361.184 | 11/11 |
| array | 314159 | pgo | 6 | 15 | 360.852 | 11/11 |
| array | 314159 | pgo-lto | 6 | 15 | 359.005 | 11/11 |
| sorting | 314159 | baseline | 6 | 6 | 369.865 | 44/44 |
| sorting | 314159 | o2 | 6 | 6 | 330.892 | 11/11 |
| sorting | 314159 | lto | 6 | 6 | 325.934 | 11/11 |
| sorting | 314159 | pgo | 6 | 6 | 375.142 | 11/11 |
| sorting | 314159 | pgo-lto | 6 | 6 | 352.547 | 11/11 |
| hashmap | 314159 | baseline | 6 | 5 | 316.652 | 44/44 |
| hashmap | 314159 | o2 | 6 | 5 | 310.750 | 11/11 |
| hashmap | 314159 | lto | 6 | 5 | 316.219 | 11/11 |
| hashmap | 314159 | pgo | 6 | 6 | 371.240 | 10/11 |
| hashmap | 314159 | pgo-lto | 6 | 5 | 310.855 | 11/11 |
| matrix | 314159 | baseline | 6 | 42 | 357.248 | 44/44 |
| matrix | 314159 | o2 | 6 | 41 | 349.583 | 11/11 |
| matrix | 314159 | lto | 6 | 30 | 348.279 | 11/11 |
| matrix | 314159 | pgo | 6 | 41 | 347.090 | 11/11 |
| matrix | 314159 | pgo-lto | 6 | 31 | 357.662 | 11/11 |
| strings | 314159 | baseline | 6 | 14 | 370.232 | 44/44 |
| strings | 314159 | o2 | 6 | 14 | 378.259 | 11/11 |
| strings | 314159 | lto | 6 | 12 | 314.148 | 11/11 |
| strings | 314159 | pgo | 6 | 14 | 357.181 | 11/11 |
| strings | 314159 | pgo-lto | 6 | 14 | 393.824 | 11/11 |
| records | 314159 | baseline | 6 | 46 | 345.491 | 44/44 |
| records | 314159 | o2 | 6 | 50 | 355.583 | 11/11 |
| records | 314159 | lto | 6 | 41 | 345.490 | 11/11 |
| records | 314159 | pgo | 6 | 46 | 338.053 | 11/11 |
| records | 314159 | pgo-lto | 6 | 45 | 347.431 | 11/11 |
| graph | 314159 | baseline | 6 | 25 | 339.316 | 44/44 |
| graph | 314159 | o2 | 6 | 26 | 344.786 | 11/11 |
| graph | 314159 | lto | 6 | 24 | 332.520 | 11/11 |
| graph | 314159 | pgo | 6 | 25 | 336.941 | 11/11 |
| graph | 314159 | pgo-lto | 6 | 26 | 347.135 | 11/11 |
| logs | 314159 | baseline | 6 | 25 | 370.929 | 43/44 |
| logs | 314159 | o2 | 6 | 19 | 291.764 | 11/11 |
| logs | 314159 | lto | 6 | 25 | 351.928 | 11/11 |
| logs | 314159 | pgo | 6 | 27 | 366.952 | 11/11 |
| logs | 314159 | pgo-lto | 6 | 24 | 339.189 | 11/11 |
| image | 314159 | baseline | 6 | 173 | 330.365 | 44/44 |
| image | 314159 | o2 | 6 | 149 | 323.929 | 11/11 |
| image | 314159 | lto | 6 | 174 | 326.587 | 11/11 |
| image | 314159 | pgo | 6 | 173 | 324.253 | 11/11 |
| image | 314159 | pgo-lto | 6 | 147 | 321.983 | 11/11 |
| kv | 314159 | baseline | 6 | 31 | 348.966 | 44/44 |
| kv | 314159 | o2 | 6 | 30 | 350.844 | 11/11 |
| kv | 314159 | lto | 6 | 31 | 352.266 | 11/11 |
| kv | 314159 | pgo | 6 | 30 | 337.348 | 11/11 |
| kv | 314159 | pgo-lto | 6 | 30 | 337.758 | 11/11 |

## Resource comparison

Peak RSS covers the whole process, including prepared input buffers. Setup is not part of compute time. Build time is one observation; PGO includes instrumented build, profile merge, and final build. Training time is reported separately.

| Workload | Config | Peak RSS MiB | Setup ms/sample | Build ms | PGO training ms | Binary KiB |
|---|---|---:|---:|---:|---:|---:|
| array | baseline | 125.508 | 177.050 | 943.733 | n/a | 27.281 |
| array | o2 | 125.508 | 176.489 | 927.629 | n/a | 27.281 |
| array | lto | 125.508 | 176.528 | 1092.888 | n/a | 30.523 |
| array | pgo | 125.508 | 176.402 | 1965.501 | 31.263 | 28.953 |
| array | pgo-lto | 125.508 | 176.487 | 2368.227 | 29.160 | 28.391 |
| sorting | baseline | 11.023 | 6.796 | 1043.838 | n/a | 31.547 |
| sorting | o2 | 11.023 | 6.722 | 1020.635 | n/a | 31.562 |
| sorting | lto | 11.023 | 6.793 | 1206.003 | n/a | 30.664 |
| sorting | pgo | 11.023 | 6.872 | 2197.586 | 22.610 | 37.898 |
| sorting | pgo-lto | 11.023 | 6.861 | 2565.870 | 21.722 | 29.070 |
| hashmap | baseline | 23.195 | 44.978 | 1123.033 | n/a | 30.867 |
| hashmap | o2 | 23.195 | 44.722 | 1114.089 | n/a | 27.719 |
| hashmap | lto | 23.195 | 45.316 | 1270.911 | n/a | 30.414 |
| hashmap | pgo | 23.195 | 57.132 | 2247.100 | 27.571 | 29.047 |
| hashmap | pgo-lto | 23.195 | 45.395 | 2713.746 | 26.837 | 28.039 |
| matrix | baseline | 8.418 | 3.934 | 1014.679 | n/a | 30.938 |
| matrix | o2 | 8.379 | 3.916 | 983.758 | n/a | 26.938 |
| matrix | lto | 8.410 | 3.456 | 1154.060 | n/a | 30.414 |
| matrix | pgo | 8.504 | 3.898 | 2076.036 | 14.298 | 28.906 |
| matrix | pgo-lto | 8.426 | 3.490 | 2423.194 | 14.298 | 28.211 |
| strings | baseline | 34.008 | 64.392 | 933.919 | n/a | 27.742 |
| strings | o2 | 34.008 | 65.303 | 1024.034 | n/a | 27.742 |
| strings | lto | 34.008 | 60.699 | 1095.748 | n/a | 26.891 |
| strings | pgo | 34.008 | 64.523 | 1949.495 | 19.638 | 29.375 |
| strings | pgo-lto | 34.008 | 63.674 | 2308.211 | 19.954 | 29.031 |
| records | baseline | 8.410 | 18.445 | 2034.377 | n/a | 39.039 |
| records | o2 | 8.418 | 18.759 | 1971.649 | n/a | 35.055 |
| records | lto | 8.410 | 18.671 | 2249.431 | n/a | 38.438 |
| records | pgo | 8.418 | 18.889 | 4142.577 | 34.164 | 40.922 |
| records | pgo-lto | 8.500 | 18.654 | 4684.584 | 33.337 | 40.336 |
| graph | baseline | 8.396 | 0.946 | 2295.993 | n/a | 39.305 |
| graph | o2 | 8.410 | 0.951 | 2243.428 | n/a | 35.328 |
| graph | lto | 8.410 | 0.933 | 2501.045 | n/a | 38.344 |
| graph | pgo | 8.504 | 0.945 | 5018.024 | 19.165 | 40.953 |
| graph | pgo-lto | 8.410 | 0.961 | 5304.432 | 17.032 | 39.969 |
| logs | baseline | 9.625 | 43.501 | 1996.823 | n/a | 43.148 |
| logs | o2 | 9.625 | 42.133 | 1964.830 | n/a | 39.148 |
| logs | lto | 9.625 | 41.882 | 2193.884 | n/a | 42.594 |
| logs | pgo | 9.625 | 42.645 | 4088.602 | 67.181 | 49.281 |
| logs | pgo-lto | 9.625 | 43.077 | 4939.327 | 70.714 | 44.422 |
| image | baseline | 8.426 | 0.461 | 2035.522 | n/a | 35.086 |
| image | o2 | 8.426 | 0.532 | 1889.507 | n/a | 35.086 |
| image | lto | 8.410 | 0.455 | 2146.722 | n/a | 34.422 |
| image | pgo | 8.379 | 0.459 | 3923.492 | 12.379 | 36.945 |
| image | pgo-lto | 8.379 | 0.465 | 4657.286 | 10.024 | 36.422 |
| kv | baseline | 14.277 | 16.663 | 2394.309 | n/a | 42.109 |
| kv | o2 | 14.277 | 15.930 | 2418.249 | n/a | 42.289 |
| kv | lto | 14.277 | 16.181 | 2797.328 | n/a | 39.180 |
| kv | pgo | 14.281 | 15.658 | 5044.347 | 39.688 | 48.320 |
| kv | pgo-lto | 14.277 | 18.040 | 5636.197 | 39.414 | 46.141 |

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
Environment classification: `wsl2`; session: `8ebc2d20d2d44e1aab1f49b496c4e39e`. Session IDs alone do not establish independent host conditions.
Measurement environment readiness is assessed separately by `aion quality`; compile/affinity validation alone is insufficient.
Requested affinity: `[0]`; verified pinned samples: 880/880. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Recorded verification methods: `['actual executable sched_getaffinity before/after compute']`. Verification is a snapshot, not exclusive CPU ownership.
Different CPU endpoints observed: 0/880; equal endpoints do not prove no intermediate migration.
Noisy configuration summaries: 17/50; drifting: 1/50.
Load average at start/end: `[1.09130859375, 1.0732421875, 1.01171875]` / `[1.13671875, 1.0751953125, 1.01318359375]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

## Gate audit

| Workload | Candidate | Failed gates |
|---|---|---|
| array | o2 | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| array | lto | improvement_floor_and_uncertainty |
| array | pgo | improvement_floor_and_uncertainty |
| array | pgo-lto | variability, improvement_floor_and_uncertainty |
| sorting | o2 | variability, improvement_floor_and_uncertainty |
| sorting | lto | none |
| sorting | pgo | variability, improvement_floor_and_uncertainty |
| sorting | pgo-lto | variability, improvement_floor_and_uncertainty |
| hashmap | o2 | improvement_floor_and_uncertainty |
| hashmap | lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty |
| hashmap | pgo | variability, improvement_floor_and_uncertainty |
| hashmap | pgo-lto | improvement_floor_and_uncertainty |
| matrix | o2 | improvement_floor_and_uncertainty |
| matrix | lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| matrix | pgo | improvement_floor_and_uncertainty |
| matrix | pgo-lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| strings | o2 | variability, improvement_floor_and_uncertainty |
| strings | lto | variability, improvement_floor_and_uncertainty |
| strings | pgo | variability, improvement_floor_and_uncertainty |
| strings | pgo-lto | variability, improvement_floor_and_uncertainty |
| records | o2 | none |
| records | lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| records | pgo | improvement_floor_and_uncertainty |
| records | pgo-lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| graph | o2 | improvement_floor_and_uncertainty |
| graph | lto | improvement_floor_and_uncertainty |
| graph | pgo | improvement_floor_and_uncertainty |
| graph | pgo-lto | improvement_floor_and_uncertainty |
| logs | o2 | variability, improvement_floor_and_uncertainty |
| logs | lto | variability, improvement_floor_and_uncertainty |
| logs | pgo | variability, drift, improvement_floor_and_uncertainty |
| logs | pgo-lto | variability, improvement_floor_and_uncertainty |
| image | o2 | acceptable_regression_bound, improvement_floor_and_uncertainty |
| image | lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| image | pgo | improvement_floor_and_uncertainty |
| image | pgo-lto | acceptable_regression_bound, improvement_floor_and_uncertainty |
| kv | o2 | variability, improvement_floor_and_uncertainty |
| kv | lto | improvement_floor_and_uncertainty |
| kv | pgo | variability, drift, improvement_floor_and_uncertainty |
| kv | pgo-lto | variability, drift, improvement_floor_and_uncertainty |
