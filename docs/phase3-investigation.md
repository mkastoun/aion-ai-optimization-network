# Phase 3 investigation of Phase 2 sorting and matrix regressions

The suspected slowdowns recur as point estimates, but neither workload has an independently verified regression across these two fresh runs under every unchanged quality gate. This is virtualized WSL2 evidence. The results do not establish a compiler defect or a causal performance explanation.

## Source and binary provenance

The preserved local wheel `aion_network-0.2.0-py3-none-any.whl` has SHA-256 `58dbec0c718f7be6c450288c391b8dcd232e405167dcebcdbc865f1a39c4f0c8`. The investigation restores only fixed sorting, matrix, common-header, and manifest members and checks the wheel's version metadata. The resulting workload fingerprints match both preserved Phase 2 runs, `20261030T133332-5c960dc216` and `20261030T134127-a9b702d915`, for both workloads. The original Phase 2 temporary executables were not retained; this is exact source reconstruction, not proof of original executable identity.

Artifacts are preserved in [the investigation directory](../.aion/phase3-investigation/20261030T232056-0fd3ea38/), including `investigation.json`, frozen source, final binary disassembly, pre-link optimized LLVM IR, inlining/vectorization remarks, raw/merged profiles, training cases, output checks, and artifact hashes. All sixteen fresh timed-build hashes (eight configurations in each run) match their preserved static diagnostic builds, recorded as `diagnostic_binary_matches`. Pre-link IR is not presented as final LTO machine code.

## Fresh controlled retest

Both runs request and verify guest logical CPU 0, use Clang 18.1.3, eleven adjacent randomized baseline/candidate pairs, and two warmups. Discovery uses scheduling seed 53200 and input seed 42; confirmation uses 53201 and 314159. Profiles are freshly trained on seed 271828. All configurations pass correctness. The two runs retain 264 measured executions in total, without pooling them.

Positive paired gain means faster than the matched O3 baseline. Intervals are adjusted moving-block bootstrap intervals, with nominal 95% family confidence across six comparisons. An interval excluding zero cannot override quality gates.

| Workload | Candidate | Discovery gain % [interval] | Confirmation gain % [interval] | Classifications |
|---|---|---|---|---|
| sorting | O2 | -9.350 [-10.563, -8.471] | -10.260 [-10.737, -10.034] | regression / inconclusive |
| sorting | PGO | -10.918 [-13.109, -9.848] | -12.283 [-12.930, -10.337] | inconclusive / inconclusive |
| sorting | PGO+LTO | -7.562 [-8.891, -6.422] | -7.923 [-8.829, -1.329] | regression / inconclusive |
| matrix | O2 | -1.336 [-2.091, 0.167] | +1.724 [0.753, 2.628] | no clear change / inconclusive |
| matrix | PGO | -14.258 [-17.085, -9.822] | -15.172 [-16.933, -14.716] | inconclusive / inconclusive |
| matrix | PGO+LTO | -52.783 [-55.931, -42.235] | -51.770 [-55.076, -50.095] | inconclusive / inconclusive |

Raw evidence:

- [Discovery JSON](../.aion/phase3-investigation/results/20261030T232129-cc5491ee80.json) and [detailed report](../.aion/phase3-investigation/results/20261030T232129-cc5491ee80.md).
- [Confirmation JSON](../.aion/phase3-investigation/results/20261030T232352-6ad5a5e136.json) and [detailed report](../.aion/phase3-investigation/results/20261030T232352-6ad5a5e136.md).

The failing quality gate is variability in at least one paired series for each inconclusive negative result. Matrix O2 confirmation also fails drift. A configuration's overall CV can differ from the CV of its matched baseline subset; the raw paired summaries determine the classification. Negative gains also fail the promotion regression bound and improvement requirement, as expected. No threshold was lowered to validate the suspected regressions.

## Verified artifact observations

- Frozen algorithms and expected-input fingerprints match Phase 2. Fresh verification, pilots, warmups, and measurements check the expected checksums. Output equivalence covers these deterministic inputs; it is not an instruction-count or general equivalence proof.
- Both baseline and PGO+LTO matrix inner regions contain SIMD `pmuludq` multiplication, loads, and `paddq` accumulation. In the preserved final disassembly, examples occur near baseline offsets `0x18a0–0x18d3` and PGO+LTO `0x1df0–0x1e26`. An explanation that all SIMD multiplication disappeared is unsupported.
- The preserved sorting remarks identify a specific changed decision: `__partial_sort` is inlined into `__introsort_loop` in baseline (cost 235, threshold 325), but is not inlined at that callsite with PGO (cost 50, threshold 45). This is a pre-link optimization observation, not proof that this callsite caused the timing difference or dominates runtime.
- Optimized pre-link IR contains four branch-weight metadata nodes and no function-entry nodes for baseline sorting, versus 42 and six with PGO. Matrix changes from four/zero to 27/four. These whole-module counts verify profile-related IR differences; they are not execution counts. Sorting binary size changes from 23064 bytes (baseline) to 24808 (PGO) and 24248 (PGO+LTO); matrix changes from 22440 to 23792 and 23368 bytes. Binary size alone does not explain runtime.
- PGO training uses equal problem sizes with different seeds and fewer rounds: sorting 100000 elements, two training rounds versus ten measurement rounds; matrix dimension 128, two versus twelve rounds. The training output is independently checked. Profile hashes and compiler invocation provenance are retained.
- CPU affinity verifies placement on guest CPU 0. It does not rule out Windows host scheduling, shared physical resources, power changes, or thermal effects. Both repeated point estimates and inconclusive gates are preserved.

## Hypotheses and next experiments

Inlining, code layout, alias/versioned-loop choices, and training-profile representativeness could affect performance. Static remarks and whole-binary mnemonic/IR counts are diagnostic clues, not evidence of dynamic execution counts or causal attribution. Equal problem size alone does not make the training inputs representative of production use.

Replicate A/A and slowdown controls on native Linux first. Then repeat frozen-source comparisons with documented stable host conditions and available hardware counters, inspecting hot regions and testing one compiler/profile change at a time. Retain separate host identities and independent input seeds. There is no justified source rewrite or AI optimization in this phase.

Exact reproduction commands are in [Phase 3 methodology](phase3-methodology.md).
