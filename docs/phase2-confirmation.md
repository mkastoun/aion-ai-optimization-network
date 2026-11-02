# AION Phase 2 performance comparison

Run: `20261030T134127-a9b702d915` (independent_confirmation); status: **completed**

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1) — x86_64-pc-linux-gnu
Machine: Linux — Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz
Measured pairs per candidate: 11; warmups: 2; schedule/bootstrap seed: 42218.

Target compute time: 250–500 ms per sample. Input generation, allocation of input buffers, and reset/copy work are excluded from compute time.

A unit is one execution of the workload's fixed input/rounds. Each configuration calibrates its batch count separately; comparisons normalize by batches and use its adjacent -O3 partner. Insertion/rehash costs in hash maps and checksum scans remain timed.

Positive paired improvement means faster. Both the reported gain and interval describe the median of paired effects. The raw JSON also retains the ratio of marginal medians used by the unchanged screening floor. Intervals use a Bonferroni adjustment across 20 declared comparisons (nominal family confidence 95%).

| Workload | Config | Batches | Unit ms | Sample ms | CV % | Paired gain % | Adjusted interval % | Outcome |
|---|---|---:|---:|---:|---:|---:|---|---|
| array | baseline | 14 | 25.648 | 359.066 | 9.722 | baseline | n/a | measured (noisy) |
| array | o2 | 10 | 26.022 | 260.222 | 2.624 | -0.350 | [-3.024, 1.292] | no_clear_change |
| array | lto | 15 | 26.228 | 393.417 | 4.810 | -0.907 | [-4.443, 1.299] | inconclusive (noisy) |
| array | pgo | 14 | 25.817 | 361.431 | 6.462 | -1.304 | [-4.207, 1.559] | inconclusive (noisy) |
| array | pgo-lto | 14 | 25.700 | 359.805 | 22.515 | 0.767 | [-4.664, 1.347] | inconclusive (noisy) |
| sorting | baseline | 6 | 59.033 | 354.197 | 1.921 | baseline | n/a | measured |
| sorting | o2 | 5 | 64.688 | 323.438 | 1.870 | -10.669 | [-11.610, -10.130] | regression |
| sorting | lto | 6 | 58.639 | 351.836 | 3.640 | -0.289 | [-0.852, 2.711] | no_clear_change |
| sorting | pgo | 6 | 64.884 | 389.304 | 1.391 | -10.782 | [-11.269, -9.305] | regression |
| sorting | pgo-lto | 6 | 64.198 | 385.191 | 1.219 | -7.948 | [-9.970, -5.939] | regression |
| hashmap | baseline | 5 | 69.482 | 347.411 | 12.298 | baseline | n/a | measured (noisy) |
| hashmap | o2 | 5 | 70.858 | 354.289 | 5.352 | 0.496 | [-5.069, 2.182] | inconclusive (noisy, drift) |
| hashmap | lto | 5 | 69.466 | 347.331 | 15.157 | -0.326 | [-1.405, 6.052] | inconclusive (noisy, drift) |
| hashmap | pgo | 5 | 69.424 | 347.121 | 12.135 | 1.234 | [0.294, 2.830] | inconclusive (noisy) |
| hashmap | pgo-lto | 5 | 70.624 | 353.118 | 13.970 | -1.832 | [-17.708, 3.862] | inconclusive (noisy) |
| matrix | baseline | 27 | 9.117 | 246.154 | 2.620 | baseline | n/a | measured (short) |
| matrix | o2 | 39 | 9.150 | 356.853 | 9.489 | 0.765 | [-1.132, 2.384] | inconclusive (noisy, short) |
| matrix | lto | 39 | 9.218 | 359.514 | 1.608 | -1.063 | [-2.960, 0.698] | inconclusive (short) |
| matrix | pgo | 33 | 10.813 | 356.818 | 6.140 | -17.176 | [-22.461, -13.655] | inconclusive (noisy, short) |
| matrix | pgo-lto | 26 | 14.096 | 366.493 | 2.181 | -54.816 | [-55.374, -51.984] | inconclusive (short) |
| strings | baseline | 14 | 27.008 | 378.114 | 9.075 | baseline | n/a | measured (noisy) |
| strings | o2 | 14 | 26.924 | 376.938 | 9.241 | -0.233 | [-9.785, 1.116] | inconclusive (noisy) |
| strings | lto | 13 | 27.952 | 363.381 | 6.113 | -2.037 | [-7.416, 1.570] | inconclusive (noisy) |
| strings | pgo | 13 | 26.774 | 348.061 | 10.413 | -0.372 | [-8.239, 3.201] | inconclusive (noisy, drift) |
| strings | pgo-lto | 13 | 27.713 | 360.274 | 2.145 | -3.492 | [-5.878, 2.526] | inconclusive (noisy) |

## Calibration and inputs

Pilots are discarded from statistics; all pilot outputs must pass correctness. Measured samples are retained even when noisy or outside the target band.

| Workload | Input seed | Config | Pilots | Batches | Pilot median ms | Samples in target band |
|---|---:|---|---:|---:|---:|---:|
| array | 314159 | baseline | 6 | 14 | 364.081 | 43/44 |
| array | 314159 | o2 | 6 | 10 | 271.505 | 11/11 |
| array | 314159 | lto | 6 | 15 | 391.147 | 11/11 |
| array | 314159 | pgo | 6 | 14 | 357.612 | 11/11 |
| array | 314159 | pgo-lto | 6 | 14 | 362.763 | 10/11 |
| sorting | 314159 | baseline | 6 | 6 | 352.159 | 44/44 |
| sorting | 314159 | o2 | 6 | 5 | 397.405 | 11/11 |
| sorting | 314159 | lto | 6 | 6 | 346.726 | 11/11 |
| sorting | 314159 | pgo | 6 | 6 | 373.488 | 11/11 |
| sorting | 314159 | pgo-lto | 6 | 6 | 370.272 | 11/11 |
| hashmap | 314159 | baseline | 6 | 5 | 347.382 | 43/44 |
| hashmap | 314159 | o2 | 6 | 5 | 342.650 | 11/11 |
| hashmap | 314159 | lto | 6 | 5 | 354.408 | 11/11 |
| hashmap | 314159 | pgo | 6 | 5 | 337.192 | 11/11 |
| hashmap | 314159 | pgo-lto | 6 | 5 | 339.423 | 11/11 |
| matrix | 314159 | baseline | 9 | 27 | 261.593 | 13/44 |
| matrix | 314159 | o2 | 6 | 39 | 377.575 | 11/11 |
| matrix | 314159 | lto | 6 | 39 | 356.086 | 11/11 |
| matrix | 314159 | pgo | 6 | 33 | 359.885 | 11/11 |
| matrix | 314159 | pgo-lto | 6 | 26 | 364.227 | 11/11 |
| strings | 314159 | baseline | 6 | 14 | 374.529 | 43/44 |
| strings | 314159 | o2 | 6 | 14 | 378.717 | 11/11 |
| strings | 314159 | lto | 6 | 13 | 354.808 | 11/11 |
| strings | 314159 | pgo | 6 | 13 | 354.965 | 11/11 |
| strings | 314159 | pgo-lto | 6 | 13 | 463.460 | 11/11 |

## Resource comparison

Peak RSS covers the whole process, including prepared input buffers. Setup is not part of compute time. Build time is one observation; PGO includes instrumented build, profile merge, and final build. Training time is reported separately.

| Workload | Config | Peak RSS MiB | Setup ms/sample | Build ms | PGO training ms | Binary KiB |
|---|---|---:|---:|---:|---:|---:|
| array | baseline | 125.258 | 179.174 | 959.379 | n/a | 22.250 |
| array | o2 | 125.258 | 153.200 | 943.172 | n/a | 22.250 |
| array | lto | 125.258 | 188.479 | 1094.498 | n/a | 21.500 |
| array | pgo | 125.258 | 179.784 | 1950.232 | 28.516 | 23.281 |
| array | pgo-lto | 125.258 | 180.584 | 2398.941 | 30.884 | 23.000 |
| sorting | baseline | 10.773 | 7.294 | 1070.833 | n/a | 22.523 |
| sorting | o2 | 10.773 | 6.796 | 1020.453 | n/a | 22.531 |
| sorting | lto | 10.773 | 7.364 | 1480.050 | n/a | 21.641 |
| sorting | pgo | 10.773 | 7.122 | 2186.485 | 22.831 | 24.227 |
| sorting | pgo-lto | 10.777 | 7.476 | 2558.044 | 23.916 | 23.680 |
| hashmap | baseline | 22.945 | 48.890 | 1118.705 | n/a | 21.844 |
| hashmap | o2 | 22.949 | 49.889 | 1103.685 | n/a | 22.695 |
| hashmap | lto | 22.945 | 48.775 | 1529.205 | n/a | 21.391 |
| hashmap | pgo | 22.945 | 49.413 | 2267.740 | 32.501 | 23.367 |
| hashmap | pgo-lto | 22.945 | 49.870 | 2707.383 | 28.032 | 22.648 |
| matrix | baseline | 8.105 | 3.608 | 1115.909 | n/a | 21.914 |
| matrix | o2 | 8.098 | 4.388 | 1005.862 | n/a | 21.914 |
| matrix | lto | 8.113 | 4.263 | 1284.725 | n/a | 21.391 |
| matrix | pgo | 8.191 | 4.026 | 2074.494 | 14.789 | 23.234 |
| matrix | pgo-lto | 8.105 | 3.630 | 2380.394 | 16.295 | 22.820 |
| strings | baseline | 33.758 | 67.464 | 972.358 | n/a | 22.789 |
| strings | o2 | 33.758 | 67.819 | 949.405 | n/a | 22.789 |
| strings | lto | 33.758 | 66.572 | 1072.705 | n/a | 21.938 |
| strings | pgo | 33.762 | 66.077 | 1944.661 | 20.244 | 27.922 |
| strings | pgo-lto | 33.758 | 65.807 | 2721.840 | 30.692 | 23.703 |

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
