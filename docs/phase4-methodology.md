# Phase 4 methodology

AION 0.4 retains the existing correctness, paired timing, calibration, uncertainty and promotion rules. `statistics.py` and `comparison_for` remain identical to 0.3. The JSON container stays schema version 1; primary calibrated runs use methodology version 4 to identify explicit session and environment-constraint provenance. Phase 1–3 results remain readable and preserved. New diagnostics use explicit non-promotion evidence kinds.

## Evidence separation

`primary-timing` alone can enter candidate/preset assessment. Profiling, sanitizer validation, preflight, measurement-quality reports and package smoke records cannot create presets. Profiling/sanitizer builds and their measured durations are never inserted into primary comparison arrays. Correctness checks, calibration pilots, warmups, outliers and out-of-band samples remain in their original records.

The 2%/twice-combined-relative-MAD improvement floor, 5% maximum regression, default 5% CV cap, minimum duration, drift, uncertainty, sufficient measurements/warmups, and independent-confirmation requirements remain. PGO profiles remain program-specific and ineligible for reusable flag-only presets. A positive point estimate or interval excluding zero does not override another failed gate. No AI optimizer or automatic source transformation is introduced.

## Sessions, preflight and compatibility

`aion preflight` checks the actual compiler/link/run path and optional counters, records available topology/SMT, frequency/governor, thermal/power, scheduler/resource/cgroup observations, and creates or uses a session file. WSL2/VM/container/native-Linux-no-indicator classifications are observational. No detected virtualization is not proof of bare metal. Logical affinity is checked in the actual workload, not treated as physical isolation.

Session records bind an explicit observation window to host and boot identities. New processes can reuse an existing session file only on that host/boot. Separate session IDs do not guarantee statistically independent conditions; operators must document genuinely separate observation windows. The replication script retains command/exit journals and runs stages sequentially. Native Linux validation is separately pending if only WSL2 is available.

Independent comparisons require matching methodology, compiler/build identity, source/input fingerprints, limits, placements, available power policy and relevant scheduler/cgroup restrictions. Dynamic load, frequency and CPU usage remain observations rather than stable identity components. Start/end observations can expose changes but cannot prove continuous stability. Cgroup namespaces can hide ancestor restrictions; visible roots, membership and resolvable process paths are recorded with this limitation.

Different sessions remain separate estimates even when compatible. Different hosts/placements/designs cannot be silently pooled or confirmed. Older records without session identity are explicitly historical, not retroactively assigned a session. The main performance report distinguishes repeated gated improvements/regressions, no clear change, inconclusive evidence, and the separate status of measurement-environment readiness.

## Measurement-quality study

Controls remain exact baseline binary copies: A/A and the same correct computation plus a declared elapsed 50 ms busy loop per timed unit. The steady clock includes descheduling; this is not a guarantee of consumed CPU time. Expected checksums, actual delay, paired records and all measurements are retained.

The quality report recomputes comparisons from raw records and links source hashes/sample identities. Compatible designs and environments form separate strata. Each stratum reports A/A false improvement signals, unexpected A/A regressions, known-slowdown detection, inconclusive outcomes, CV/drift/duration gates, adjusted intervals, and start/end environment observations. Different CPU placements remain separate strata. No timing samples or effect estimates are pooled.

Descriptive rates show successes, denominators and approximate 95% Wilson intervals. Both all-attempt and quality-valid denominators are shown so inconclusive results cannot silently dilute a conditional error rate. Controls/workloads within sessions are dependent, so binomial interval coverage is approximate; these numbers do not establish a universal false-positive rate or equivalence. Operational study completeness requires at least two explicit sessions, at least two runs per session/placement, different scheduling seeds and different measured input seeds. Operational quality passes only if all included controls have expected valid outcomes and recorded static settings remain stable. These completeness checks are separate from, and never relax, the existing performance thresholds.

Readiness distinguishes validation passed on available environments, native Linux evidence available, measurement-quality checks passed, and insufficient/inconclusive evidence. Ten-workload differential plus ASan/UBSan evidence must match the relevant host/compiler/source identities. Native performance validation cannot be borrowed from WSL tests or from a preflight. Readiness remains scoped to the tested controls and conditions.

## Profiling and compiler behavior

See [hardware-counter methodology](hardware-counter-methodology.md). Counting and user-cycle IP sampling use separate processes and retain exact compiler/binary/input identities. Every configuration uses a common baseline batch count for equal-work profiling; source timing batch counts remain separately recorded. Counters include whole-process setup/startup, whereas primary timing excludes them. Hardware/software types, permissions, enabled/running times, multiplexing/scaled estimates, suppressed invalid ratios, wait4 software observations and unresolved/lost samples stay explicit.

Preserved Phase 3 records/LTO, logs/PGO, and matrix LTO/PGO+LTO evidence is investigated by rebuilding unchanged source fingerprints, checking executable hashes, preserving disassembly/pre-link IR/optimization remarks/PGO profiles, and profiling equal inputs/work units. Changed static decisions, sampled symbols, retired-instruction counts and primary timing effects are different facts. Hypotheses about code layout, inlining, vectorization, memory access or training representativeness are not established causes without controlled interventions and valid independent timings. No compiler defect is inferred from assembly alone.

## Correctness and expanded applications

Image filtering and in-memory key/value processing each have four translation units. Image processing uses deterministic uint16 images, separable integer Gaussian filtering, Sobel edges, histogram/weighted output and row-byte hashes. Flat, checkerboard and random distributions are explicit. Key/value processing uses variable-length values, insert/lookup/update/delete operations, hot-set/sequential/mixed access, observed query results and sorted serialized final state. Independent Python array/dict specifications generate all expected outputs. Setup generates input buffers; application processing, allocations, aggregation, serialization and result hashing remain timed. These ten workloads are not a representation of every production program.

The original eight timing cases and source/header fingerprints remain unchanged. A separate `validation.json` adds singleton, wrapping-seed, large, fresh-seed and new-application pattern cases. Separate differential O3 and ASan/UBSan pipelines test these cases. Sanitizer flags are fixed internal validation recipes, not optimization proposals. ASan reserves large shadow address space, so only these diagnostic child runs explicitly omit the virtual-address ceiling while retaining wall/CPU/output limits; primary timing limits do not change. Sanitizer diagnostics fail validation even if output/exit status appears successful. See official [ASan](https://clang.llvm.org/docs/AddressSanitizer.html) and [UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) documentation for runtime behavior.

## Exact local commands

Run inside Ubuntu from the project directory with `.aion/venv-linux` activated. Profiling/sanitizers and compilation must finish before primary timing starts. These commands intentionally require no machine-wide settings change.

```bash
source .aion/venv-linux/bin/activate
AION_REQUIRE_COMPILER=1 python -m pytest -q --junitxml=.aion/validation/phase4-linux-tests.xml
aion --store .aion/phase4-validation sanitize --benchmark all --cpus auto --evidence .aion/phase4-sanitizers
aion --store .aion/phase4-profiling profile \
  --from-result .aion/phase3/results/20261030T234834-de3eb6de82.json \
  --benchmark records,logs,matrix --candidate baseline --candidate lto --candidate pgo --candidate pgo-lto \
  --samples 3 --cpus auto --codegen --hotspots --evidence .aion/phase4-profile-artifacts
aion --store .aion/phase4-profiling profile \
  --from-result .aion/phase3/results/20261031T000202-01808fcd04.json \
  --benchmark records,logs,matrix --candidate baseline --candidate lto --candidate pgo --candidate pgo-lto \
  --samples 3 --cpus auto --codegen --hotspots --evidence .aion/phase4-profile-artifacts

aion --store .aion/phase4-preflight preflight --cpus auto --counters \
  --session-file .aion/phase4-sessions/a.json --label phase4-session-a
aion --store .aion/phase4-controls-a controls --benchmark matrix,records,logs --cpus auto \
  --session-file .aion/phase4-sessions/a.json --compare-unpinned --repetitions 2 --iterations 11 --warmups 2 --seed 64100
aion --store .aion/phase4 benchmark --benchmark all --cpus auto --session-file .aion/phase4-sessions/a.json \
  --candidate o2 --candidate lto --candidate pgo --candidate pgo-lto --iterations 11 --warmups 2 --seed 64300

# At the separately delimited second observation session:
aion --store .aion/phase4-preflight preflight --cpus auto --counters \
  --session-file .aion/phase4-sessions/b.json --label phase4-session-b
aion --store .aion/phase4-controls-b controls --benchmark matrix,records,logs --cpus auto \
  --session-file .aion/phase4-sessions/b.json --compare-unpinned --repetitions 2 --iterations 11 --warmups 2 --seed 64200
aion --store .aion/phase4 benchmark --benchmark all --cpus auto --session-file .aion/phase4-sessions/b.json \
  --input-role confirmation --candidate o2 --candidate lto --candidate pgo --candidate pgo-lto \
  --iterations 11 --warmups 2 --seed 64400

aion --store .aion/phase4-quality quality --directory .aion/phase4-controls-a/results \
  --directory .aion/phase4-controls-b/results \
  --validation .aion/phase4-validation/results/20261031T022349-7594ef3329.json --output docs/phase4-quality.md
```

Use actual newly generated run IDs for `aion report --result ... --confirmation ... --audit-json ...`. The validation JSON above is the preserved local record; fresh executions produce new IDs. Native Linux reproduction and optional administrator considerations are in [the native guide](native-linux-benchmarking.md). See [validation](phase4-validation.md) and [performance](phase4-performance.md) for real outcomes, unavailable evidence and Phase 5 readiness.

The completed local timing pair can be rendered without changing its raw inputs:

```bash
aion report --result .aion/phase4/results/20261031T025701-07d35075c3.json \
  --confirmation .aion/phase4/results/20261031T032139-5ccfa44eff.json \
  --audit-json .aion/validation/phase4-gate-audit.json --output .aion/phase4/confirmed.md
python .aion/validation/phase4-evidence-audit.py
python .aion/validation/phase4-render.py
```

The retained local render script adds the curated result summary and complete failed-gate table while asserting that raw source hashes stay unchanged.
