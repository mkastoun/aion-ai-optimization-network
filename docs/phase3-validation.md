# Phase 3 validation — October 30, 2026

AION 0.3 adds controlled benchmarking and representative applications while retaining the Phase 2 statistics and promotion rules. No AI optimization, cloud dependency, remote execution, or autonomous source rewriting is introduced. The five original kernel `.cpp` files are byte-identical to their copies in the preserved 0.2 wheel; the common timing/control harness is extended.

## Implemented behavior

- Optional Linux affinity validates the requested CPUs against the caller's allowed set, applies them in the actual child before exec, and checks effective masks. Current C++ programs additionally report their PID, start/end masks, and CPU endpoints. `none` disables narrowing, `auto` selects the first allowed CPU, and explicit unsupported requests fail clearly. No root or machine-wide settings change is needed.
- Start/end metadata records host/guest identity, exposed topology, allowed CPUs, available frequency/governor/power/thermal data, scheduling/resource restrictions, and load. Missing values stay unavailable. Compiler/linker versions and digests, C++ library identity, source/header digests, binary hashes, training cases, and profile provenance accompany the measurements.
- Byte-identical A/A and declared 50 ms-per-unit slowdown controls audit the measurement system. Repeated seeds and balanced pinned/unpinned order are supported. Controls cannot become presets, and performance false-positive diagnostics are audited independently of that prohibition.
- Independent runs retain separate estimates. Incompatible host identity, toolchain, sources, recipes, limits, or requested/effective controls prevents confirmation. Side-by-side reports label incompatibility and never pool samples. Legacy 0.2 reports remain readable with explicitly unverified legacy host identity.
- Structured records, shortest-path graph routing, and log analytics each compile four translation units with real inter-module calls. Independent Python parsing/serialization and graph oracles supply expected outputs. Every application has empty, small, alternate, performance, training, and confirmation cases. Input generation is outside compute timing; parsing, construction, algorithms, aggregation, serialization, and result hashing remain timed. LTO and program-specific PGO work across these sources.
- CLI/reporting adds host summaries, control series, preserved regression diagnostics, independent-run comparisons, detailed gate outcomes, and a source-hash-linked gate audit. Failed/interrupted experiments preserve samples already collected. Report/audit outputs cannot overwrite their input results.

The manifest supports additional source/header lists and reference dispatch; there is no fixed eight-workload limit. Two more applications can be added without replacing the runner. The three applications are self-contained synthetic programs, not a claim to cover all production software.

## Test and package validation

The final suites ran after independent performance collection finished:

| Check | Result |
|---|---|
| Full Linux suite, `AION_REQUIRE_COMPILER=1` | **96 passed, 79 subtests passed, no skips**, 159.08 s |
| Windows-compatible suite | **83 passed, 13 skipped, 48 subtests passed**, 2.69 s |
| Real discovery and independent confirmation | All 80 workload/configuration combinations correct and measured |
| Cross-run identity and binary reproducibility | Compatible; all 40 fresh final binaries match by SHA-256 |
| CLI recomputation of proposal gates | Saved source-hash-linked audit for both runs; no eligible candidate |
| Isolated AION 0.3 wheel smoke | Passed; all eight workloads bundled; real compilation, six-case correctness, and calibrated execution of all three new applications |

JUnit records and final transcripts are `.aion/validation/phase3-{linux,windows}-tests.{xml,log}`. Windows skips cover the absent native Clang toolchain, Linux affinity/worker and POSIX resource/process capabilities, and unavailable compiler-driver symlink privilege. Linux exercises the optional PGO and LTO integrations with no skips.

The wheel is `.aion/wheels/aion_network-0.3.0-py3-none-any.whl`, SHA-256 `20d97a18736a1eaf90e6b0531c5b05593c9668b7072d1522432647712694d0ac`. It was built using pip's isolated build backend and installed with `--no-index --no-deps` into `.aion/wheel-smoke-phase3`. Running from `/tmp` asserted that imports and every bundled source/header came from that target, then passed a real Clang probe and all three multi-file application builds/correctness checks. [Smoke metadata](../.aion/validation/phase3-wheel-smoke.json) identifies separate result `20261031T002119-75c967731c` under `.aion/wheel-smoke-phase3-evidence`; its three single measurements are packaging validation, not improvement evidence.

Coverage includes real C++ compilation at O3/O2/unroll across all eight workloads; all input cases; repeated-batch timing; multi-file PGO training and held-out verification; multi-file LTO; actual child affinity and failure paths; actual slowdown timing with unchanged checksum; host metadata; synthetic false-positive/negative controls; incompatible-run and preset rejection; 0.2 report compatibility; partial-evidence preservation; and existing CLI/storage/resource behavior. Synthetic fixtures test decisions only and are never presented as real measurements.

GitHub Actions was **not executed**. This workspace has no `.git` repository/configured GitHub remote, and `gh` is unavailable. The Linux workflow was updated to exercise the eight-workload suite and affinity on its runner. Local test results do not stand in for a successful GitHub Actions run.

## Eight-workload discovery and confirmation

Both runs compare O3 with O2, LTO, PGO, and PGO+LTO using eleven measured pairs per candidate, two warmups, and verified guest CPU 0. Training seed 271828 is separate from both measured seeds. Forty fresh final binary hashes match across runs, including all baselines; profiles are independently regenerated, not copied between experiments. Compatibility checks pass with no required identity unavailable, and no raw samples are pooled.

| Evidence | Discovery | Held-out confirmation |
|---|---|---|
| Run ID | `20261030T234834-de3eb6de82` | `20261031T000202-01808fcd04` |
| Scheduling/bootstrap seed | 53300 | 53301 |
| Measured input seed | 42 | 314159 |
| Correct/measured workload configurations | 40/40 | 40/40 |
| Correct measured executions | 704/704 | 704/704 |
| Verified pinned executions | 704/704 | 704/704 |
| Correct warmups | 128/128 | 128/128 |
| Discarded correctness-checked pilots | 243 | 240 |
| Samples inside 250–500 ms | 667/704 | 685/704 |
| Configuration median compute range | 238.0–466.9 ms | 240.6–404.9 ms |
| Fresh workload-specific PGO builds | 16 | 16 |
| Noisy overall configuration summaries | 34/40 | 34/40 |
| Drifting overall summaries | 6/40 | 4/40 |
| Comparison classifications | 28 inconclusive, 4 no clear change | 28 inconclusive, 3 no clear change, 1 regression |

Across both runs, **1352/1408 samples (96.0%)** are in the duration band. All 56 out-of-band samples remain. Successful discarded-pilot calibration does not guarantee subsequent sample duration on a changing host; below-minimum configuration medians are correctly rejected. The paired subset of baseline samples, rather than the baseline's overall summary alone, determines each candidate's quality gates.

**No candidate is promoted and no main-run improvement or regression is independently verified across both runs.** Records/LTO has a valid confirmation regression (-14.60% paired gain) but inconclusive discovery (-15.76%). Logs/PGO has promising +12.15% / +9.08% point estimates, but both fail variability. Current matrix LTO/PGO+LTO slowdowns also remain inconclusive. Current sorting and matrix use a changed common harness and therefore different fingerprints from the frozen Phase 2 investigation. These are distinct evidence sets, not pooled estimates or identical-source repetitions.

See [the combined performance report](phase3-performance.md), [discovery](phase3-discovery.md), and [confirmation](phase3-confirmation.md) for all eight workloads, intervals, CV, calibration, resources, and exact failed gates. The [evidence audit](../.aion/validation/phase3-evidence-audit.json) records raw-result hashes and counts. The [proposal audit](../.aion/validation/phase3-gate-audit.json) recomputes per-run eligibility without changing evidence. Raw results live in `.aion/phase3/results`.

## Preserved real control and regression evidence

[Control results](phase3-controls.md) retain four experiments and **352 measured executions**. All outputs pass correctness and all A/A/slowdown binaries match their baseline hash. Eight A/A comparisons produce zero false-positive improvement signals: four are consistent with no clear change and four are inconclusive. Three of eight known slowdowns are quality-valid detected regressions; five remain inconclusive. Pinning did not consistently remove host variability, and this small series does not establish a zero false-positive rate.

[The frozen-source investigation](phase3-investigation.md) retains **264 measured executions** across fresh discovery and confirmation. Source/input fingerprints match both preserved Phase 2 runs. All sixteen diagnostic-versus-timed binary checks match and all configurations pass correctness. Sorting O2/PGO and matrix PGO+LTO slowdowns recur numerically, but unchanged variability/drift gates prevent independent verification across these two runs. Both baseline and PGO+LTO matrix code still contain SIMD multiplication. Static differences are not a proven runtime cause. Original Phase 2 executables were not retained, so exact source reconstruction is explicitly distinguished from original-binary identity.

Raw controls live in `.aion/phase3-controls/results`; the balanced series index is `.aion/phase3-controls/control-series.json`. Regression code, disassembly, pre-link IR, remarks, and raw/merged profiles live in `.aion/phase3-investigation/20261030T232056-0fd3ea38`, with timed JSON under that store's `results` directory. Separate transcripts are in `.aion/validation/phase3-controls.log`, `phase3-investigation.log`, and `phase3-experiment.log`. Phase 2 files remain preserved.

## Threshold preservation

[The threshold audit](../.aion/validation/phase3-threshold-audit.json) compares the current source with the archived 0.2 wheel. `statistics.py` is byte-identical (SHA-256 `9e2af3e31e7924fd88ff737c8cc2de48048987ca5223b4bc4f1950b8eb2a92b8`), and `comparison_for` has identical AST. The 2%/twice-combined-relative-MAD improvement floor, 5% maximum regression, default 5% CV cap, physical minimum duration, drift, uncertainty, correctness, warmups/sample completeness, and independent confirmation remain. No inconvenient measured sample is removed. Program-specific PGO remains ineligible for generic flag-only presets.

## Changed files

New implementation files:

- `src/aion/controls.py`, `host.py`, `provenance.py`, and `reproducibility.py`.
- `src/aion/experiments.py`, `investigation.py`, and `application_reference.py`.
- `src/aion/workloads/application.hpp`; `records/{main,parser,aggregate,format}.cpp` and `records.hpp`; `graph/{main,graph,routing,report}.cpp` and `graph.hpp`; `logs/{main,parser,aggregate,format}.cpp` and `logs.hpp`.

Extended implementation/configuration files:

- `src/aion/{__init__,models,process,_worker,compiler,benchmarks,engine,optimization,verification,reference,registry,report,cli}.py`.
- `src/aion/workloads/{common.hpp,manifest.json}`, `tools/generate_expectations.py`, `pyproject.toml`, and `.github/workflows/ci.yml`.

New tests: `tests/test_host_controls.py`, `test_control_experiments.py`, `test_investigation.py`, and `test_applications.py`. Extended tests: `test_engine.py`, `test_reliable_benchmarking.py`, `test_integration.py`, `test_verification.py`, and `test_cli.py`. Existing tests remain.

Documentation: `README.md`, `ROADMAP.md`, `docs/{architecture,data-formats,validation}.md`, the four required `phase3-{plan,methodology,validation,performance}.md` documents, and supporting control/investigation/discovery/confirmation reports. Raw local evidence and audit/smoke scripts are retained under `.aion`; that directory remains ignored by Git.

## Limits and Phase 4

The development host is Ubuntu 24.04 under WSL2 on an Intel Core i7-8665U, using Python 3.12.3, Ubuntu Clang 18.1.3, GNU ld 2.42, and GCC 13 C++ libraries. Logical affinity does not establish physical-core isolation. Sysfs frequency/governor and thermal readings are unavailable; guest power data is only partial. Host Windows activity, power state, shared resources, and scheduler effects remain uncontrolled. Eleven-pair bootstrap coverage is approximate under nonstationarity. Correctness covers supplied deterministic inputs; build/RSS measurements have their documented scope.

Phase 4 should first replicate A/A and known-slowdown controls across sessions on native Linux, retaining each host identity. Add available hardware/scheduling counters and separate sanitizer validation, broaden input/training distributions, test causal codegen hypotheses, and add two representative applications to reach ten. Keep AI candidate generation deferred until controls demonstrate reliable measurement quality. Native Windows accounting/limits remain future work.

See [the plan](phase3-plan.md), [exact methodology and reproduction commands](phase3-methodology.md), and [the performance report](phase3-performance.md).

## Reproduce validation

From the Ubuntu project directory, after completing performance collection:

```bash
AION_REQUIRE_COMPILER=1 .aion/venv-linux/bin/python -m pytest -q \
  --junitxml=.aion/validation/phase3-linux-tests.xml
.aion/venv-linux/bin/python -m pip wheel . --no-deps --wheel-dir .aion/wheels
.aion/venv-linux/bin/python -m pip install --no-index --no-deps \
  --target .aion/wheel-smoke-phase3 .aion/wheels/aion_network-0.3.0-py3-none-any.whl
```

The isolated smoke script is retained as `.aion/validation/phase3-wheel-smoke.py`. In this checkout it runs from `/tmp`, using `AION_PHASE3_ROOT=/mnt/c/Projects/AION_AI_Optimization_Network` and `PYTHONPATH=/mnt/c/Projects/AION_AI_Optimization_Network/.aion/wheel-smoke-phase3`, with the absolute virtual-environment interpreter path. It asserts that imports and all bundled source/header files come from the installed target, probes Clang, and compiles/checks/measures each of the three applications. Its one sample per application is package validation only and stays separate from performance conclusions.

From the Ubuntu project directory after installing the wheel:

```bash
aion_phase3_root="$PWD"
cd /tmp
AION_PHASE3_ROOT="$aion_phase3_root" \
PYTHONPATH="$aion_phase3_root/.aion/wheel-smoke-phase3" \
"$aion_phase3_root/.aion/venv-linux/bin/python" \
"$aion_phase3_root/.aion/validation/phase3-wheel-smoke.py"
```

Windows PowerShell, from the project directory:

```powershell
$env:TEMP = Join-Path (Get-Location) '.aion\tmp'
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q --junitxml=.aion/validation/phase3-windows-tests.xml
.\.venv\Scripts\python.exe .aion/validation/phase3-evidence-audit.py
```

The final evidence audit records raw JSON SHA-256 values, counts, duration bands, verified affinity, classifications, compatibility, and control verdicts. The report CLI can independently recompute proposal assessments with `--audit-json`, while the registry remains responsible for independent confirmation and publication policy.
