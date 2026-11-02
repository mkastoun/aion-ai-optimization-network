# Phase 5 validation

Implementation and scientific evidence are assessed separately. Native bare-metal
performance validation is pending: only WSL2 is available on this workstation.

- Final full Linux suite: **149 passed, 97 subtests, no skips**, 383.50 seconds.
  [Log](../.aion/phase5/linux-release-tests.txt), [JUnit](../.aion/phase5/linux-release-tests.xml).
- Final Windows-compatible suite: **132 passed, 17 skipped, 54 subtests**, 25.02 seconds.
  [Log](../.aion/phase5/windows-release-tests.txt), [JUnit](../.aion/phase5/windows-release-tests.xml).
- Independent research fixture rerun: **14 passed**, 113.55 seconds, including
  real Clang variants and measurement-path PGO.
- [Compatibility audit](../.aion/phase5/compatibility-audit.json): all ten original
  source/input fingerprints match Phase 4; `comparison_for` has the same AST as
  the 0.4 wheel; statistics SHA-256 remains
  `9e2af3e31e7924fd88ff737c8cc2de48048987ca5223b4bc4f1950b8eb2a92b8`.
- [Strict native-required preflight](../.aion/phase5/native-required.json):
  `20261031T120252-3e5bfd47bc`, expected exit 2, environment WSL2. Local compiler
  readiness does not satisfy native performance validation.
- [CI availability](../.aion/phase5/ci-availability.json): no `.git` directory,
  `gh` command or GitHub token. GitHub Actions **was not run**; the configured
  workflow's wheel reference is updated to 0.5.
- Original sanitizer/differential record
  [`20261031T121706-e04b194519`](../.aion/phase5/validation/results/20261031T121706-e04b194519.json):
  **30 builds and 312/312 checks passed**, covering all ten workloads.
- Research sanitizer/differential record
  [`20261031T122109-c46b72e281`](../.aion/phase5/research-validation/results/20261031T122109-c46b72e281.json):
  **18 builds and 240/240 checks passed** across six variant/distribution
  combinations and all three modes. Its catalog
  hash binds this correctness evidence to the subsequent declaration.
- Final research declaration: [study.json](../.aion/phase5/study.json), SHA-256
  seal `9baa6754247284b326984df4d14ec2abc8d8e7ed6bf9293c97d22255e5727258`;
  [preserved sources](../.aion/phase5/study.sources/). The earlier unused
  implementation-stage `declaration.json` is retained; the final study uses
  `study.json` exclusively.
- Isolated installed-wheel smoke
  [`20261031T131314-6d702b84b3`](../.aion/phase5/wheel-final-evidence/results/20261031T131314-6d702b84b3.json):
  all ten baseline workloads compile, pass independent checks, calibrate and
  execute; all six research variant/distribution combinations compile and pass
  output and measurement-protocol checks. All imports and bundled sources come
  from `.aion/wheel-smoke-phase5-final`, with no checkout fallback. These single-sample
  package checks are typed `package-smoke`, not performance evidence.
- Wheel: [aion_network-0.5.0-py3-none-any.whl](../.aion/wheels/aion_network-0.5.0-py3-none-any.whl),
  SHA-256 `74f89c165007fe1220b939e846be6483d8f4d098d09c71140fe969b85d37b432`.
  [Package audit](../.aion/phase5/package-audit-final.json): **82/82 package source/data
  files match the checkout**. Build/install/smoke all returned 0 in
  [the package journal](../.aion/phase5/package-sequence-final.json).

Diagnostic-path review found a nested-build-schema compatibility error in the
new counter workflow. It was fixed, and both available/unavailable helper
fixtures passed in [the regression check](../.aion/phase5/diagnostic-fixtures.txt).
The final wheel above includes this correction. The earlier discovery-window
wheel, audit and smoke remain preserved under `.aion/phase5/discovery-wheel/`
and `.aion/phase5/wheel-evidence/`. Timing code, source variants and the sealed
declaration were unchanged by this diagnostic correction.

The first no-isolation wheel build failed because the Linux test venv lacks
setuptools. Its [log](../.aion/phase5/wheel-build-attempt1.txt) and
[journal](../.aion/phase5/package-sequence-attempt1.json) remain intact. The
successful retry used pip's isolated backend, then installed the built wheel
without dependencies or index access. AION itself gained no runtime dependency.

The first expanded Linux run retained 145 passes and two declaration-guard
failures because source files were still being edited while tests ran. Those
failures were preserved in [the initial log](../.aion/phase5/full-linux-tests.txt).
The subsequent complete rerun passed 147 tests; the final release run above adds
the two diagnostic-schema regressions and passes all 149. An earlier sandbox Windows temp-folder
access failure was resolved by using the project-local temp directory below.

Run the full suites from the repository root:

```bash
.aion/venv-linux/bin/python -m pytest -q --junitxml=.aion/phase5/linux-release-tests.xml
```

```powershell
New-Item -ItemType Directory -Force .aion/tmp-phase5 | Out-Null
$env:TEMP=(Resolve-Path .aion/tmp-phase5).Path
$env:TMP=$env:TEMP
.venv/Scripts/python.exe -m pytest -q --junitxml=.aion/phase5/windows-release-tests.xml
```

The project-local Windows temp directory avoids a sandbox temp-folder access
failure; it does not change application behavior. Windows compiler/SDK-dependent
checks retain their explicit skips. Linux runs include real Clang integration.

Research fixtures cover catalog closure, independent ordinary/distribution
expectations, unchanged measurement gates, preset rejection, failure journals,
retry/session restrictions, command/time budgets, foreign-source rejection,
profile freshness and measurement-path training, declaration tampering, source
and input validation coverage, and changed-result hash rejection.

Separate original and research-variant validation commands:

```bash
aion --store .aion/phase5/validation sanitize --benchmark all --cpus auto \
  --session-file .aion/phase5/session-a.json --evidence .aion/phase5/sanitizer-artifacts
aion --store .aion/phase5/research-validation research validate --cpus auto \
  --session-file .aion/phase5/session-a.json
```

ASan explicitly needs an uncapped virtual address space for its shadow mapping;
primary experiments keep their original memory limit. Sanitizer timings are
never optimization evidence. All Phase 1–4 raw evidence is preserved.

GitHub Actions is runnable through the updated 0.5 workflow only in a configured
repository. A local workflow file or local pytest pass is not a remote CI run.

## Research and diagnostic evidence

The [evidence index](../.aion/phase5/final-evidence-index.json) links both complete
17-panel studies, the stratified quality report, research report, pending native
report, original/research validation and both diagnostic records. The
[primary audit](../.aion/phase5/evidence-audit.json) verifies 748/748 measured
executions, 596/596 premeasurement checks, 136/136 warmups and 408/408 pilots.
All 68 archived final executables match timing hashes; all source hashes match
the declared snapshot; all 22 program-specific PGO builds have fresh matching
profiles. Both roles use 1,147/2,500 commands and less than 3,600 seconds.

Separate diagnostics preserve all 68 timing-binary identities, pass another
596 output checks and 204/204 counter executions, and retain 1,836/1,836 counted
unmultiplexed event observations. The [codegen audit](../.aion/phase5/codegen-audit.json)
passes all 280 process/artifact checks for 68 disassemblies and 212 pre-link TU
artifacts. Counters/codegen are not primary timing or causal proof.

There is no independently confirmed optimization improvement. Records/LTO
repeats as a local per-comparison regression; promising discovery-only results
fail independent confirmation gates. The control environment remains
unvalidated, and all native hypotheses remain unsupported under WSL2. See
[performance](phase5-performance.md), [findings](phase5-research-findings.md),
and [native instructions](phase5-native-instructions.md).

[Final release audit](../.aion/phase5/final-audit.json) verifies the wheel SHA,
all 82 package files, declaration/source snapshots, preserved original workload
fingerprints and statistical implementation, unchanged prior Phase 4 evidence,
no research presets, pending native status, final test results and local
documentation links.

## Changed implementation files

- New workflow modules: `budget.py`, `research_catalog.py`, `research.py`,
  `research_cli.py`, `research_reference.py`, `research_diagnostics.py`, and
  `native_report.py` under `src/aion/`.
- New bundled data: five fixed C++ variants/wrappers and `inputs.json` under
  `src/aion/research_sources/`. Original workload files remain unchanged.
- Existing engine/compiler/process/verification modules gain research reference
  overrides, typed evidence, retained probe failures, scoped execution budgets,
  archived builds/profiles and measurement-path training. Normal primary
  experiment behavior and statistics remain unchanged.
- `experiments.py`, `quality.py`, `host.py`, `registry.py`, `cli.py`, `report.py`
  and `diagnostic_report.py` add distribution controls, source/input coverage
  matching, descriptive distributions, hosted-CI exclusion, research preset
  rejection, observation notes and typed reports.
- `tests/test_research.py` adds controlled fixtures and real compiler checks.
  `tools/replicate_linux.py` and `tools/wheel_smoke.py` extend the existing
  workflows. Package version/data and CI wheel references advance to 0.5.
- Required Phase 5 documents, native instructions, README, architecture, data
  formats and roadmap describe the final scope and pending native milestone.
