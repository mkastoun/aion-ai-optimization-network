# AION Phase 2 performance report

**Recorded outcome:** no preset qualified for promotion. Correctness passed in both runs; host variability still limits many comparisons. All measurements, including out-of-band samples and regressions, are retained. See [validation](phase2-validation.md) and [methodology](reliable-benchmarking.md) for the audit and interpretation limits.

Discovery: `20261030T133332-5c960dc216`; confirmation: `20261030T134127-a9b702d915`.

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1). Machine: Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz.
Scheduling/bootstrap seeds: 42217 and 42218.

Inputs differ between runs; each configuration is compared only against its matched -O3 measurement within that run. A workload-level repeatable improvement does not by itself qualify a configuration for a suite-wide preset.

Each candidate has 11 measured pairs per workload and 10000 circular moving-block bootstrap resamples. Intervals use nominal 95% family confidence across 20 declared comparisons (99.75% per interval). Coverage is approximate, especially for short or nonstationary series.

A confidence interval away from zero does not override the unchanged CV, drift, duration, 2%/combined-MAD improvement floor, or 5% regression checks. All measured samples are retained. PGO profiles remain program-specific research evidence, not reusable flag-only presets.

| Workload | Candidate | Discovery paired gain % | Confirmation paired gain % | Discovery interval % | Confirmation interval % | Outcome |
|---|---|---:|---:|---|---|---|
| array | o2 | -0.181 | -0.350 | [-7.323, 1.790] | [-3.024, 1.292] | inconclusive / no_clear_change |
| array | lto | -2.397 | -0.907 | [-6.221, -1.043] | [-4.443, 1.299] | inconclusive / inconclusive |
| array | pgo | 1.733 | -1.304 | [-1.793, 8.637] | [-4.207, 1.559] | inconclusive / inconclusive |
| array | pgo-lto | 1.079 | 0.767 | [-0.858, 5.901] | [-4.664, 1.347] | inconclusive / inconclusive |
| sorting | o2 | -11.123 | -10.669 | [-12.560, -6.955] | [-11.610, -10.130] | inconclusive / regression |
| sorting | lto | 1.173 | -0.289 | [-4.875, 7.456] | [-0.852, 2.711] | inconclusive / no_clear_change |
| sorting | pgo | -10.620 | -10.782 | [-12.093, -1.997] | [-11.269, -9.305] | inconclusive / regression |
| sorting | pgo-lto | -7.446 | -7.948 | [-11.511, -4.264] | [-9.970, -5.939] | inconclusive / regression |
| hashmap | o2 | 1.105 | 0.496 | [-2.365, 2.939] | [-5.069, 2.182] | inconclusive / inconclusive |
| hashmap | lto | -3.968 | -0.326 | [-7.976, 6.070] | [-1.405, 6.052] | inconclusive / inconclusive |
| hashmap | pgo | 1.512 | 1.234 | [-3.894, 2.945] | [0.294, 2.830] | inconclusive / inconclusive |
| hashmap | pgo-lto | 3.840 | -1.832 | [1.798, 6.258] | [-17.708, 3.862] | inconclusive / inconclusive |
| matrix | o2 | 1.301 | 0.765 | [-1.891, 4.362] | [-1.132, 2.384] | inconclusive / inconclusive |
| matrix | lto | 0.233 | -1.063 | [-0.474, 6.076] | [-2.960, 0.698] | inconclusive / inconclusive |
| matrix | pgo | -14.765 | -17.176 | [-17.174, -12.666] | [-22.461, -13.655] | inconclusive / inconclusive |
| matrix | pgo-lto | -56.513 | -54.816 | [-60.812, -51.835] | [-55.374, -51.984] | inconclusive / inconclusive |
| strings | o2 | 0.500 | -0.233 | [-0.829, 1.346] | [-9.785, 1.116] | inconclusive / inconclusive |
| strings | lto | -2.793 | -2.037 | [-7.471, -1.285] | [-7.416, 1.570] | no_clear_change / inconclusive |
| strings | pgo | -0.228 | -0.372 | [-2.361, 1.040] | [-8.239, 3.201] | no_clear_change / inconclusive |
| strings | pgo-lto | -1.936 | -3.492 | [-2.963, 0.144] | [-5.878, 2.526] | no_clear_change / inconclusive |

## Duration and correctness audit

| Run | Verified configurations | Median compute sample range ms | Measured samples inside 250–500 ms |
|---|---:|---:|---:|
| optimize | 25/25 | 289.5–387.2 | 435/440 |
| independent_confirmation | 25/25 | 246.2–393.4 | 405/440 |

Full raw samples, calibration pilots, physical durations, paired intervals, drift, resources, correctness checks, and PGO provenance remain in each experiment's JSON and detailed Markdown report.
