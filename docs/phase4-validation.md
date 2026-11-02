# Phase 4 local validation

AION 0.4 implements native replication support, runtime profiling, separate sanitizer validation, cross-session measurement-quality studies, and ten workloads. The available development environment is Ubuntu 24.04 under **WSL2**, not native Linux. Native performance validation remains pending. No AI optimizer, cloud requirement, privileged system tuning, remote execution, or autonomous source rewriting is added.

## Executed tests

| Check | Result |
|---|---|
| Full Linux suite, compiler required | **133 passed, 97 subtests passed, no skips**, 179.54 s |
| Windows-compatible suite | **118 passed, 15 skipped, 54 subtests passed**, 4.13 s |
| Separate ten-workload differential/ASan/UBSan pipeline | **30 builds and 312 checks passed** |
| Preserved Phase 3 compiler profiles | **24/24 final binary hashes match**; **72/72 counter executions pass** |
| Optional counter observations | **648/648 counted**, all enabled/running fractions 1.0, no multiplexing in these observations |
| Separate sampled profiles | **24 available**, no reported sample loss or buffer overrun |
| Current profiler CLI / strict symbol resolution check | Passed; matching baseline binary and resolution version 2 |
| Independent AION 0.4 wheel smoke | Passed; all ten packaged baselines compile, verify and calibrate; packaged counter helper available |

JUnit and transcripts are `.aion/validation/phase4-{linux,windows}-tests.{xml,log}`. Windows skips cover missing native Clang, Linux counter/affinity/worker capabilities, POSIX resource/process support, and compiler-driver symlink privilege. Linux exercises real multi-file compilation at O3/O2/unroll, LTO for all five applications, PGO for sorting and the five applications, actual affinity, counters/sampling, and sanitizer error fixtures. Synthetic fixtures test native/VM detection, permissions, multiplexing, missing events, control failures, cross-session compatibility/readiness and symbol-resolution failures; they are never presented as native or hardware performance measurements.

The final suite also checks graceful rejection of malformed diagnostic report JSON. No workload or statistical logic changed after scientific collection. A real native-required preflight [refuses this WSL2 environment](../.aion/phase4-native-check/required-native.json) while preserving local-validation readiness; it does not turn guest evidence into native evidence.

The profiler output-directory change is also covered by the real CLI check `.aion/phase4-profile-check/results/20261031T024755-ad47c08bbf.json`. This contains one counter and one sampled run, kept separate from the 72/24 investigation totals. It verifies source/binary/placement identity and function-range resolution in the current code.

## Correctness validation

The saved sanitizer/differential record is [20261031T022349-7594ef3329](../.aion/phase4-validation/results/20261031T022349-7594ef3329.json), with [its report](../.aion/phase4-validation/results/20261031T022349-7594ef3329.md). Each original workload has ten cases per mode and each new application twelve. The pipeline performs **104 O3 differential checks, 104 ASan checks, and 104 UBSan checks**, all passed. Each application compiles four real translation units. Healthy sanitizer probes work; separate trusted error fixtures confirm that actual ASan/UBSan errors are detected. A detected diagnostic fails validation even if an execution otherwise appears successful.

Additional cases include singleton, wrapping round seeds, larger inputs, fresh seeds, flat/checkerboard images and hotspot/sequential key/value access. All expected outputs come from independent Python implementations. The separate validation manifest leaves the original eight timing source/input fingerprints intact. Sanitizer shadow-memory address-space exceptions are explicit diagnostic settings; primary timing still uses the normal 1024 MiB limit. No instrumented timing is compared as an optimization result.

## Real profiling and compiler investigation

[The investigation](phase4-investigation.md) covers records/LTO, logs/PGO, and matrix LTO/PGO+LTO against both preserved Phase 3 input datasets. All hardware/software event observations here are guest-visible WSL2 observations. Six hardware-type events and three software-type events were available: 432 hardware-type and 216 software-type observations across 72 executions. Linux wait4 resource accounting is recorded separately. Unsupported/denied event behavior is tested; no permission or kernel policy was changed.

All configurations use equal total work within each profile and retain the source timing batch counts/sample identities. Final disassembly, pre-link IR, remarks, training/profile provenance and binaries are retained. Sampling is a separate execution. Symbol audits preserve original IPs and source hashes while requiring sized function ranges: older nearest-symbol guesses from stripped libraries are not named-function evidence. No profiler-only result can create a preset. Counter differences and hypotheses are explicitly separated from primary timing validity and causal conclusions. The default CLI user was independently checked as UID 1000; [permission context](../.aion/validation/phase4-counter-permission-context.json) records the unprivileged observation and existing paranoid value 2.

## Two-session timing and measurement quality

The predeclared study uses separate CLI processes and two explicitly delimited WSL2 observation windows. Session A runs balanced pinned/unpinned controls with seeds 64100/64101, then ten-workload discovery with seed 64300/input 42. Session B repeats controls with 64200/64201, then held-out confirmation with 64400/input 314159. Both use eleven measured pairs, two warmups, unchanged gates and independently trained PGO seed 271828. Session labels alone do not establish statistically independent physical conditions.

Exact commands are in [methodology](phase4-methodology.md); commands/exit statuses/timestamps are journaled in `.aion/validation/phase4-sequence.json`. Raw controls are separate under `.aion/phase4-controls-{a,b}/results`, primary timing under `.aion/phase4/results`. The final [performance report](phase4-performance.md) and [measurement-quality report](phase4-quality.md) record actual totals, duration validity, all failed gates and scoped readiness. No primary timings are pooled. Inconclusive controls and out-of-band measurements remain evidence, not discarded attempts.

## Compatibility and threshold audit

The two-session study completed successfully with all journaled stage exit codes zero. Main discovery `20261031T025701-07d35075c3` and held-out confirmation `20261031T032139-5ccfa44eff` use different explicit session IDs, scheduling seeds 64300/64400 and input seeds 42/314159. Recorded compatibility checks pass with no required identity unavailable; all 50 independent final binary hashes match.

| Main timing evidence | Discovery | Confirmation |
|---|---:|---:|
| Correct verified configurations | 50/50 | 50/50 |
| Correct measured executions / verified guest affinity | 880/880 | 880/880 |
| Correct warmups | 160/160 | 160/160 |
| Correct discarded pilots | 300/300 | 300/300 |
| Samples inside 250–500 ms | 871/880 | 878/880 |
| Configuration median duration range | 277.0–384.4 ms | 282.5–374.4 ms |
| Noisy overall summaries | 35/50 | 17/50 |
| Drifting overall summaries | 2/50 | 1/50 |
| Fresh program-specific PGO builds | 20 | 20 |

Across main runs, **1749/1760 samples (99.4%)** meet the target band; all eleven outside remain. All configuration medians meet the minimum duration. Records/LTO passes the repeated regression classification (-15.16% / -14.16% paired gain). No improvement passes independent confirmation. Sorting/LTO and records/O2 improve only in confirmation; logs/PGO remains inconclusive. The image and key/value additions pass correctness across all five configurations; their performance findings remain separately gated. All four recipes fail per-run proposal eligibility in both runs. No preset was created.

The eight control runs retain **1056 measured executions**, all correct. There are zero false A/A improvement signals in 24 comparisons (14 consistent with no clear change, ten inconclusive) and **18 detected known slowdowns out of 24**, with six inconclusive. Each pinned/unpinned stratum has 0/12 false gains and 9/12 detections; conditional detection is 9/9 among quality-valid negative controls. Approximate Wilson intervals are wide and within-session/workload dependence limits coverage. There is no established universal false-positive rate or demonstrated stability benefit from pinning.

[Measurement-quality readiness](phase4-quality.md) reports validation passed on the available environment, complete two-session designs and compatible validation sources, but **measurement-quality checks failed** due to inconclusive controls. Native evidence and native performance validation remain unavailable. [The performance report](phase4-performance.md) and [evidence audit](../.aion/validation/phase4-evidence-audit.json) retain all classifications, gates, source hashes and counts; [the proposal audit](../.aion/validation/phase4-gate-audit.json) recomputes eligibility. No samples are pooled.

[The preservation audit](../.aion/validation/phase4-threshold-audit.json) checks against the exact 0.3 wheel (SHA-256 `20d97a18736a1eaf90e6b0531c5b05593c9668b7072d1522432647712694d0ac`). The statistics module remains byte-identical (SHA-256 `9e2af3e31e7924fd88ff737c8cc2de48048987ca5223b4bc4f1950b8eb2a92b8`), and `comparison_for` has identical AST. All original eight timing fingerprints match their preserved Phase 3 results. Existing Phase 1–3 records are retained and readable; missing old session/native identities are not invented.

The 2%/combined-MAD floor, 5% regression bound, default 5% CV cap, drift, uncertainty, physical duration, correctness, warmup/sample completeness and independent confirmation gates remain. Experimental controls, profiling, sanitizer and package-smoke evidence are rejected for presets. Program-specific PGO cannot become a generic flag-only preset.

## Files changed

New implementation:

- `src/aion/{sessions,preflight,evidence,profiling,quality,validation,diagnostic_report,expanded_reference}.py`.
- `src/aion/helpers/perf_runner.cpp`.
- `src/aion/workloads/image/{main,filter,edges,format}.cpp`, `image.hpp`.
- `src/aion/workloads/kv/{main,store,process,format}.cpp`, `kv.hpp`.
- `src/aion/workloads/validation.json`.

Extended implementation/configuration: `src/aion/{__init__,host,engine,experiments,reproducibility,compiler,models,_worker,registry,cli,reference,report}.py`, `workloads/manifest.json`, `pyproject.toml`, `.github/workflows/ci.yml` and `tools/generate_expectations.py`. New tracked tools are `tools/replicate_linux.py` and `tools/wheel_smoke.py`. The original eight C++ workloads and shared headers remain unchanged.

New tests: `tests/test_{replication,profiling,sanitizers,expanded_applications,quality,phase4_cli}.py`. Extended tests: `test_applications.py`, `test_verification.py`, `test_reliable_benchmarking.py` and `test_integration.py`. Documentation includes the six required Phase 4/native/counter files, supporting investigation/quality/detail reports, README, roadmap, architecture, aggregate validation links and data formats. Local raw evidence/audit scripts stay under ignored `.aion`.

## Native Linux, CI and Phase 5

Only WSL2 distributions are available here. No real native Linux performance experiment was executed, and native validation is **not complete**. Logical CPU 0 is not physical-core isolation. Sysfs frequency/governor and thermal observations remain unavailable; power observations are partial. Guest PMU events do not remove virtualization, power, scheduling, cache-history or shared-resource uncertainty. Start/end snapshots do not establish continuous stability. Counter/sampling/profile series have their stated scope and uncertainty limits.

GitHub Actions was **not executed**: there is no Git repository/configured remote in this workspace, no `gh`, and no configured GitHub credential environment. The updated workflow tests all ten workloads, separate sanitizers, optional counter preflight and an independently installed wheel; local results are not cloud CI results.

Phase 5 should prioritize the [native replication workflow](native-linux-benchmarking.md), additional sessions/control counts, broader held-out distributions and one-factor tests of the documented compiler hypotheses. Full native ten-workload timing and quality review remain separate from scoped control readiness. Keep AI candidate generation deferred until evidence quality justifies it; no reliable speedup is required for Phase 4 implementation success.

## Reproduce tests and packaging

Linux, after all scientific collection finishes:

```bash
AION_REQUIRE_COMPILER=1 .aion/venv-linux/bin/python -m pytest -q --junitxml=.aion/validation/phase4-linux-tests.xml
.aion/venv-linux/bin/python -m pip wheel . --no-deps --wheel-dir .aion/wheels
.aion/venv-linux/bin/python -m pip install --no-index --no-deps --target .aion/wheel-smoke-phase4 \
  .aion/wheels/aion_network-0.4.0-py3-none-any.whl
aion_phase4_root="$PWD"
cd /tmp
"$aion_phase4_root/.aion/venv-linux/bin/python" "$aion_phase4_root/tools/wheel_smoke.py" \
  --target "$aion_phase4_root/.aion/wheel-smoke-phase4" --store "$aion_phase4_root/.aion/wheel-smoke-phase4-evidence"
```

The isolated pip build backend is used because the local runtime environment need not contain setuptools. The built wheel is `.aion/wheels/aion_network-0.4.0-py3-none-any.whl`, SHA-256 `6245f4b17d45e7123ba776a0de771412feb99f51f630a5111988b40a19189efc`. It was installed using `--no-index --no-deps` into `.aion/wheel-smoke-phase4` and tested from `/tmp`. Imports resolve to that installed target. All ten packaged source/header sets and the packaged counter helper are present; all ten baseline builds, six-case correctness groups, calibration and single measured executions pass. Counter-helper execution also succeeds.

The [smoke record](../.aion/wheel-smoke-phase4-evidence/smoke.json) identifies result [20261031T074850-6bab6054a3](../.aion/wheel-smoke-phase4-evidence/results/20261031T074850-6bab6054a3.json). These ten single samples are typed `package-smoke`, cannot promote presets and are separate from the 1760 main measurements. [The package audit](../.aion/validation/phase4-package-audit.json) verifies source payload, wheel and smoke hashes. The wheel contains the tested implementation, with no runtime Python dependencies.

Windows PowerShell:

```powershell
$env:TEMP = Join-Path (Get-Location) '.aion\tmp'
$env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q --junitxml=.aion/validation/phase4-windows-tests.xml
```
