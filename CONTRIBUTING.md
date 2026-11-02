# Contributing to AION

AION 0.6 is an experimental research prototype. Contributions should improve
correctness, portability, reproducibility or clarity without turning a noisy
local result into a verified speedup.

Use Python 3.12+ and Clang with a C++17 library/linker. Create an isolated Python
environment and run `python -m pip install -e '.[dev]'`. See the
[Apple Silicon guide](docs/install-macos-apple-silicon.md) for macOS toolchains.
Keep Windows and WSL virtual environments separate.

Trusted source/input files and historical reports retain their exact existing
bytes through `.gitattributes`. Avoid incidental newline normalization; intentional
source changes need fresh fingerprints, contexts and experiment declarations.

Run `python -m pytest -q`. Compiler tests require a working C++ toolchain;
`AION_REQUIRE_COMPILER=1` makes missing baseline compiler support a failure.
Platform-specific tests explain each skip. Do not skip unrelated failures.
An optional sanitizer/recipe can be unsupported, but preserve its exact reason.

Changes to execution must retain timeouts, output limits, supported memory/CPU
protections, shell-free arguments, trusted candidate boundaries and evidence of
partial failures. These controls are not a security sandbox for arbitrary code.
Never execute imported model code or commands. AI proposals select trusted IDs.

Keep correctness instrumentation separate from primary timing. Preserve raw
samples, checks, provenance, uncertainties and unsuccessful experiments. Do not
weaken quality or preset-promotion gates, pool incompatible evidence, select
from held-out confirmation or retry until an experiment looks successful.
Native scientific readiness requires its separate existing protocol.

Before submitting, run `git diff --check`, review `git diff`, and run the
[public-tree audit](docs/github-publication.md). Keep local `.aion/` data,
virtual environments, compiler outputs, credentials and private paths out of
commits. Supply a redacted minimal reproduction rather than an unreviewed raw
report. CI tests compatibility, not scientific measurement stability.

Explain the problem, resulting behavior, validation and remaining limits in the
pull request. You must have the right to contribute your changes under the
existing [MIT license](LICENSE). No contributor identity or ownership is inferred
from automated generation. See [security reporting](SECURITY.md) and our
[code of conduct](CODE_OF_CONDUCT.md).
