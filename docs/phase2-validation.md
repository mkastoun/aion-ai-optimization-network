# Phase 2 validation — October 30, 2026

AION 0.2's calibrated computation pipeline completed real discovery and independent confirmation on all five workloads. Correctness passed throughout. **No candidate met the unchanged suite-wide preset-promotion requirements.** Most comparisons remain limited by host variability; some confirmation results detect regressions rather than gains.

## Environment and tests

- Ubuntu 24.04 / WSL2, Python 3.12.3, Clang 18.1.3, matching LLVM profiling tools, Intel Core i7-8665U.
- Full Linux suite: **70 passed, no skips**, with 49 additional passing subtests.
- Windows regression suite: **62 passed, 8 skipped**, with 34 passing subtests. Skips cover the missing native C++ toolchain, POSIX resource/metadata tests, and driver-symlink permissions.
- Real integration coverage includes all workload correctness cases at O3/O2/unroll, repeated-batch timing protocol checks, calibrated paired measurement, and instrument/train/merge/rebuild PGO compilation.
- New unit coverage includes calibration bounds/failures, setup/timing validation, normalized work, matched balanced pairs, block-bootstrap uncertainty, drift/outlier diagnostics, held-out confirmation, strict promotion limits, PGO preset rejection, and legacy report/CLI workflows.
- An output-limit race exposed by testing was fixed: POSIX supervisor metadata is now published atomically and incomplete metadata becomes a recorded process failure.

JUnit records: `.aion/validation/phase2-linux-tests.xml` and `phase2-windows-tests.xml`. The experiment transcript is `.aion/validation/phase2-experiment.log`. GitHub Actions has not been run from this workspace.

The AION 0.2 wheel was built and installed separately under `.aion/wheel-smoke-phase2`, with an assertion that imports came from the installed wheel. A real calibrated matrix compilation/correctness/measurement smoke test passed from that installation. Its single sample is packaging validation only, not improvement evidence, and is stored separately under `.aion/wheel-smoke-evidence`. The wheel is `.aion/wheels/aion_network-0.2.0-py3-none-any.whl` (SHA-256 `58dbec0c718f7be6c450288c391b8dcd232e405167dcebcdbc865f1a39c4f0c8`). After report presentation changes, the 35 affected report/CLI/orchestration tests also passed.

## Real experiments

Both runs compare O3 against O2, O3+LTO, O3+PGO, and O3+PGO+LTO. Existing size/unroll/scalar candidates remain available. Every run uses eleven measured pairs per candidate and two warmup pairs. Separate training seed 271828 produces fresh profiles; training output is independently checked and is not timed as a performance result.

| Evidence | Discovery | Independent confirmation |
|---|---|---|
| Run ID | `20261030T133332-5c960dc216` | `20261030T134127-a9b702d915` |
| Scheduling/bootstrap seed | 42217 | 42218 |
| Measured input seed | 42 | 314159 |
| Correct workload/configuration combinations | 25/25 | 25/25 |
| Successful calibration | 25/25 | 25/25 |
| Discarded correctness-checked calibration pilots | 150 | 153 |
| Measured executions | 440 | 440 |
| Measured executions within 250–500 ms | 435/440 | 405/440 |
| Configuration median compute duration range | 289.478–387.214 ms | 246.154–393.417 ms |
| Fresh workload PGO builds | 10 | 10 |

Across both runs, **840 of 880 measured executions (95.5%)** fall in the target band. All measured and pilot outputs pass correctness. Forty out-of-band measurements are retained, not discarded. One confirmation configuration median is slightly below 250 ms and is treated as insufficient duration by the strict Phase 2 gate. Calibration cannot prevent subsequent host speed changes.

Raw JSON remains in `.aion/results/<run-id>.json`, with detailed sidecar reports. [The combined performance report](phase2-performance.md) pairs both runs' gains and uncertainty bounds; [discovery details](phase2-discovery.md) and [confirmation details](phase2-confirmation.md) retain calibration, durations, resources, flags, and diagnostics.

## Findings and limits

No repeatable improvement qualifies for a preset. In confirmation, O2 and PGO sorting are about 10.7–10.8% slower by the paired median effect; combined PGO+LTO sorting is about 7.9% slower. Their adjusted intervals and CV checks classify those confirmation observations as regressions. Discovery sorting measurements are noisier, so this is not a universal or suite-wide performance claim. Other apparent changes are inconclusive or fail the improvement floor.

Longer compute samples fix Phase 1's short matrix measurement problem, but they do not remove OS scheduling, thermal/power variability, shared-host activity, or allocator effects. CV and median drift still block many comparisons. Circular block-bootstrap intervals are empirical approximations, particularly with eleven pairs; the square-root block length is a heuristic. The Bonferroni adjustment does not guarantee exact coverage when bootstrap assumptions fail.

Single-translation-unit toy workloads also do not characterize the full benefit of LTO on multi-file applications. PGO profiles belong to their training program and cannot be published as reusable flag-only presets for unrelated applications. No AI optimization or remote execution was introduced.

The next engineering milestone is controlled CPU placement/power metadata and steadier-host replication, followed by larger application benchmarks. Keep the current noise, uncertainty, correctness, and confirmation gates intact.

## Reproduce and render

```bash
source .aion/venv-linux/bin/activate
AION_REQUIRE_COMPILER=1 python -m pytest -q
aion optimize --benchmark all --candidate o2 --candidate lto --candidate pgo --candidate pgo-lto \
  --iterations 11 --warmups 2 --seed 42217 --confirm-all
aion report --result .aion/results/20261030T133332-5c960dc216.json \
  --confirmation .aion/results/20261030T134127-a9b702d915.json --output docs/phase2-performance.md
```

New experiments get new IDs. Use those new result paths when rendering their reports; the IDs above reference the preserved experiment described here. See [the methodology](reliable-benchmarking.md) for timing boundaries, unchanged promotion limits, and profiling provenance.
