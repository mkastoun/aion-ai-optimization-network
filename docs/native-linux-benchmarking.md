# Native Linux replication

Native Linux performance validation is a separate milestone. AION's WSL2 implementation/tests and guest PMU counters do not complete it. The preflight distinguishes WSL2, exposed virtual machines/containers, non-Linux platforms, and Linux with no detected virtualization. The last classification is observational, not proof of bare metal or exclusive physical cores.

## Ordinary user workflow

Use Python 3.12+, Clang with its C++ libraries/linker, and matching LLVM profile tools. Install AION in a separate virtual environment. A native workstation is optional for development; the same commands work on WSL2 when `--require-native` is omitted. No governor, turbo, IRQ, scheduler, kernel permission, or boot setting is changed by AION.

```bash
python3 -m venv .venv-native
source .venv-native/bin/activate
python -m pip install -e '.[dev]'
aion --store .aion/native-preflight preflight --cpus auto --counters --require-native \
  --session-file .aion/native-session-a.json --label native-session-a
```

Inspect the saved topology and SMT sibling lists before choosing CPUs. `auto` selects the first allowed logical CPU; it does not find an idle core, reserve a physical core, or prevent a sibling from sharing resources. An explicit allowed CPU (for example `--cpus 2`, only if it is actually allowed) replaces `auto`. Effective placement is checked inside each current workload. Never infer isolation from equal start/end CPU snapshots.

Run one session from the repository using the installed interpreter:

```bash
python tools/replicate_linux.py --store .aion/native-a --cpus auto --seed 64100 \
  --label native-a --require-native --compare-unpinned
```

This runs preflight, repeated controls on matrix/records/logs, all ten workloads against O2/LTO/PGO/PGO+LTO with independent confirmation, and separate ASan/UBSan/differential correctness checks. `--stage preflight`, `controls`, `timing`, or `validation` can run individual stages using the same store/session. It is deliberately sequential; do not run other builds or profiling concurrently with primary timings. Invocation commands/exit statuses and all evidence are retained. Missing optional profiler or sanitizer support remains explicit.

At a separately delimited session, repeat with a new store/seed, for example `.aion/native-b` and `64200`. Record the actual time, power/cooling conditions and background workload. Distinct session IDs alone do not establish independent host conditions; avoid immediately rerunning until an attractive result appears. Session records bind the OS installation/host and boot observation. A reboot requires a new session file. Measurements from different sessions remain separate estimates.

After both sessions, use the actual saved sanitizer JSON path:

```bash
aion --store .aion/native-quality quality --directory .aion/native-a/results \
  --directory .aion/native-b/results --validation ACTUAL_SANITIZER_RESULT.json \
  --output native-measurement-quality.md
```

Directory discovery selects control evidence, including incomplete controls, without deleting other records. Incompatible hosts, placements, designs, or fingerprints form separate strata. No timing samples are pooled. The report distinguishes compiler/correctness validation, native evidence availability, quality-check outcomes, and insufficient evidence. It is scoped to tested control workloads and cannot establish an industry-wide false-positive rate.

## Stable conditions without privileged tuning

Use a documented, consistent power source and cooling arrangement. Allow the machine to settle; close optional CPU-heavy work and avoid concurrent compilation/indexing. Record load, available frequencies/governors/thermal/power observations, allowed CPUs, SMT siblings, scheduler policy, cgroup constraints and unavailable values. Use equal work units/distributions within comparisons and independent scheduling/input seeds across runs. Check A/A and negative controls before interpreting candidate gains. Retain noisy/out-of-band samples and failed gates. Preflight success alone is insufficient.

WSL2 may expose useful hardware-type counter events, but Windows scheduling, virtual PMU behavior and physical shared resources remain limitations. Native virtual machines are also virtualized evidence. Different installations/hosts must not be silently pooled, even if CPU model names match.

## Optional administrator decisions, outside AION

Installing system compiler/profiler packages may require an administrator; it is not a runtime privileged requirement. Likewise, changing governor/frequency or turbo policy, boot CPU isolation parameters, IRQ placement, SMT policy, scheduler/cgroup reservations, or `perf_event_paranoid` are optional administrator-controlled changes. AION never performs them and this workflow does not require them. If chosen independently, document exact commands, prior/current settings, scope and restoration separately and start a new observation session. They change experimental conditions and do not automatically prove isolation or stability. If permissions block counters, preserve the error and continue supported validation rather than weakening system policy.

See [counter methodology](hardware-counter-methodology.md), [Phase 4 methodology](phase4-methodology.md), and [validation](phase4-validation.md).
