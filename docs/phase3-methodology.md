# Phase 3 methodology: controls, provenance, and representative applications

The Phase 2 calibration, paired scheduling, block bootstrap, correctness checks, 2%/combined-MAD improvement floor, 5% regression/CV caps, minimum duration, drift, and independent-confirmation rules remain. Methodology version 3 adds controlled placement and provenance to the existing schema-version-1 JSON container. Earlier reports remain readable.

## Requested and effective CPU placement

`--cpus none` disables narrowing the workload mask. `--cpus auto` selects the first CPU in the caller's allowed affinity set; it does not identify an idle or optimal CPU. Explicit CPU IDs/ranges, such as `--cpus 2` or `--cpus 2,4-5`, must belong to that set. Linux `sched_setaffinity` is applied in the actual child process immediately before `exec`, followed by `sched_getaffinity` verification. The supervisor records that child PID and effective mask. Linux preserves the mask across exec, as documented by [Linux man-pages](https://www.man7.org/linux/man-pages/man2/sched_setaffinity.2.html).

Current bundled executables also report their own PID, effective mask, and observed CPUs before/after computation. AION checks these against the request and supervisor PID. Frozen Phase 2 executables lack those added fields: their explicitly labeled proof is the child snapshot plus Linux exec inheritance, not a fabricated in-executable observation. Verification is a snapshot, not exclusive CPU ownership or proof that an unrestricted process never migrated between endpoints.

No root privilege, governor change, turbo change, scheduler-policy change, or system power modification is required. Unsupported explicit requests fail clearly; Windows and other platforms retain unpinned execution and unavailable metadata. WSL2 controls guest logical CPU placement, not verified physical host-core placement.

## Honest host and build identity

Start/end observations retain exposed CPU topology, allowed mask, kernel/OS, virtualization evidence, sysfs frequency/governor readings, guest-visible proc MHz, thermal/power indicators, load, scheduling policy/nice, resource limits, and available cgroup restrictions. Missing values remain null with availability notes. Guest-visible frequency is not asserted to be physical frequency.

Stable host identity combines exposed hardware/kernel characteristics and a hashed OS installation/node identity. Raw machine ID/hostname are not published as identity fields. Dynamic load, frequency, and temperatures do not enter the stable fingerprint. This identifies the current guest/OS installation; it is not physical-host authentication. Compiler/linker versions and binary hashes, C++ library identity, source/header hashes, flags, final binary hashes, PGO profiles/training, and actual timing/resource records are retained separately.

Independent confirmation requires compatible host identity, toolchain, workload fingerprints, resource limits, and requested/effective placement. Different hosts, native Linux versus WSL2, changed CPU policies, or unverifiable required identities cannot be silently pooled or called independent confirmation. `aion report --comparison OTHER.json` supports explicitly incompatible side-by-side inspection; no raw samples are pooled, even when compatibility checks pass. Phase 2 data without host fingerprints remains legacy identity-unverified evidence.

`aion report --audit-json AUDIT.json` recomputes per-run proposal gates from raw samples, preserves the source result SHA-256, and records exact failure reasons. This is not a substitute for independent confirmation or registry policy. Report/audit output paths cannot overwrite raw input results. Failures or interruptions during an experiment retain already collected samples in a failed/interrupted result through the CLI's failure callback.

## Measurement-system controls

`aion controls` uses two copies of the exact baseline binary, verified by SHA-256:

- A/A: the same input, binary, computation, and expected checksum, with ordinary randomized paired measurement.
- Negative control: the same binary/checksum plus a declared 50 ms steady-clock busy-loop delay per timed unit. Its actual elapsed injected duration is reported, included in compute time, and never subtracted. This is not a consumed-CPU-time guarantee; descheduling also advances the steady clock. It validates sensitivity to a known slowdown; it is not an optimization candidate or a production workload.

The control series repeats independent scheduling seeds and held-out input seeds. `--compare-unpinned` balances mode order across repetitions: unpinned/pinned, then pinned/unpinned. All samples remain, including outliers and out-of-band durations. A/A improvement signals are counted as false-positive diagnostics even though controls are forbidden from becoming presets. A/A no-clear-change observations are consistency checks, not proofs of equivalence or an engine-wide false-positive rate. Known slowdowns are called verified only when the unchanged quality/uncertainty/regression gates permit it; otherwise they remain inconclusive.

## Frozen-source regression investigation

`aion investigate` can restore the exact sorting, matrix, common-header, and manifest bytes from the preserved local AION 0.2 wheel. It extracts only explicit fixed member names, checks the version metadata, hashes the bundle, and compares source/input fingerprints with available Phase 2 result files. The original temporary executables were not retained, so reconstructed-source provenance must not be described as an original-binary identity check.

Each selected configuration gets preserved final binary disassembly, optimized per-translation-unit LLVM IR, inlining/vectorization remarks, source/build hashes, independent output checks, and PGO training/profile provenance. Pre-link IR is labeled as such; final LTO code is inspected through final-binary disassembly. Whole-binary mnemonic/vector-type counts are static text diagnostics, not dynamic retired instructions or a causal explanation. Clang's [optimization remarks](https://clang.llvm.org/docs/UsersManual.html) provide additional code-generation evidence.

Fresh timed discovery/confirmation then rebuild the frozen sources, change scheduling and input seeds, and record whether diagnostic binaries match measured binary hashes. Only sufficiently stable, independently repeated runtime results support verified regression/improvement claims. Different assembly, branch weights, training sizes, or inlining decisions are facts about those artifacts; attributing a runtime difference to them remains a hypothesis without stronger causal evidence. PGO training uses independent inputs of equal problem size but fewer rounds; that does not establish production representativeness.

## Multi-translation-unit applications

The manifest supports multiple sources, explicit local headers, categories, and independent input cases. The compiler links all translation units together and supports existing O3/O2/size/unroll/scalar/LTO/PGO recipes. Each application prepares deterministic inputs outside timing and performs real parsing/algorithm/aggregation/serialization inside timing, with observable checksums verified by independent Python implementations. Existing kernels remain available through `--benchmark micro`; application suites use `--benchmark applications`, and `all` includes both.

These are self-contained synthetic application benchmarks, not claims about all production programs. Additional applications can be added through the same manifest/reference interface to reach ten or more workloads. No new cloud dependency, AI optimization, remote execution, or autonomous source rewriting is involved. PGO profiles remain program-specific and cannot become generic flag-only presets.

## Reproduction commands

From the Ubuntu project directory:

```bash
source .aion/venv-linux/bin/activate
aion doctor --json --cpus auto
aion --store .aion/phase3-controls controls --benchmark sorting,matrix --cpus auto \
  --compare-unpinned --repetitions 2 --iterations 11 --warmups 2 --seed 53100
aion --store .aion/phase3-investigation investigate --benchmark sorting,matrix --cpus auto \
  --candidate o2 --candidate pgo --candidate pgo-lto --iterations 11 --warmups 2 --seed 53200 \
  --phase2-wheel .aion/wheels/aion_network-0.2.0-py3-none-any.whl
aion --store .aion/phase3 optimize --benchmark all --cpus auto --candidate o2 --candidate lto \
  --candidate pgo --candidate pgo-lto --iterations 11 --warmups 2 --seed 53300 --confirm-all
AION_REQUIRE_COMPILER=1 python -m pytest -q
```

Use the actual newly generated run IDs with `aion report --result ... --confirmation ...` or `--comparison ...`. Commands work on native Linux with a compatible toolchain; a second machine is not required for development. WSL2 results stay labeled virtualized-host evidence. If conditions remain unstable, record that limitation rather than lowering gates or rerunning until a desired result appears.

For the preserved completed Phase 3 runs:

```bash
aion report --result .aion/phase3/results/20261030T234834-de3eb6de82.json \
  --confirmation .aion/phase3/results/20261031T000202-01808fcd04.json \
  --audit-json .aion/validation/phase3-gate-audit.json --output .aion/phase3/confirmed.md
aion report --result .aion/phase3-controls/results/20261030T231154-11ef27a24d.json \
  --comparison .aion/phase3-controls/results/20261030T231315-d0bab9b7ef.json \
  --output docs/phase3-placement-comparison.md
```

The retained `.aion/validation/phase3-render.py` adds the curated evidence summary and gate table to the generated main performance report while asserting that raw inputs remain byte-identical. The evidence/count audit and isolated package commands are documented in [Phase 3 validation](phase3-validation.md).
