# Phase 4 compiler-behavior investigation

The counters provide repeated diagnostic observations about the preserved Phase 3 binaries. They do not establish a compiler defect, a production speedup, or the cause of a timing regression. All measurements here are WSL2 guest-visible evidence, separate from primary compute timing.

## Provenance and scope

Two profiling records reconstruct the preserved Phase 3 discovery and confirmation configurations:

- [Profile of discovery](../.aion/phase4-profiling/results/20261031T022822-f21322d758.json), from timing run `20261030T234834-de3eb6de82`, input seed 42.
- [Profile of confirmation](../.aion/phase4-profiling/results/20261031T023042-13a2f1e4e9.json), from timing run `20261031T000202-01808fcd04`, held-out input seed 314159.

Each covers records, logs, and matrix under baseline O3, LTO, PGO, and PGO+LTO. All **24 rebuilt final binaries match their source timing binary hashes**, and recorded host/toolchain/placement identities match. All **72 counter executions** pass output/PID/affinity checks. All **648 event observations** are counted; enabled/running fractions are 1.0, so these observations are unmultiplexed and require no scaled estimates. There are also **24 separate sampled executions**, all available with no reported lost samples or buffer overrun. Each configuration passes six independent correctness cases before profiling.

Counters cover main-thread user execution from exec to exit, including input generation, setup/reset, computation, serialization and output. Primary compute timing excludes input preparation/reset. Within each workload/profile, every configuration uses the same input and common baseline batch count. Source timing batch counts remain separately recorded. Across profiles, seeds differ and estimates remain separate. Counter medians/ranges have only three repetitions per configuration, without a significance or causality claim. Profiling configuration order is not an independently randomized primary timing experiment.

Complete final binaries, disassembly, pre-link IR, optimization remarks, and raw/merged PGO profiles are retained under `.aion/phase4-profile-artifacts/<profile-id>/`. Each configuration's codegen reference hashes its `evidence.json`. [The descriptive counter summary](../.aion/validation/phase4-profile-summary.json) links figures to raw profile hashes and retains medians/ranges.

## Observed counter differences

Values are percent changes in median **whole-process counter counts** against the matched baseline in the same profile. Positive means more events, not faster execution. First/second values refer to the two separate input datasets above. They are not pooled and are not compute-only speedup estimates.

| Candidate/workload | Retired instructions % | Cycles % | Cache misses % | Branch misses % |
|---|---:|---:|---:|---:|
| records/LTO | +2.07 / +2.07 | +15.83 / +17.41 | -9.55 / +1.13 | +10.81 / +11.09 |
| logs/PGO | -3.80 / -3.89 | -8.55 / -8.65 | +0.83 / -0.93 | -1.15 / -1.03 |
| matrix/LTO | +0.40 / +0.40 | +47.63 / +36.46 | +71.55 / +25.02 | +14.11 / +2.44 |
| matrix/PGO+LTO | -0.08 / -0.08 | +37.74 / +39.19 | +25.16 / +72.46 | +0.71 / +5.08 |

IPC, cache/branch miss rates, raw counts, and separately sourced wait4 context-switch/fault observations remain in each per-sample report/JSON. Generic cache events do not identify a specific cache level. Virtual PMU behavior, scheduling, frequency/power state, cache history and the small noninterleaved diagnostic series limit interpretation.

## Records/LTO

Direct observations:

- LTO executes approximately 2.07% more instructions and 15.83–17.41% more cycles in these equal-work observations. Cache-miss direction is not consistent across datasets, while branch-miss counts are about 11% higher.
- Range-verified baseline samples place 51.5% / 54.6% of recorded IP samples in `parse_records`; LTO samples place 77.3% / 74.3% in `main`.
- The preserved baseline disassembly names `parse_records`, while the LTO disassembly contains no named occurrence. Binary sizes are 39976 and 39360 bytes. Pre-link IR alone cannot describe final cross-TU LTO decisions.

The observations are consistent with cross-module inlining/internalization and changed layout/prediction behavior. They do not mean parsing disappeared, nor do sample labels prove a specific inlining decision caused a slowdown. The hypothesis that a universal increase in cache misses alone explains the regression is not supported by these two datasets. A smaller binary is not necessarily faster. Native replication and controlled layout/inlining interventions remain needed.

## Logs/PGO

Direct observations:

- PGO retires about 3.8–3.9% fewer instructions and records about 8.6% fewer cycles in each profile. Cache-miss changes are near zero and change sign; branch misses fall by about 1%.
- Range-verified samples place 47.3% / 47.9% of baseline IP samples and 45.5% / 40.7% of PGO samples in `parse_log`. These are separate sample distributions, not exact time shares.
- The preserved pre-link parser remarks contain 102 successful/zero missed inline remarks for baseline and 96/six for PGO. Some char-conversion inline thresholds change from 375 to 45. These are whole-TU remarks, not dynamic calls or final hot-path cost.

These observations support investigation of different instruction/branch paths, rather than attributing the apparent timing gain solely to fewer cache misses. They do not validate the noisy Phase 3 +12.15% / +9.08% timing signals. PGO+LTO also demonstrates why instruction count is not enough: it reduces instructions by about 10% but cycles by only about 3.5% in these profiles.

## Matrix LTO and PGO+LTO

Direct observations:

- Instructions differ by less than half a percent, while cycles increase substantially. A simple explanation based on large extra retired-instruction work is not supported by these observations.
- Baseline, LTO, and PGO+LTO final disassembly each retain two static `pmuludq` occurrences. Pre-link remarks report vector width two and interleave count two at the matrix inner loop. Thus an explanation that all SIMD multiplication disappeared is unsupported. Static counts are not retired multiplication counts.
- About 97–99% of recorded samples land in the workload's `main` or its computation lambda, rather than explaining the result through startup alone. LTO/PGO can change whether source operations are attributed to `main` or an outlined lambda.
- Cache-miss increases recur but their magnitudes vary greatly. Generic guest counters cannot isolate a cache level, memory-latency mechanism, alignment effect, or physical-host interference.

Layout, memory dependency/alias handling, locality and execution latency remain hypotheses. The measurements test the simpler extra-instructions/lost-all-SIMD explanations without establishing an alternative cause. Valid primary timings and one-factor interventions on a documented native host remain necessary.

## Training representativeness

Profiles are freshly trained on seed 271828, with independently checked outputs. Problem sizes match measurement sizes: records 40000, logs 60000, matrix dimension 128. Training uses two rounds; records/logs measurement uses three and matrix twelve. Training invokes the ordinary checksum mode with one batch, while timed/profiled computation uses measurement mode and calibrated batches. Those are verified harness/input differences. They can affect branch weights, outlining, layout and profile relevance; their causal runtime effect is untested. Equal problem size does not establish production representativeness.

## Symbol-resolution audit

Initial addr2line-only labels can select an unrelated nearby exported symbol for stripped libc code. Such labels must not be described as a named hot function. The raw IPs/counters are unchanged; the separate [discovery symbol audit](../.aion/phase4-symbols/results/20261031T023722-4f6d5a6644.json) and [confirmation symbol audit](../.aion/phase4-symbols/results/20261031T023747-9e323a646c.json) verify object hashes and require enclosing sized text-function ranges from `nm`. Private stripped library regions remain unresolved, preserving their samples. The function names above use these corrected audits. Raw profiling reports explicitly label older nearest-symbol names as unverified hints.

The current profiler CLI's new resolution path was additionally checked in `.aion/phase4-profile-check/results/20261031T024755-ad47c08bbf.json` (one counter and one sampled execution, kept separate from the 72/24 investigation counts). No new timing or causal claim is based on that check.

Reproduction commands are in [Phase 4 methodology](phase4-methodology.md); interpretation and availability details are in [counter methodology](hardware-counter-methodology.md). The main [performance report](phase4-performance.md) separately assesses ordinary timing and independent confirmation. No profiler-only result is promoted.
