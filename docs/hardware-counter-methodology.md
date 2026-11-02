# Optional hardware and software observations

AION uses a bundled trusted C++ launcher around Linux's standard [`perf_event_open`](https://man7.org/linux/man-pages/man2/perf_event_open.2.html) interface. It does not require a system `perf` executable, root, or a change to kernel permissions. The launcher forks the target, holds it until counters are configured for its PID, enables events at exec, and waits for exit. Counter and sampled profiling are separate executions from primary timing and can never qualify for presets.

## Counting scope and provenance

Each event records its generic name, hardware/software type and config, error/status, raw value, nanoseconds enabled/running, filters and scope. Hardware-type events are cycles, retired instructions, cache references/misses and branch instructions/misses. Software-type events are context switches, CPU migrations and page faults. Kernel/hypervisor execution is excluded; the workload main thread is counted without thread inheritance. These bundled programs are single-threaded. Whole-process counting includes dynamic startup, input generation, setup, work, checksum output and exit; it is not compute-region instrumentation.

The current process environment determines counter semantics. Under WSL2 or a VM these are guest-visible PMU observations, not proof of physical-host isolation or physical counter attribution. Generic cache events are architecture dependent and do not identify a particular cache level. Missing/denied/unsupported events stay null with errno and diagnostics; unavailable values are never substituted with zero. A successfully counted zero remains a real zero observation.

Final binary, source/header, compiler/linker/library and PGO training/profile identities accompany each execution. Profiling rebuilds a selected saved timing configuration and checks binary SHA-256. It uses that timing result's input case and a common batch count taken from its baseline, so configurations execute equal total work. Each configuration's original timing batch count and source sample identities are retained separately. Host/toolchain/placement matches are recorded independently. A binary mismatch prevents attribution to the old executable; even a full identity match does not make whole-process counter ratios equivalent to compute-only timing effects. Source JSON and its SHA-256 stay linked, and raw samples have explicit identities.

## Multiplexing and derived values

Events are opened individually so unsupported events do not disable all others. Linux can multiplex available PMU slots. Raw counts and enabled/running times remain intact. When running time differs from enabled time, `raw * enabled / running` is recorded as a **scaled estimate**, with running fraction and multiplexing flag. Zero running time is not counted. AION conservatively suppresses IPC/cache-miss/branch-miss ratios if either source event is multiplexed or missing, or its denominator is zero. Unmultiplexed ratios describe the same execution's filtered whole-process events; they are not causal explanations.

Separately, Linux `wait4` reports voluntary/involuntary context switches, minor/major page faults and user/system CPU time. This is **software resource accounting**, including pre-exec child setup. It has a different scope from user-filtered perf events. It is useful when PMU access is denied but is never relabeled as hardware instructions, cache misses, migrations or estimated hardware counts.

## Sampled hot regions

`--hotspots` starts another independent execution using user-cycle IP sampling through `perf_event_open`, requesting 997 Hz. The helper maps a bounded ring buffer, retains sampled IPs, mapping snapshots, lost-event counts and overrun indicators, and resolves ELF-relative addresses with the available local `addr2line`. Unresolved IPs stay unresolved. PIE/shared-library addresses use mapping offsets; ordinary ET_EXEC addresses remain absolute. Mapping snapshots can miss transient mappings. Lost or damaged sampling data is explicitly incomplete.

Symbol attribution requires a sized text-function range from `nm` that encloses the sampled object-relative IP. `addr2line` can return an unrelated nearby exported name for stripped private library code; such names are retained only as unverified hints. Unresolved library samples are preserved. Object hashes are checked before re-resolving older profiles with `aion symbols --from-profile PROFILE.json`; the resulting hash-linked audit does not edit raw observations.

Symbol fractions are fractions of recorded samples, not exact CPU-time percentages, call counts or retired instruction totals. Whole-process setup/library code can appear hot. Static disassembly/IR counts do not identify hot regions. Sampling can change runtime and memory behavior, so sampled durations are excluded from optimization evidence. No compiler defect or causal optimization claim follows from a symbol distribution alone.

## Commands

```bash
aion --store .aion/counter-preflight preflight --cpus auto --counters
aion --store .aion/profiles profile --from-result SAVED_TIMING.json \
  --benchmark records,logs,matrix --candidate baseline --candidate lto \
  --candidate pgo --candidate pgo-lto --samples 3 --cpus auto --codegen --hotspots \
  --evidence .aion/profile-artifacts --session-file EXISTING_SESSION.json
```

When `--benchmark all` is used, the saved result's suite is selected, allowing an eight-workload Phase 3 result to remain usable in the ten-workload checkout. Current sources/cases must match the saved fingerprints; historical source reconstruction is explicit. CLI/JSON retain execution errors and unavailable capabilities. The independent count and sampling paths do not modify governors, turbo, kernel permissions or primary timing thresholds.
