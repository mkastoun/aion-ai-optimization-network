# AION performance comparison

Run: `20261030T123456-4e1256c7c0` (optimize)
Status: **completed**

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1) — x86_64-pc-linux-gnu
Machine: Linux x86_64 — Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz
Iterations: 11; warmups: 2; schedule seed: 1730

Positive time change means faster than -O3. Memory is median peak RSS per run.

| Workload | Configuration | Median ms | CV % | Peak RSS MiB | Compile ms | Binary KiB | Time change | Outcome |
|---|---|---:|---:|---:|---:|---:|---:|---|
| array | baseline | 49.288 | 3.190 | 8.188 | 733.213 | 16.891 | baseline | measured |
| array | o2 | 48.968 | 3.232 | 8.102 | 861.520 | 16.891 | 0.649% | no_clear_change |
| array | size | 65.726 | 2.289 | 8.188 | 872.215 | 17.883 | -33.351% | regression |
| array | unroll | 48.782 | 2.913 | 8.184 | 739.169 | 16.891 | 1.025% | no_clear_change |
| array | no-vectorize | 57.284 | 3.902 | 8.102 | 707.739 | 16.891 | -16.223% | regression |
| sorting | baseline | 64.231 | 1.979 | 8.184 | 826.136 | 17.352 | baseline | measured |
| sorting | o2 | 65.395 | 2.137 | 8.094 | 866.609 | 17.219 | -1.812% | no_clear_change |
| sorting | size | 64.464 | 2.100 | 8.094 | 779.714 | 18.898 | -0.362% | no_clear_change |
| sorting | unroll | 63.125 | 1.491 | 8.188 | 835.032 | 17.352 | 1.723% | no_clear_change |
| sorting | no-vectorize | 64.038 | 1.841 | 8.188 | 789.560 | 17.352 | 0.301% | no_clear_change |
| hashmap | baseline | 71.173 | 11.780 | 8.102 | 804.364 | 18.094 | baseline | measured (noisy/short) |
| hashmap | o2 | 70.812 | 5.826 | 8.109 | 788.917 | 18.359 | 0.507% | inconclusive (noisy/short) |
| hashmap | size | 87.919 | 5.404 | 8.109 | 800.935 | 20.789 | -23.527% | inconclusive (noisy/short) |
| hashmap | unroll | 71.129 | 11.495 | 8.109 | 794.844 | 18.094 | 0.062% | inconclusive (noisy/short) |
| hashmap | no-vectorize | 69.660 | 6.201 | 8.109 | 817.872 | 18.094 | 2.127% | inconclusive (noisy/short) |
| matrix | baseline | 12.646 | 2.613 | 8.184 | 744.712 | 16.891 | baseline | measured (noisy/short) |
| matrix | o2 | 12.523 | 2.977 | 8.188 | 728.261 | 16.891 | 0.972% | inconclusive (noisy/short) |
| matrix | size | 24.362 | 2.781 | 8.102 | 750.788 | 18.000 | -92.645% | inconclusive |
| matrix | unroll | 12.692 | 2.870 | 8.188 | 765.094 | 16.891 | -0.362% | inconclusive (noisy/short) |
| matrix | no-vectorize | 23.179 | 1.983 | 8.102 | 872.648 | 16.891 | -83.286% | inconclusive |
| strings | baseline | 53.995 | 3.075 | 8.188 | 698.092 | 17.016 | baseline | measured |
| strings | o2 | 52.634 | 2.084 | 8.109 | 645.786 | 17.016 | 2.521% | no_clear_change |
| strings | size | 63.751 | 3.699 | 8.102 | 617.591 | 17.672 | -18.070% | regression |
| strings | unroll | 53.766 | 2.695 | 8.094 | 666.243 | 17.016 | 0.423% | no_clear_change |
| strings | no-vectorize | 56.859 | 2.370 | 8.109 | 645.623 | 17.016 | -5.305% | regression |

## Configurations

- `baseline`: `-O3`
- `o2`: `-O2`
- `size`: `-Os`
- `unroll`: `-O3 -funroll-loops`
- `no-vectorize`: `-O3 -fno-vectorize -fno-slp-vectorize`

## Measurement limits

- Wall time includes process startup and deterministic input generation.
- Peak RSS is per-process maximum resident memory; null means unsupported.
- Classification is a conservative screening heuristic, not statistical significance.
- Correctness covers supplied deterministic cases, not arbitrary C++ programs.
- Compile time is a single observation; it is not a statistically stable comparison.
- An improvement applies only to these workloads and this recorded environment.
- Preset promotion requires fresh builds and measurements with a different schedule seed.
- This runner executes trusted local code; resource limits are not a security sandbox.
