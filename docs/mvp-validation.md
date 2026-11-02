# MVP validation

This records the **original MVP build and demos**. Its retained wheel/evidence
identities are historical, not the later release-preparation package. For the
current cross-platform regression results, package checks and pending Mac status,
see [release readiness](release-readiness.md).

The engineering milestone is AION 0.6 MVP Preview (`0.6.0.dev0`). It does not
complete Phase 6 scientific validation. Native Linux remains pending.

## Executed suites

All final suites below ran against the same implementation used by the retained
MVP demos on October 31, 2026.

| Check | Actual result | Retained evidence |
|---|---|---|
| Full Ubuntu/WSL2 Linux suite | 181 passed; 97 subtests passed; 579.70 s | [text](../.aion/mvp-preview/linux-tests.txt), [JUnit](../.aion/mvp-preview/linux-tests.xml) |
| Windows-compatible suite | 163 passed; 18 skipped; 54 subtests passed; 40.07 s | [text](../.aion/mvp-preview/windows-tests.txt), [JUnit](../.aion/mvp-preview/windows-tests.xml) |
| Real compiler integration | Passed in the full Linux suite, including an actual one-command MVP execution with separate validation, discovery and confirmation | Linux suite above; `tests/test_mvp.py` |
| Independent installed wheel | Passed for all ten original workloads, six research variants and a real installed MVP run | [metadata](../.aion/mvp-preview/wheel-evidence/smoke.json), [log](../.aion/mvp-preview/wheel-smoke.txt), [installed MVP report](../.aion/mvp-preview/wheel-evidence/mvp/report.html) |
| Package/evidence compatibility audit | All 22 checks passed; all 88 packaged files match checkout; 41 original C++/header/input files unchanged | [audit](../.aion/mvp-preview/final-audit.json) |
| Generated HTML structural QA | Passed for both demos and the installed-wheel MVP report | [audit](../.aion/mvp-preview/html-audit.json) |
| GitHub Actions | Not executed: this workspace has no configured authenticated repository access | CI workflow updated for future execution |

The 32 added MVP tests include the real Clang CLI integration. Previous tests
remain present. The Windows skips are explicit platform/toolchain restrictions;
they are not reported as passes. No failed test was skipped to make a demo pass.

The independently installed package was imported from
`.aion/wheel-smoke-mvp-preview/aion/`, and its real selected C++ sources were
checked to reside beneath that installed target. Its MVP run
`mvp-ed20c47ac82840e58d24f2100bc7fc6e` completed with 20/20 output-correct measured
executions, four output-correct warmups, 24 ordinary verification checks and
30/30 separate differential/ASan/UBSan checks. This is a functionality/package
smoke, not an independent scientific performance replication. Its 18/20 samples
in the calibration target band do not erase the two outliers.

The [built wheel](../.aion/wheels/aion_network-0.6.0.dev0-py3-none-any.whl) has
SHA-256 `e40d650c3b1ed17acd555bec9159a603874fbdae0dae39705aed60d48bba4e47`.
Build, install and smoke commands/exit codes are retained in
[the package journal](../.aion/mvp-preview/package-validation.json).

The final audit verifies sealed declarations and snapshots, archived executable
and source hashes, separate discovery/confirmation session IDs and seeds, raw
output correctness, full family size, global nested command accounting, explicit
non-AI fallback and disabled promotion/native readiness. It also checks all ten
original workload fingerprints, the prior Phase 4 raw result, Phase 5 study/raw
hashes and wheel, and unchanged bytes for `engine.py`, `statistics.py` and
`optimization.py`. It checks all MVP/README local document links.

HTML QA checks the actual artifacts for both tables, candidate and status text,
prominent no-winner/native-pending messages, restrictive CSP, responsive table
wrappers, a local evidence link and absence of scripts/remote resources. Visual
browser review was **not completed**: Browser Use security policy rejected local
`file:` navigation. No alternate browser surface or workaround was attempted.

Validation covers the closed proposal schema, malicious inputs, deterministic
ranking, explicit fallback, nested budgets, source/plan integrity, discovery-only
selection, correctness failure handling, WSL labels, preset rejection, escaped
reports and real Clang end-to-end execution. All prior 0.5 tests remain.

Run the full Linux suite:

```bash
.aion/venv-linux/bin/python -m pytest -q
```

Run Windows-compatible checks using the project-local writable temp directory:

```powershell
New-Item -ItemType Directory -Force .aion/mvp-preview/tmp | Out-Null
$env:TEMP=(Resolve-Path .aion/mvp-preview/tmp).Path
$env:TMP=$env:TEMP
.venv/Scripts/python.exe -m pytest -q
```

Compiler-dependent tests run in Linux/WSL; explicit Windows SDK/POSIX skips remain
visible. Source/binary/profile identities, exact output checks and all failed
gates remain in actual demo reports. An engineering success is not a speedup or
a validated measurement environment. GitHub Actions is executed only when an
authenticated repository is configured; no remote CI success is inferred from
local tests.

The deterministic records demo and genuine imported AI array demo are documented
in [actual demo results](mvp-demo-results.md). They use separate sanitizer and
differential validation before primary measurements. Each selected panel has a
fresh confirmation session with a different seed and held-out inputs. Execution
completion does not depend on the statistical gates passing.

## Implementation changes

| Files | Change |
|---|---|
| `src/aion/mvp.py`, `mvp_cli.py` | User workflow, sealed plans, approval, journal, global budget and existing-engine orchestration |
| `src/aion/mvp_catalog.py`, `mvp_proposals.py`, `mvp_context.py` | Trusted IDs for all ten workloads, deterministic ranking, strict AI import and bounded discovery-only context |
| `src/aion/mvp_report.py` | JSON/Markdown/standalone HTML, uncertainty, actual AI usage, failed gates and separate scientific readiness |
| `src/aion/cli.py`, `report.py` | CLI registration and report-kind dispatch |
| `src/aion/research.py`, `research_catalog.py`, `research_diagnostics.py` | Explicit trusted catalog provider, frozen selected subset, source checks and catalog traversal reuse |
| `src/aion/budget.py`, `benchmarks.py` | Parent budget accounting and reduced repeated filesystem traversal |
| `src/aion/__init__.py`, `pyproject.toml` | Preview version `0.6.0.dev0` |
| `tests/test_mvp.py` | 32 additional tests, including the actual compiler CLI integration |
| `tools/wheel_smoke.py`, `.github/workflows/ci.yml` | Installed preview workflow check and updated CI package name/time allowance |
| `README.md`, `ROADMAP.md`, `docs/architecture.md`, `docs/data-formats.md` | Entry points and additive engineering-preview documentation |
| `docs/mvp-{overview,quickstart,architecture,validation,demo-results}.md` | The five requested MVP documents |

Original C++ workloads, research variants and inputs are retained. The existing
statistical implementation and preset-promotion thresholds are unchanged. The
31-entry preview family does not replace the original 17-entry research family.
