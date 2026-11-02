# AION 0.6 public-release readiness

This milestone keeps version `0.6.0.dev0`. It prepares an experimental source
release and Apple Silicon compatibility; it does not qualify scientific Phase 6.

## Initial audit and checklist

- [x] Inspect source entry points: `aion = aion.cli:main`; MVP commands delegate
  to the existing research, compiler, validation and paired measurement engine.
- [x] Inspect packaging: Python 3.12+, standard-library runtime, pytest developer
  extra, setuptools build backend, bundled trusted C++ sources and JSON inputs.
- [x] Inspect Git: no existing `.git`, history, remote or authenticated GitHub CLI.
- [x] Inspect CI: existing Linux-only workflow; no executed GitHub Actions result.
- [x] Identify local artifacts: `.aion/`, `.venv/`, `build/`, caches and egg-info.
  Preserve these on disk and exclude them from the intended public file set.
- [x] Preserve the existing MIT license. No third-party source directory or
  vendored dependency was found. Maintainers must confirm ownership and rights
  to license all contributions; the existing generic copyright notice alone
  does not establish that chain of ownership.
- [x] Identify portability gaps: Linux MVP execution guard and affinity default,
  unconditional Linux host probes, macOS memory protection, sanitizer options,
  compiler/library/linker provenance and GNU diagnostic tool assumptions.
- [x] Prepare community/security files, ignore rules and public README.
- [x] Implement capability detection, macOS process safeguards and LLVM handling.
- [x] Add portability fixtures and native-Mac-only execution tests.
- [x] Prepare Linux, Windows and ARM64 macOS CI with verified pinned actions.
- [x] Build wheel/sdist and validate an isolated install outside the checkout.
- [x] Run final Linux/Windows suites; real final installed MVP check follows them.
- [x] Audit the intended Git file set, secrets, source bytes and whitespace; retain the final manifest.
- [ ] Perform real Apple M4 testing (requires an actual Mac; remains pending).
- [ ] Publish (requires owner review/authorization; not performed here).

The initial local manifest is retained in `.aion/release-readiness/baseline.json`.
It is not part of the public repository. Historical local scientific evidence
must not be deleted or rewritten during release preparation.

## Available-platform test results

| Check | Actual result |
|---|---|
| Final full Ubuntu/WSL2 Linux suite | 212 passed, 2 native-Mac-only skipped, 97 subtests passed; 838.13 s |
| Final Windows-compatible suite | 193 passed, 21 skipped, 54 subtests passed; 79.21 s |
| Real Clang integration | Passed in the final Linux suite, including the actual MVP CLI pipeline |
| Actual Apple Silicon/M4 execution | Pending; no Mac execution environment was available |
| Hosted GitHub Actions | Not executed; no remote repository or authentication configured |

The final suites include regressions for concurrent-exit memory-limit failure
and honest leak-detector availability. Earlier successful suites and an initial
Windows failure are retained separately. That initial failure expected Linux
topology on Windows; the OS-specific check now has an explicit Linux-capability
skip, with separate tests proving non-Linux hosts do not probe Linux paths.
Unrelated tests were not skipped to conceal failures. Windows compiler/SDK and
POSIX/Linux-only limitations remain explicit in its JUnit skip records.

The current source tree's logs, JUnit XML and command/exit records are in
`.aion/release-readiness/{linux,windows}-tests.*`. These are local retained
evidence, not files bundled into a public clone. The original 0.6 MVP's validation
document and 112/112 measured executions remain historical records.

Git attributes preserve exact source and historical-report bytes, including
existing CRLF files. A new clone must not silently change trusted fingerprints.
The staged blobs are compared to working bytes, and whitespace checks recognize
the retained line endings. No scientific source/report is normalized on disk.
See the [complete changed-file list](release-changes.md).

## Scope of the compatibility implementation

`platform_support.py` makes capability/readiness distinctions explicit;
`darwin_memory.py` implements a sampled aggregate libproc resident-memory
watchdog, not an allocation ceiling or hostile-code sandbox. Missing monitoring
refuses the affected operation. POSIX CPU/file/core limits, wall/output bounds
and process-group termination remain. A recorded memory-limit event is a
verification failure even if a concurrent exit reports status zero.

macOS skips Linux host paths, affinity and perf counters with explicit reasons.
The MVP accepts Darwin execution and records unpinned controls. Separate macOS
and Windows sanitizer runs disable unsupported leak detection explicitly;
Linux requests it without claiming that leak detection was independently
validated. ASan/UBSan checks remain separate from primary timings.

Compiler drivers retain their invocation names. Apple Clang is identified
separately from upstream LLVM. PGO checks major/vendor and Apple build identity.
Tool paths support Homebrew prefixes and explicit environment configuration.
Mach-O, SDK stubs and missing dyld-cache library hashes are reported honestly;
GNU/Linux-only diagnostics never become macOS capability claims.

See [Mac instructions](install-macos-apple-silicon.md) and
[publication commands](github-publication.md). These contain the exact commands
for subsequent owner-authorized publication and real M4 validation. No username,
remote URL, contributor identity or successful cloud/Mac run is invented.

## CI preparation

The workflow declares `ubuntu-24.04`, `windows-latest` and `macos-15`, asserts
ARM64 in the macOS job, installs toolchains/isolated Python environments and runs
tests plus a clean installed-wheel smoke. Windows gets the C++ SDK environment;
its complete MVP remains a WSL operation. Linux/macOS run a bounded MVP smoke,
not the full scientific matrix. Jobs have read-only contents permissions and a
40-minute cap. Checkout credentials are not persisted; no secrets are supplied.

Action commits are pinned to verified official `v7` refs for
[checkout](https://github.com/actions/checkout),
[setup-python](https://github.com/actions/setup-python) and
[upload-artifact](https://github.com/actions/upload-artifact), checked using
`git ls-remote` on October 31, 2026. Dependabot is configured for future action
updates. YAML, all seven Bash blocks and the Windows PowerShell block are
validated locally. **GitHub Actions has not executed**; runner setup and complete
cross-platform behavior remain to be confirmed there. The hosted ARM64 Mac is
not described as M4 validation.

## Packaging, demonstration and publication verdict

Both formats build using the declared isolated backend. The final wheel is
installed with no dependencies from the local archive into a fresh venv outside
the checkout, and tested from an outside working directory. The smoke asserts
the package import is under that venv, verifies the installed console entry,
bundled array/records source paths, real Clang builds and independent outputs,
then runs the installed MVP with one candidate and separate confirmation.

Final installed MVP `mvp-d3f2f25e9be94c48bd88dc2ea891e721` completed with correctness
passed, 30/30 separate differential/ASan/UBSan checks and 136/700 logical commands.
It uses Ubuntu Clang 18.1.3 on WSL2. The fresh two-candidate records demonstration
also completed; its pre-final-guard package/run is retained as an earlier
engineering iteration rather than relabeled as the final package.

**No independently verified improvement found.** None of these functionality
checks validates WSL measurement quality, native physical Linux readiness or
M4 compatibility. Research promotion remains disabled. Exact raw paths, final
archive hashes and stage/source/binary checks are in the local
`.aion/release-readiness/final-audit.json` and evidence index. Local evidence is
not committed or bundled into a public clone.

The intended public tree is staged locally on `main` for review, with no remote,
commit, tag, push or package publication created. The pattern scan found no
credential/private-home-path matches; this is not a proof that every possible
secret is absent. A historical nonpersonal project-checkout path remains in the
unchanged Phase 3 validation record. New installation/publication instructions
use portable paths and owner-supplied repository names.

**Verdict: technically prepared for owner review, with publication decisions
pending.** Confirm source ownership and MIT licensing authority, provide private
security/conduct contacts and choose the actual repository before public push.
There was no preexisting Git history to rewrite or remediate. Actual M4 tests and
hosted CI are pending and must be reported as such. Native scientific validation
remains a separate milestone. See [exact publication commands](github-publication.md),
[exact M4 commands](install-macos-apple-silicon.md), and
[all 51 added/modified public files](release-changes.md).
