# AION performance comparison

Run: `20261030T123345-9ecf069f39` (benchmark)
Status: **completed**

Compiler: Ubuntu clang version 18.1.3 (1ubuntu1) — x86_64-pc-linux-gnu
Machine: Linux x86_64 — Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz
Iterations: 11; warmups: 2; schedule seed: 1729

Positive time change means faster than -O3. Memory is median peak RSS per run.

| Workload | Configuration | Median ms | CV % | Peak RSS MiB | Compile ms | Binary KiB | Time change | Outcome |
|---|---|---:|---:|---:|---:|---:|---:|---|
| array | baseline | 63.750 | 5.822 | 8.188 | 1018.861 | 16.891 | baseline | measured (noisy/short) |
| array | o2 | 63.931 | 7.644 | 8.094 | 958.496 | 16.891 | -0.284% | inconclusive (noisy/short) |
| sorting | baseline | 79.790 | 10.650 | 8.094 | 1296.968 | 17.352 | baseline | measured (noisy/short) |
| sorting | o2 | 82.890 | 9.706 | 8.188 | 1087.217 | 17.219 | -3.885% | inconclusive (noisy/short) |
| hashmap | baseline | 73.232 | 10.159 | 8.188 | 809.495 | 18.094 | baseline | measured (noisy/short) |
| hashmap | o2 | 73.547 | 7.784 | 8.109 | 806.500 | 18.359 | -0.430% | inconclusive (noisy/short) |
| matrix | baseline | 13.305 | 3.345 | 8.094 | 900.173 | 16.891 | baseline | measured (noisy/short) |
| matrix | o2 | 13.274 | 2.196 | 8.188 | 778.758 | 16.891 | 0.231% | inconclusive (noisy/short) |
| strings | baseline | 58.776 | 1.632 | 8.109 | 705.718 | 17.016 | baseline | measured |
| strings | o2 | 59.034 | 0.944 | 8.188 | 691.744 | 17.016 | -0.439% | no_clear_change |

## Configurations

- `baseline`: `-O3`
- `o2`: `-O2`

## Measurement limits

- Wall time includes process startup and deterministic input generation.
- Peak RSS is per-process maximum resident memory; null means unsupported.
- Classification is a conservative screening heuristic, not statistical significance.
- Correctness covers supplied deterministic cases, not arbitrary C++ programs.
- Compile time is a single observation; it is not a statistically stable comparison.
- An improvement applies only to these workloads and this recorded environment.
- Preset promotion requires fresh builds and measurements with a different schedule seed.
- This runner executes trusted local code; resource limits are not a security sandbox.
