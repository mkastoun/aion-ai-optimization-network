# AION Phase 2 performance comparison

Run: `20261030T133332-5c960dc216` (optimize); status: **completed**

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1) — x86_64-pc-linux-gnu
Machine: Linux — Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz
Measured pairs per candidate: 11; warmups: 2; schedule/bootstrap seed: 42217.

Target compute time: 250–500 ms per sample. Input generation, allocation of input buffers, and reset/copy work are excluded from compute time.

A unit is one execution of the workload's fixed input/rounds. Each configuration calibrates its batch count separately; comparisons normalize by batches and use its adjacent -O3 partner. Insertion/rehash costs in hash maps and checksum scans remain timed.

Positive paired improvement means faster. Both the reported gain and interval describe the median of paired effects. The raw JSON also retains the ratio of marginal medians used by the unchanged screening floor. Intervals use a Bonferroni adjustment across 20 declared comparisons (nominal family confidence 95%).

| Workload | Config | Batches | Unit ms | Sample ms | CV % | Paired gain % | Adjusted interval % | Outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| array | baseline | 14 | 25.860 | 362.041 | 9.758 | baseline | n/a | measured (noisy) |
| array | o2 | 14 | 26.021 | 364.290 | 10.946 | -0.181 | [-7.323, 1.790] | inconclusive (noisy) |
| array | lto | 14 | 26.189 | 366.646 | 10.167 | -2.397 | [-6.221, -1.043] | inconclusive (noisy) |
| array | pgo | 15 | 25.743 | 386.148 | 9.823 | 1.733 | [-1.793, 8.637] | inconclusive (noisy, drift) |
| array | pgo-lto | 14 | 25.731 | 360.237 | 5.321 | 1.079 | [-0.858, 5.901] | inconclusive (noisy) |
| sorting | baseline | 6 | 60.063 | 360.378 | 15.800 | baseline | n/a | measured (noisy, drift) |
| sorting | o2 | 5 | 66.326 | 331.632 | 12.857 | -11.123 | [-12.560, -6.955] | inconclusive (noisy, drift) |
| sorting | lto | 6 | 58.821 | 352.924 | 13.045 | 1.173 | [-4.875, 7.456] | inconclusive (noisy, drift) |
| sorting | pgo | 5 | 66.152 | 330.761 | 14.062 | -10.620 | [-12.093, -1.997] | inconclusive (noisy, drift) |
| sorting | pgo-lto | 6 | 64.536 | 387.214 | 21.165 | -7.446 | [-11.511, -4.264] | inconclusive (noisy, drift) |
| hashmap | baseline | 5 | 70.620 | 353.102 | 8.501 | baseline | n/a | measured (noisy) |
| hashmap | o2 | 5 | 70.401 | 352.007 | 8.956 | 1.105 | [-2.365, 2.939] | inconclusive (noisy, drift) |
| hashmap | lto | 4 | 72.370 | 289.478 | 12.781 | -3.968 | [-7.976, 6.070] | inconclusive (noisy) |
| hashmap | pgo | 5 | 68.911 | 344.554 | 14.673 | 1.512 | [-3.894, 2.945] | inconclusive (noisy) |
| hashmap | pgo-lto | 5 | 70.181 | 350.903 | 11.585 | 3.840 | [1.798, 6.258] | inconclusive (noisy) |
| matrix | baseline | 39 | 9.279 | 361.896 | 9.334 | baseline | n/a | measured (noisy) |
| matrix | o2 | 40 | 9.064 | 362.565 | 28.182 | 1.301 | [-1.891, 4.362] | inconclusive (noisy) |
| matrix | lto | 39 | 9.273 | 361.633 | 9.342 | 0.233 | [-0.474, 6.076] | inconclusive (noisy) |
| matrix | pgo | 34 | 10.800 | 367.206 | 7.213 | -14.765 | [-17.174, -12.666] | inconclusive (noisy) |
| matrix | pgo-lto | 24 | 14.274 | 342.572 | 5.751 | -56.513 | [-60.812, -51.835] | inconclusive (noisy) |
| strings | baseline | 13 | 26.985 | 350.804 | 3.267 | baseline | n/a | measured |
| strings | o2 | 13 | 26.808 | 348.505 | 9.775 | 0.500 | [-0.829, 1.346] | inconclusive (noisy) |
| strings | lto | 13 | 27.729 | 360.477 | 3.525 | -2.793 | [-7.471, -1.285] | no_clear_change |
| strings | pgo | 13 | 27.019 | 351.249 | 1.582 | -0.228 | [-2.361, 1.040] | no_clear_change |
| strings | pgo-lto | 13 | 27.428 | 356.561 | 3.575 | -1.936 | [-2.963, 0.144] | no_clear_change |

## Calibration and inputs

Pilots are discarded from statistics; all pilot outputs must pass correctness. Measured samples are retained even when noisy or outside the target band.

| Workload | Input seed | Config | Pilots | Batches | Pilot median ms | Samples in target band |
|---|---:|---|---:|---:|---:|---:|
| array | 42 | baseline | 6 | 14 | 386.389 | 44/44 |
| array | 42 | o2 | 6 | 14 | 373.604 | 11/11 |
| array | 42 | lto | 6 | 14 | 368.188 | 11/11 |
| array | 42 | pgo | 6 | 15 | 399.465 | 11/11 |
| array | 42 | pgo-lto | 6 | 14 | 370.312 | 11/11 |
| sorting | 42 | baseline | 6 | 6 | 354.152 | 42/44 |
| sorting | 42 | o2 | 6 | 5 | 336.795 | 11/11 |
| sorting | 42 | lto | 6 | 6 | 390.596 | 11/11 |
| sorting | 42 | pgo | 6 | 5 | 413.871 | 11/11 |
| sorting | 42 | pgo-lto | 6 | 6 | 381.856 | 10/11 |
| hashmap | 42 | baseline | 6 | 5 | 358.911 | 44/44 |
| hashmap | 42 | o2 | 6 | 5 | 348.261 | 11/11 |
| hashmap | 42 | lto | 6 | 4 | 296.328 | 11/11 |
| hashmap | 42 | pgo | 6 | 5 | 344.670 | 11/11 |
| hashmap | 42 | pgo-lto | 6 | 5 | 340.590 | 11/11 |
| matrix | 42 | baseline | 6 | 39 | 364.561 | 43/44 |
| matrix | 42 | o2 | 6 | 40 | 368.416 | 10/11 |
| matrix | 42 | lto | 6 | 39 | 368.256 | 11/11 |
| matrix | 42 | pgo | 6 | 34 | 365.643 | 11/11 |
| matrix | 42 | pgo-lto | 6 | 24 | 343.990 | 11/11 |
| strings | 42 | baseline | 6 | 13 | 355.823 | 44/44 |
| strings | 42 | o2 | 6 | 13 | 346.763 | 11/11 |
| strings | 42 | lto | 6 | 13 | 363.864 | 11/11 |
| strings | 42 | pgo | 6 | 13 | 357.394 | 11/11 |
| strings | 42 | pgo-lto | 6 | 13 | 360.949 | 11/11 |

## Resource comparison

Peak RSS covers the whole process, including prepared input buffers. Setup is not part of compute time. Build time is one observation; PGO includes instrumented build, profile merge, and final build. Training time is reported separately.

| Workload | Config | Peak RSS MiB | Setup ms/sample | Build ms | PGO training ms | Binary KiB |
|---|---|---:|---:|---:|---:|---:|
| array | baseline | 125.258 | 179.415 | 752.617 | n/a | 22.250 |
| array | o2 | 125.258 | 181.162 | 958.635 | n/a | 22.250 |
| array | lto | 125.258 | 183.453 | 1370.997 | n/a | 21.500 |
| array | pgo | 125.258 | 187.977 | 1904.850 | 27.855 | 23.281 |
| array | pgo-lto | 125.258 | 178.017 | 2330.929 | 29.639 | 23.000 |
| sorting | baseline | 10.773 | 7.445 | 1087.724 | n/a | 22.523 |
| sorting | o2 | 10.773 | 7.007 | 1092.931 | n/a | 22.531 |
| sorting | lto | 10.773 | 7.315 | 1234.977 | n/a | 21.641 |
| sorting | pgo | 10.777 | 7.040 | 2239.449 | 23.342 | 24.227 |
| sorting | pgo-lto | 10.773 | 7.466 | 2686.150 | 31.197 | 23.680 |
| hashmap | baseline | 22.996 | 49.270 | 1062.854 | n/a | 21.844 |
| hashmap | o2 | 22.996 | 49.328 | 1083.950 | n/a | 22.695 |
| hashmap | lto | 22.996 | 36.579 | 1266.788 | n/a | 21.391 |
| hashmap | pgo | 22.996 | 50.185 | 2332.730 | 28.826 | 23.367 |
| hashmap | pgo-lto | 22.996 | 50.024 | 2786.850 | 28.430 | 22.648 |
| matrix | baseline | 8.150 | 4.269 | 1215.729 | n/a | 21.914 |
| matrix | o2 | 8.191 | 4.246 | 1006.137 | n/a | 21.914 |
| matrix | lto | 8.098 | 4.243 | 1164.563 | n/a | 21.391 |
| matrix | pgo | 8.188 | 4.056 | 2191.432 | 17.577 | 23.234 |
| matrix | pgo-lto | 8.191 | 3.577 | 2540.340 | 14.440 | 22.820 |
| strings | baseline | 33.758 | 65.652 | 987.670 | n/a | 22.789 |
| strings | o2 | 33.758 | 65.371 | 928.696 | n/a | 22.789 |
| strings | lto | 33.758 | 65.944 | 1081.151 | n/a | 21.938 |
| strings | pgo | 33.758 | 65.966 | 1994.539 | 20.135 | 27.922 |
| strings | pgo-lto | 33.758 | 65.864 | 2239.806 | 20.009 | 23.703 |

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
