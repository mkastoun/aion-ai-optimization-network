# macOS Apple Silicon / M4 installation and verification

**Actual macOS and M4 execution remains pending.** These commands match the
implemented CLI; portability fixtures run on other OSes do not verify a Mac.
This is software compatibility validation, not native Linux scientific readiness.

## Clone and install

Use a native ARM64 terminal on the M4. `uname -m` must report `arm64`; a terminal
running under Rosetta can instead install/use an x86-64 Python and toolchain.
Intel Macs use `x86_64`; they are not Apple Silicon verification. No Homebrew
prefix is hardcoded below.

The repository has not been published by this development task. After its owner
publishes, substitute its verified clone URL when prompted:

```bash
read -r "AION_REPOSITORY_URL?Paste the verified repository clone URL: "
git clone "$AION_REPOSITORY_URL" AION
cd AION
uname -m
xcode-select --install
# Finish Apple's installation dialog, or use the already-installed tools.
xcode-select -p
brew install python@3.12 llvm@18
"$(brew --prefix python@3.12)/bin/python3.12" -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
export AION_LLVM_BIN="$(brew --prefix llvm@18)/bin"
export AION_CXX="$AION_LLVM_BIN/clang++"
export PATH="$AION_LLVM_BIN:$PATH"
export SDKROOT="$(xcrun --sdk macosx --show-sdk-path)"
"$AION_CXX" --version
python -c 'import platform; print(platform.machine())'
```

The `read` prompt above uses macOS's default zsh. In bash use
`read -r -p 'Repository clone URL: ' AION_REPOSITORY_URL` instead.
Homebrew's [LLVM 18 formula](https://formulae.brew.sh/formula/llvm@18) is keg-only;
the explicit prefix avoids accidentally selecting `/usr/bin/clang++` (Apple
Clang). Command Line Tools supply the macOS SDK, system linker and libc++.
`SDKROOT` selects that SDK for the local shell and is retained in build provenance.
No global privileged tuning, CPU governor changes or forced linker flags are
needed. Homebrew installation itself is a prerequisite; use its official process
if it is not already installed.

## Run the actual M4 validation

```bash
set -o pipefail
export AION_M4_STORE=".aion/m4-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$AION_M4_STORE"
uname -m | tee "$AION_M4_STORE/architecture.txt"
sysctl -n machdep.cpu.brand_string | tee "$AION_M4_STORE/cpu.txt"
aion doctor --json | tee "$AION_M4_STORE/doctor.json"
aion mvp list
AION_REQUIRE_COMPILER=1 python -m pytest -q \
  --junitxml="$AION_M4_STORE/tests.xml" | tee "$AION_M4_STORE/tests.txt"
aion mvp demo --workload records --strategy deterministic --cpus none \
  --compiler "$AION_CXX" --output "$AION_M4_STORE/demo"
open "$AION_M4_STORE/demo/report.html"
```

Keep all failed attempts and use a fresh directory when making an intentional
new attempt. Record the OS version, actual CPU, compiler version, power/thermal
conditions and exit status. Do not call a test M4-validated based only on the
`arm64` architecture string. A successful demo can still be noisy, inconclusive
or regressive and must not invent a winner.

The tests include real Clang builds for all ten workloads, multi-TU correctness,
sanitizer fixtures, LTO/PGO where supported, process termination, proposal safety,
reports, budgets and a one-command MVP run. Native-Mac-only tests additionally
exercise libproc memory termination and Mach-O execution. A real compiler is
required by the command above; unrelated failures must not be hidden by skips.

## LLVM tools and optional diagnostics

`--compiler` accepts an explicit executable. `AION_CXX` supplies the default when
the command's compiler is `clang++`. `AION_LLVM_BIN` prefers a matching tool
directory, then discovery checks compiler siblings and PATH. Per-tool overrides
are single executable paths, never shell commands:

```bash
export AION_LLVM_PROFDATA="$AION_LLVM_BIN/llvm-profdata"
export AION_LLVM_OBJDUMP="$AION_LLVM_BIN/llvm-objdump"
export AION_LLVM_NM="$AION_LLVM_BIN/llvm-nm"
export AION_LLVM_SYMBOLIZER="$AION_LLVM_BIN/llvm-symbolizer"
```

PGO requires matching LLVM major/vendor. Apple Clang PGO additionally requires
the same Apple clang build identity; upstream major numbers do not establish
Apple-tool compatibility. The recommended upstream LLVM 18 toolchain avoids
that ambiguity. Instrumentation, independent training, profile merge and fresh
rebuild remain separate and retain hashes. LTO uses the compiler's macOS linker
behavior; no Linux linker options are injected. An unsupported recipe retains
its precise compile/link/runtime failure; AION does not substitute a candidate.

Static IR/remarks and LLVM Mach-O/ARM64 disassembly can be collected where the
tools support them. AION's Linux hardware counters, cycle-IP sampling and ELF
sized-symbol attribution are unsupported on macOS. Installing `llvm-symbolizer`
does not enable those features; its discovery is recorded separately.
There is no claim that optional diagnostics replace hardware counter evidence.

## Resource and sanitizer differences

No Linux affinity API, `/proc`, `/sys` or `perf_event_open` is used on macOS.
`--cpus none` is explicit; `--cpus auto` records unpinned/unavailable status.
An explicit numeric CPU request is refused. No performance/efficiency core
placement or physical isolation is claimed.

Wall timeouts, bounded output, POSIX process-group termination and CPU/file/core
limits remain enforced. Per-child wait4 RSS uses macOS bytes rather than Linux
KiB. macOS does **not** claim a Linux `RLIMIT_AS` ceiling. Instead libproc polls
the invocation's process-group resident memory, including the supervisor and
descendants, and kills the group if its observed aggregate exceeds the requested
budget. The nominal polling interval is 5 ms, subject to scheduler delays;
transient peaks can be missed. It is not an allocation ceiling or a sandbox.
If monitoring is unavailable or loses a live process observation, the protected
operation is refused/terminated rather than silently becoming unprotected.

Separate sanitizer invocations explicitly use uncapped memory for shadow
mappings while retaining CPU/time/output protections. ASan and UBSan remain
required by the complete MVP. LeakSanitizer is disabled **with an explicit
unsupported record** on macOS; do not claim leak validation passed there.
SDK `.tbd` library stubs are recorded as stubs, never as runtime dyld library
bytes. Missing runtime-library hashes stay unavailable.

## Check a built wheel outside the checkout

From the activated development environment, build both formats, create a new
external venv, then execute the real installed-package smoke from an external
working directory. Keep the development and wheel evidence distinct.

```bash
python -m build
export AION_CHECKOUT="$PWD"
export AION_WHEEL_ENV="$(mktemp -d)/venv"
python -m venv "$AION_WHEEL_ENV"
"$AION_WHEEL_ENV/bin/python" -m pip install --no-index --no-deps \
  "$AION_CHECKOUT/dist/aion_network-0.6.0.dev0-py3-none-any.whl"
cd "$(mktemp -d)"
"$AION_WHEEL_ENV/bin/python" "$AION_CHECKOUT/tools/installed_smoke.py" \
  --store "$AION_CHECKOUT/$AION_M4_STORE/installed-wheel" --mvp
cd "$AION_CHECKOUT"
```

The smoke checks console installation, package version/import prefix, bundled
sources, real array/records output verification and an installed MVP run. It
fails if the checkout's `src/` package is imported. Retain the fresh venv and
evidence until review; do not delete earlier scientific results.

## Troubleshooting and reporting

- Wrong compiler: inspect `"$AION_CXX" --version`, `aion doctor --json`, PATH and
  `AION_LLVM_BIN`. A driver invocation named `clang++` is preserved through
  symlinks so C++ linking stays enabled.
- Missing SDK/C++ headers: finish Command Line Tools installation and check
  `xcode-select -p`. Do not add arbitrary flags or disable checks to make a run pass.
- PGO mismatch: use the compiler's matching tools; inspect the exact refusal.
- Missing counters or pinning: expected macOS limitation, not a zero counter or
  proof of physical placement. macOS and M4 measurement quality remain unvalidated.
- Sanitizer failure: inspect the separate validation JSON and captured stderr.
  Instrumented times never become primary performance evidence.
- Memory monitoring failure: preserve the error and platform capabilities;
  do not silently remove the requested protection.

Report failures with version, OS/architecture, compiler, redacted command,
bounded settings, exit status and relevant failed stage. Raw reports may include
private filesystem paths and host observations; review them before attaching.
Never post credentials. Follow [SECURITY](../SECURITY.md) for vulnerabilities.

GitHub documents `macos-15` as an ARM64 M1 hosted runner, not an M4 validation
machine ([runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)).
The workflow asserts ARM64 at runtime. Its success, when it actually runs, is
software compatibility evidence rather than scientific benchmarking readiness.
