# Local validation record

The latest implementation and real experiments are documented in [Phase 4 validation](phase4-validation.md), [performance](phase4-performance.md), and [measurement quality](phase4-quality.md). Phase 2–3 validation/performance records remain preserved, including [Phase 3 validation](phase3-validation.md). The record below preserves the Phase 1 validation history.

Validation date: October 30, 2026.

## Available environment

- Ubuntu 24.04 under WSL2, Python 3.12.3.
- Ubuntu Clang 18.1.3, target `x86_64-pc-linux-gnu`, with GCC 13.3.0 C++ libraries/build tools.
- Intel Core i7-8665U, eight logical CPUs. This is a shared laptop environment; CPU power state, temperature, and background activity are not controlled.
- Separate Linux environment: `.aion/venv-linux`. The existing `.venv` remains the Windows Python 3.12.10 environment.

**The real end-to-end workflow now passes:** detect Clang, compile C++, verify expected outputs, measure repeated executions, save JSON, and generate Markdown reports. The initial missing-compiler limitation has been resolved in Ubuntu. Both recorded experiments completed without correctness failures.

| Check | Result |
|---|---|
| Ubuntu/WSL pytest suite, compiler required | **49 passed, no skips** |
| Additional Ubuntu correctness subtests | 48 passed |
| Windows pytest regression suite | 43 passed, 6 skipped; 33 subtests passed |
| Linux editable installation and compiler diagnostic | Passed; Clang compile/link/run probe reports `ready: true` |
| Rebuilt wheel, installed in a separate target | Import and all five bundled workloads verified; real Clang probe reports `ready: true` |
| Real baseline-versus-O2 experiment | All 10 workload/configuration combinations correct and measured |
| Real optimization discovery | All 25 workload/configuration combinations correct and measured |
| Preset promotion | No candidate qualified; no preset created |

The Linux integration tests compile all five workloads under `-O3`, `-O2`, and `-O3 -funroll-loops`, verify all four input cases, and run a real baseline/candidate measurement test. `AION_REQUIRE_COMPILER=1` makes unavailable compilation fail rather than skip. The Windows skips cover its missing native Clang, three POSIX resource tests, and unavailable permission to create the driver-symlink regression fixture. Windows validation uses `.aion/tmp` because the execution sandbox restricts the default temporary directory.

## Recorded experiments

Both experiments use eleven measured iterations and two warmups per workload/configuration, with identical inputs and correctness expectations across configurations.

| Experiment | Run ID | Schedule seed | Report |
|---|---|---:|---|
| `-O3` versus `-O2`, all five workloads | `20261030T123345-9ecf069f39` | 1729 | [Baseline comparison](baseline-comparison.md) |
| `-O3` versus all four allowlisted alternatives | `20261030T123456-4e1256c7c0` | 1730 | [Optimization comparison](optimization-comparison.md) |

Raw JSON and matching reports live under `.aion/results/<run-id>.json` and `.md`. JUnit test records and the successful compiler diagnostic live under `.aion/validation/`.

The updated wheel is `.aion/wheels/aion_network-0.1.0-py3-none-any.whl` (SHA-256 `110dfc0cfd345aacc7c4c6ff047e6dd5a58e9e796117df8077a01ddb3fbe4fe0`). Its separate installation under `.aion/wheel-smoke-linux` was tested without importing the source checkout. The wheel compiler diagnostic is saved as `.aion/validation/linux-wheel-doctor.json`.

No candidate satisfied the promotion criteria. The discovery run found regressions for `-Os` on array/string processing and for disabled vectorization on array/string processing. Apparent small improvements did not clear the conservative noise floor. Hash-map measurements were too variable; the baseline matrix workload was about 13 ms, below the 20 ms minimum for trustworthy classification. The baseline experiment likewise found no clear O2 improvement. All these outcomes are retained, including inconclusive results.

Because no candidate qualified, no independent confirmation or preset re-verification run was needed. Those gates remain covered by automated workflow tests. There is no claimed speedup or fabricated preset. The two experiments have different timing conditions; compare configurations within each run, not absolute medians across runs.

## Compiler fix discovered by real validation

The first real probe exposed an adapter bug: resolving Ubuntu's `clang++` symlink changed the invoked driver to `clang`, which omitted automatic C++ library linking. The adapter now preserves the absolute driver invocation name. A regression test reproduced the failure before the fix; the complete Linux suite and real experiments pass with the fix.

## Reproduce in the Ubuntu project directory

```bash
source .aion/venv-linux/bin/activate
AION_REQUIRE_COMPILER=1 python -m pytest -q
aion doctor --json
aion benchmark --benchmark all --candidate o2 --iterations 11 --warmups 2
aion report --latest --output docs/baseline-comparison.md
aion optimize --benchmark all --iterations 11 --warmups 2 --seed 1730
aion report --latest --output docs/optimization-comparison.md
```

The next engineering milestone is to lengthen/calibrate short workloads and collect evidence under steadier CPU conditions before attempting to promote improvements. Keep the noise and verification thresholds intact. GitHub Actions requires real compiler coverage, but the workflow has not been executed on GitHub in this workspace.

Historical note: on October 29, before the toolchain installation, Ubuntu reported 46 passing tests with two compiler skips; Windows reported 43 passing tests with five skips. Today's Ubuntu results replace that initial compiler limitation.
