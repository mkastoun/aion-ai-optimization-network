# Phase 5 controlled research findings

**Seventeen hypotheses were tested in two WSL observation sessions. None is a validated native optimization result.** The finite catalog, source snapshots, actual compiler/binary/input/training identities, all attempts and independent estimates are preserved.

Records/LTO again produced a quality-valid per-comparison WSL regression in
both runs. No intervention produced a qualified local improvement in both
discovery and confirmation. The two source optimization candidates, branchless
records aggregation and transposed matrix multiplication, did not establish an
independently confirmed improvement. The control study still fails measurement
quality: zero false A/A improvement signals coexist with many inconclusive
outcomes and only seven detected slowdowns out of twenty attempts. Individual
strata and uncertainty remain in the performance/quality reports.

## Intervention contracts

| Panel | Hypothesis | Reference flags / variant / training | Candidate flags / variant / training |
|---|---|---|
| records-lto | LTO changes records runtime relative to O3 | -O3; original; standard/default/ordinary | -O3 -flto; original; standard/default/ordinary |
| records-parser-noinline | Preventing parser inlining improves LTO | -O3 -flto; original; standard/default/ordinary | -O3 -flto; records_parser_noinline; standard/default/ordinary |
| records-aggregate-noinline | Preventing aggregate inlining improves LTO | -O3 -flto; original; standard/default/ordinary | -O3 -flto; records_aggregate_noinline; standard/default/ordinary |
| records-scalar | Disabling vectorization improves LTO | -O3 -flto; original; standard/default/ordinary | -O3 -flto -fno-vectorize -fno-slp-vectorize; original; standard/default/ordinary |
| records-no-unroll | Disabling loop unrolling improves LTO | -O3 -flto; original; standard/default/ordinary | -O3 -flto -fno-unroll-loops; original; standard/default/ordinary |
| records-pgo-lto | Program-specific PGO improves LTO | -O3 -flto; original; standard/default/ordinary | -O3 -flto; original; pgo/default/ordinary |
| records-branchless | Branchless aggregation improves O3 | -O3; original; standard/default/ordinary | -O3; records_branchless; standard/default/ordinary |
| logs-pgo | Default program-specific PGO improves O3 | -O3; logs_distributions; standard/default/ordinary | -O3; logs_distributions; pgo/default/ordinary |
| logs-training-rounds | More training rounds improve PGO | -O3; logs_distributions; pgo/default/ordinary | -O3; logs_distributions; pgo/long/ordinary |
| logs-training-path | Measurement-path training improves PGO | -O3; logs_distributions; pgo/default/ordinary | -O3; logs_distributions; pgo/default/measure-one-batch |
| logs-training-mix | Mixed training improves PGO on ordinary held-out inputs | -O3; logs_distributions; pgo/uniform/ordinary | -O3; logs_distributions; pgo/mixed/ordinary |
| logs-unseen | Mixed training generalizes to unseen malformed-heavy inputs | -O3; logs_distributions; pgo/uniform/ordinary | -O3; logs_distributions; pgo/mixed/ordinary |
| matrix-lto | LTO changes matrix runtime relative to O3 | -O3; original; standard/default/ordinary | -O3 -flto; original; standard/default/ordinary |
| matrix-scalar | Disabling vectorization improves LTO | -O3 -flto; original; standard/default/ordinary | -O3 -flto -fno-vectorize -fno-slp-vectorize; original; standard/default/ordinary |
| matrix-no-unroll | Disabling loop unrolling improves LTO | -O3 -flto; original; standard/default/ordinary | -O3 -flto -fno-unroll-loops; original; standard/default/ordinary |
| matrix-pgo-lto | Program-specific PGO improves LTO | -O3 -flto; original; standard/default/ordinary | -O3 -flto; original; pgo/default/ordinary |
| matrix-transposed | Transposed dot-product implementation improves O3 | -O3; original; standard/default/ordinary | -O3; matrix_transposed; standard/default/ordinary |

Each compiler-policy comparison changes one named policy relative to its declared reference. Source interventions test a complete implementation. They do not isolate all possible microarchitectural mediators. No adaptive source rewriting, language-model call, evolutionary search or automatic preset promotion occurs.

## Separate diagnostic observations

Diagnostics verify archived executable hashes, recheck all independent cases and run three equal-work whole-process counter executions per arm. Each panel uses its baseline-calibrated batch count for both arms; primary timing calibrates arms independently. Counting includes setup/startup/reset/serialization, whereas primary compute timing excludes preparation/reset. Per-TU IR is pre-link, not final post-LTO IR. Assembly/counter changes do not by themselves prove causality.

68 configurations retain exact timing-binary identities. Independent checks pass 596/596; counter executions pass 204/204. Counted event observations: 1836/1836; multiplexed: 0.

[Codegen audit](../.aion/phase5/codegen-audit.json): all **280** disassembly/IR
process and archived-content checks pass, covering 68 final disassemblies and
212 pre-link TU artifacts. Remarks match captured compiler stderr; their hashes
are retained in this audit. Static counts below are whole-binary/TU facts.

- [20261031T131526-7a7845de17.json](../.aion/phase5/diagnostics/results/20261031T131526-7a7845de17.json)
- [20261031T132040-d9b0451f5d.json](../.aion/phase5/diagnostics/results/20261031T132040-d9b0451f5d.json)

| Panel | Role | Instructions % | Cycles % | Cache misses % | Branch misses % |
|---|---|---:|---:|---:|---:|
| records-lto | discovery | +2.038 | +13.296 | -6.998 | +8.957 |
| records-parser-noinline | discovery | -2.094 | +0.596 | +16.355 | -6.380 |
| records-aggregate-noinline | discovery | -0.533 | -20.936 | -40.992 | -4.845 |
| records-scalar | discovery | -0.219 | -10.334 | -0.153 | -4.105 |
| records-no-unroll | discovery | +14.340 | -14.511 | +4.536 | -8.465 |
| records-pgo-lto | discovery | +8.212 | -14.181 | -19.437 | -7.322 |
| records-branchless | discovery | +2.194 | -2.018 | +1.286 | -51.149 |
| logs-pgo | discovery | -3.756 | -6.371 | -0.206 | -0.952 |
| logs-training-rounds | discovery | +0.000 | +3.573 | -0.933 | +1.300 |
| logs-training-path | discovery | -0.000 | +0.476 | -0.179 | +0.879 |
| logs-training-mix | discovery | +0.013 | +0.025 | -1.229 | -2.289 |
| logs-unseen | discovery | +0.124 | -0.011 | -0.269 | -1.162 |
| matrix-lto | discovery | +0.404 | +37.757 | +8.721 | +8.966 |
| matrix-scalar | discovery | +59.969 | +60.027 | +18.348 | +10.104 |
| matrix-no-unroll | discovery | +31.439 | +1.064 | -1.529 | +8099.447 |
| matrix-pgo-lto | discovery | -0.482 | -0.234 | -1.110 | -4.396 |
| matrix-transposed | discovery | +1.013 | -1.623 | -4.169 | +19.928 |
| records-lto | confirmation | +2.047 | +17.312 | +6.901 | +10.696 |
| records-parser-noinline | confirmation | -2.087 | +1.811 | +28.264 | -6.982 |
| records-aggregate-noinline | confirmation | -0.533 | -10.787 | +4.127 | -8.073 |
| records-scalar | confirmation | -0.217 | -7.063 | +27.155 | -3.548 |
| records-no-unroll | confirmation | +14.266 | -19.551 | -19.876 | -8.635 |
| records-pgo-lto | confirmation | +8.217 | -9.401 | -2.368 | -9.004 |
| records-branchless | confirmation | +2.194 | -0.452 | +1.224 | -51.018 |
| logs-pgo | confirmation | -3.756 | -5.295 | -1.103 | -1.393 |
| logs-training-rounds | confirmation | +0.000 | +5.832 | +1.473 | +2.233 |
| logs-training-path | confirmation | -0.000 | +3.649 | +0.737 | +0.624 |
| logs-training-mix | confirmation | +0.010 | +4.230 | +0.467 | -0.439 |
| logs-unseen | confirmation | +0.125 | +2.331 | +0.972 | -0.985 |
| matrix-lto | confirmation | +0.404 | +36.204 | +17.057 | +7.963 |
| matrix-scalar | confirmation | +59.957 | +49.912 | +6.446 | -0.104 |
| matrix-no-unroll | confirmation | +31.434 | +3.242 | +3.243 | +8396.211 |
| matrix-pgo-lto | confirmation | -0.482 | -0.462 | +4.396 | -5.779 |
| matrix-transposed | confirmation | +1.018 | +0.122 | +0.992 | +18.703 |

Positive counter changes mean more events, not faster execution. These three-repetition medians remain separate by role and input. Generic cache events do not identify a cache level; virtual PMU behavior, code/data placement, power, scheduling and cold/warm history limit interpretation. No significance or causal claim is attached to these counter differences.

The large matrix/no-unroll branch-miss percentages have explicit denominators:
discovery medians are 68,586 versus 5,623,673 misses; confirmation medians are
61,146 versus 5,195,093. Instructions increase about 31.4%, but cycles increase
only 1.1–3.2% in these separate diagnostics. This demonstrates why a large event
percentage cannot be substituted for compute timing or a causal explanation.

## Records / LTO

The original direct-index aggregator remains the reference. Parser noinline, aggregate noinline, scalar-policy, no-unroll and PGO+LTO panels test named policy interventions relative to LTO. Branchless aggregation against O3 writes each row's group using a zero/one acceptance mask; it can reduce unpredictable branching while increasing memory traffic. Each variant matches independent outputs and separate sanitizers. The [performance table](../docs/phase5-performance.md) retains positive, negative and inconclusive outcomes and each failed gate.

The LTO anchor's paired gains are **−13.328% / −11.112%**, both classified as
regressions with quality gates passing for those individual comparisons.
Retired instructions rise about 2.04% and diagnostic cycles about 13.3% / 17.3%.
The overall WSL control study remains unvalidated; this is a repeated local
regression observation, not native certification.

Aggregate noinline improves the discovery point by 10.896% and passes that
comparison, but confirmation fails variability/drift and has an interval spanning
−15.277% to +14.763%. Parser noinline, scalar and no-unroll interventions also
have positive point estimates, with failed uncertainty/variability/drift gates.
No one of these is a confirmed optimization.

Branchless aggregation reduces whole-process branch misses by approximately
51% in each diagnostic dataset while increasing retired instructions about
2.19%. Compute gains of 1.234% / 3.817% remain inconclusive. Fewer branch misses
alone did not establish a useful speedup.

Even a repeated response to noinline would identify the effect of that policy on this declared program, not prove that inlining alone caused the earlier 14–15% slowdown. Preventing inlining can alter layout, branch behavior and instruction dependencies too. The original Phase 4 instruction/cycle observations remain separate; there is no native causal conclusion.

## Logs / PGO

Fresh program-specific profiles compare two versus six rounds; ordinary checksum versus one-batch measurement-path training; uniform versus mixed training with equal total work; and an unseen malformed-heavy measured domain. Exact cases, training outputs, compatible llvm-profdata identity, raw/merged profile hashes and final builds remain in the research report. No discovery profile is reused in confirmation. Held-out measured seeds do not occur in training.

Both arms use the same extended input generator, whose ordinary outputs preserve the original checksums. Its setup-code changes can affect main layout/profile decisions, so this is not a byte-identical replication of the original Phase 4 logs program. The native all-ten workflow repeats that original O3/PGO anchor. These synthetic domains and one measured size do not establish production representativeness or general PGO flags. Pre-link inline/branch remarks are archived; changed decisions alone do not establish a speedup or its cause.

Default PGO has paired gains **8.612% / 6.021%**, but discovery fails variability
and confirmation fails the unchanged improvement rule. Confirmation's marginal
matched-median gain is 6.535%, below the 8.810% combined-MAD requirement; its
paired interval lower bound is 4.194%. The nominal 2% floor does not override
the larger measured noise floor.

More training rounds have negative points (−3.347% / −5.444%); changing the
training path is near zero (+1.235% / −0.724%). Mixed versus uniform training
has −4.228% / −6.758% on ordinary inputs and +0.849% / −1.999% on the unseen
malformed-heavy domain. None clears independent improvement requirements.
These results do not justify a general training recipe or a generic PGO preset.

In both datasets the parser TU has 102 successful / zero missed inline remarks
under O3 versus 96 / six under default PGO. Its branch-weight metadata entries
increase from four to nineteen. The six-round and measurement-path profiles
alter main-TU inline/branch metadata, while parser inline counts stay 96 / six.
Mixed training changes parser branch-weight entries to twenty-one. These are
pre-link static observations; they do not establish which decision caused a
runtime change.

## Matrix

The O3/LTO anchor, scalar-policy, no-unroll, PGO+LTO and transposed-dot-product panels test compiler policies and a complete alternative implementation. Transposition during setup makes dot-product accesses contiguous but also changes loop/reduction dependencies and traffic to C. Its setup cost is excluded from compute timing and included in whole-process counters; end-to-end usefulness needs a separate evaluation.

The Phase 4 finding that SIMD instructions remain present in the original matrix baseline/LTO/PGO+LTO is retained. Disabling vectorization tests a different policy; it does not mean original LTO lost SIMD. Final disassembly and pre-link vectorization remarks are preserved for every arm. Cache, instruction-dependency, layout and SIMD explanations remain hypotheses without valid native controlled evidence.

The original O3/LTO anchor has paired gains **−35.876% / −39.523%**, with
variability failures in both runs. Its diagnostic instructions rise only about
0.404%, while cycles rise 37.8% / 36.2%. Cache-miss changes are +8.7% / +17.1%
in these datasets; they do not isolate a memory mechanism.

The original O3 and LTO binaries each retain two static `pmuludq` sites and one
successful pre-link loop-vectorization remark. The scalar-policy candidate has
zero such multiply sites and zero successful vectorization remarks. It worsens
the paired point by 59.094% / 57.744% relative to LTO, with confirmation failing
quality gates. The observation does not support an explanation that original
LTO removed those SIMD sites.

No-unroll and PGO+LTO do not establish a recovery. The transposed implementation
has paired gains +0.086% / −0.949% against O3: discovery reports no clear change,
and confirmation fails variability/drift and the regression-bound check.
Neither this implementation nor its counter differences prove a cache or
dependency cause for the original slowdown.

## Reproduction and support status

[Reproducible research report](../.aion/phase5/reports/results/research-report-65d872468cb144149ab2fa6a629d662d.json) contains source and binary fingerprints, compiler/build/environment identity, input/training cases, correctness, estimates/uncertainty, attached diagnostics, compatibility and support status. Every native hypothesis is unsupported in this WSL environment; point estimates and local gate outcomes remain visible. No negative result is removed or converted to a preset.

Commands and IDs are preserved in [sequence-a-final.json](../.aion/phase5/sequence-a-final.json), [sequence-b.json](../.aion/phase5/sequence-b.json) and [postprocess-sequence.json](../.aion/phase5/postprocess-sequence.json). Use [native instructions](../docs/phase5-native-instructions.md) for the pending physical-host study. Phase 6 remains not ready.
