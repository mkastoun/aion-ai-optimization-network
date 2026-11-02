# AION 0.5 research methodology

Phase 5 adds controlled, deterministic experiments. It does not implement an AI
optimizer. Native scientific validation and implementation validation are
different milestones. WSL2, containers, and GitHub-hosted runners cannot supply
bare-metal validation. Kernel/CPU/DMI/container/CI detection is observational;
absence of an indicator is not proof of physical ownership.

## Declaration and computational bounds

`aion research declare` seals the fixed bundled catalog, selected panels,
complete source/include closures, independent expectations, compiler/linker/C++
library identity, placement, measurement settings, independent scheduling seeds,
and budgets. It preserves a source snapshot beside the declaration. Each role
defaults to at most 2,500 logical external commands and 3,600 elapsed seconds;
hard limits are 10,000 commands and 7,200 seconds. Pairs are bounded to 5–15,
warmups to 1–3, and panels to the 17 fixed catalog entries. Every experiment
uses a family size of 17, including selected subsets.

The budget includes compiler/profdata probes, compilation, profile training,
correctness checks, calibration, warmups and measured executions. It counts
logical `run_process` invocations, not every kernel child process. Per-command
timeouts are capped by the remaining wall budget. Python bookkeeping can finish
after the deadline while preserving evidence; the budget prohibits further
external launches. Each process keeps existing address-space/output/CPU/wall
limits. Separate diagnostics have fixed finite loops and per-process limits;
their costs do not enter primary timing or the study's primary command budget.

There is no arbitrary recipe/source loader. Declaration verification reconstructs
the installed trusted catalog and compares its bytes. A new study is required
after source/toolchain changes. A declaration seal is a reproducibility checksum,
not a signature or security attestation. The operator still trusts the installed
checkout and compiler. Finite source variants are checked in; AION does not
generate, mutate, evolve, or rewrite sources at runtime.

`research run` journals an invocation before initializing its compiler. It
records all selected attempts, including unsupported builds, incorrect outputs,
budget exhaustion, exceptions and interruptions. A failed role cannot be
silently retried under the same declaration/store. An intentional new study
uses a new declaration and keeps the earlier evidence. Discovery and confirmation
are separate commands with distinct explicit sessions and scheduling seeds;
confirmation uses the existing held-out input role. Separate IDs alone do not
prove independent conditions. The report rejects overlapping recorded windows.

## Measurement and correctness

The existing engine performs output checks against independent Python
expectations for every baseline and candidate, calibrates each configuration to
250–500 ms, retains discarded pilots, warms up, then randomizes balanced adjacent
baseline/candidate pairs. Input creation, transpose preparation and reset work
stay outside the compute interval; computation, aggregation and checksum work
stay inside. Whole-program end-to-end cost can differ, particularly for the
transposed matrix variant, and must be evaluated separately before practical use.

The statistical implementation and thresholds are unchanged: the 2%/twice
combined relative MAD floor, maximum 5% regression, default 5% CV, duration,
drift, complete correctness/samples/warmups, and empirical paired moving-block
bootstrap uncertainty with family adjustment all remain. No outlier removal,
sample pooling, stopping on a positive signal, or choosing a new candidate from
the observed outcome occurs. Seventeen comparisons and eleven pairs provide
limited extreme-tail resolution; adjusted intervals are descriptive empirical
evidence, not guaranteed coverage under dependence or nonstationarity.

Research timing has type `research-timing`. Its `baseline` is the explicitly
declared reference, which can be LTO or program-specific PGO. The O3 anchor
panels and source-variant optimization panels use standard Clang O3. Actual
variant fingerprints and source closures are in each configuration's build
record; the engine's workload fingerprint identifies the shared input/reference
contract. The primary ten-workload manifest and original sources are unchanged.

All replacements/wrappers receive separate differential O3, ASan and UBSan
checks. Original extended validation remains included. The log extension has an
independent semantic Python oracle and preserved ordinary checksum expectations.
Coverage is finite and covers trusted generated records; it is not a proof of
equivalence for arbitrary C++ inputs or production data.

## Controlled interventions

Records compares O3/LTO, parser noinline, aggregate noinline, disabled
vectorization, disabled unrolling, PGO+LTO, and branchless aggregation. The
branchless implementation retains the existing 4,096-slot direct index; it
updates each row's slot using a zero/one acceptance mask. This may increase
memory traffic, so a negative result is meaningful. Each compiler panel changes
one named policy relative to its declared reference. Disabling unrolling or
inlining can also change layout and branch behavior; a timing response alone
does not isolate one microarchitectural mediator.

Logs compares O3/PGO, two versus six training rounds on the same seed, ordinary
checksum versus one-batch measurement-path training, and uniform versus mixed
training at equal total work (three distinct training seeds, two rounds each).
Mixed training includes ordinary, all-error/status-500 and all-info/status-200
records. Held-out seed 42 versus 314159 is never a training seed. A separate
panel measures the unseen malformed-heavy domain, with every third line
malformed, rather than the ordinary every-97th-line rule. Both panel arms use
the same extended generator. Training and measurement paths are explicit.
The extension changes setup code in `main`; these panels are experiments on
that declared program, not a byte-identical rerun of the original Phase 4 logs
binary. Original-source evidence stays separate. The native all-ten workflow
also repeats the unchanged original logs O3/PGO anchor.

Each independent PGO build instruments, executes correct declared training,
merges with a matching-major `llvm-profdata`, checks profile compatibility during
rebuild, and archives raw/merged profiles and final binaries with hashes. No
profile from discovery is reused in confirmation. An improvement for this
program/training domain cannot become a reusable generic PGO preset.

Matrix compares O3/LTO, disabled vectorization, disabled unrolling, PGO+LTO,
and a transposed dot-product source variant against O3. The last is a complete
implementation intervention: transposing B during preparation makes its dot
products contiguous but changes loop dependencies and reduction structure too.
It tests that implementation; it cannot separately prove a cache, dependency,
or SIMD explanation. The Phase 4 fact that SIMD remains present in original
LTO/PGO+LTO is retained. An intervention that disables SIMD tests a policy,
without retroactively asserting that original SIMD disappeared.

## Diagnostics and hypothesis status

`research diagnose` checks archived executable hashes and host/build identity,
verifies outputs again, then runs three separate whole-process counter
executions per arm using the same baseline-calibrated batch count. It retains
disassembly, per-TU pre-link IR, inline/vectorization remarks and profile-based
branch metadata. Optional unavailable PMU events stay unavailable. Counters
include setup and process startup, whereas compute timing excludes preparation.
Static instructions and counters alone never establish causality. Final LTO
decisions cannot be inferred solely from pre-link IR.

`research report` links declarations, individual timing records, correctness,
actual sources/binaries, compiler/build/environment identity, inputs/training,
uncertainty, failed gates, separate diagnostics and independent confirmation.
Statuses remain distinct: observed change, validated change, inconclusive,
rejected hypothesis, unsupported environment. A validated native hypothesis
requires compatible independent timing, relevant quality controls and compatible
research sanitizer evidence. An improvement hypothesis can be rejected by a
quality-valid independently repeated regression. A no-clear-change result does
not prove equivalence. WSL estimates remain observable, with native hypotheses
marked unsupported in this environment.

The registry rejects research evidence, including a research marker on an
otherwise relabeled primary record. Research reports never create presets.
Phase 6 readiness requires a separate all-ten native review as well as quality,
correctness, reproducibility, bounded search, explicit budgets and separation.

## More controls and native replication

The original byte-identical A/A and injected known-slowdown controls remain.
`controls --benchmark image,kv --distribution-suite` selects existing,
independently validated flat/hotspot and checkerboard/sequential cases. This is
an explicit new input contract. Quality reports keep its stratum separate from
ordinary cases. Validation compatibility requires identical source closures and
every chosen argument/expected-output pair in the all-ten sanitizer evidence.

Reports retain valid and inconclusive outcomes, false-positive signals,
slowdown detection, all-attempt and conditional Wilson intervals, CV and drift
distributions, measured durations, CPU placement, start/end power/scheduler/
cgroup observations and source hashes. Counts describe these dependent local
observations; they do not establish a universal error rate.

`tools/replicate_linux.py` supports explicit discovery/confirmation roles in
separate stores/sessions, original and distribution controls, all-ten O3/O2/LTO/
PGO/PGO+LTO timing, separate validation, research and a source-linked native
report. The native report recomputes control quality and checks compatibility,
held-out inputs, nonoverlapping sessions, documented physical host, all-ten
coverage and unchanged measurement gates. No privileged tuning is performed.
