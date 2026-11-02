# Complete release-preparation change list

Compared with the existing 0.6 MVP Preview checkout before this milestone. The
version remains `0.6.0.dev0`. No new optimization algorithm is introduced.

## Added public files

- [.gitattributes](../.gitattributes)
- [.github/ISSUE_TEMPLATE/bug_report.md](../.github/ISSUE_TEMPLATE/bug_report.md)
- [.github/ISSUE_TEMPLATE/experiment_report.md](../.github/ISSUE_TEMPLATE/experiment_report.md)
- [.github/dependabot.yml](../.github/dependabot.yml)
- [.github/pull_request_template.md](../.github/pull_request_template.md)
- [CHANGELOG.md](../CHANGELOG.md)
- [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [MANIFEST.in](../MANIFEST.in)
- [SECURITY.md](../SECURITY.md)
- [docs/github-publication.md](../docs/github-publication.md)
- [docs/install-macos-apple-silicon.md](../docs/install-macos-apple-silicon.md)
- [docs/release-changes.md](../docs/release-changes.md)
- [docs/release-readiness.md](../docs/release-readiness.md)
- [src/aion/darwin_memory.py](../src/aion/darwin_memory.py)
- [src/aion/platform_support.py](../src/aion/platform_support.py)
- [src/aion/toolchain.py](../src/aion/toolchain.py)
- [tests/test_macos.py](../tests/test_macos.py)
- [tests/test_release.py](../tests/test_release.py)
- [tools/installed_smoke.py](../tools/installed_smoke.py)
- [tools/public_audit.py](../tools/public_audit.py)

## Modified public files

- [.github/workflows/ci.yml](../.github/workflows/ci.yml)
- [.gitignore](../.gitignore)
- [README.md](../README.md)
- [ROADMAP.md](../ROADMAP.md)
- [docs/architecture.md](../docs/architecture.md)
- [docs/data-formats.md](../docs/data-formats.md)
- [docs/mvp-architecture.md](../docs/mvp-architecture.md)
- [docs/mvp-demo-results.md](../docs/mvp-demo-results.md)
- [docs/mvp-quickstart.md](../docs/mvp-quickstart.md)
- [docs/mvp-validation.md](../docs/mvp-validation.md)
- [pyproject.toml](../pyproject.toml)
- [src/aion/_worker.py](../src/aion/_worker.py)
- [src/aion/compiler.py](../src/aion/compiler.py)
- [src/aion/controls.py](../src/aion/controls.py)
- [src/aion/host.py](../src/aion/host.py)
- [src/aion/investigation.py](../src/aion/investigation.py)
- [src/aion/models.py](../src/aion/models.py)
- [src/aion/mvp.py](../src/aion/mvp.py)
- [src/aion/process.py](../src/aion/process.py)
- [src/aion/profiling.py](../src/aion/profiling.py)
- [src/aion/research_catalog.py](../src/aion/research_catalog.py)
- [src/aion/research_diagnostics.py](../src/aion/research_diagnostics.py)
- [src/aion/validation.py](../src/aion/validation.py)
- [src/aion/verification.py](../src/aion/verification.py)
- [tests/test_mvp.py](../tests/test_mvp.py)
- [tests/test_process.py](../tests/test_process.py)
- [tests/test_replication.py](../tests/test_replication.py)
- [tests/test_research.py](../tests/test_research.py)
- [tests/test_verification.py](../tests/test_verification.py)
- [tools/wheel_smoke.py](../tools/wheel_smoke.py)

## Preservation and local state

- Existing `LICENSE` is preserved byte-for-byte (MIT); ownership/authority still needs owner review.
- No original source file is deleted. Original C++/header/input contracts and statistical/promotion engines are preserved.
- Historical Phase 1–5 documents and raw scientific evidence remain intact.
- Local Git is initialized on `main`; no remote, commit, tag or publication is created by this task.
- Ignored generated logs, test XML, package archives, retained iterations and integrity manifests are in `.aion/release-readiness/`.
- Development environments received declared build/YAML tools; these are development dependencies, not runtime dependencies.
