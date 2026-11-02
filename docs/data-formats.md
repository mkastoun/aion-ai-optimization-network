# JSON formats, version 1

The 0.6 release preparation adds optional `memory_limited` and
`resource_protection` process fields, an `apple-clang` compiler family, binary
format observations and explicit OS capability records. macOS observations use
environment classification `macos` without authenticating physical hardware.
An RSS watchdog record identifies its sampled aggregate scope and limitations;
it is never represented as an address-space allocation ceiling. Older evidence
without these additive fields remains readable. Statistics, family policy and
promotion thresholds are unchanged.

The 0.6 engineering preview adds closed-schema `mvp-proposals`, bounded
`mvp-selection-context`, sealed `mvp-plan`, journaled `mvp-run`, planning receipts
and derived `mvp-report` records. Schema version 1 and measurement methodology 4
remain. The preview catalog provider contains 31 approved entries; the original
research provider remains 17. A nested role's logical commands also count in the
preview's global budget. See [MVP architecture](mvp-architecture.md) and
[proposal schema](mvp-quickstart.md). Preview records cannot qualify production
presets or scientific Phase 6 readiness.

Phase 5 keeps schema version 1 and measurement methodology version 4. Its new
evidence kinds are additive: `research-declaration`, `research-study`,
`research-timing`, `research-report`, `research-diagnostics`, and
`native-replication-report`. Existing Phase 1–4 records keep their original bytes
and interpretation. Research kinds and research markers cannot enter presets.

A declaration contains the finite catalog, file SHA-256 map, complete cases and
training contracts, selected panel names, family size 17, compiler/build identity,
placement, settings/seeds and per-role command/wall budgets. Its seal hashes
canonical sorted-key JSON excluding the seal field. A sibling `.sources`
directory preserves the declared bytes and include layout. Seals are not signed
attestations. Declaration reconstruction rejects changed installed source/input
bytes; arbitrary recipe/source paths are not accepted.

A study stores its declaration/hash, explicit role/session, attempts, start/end
times, failures/partial results, unattempted panels and command-budget ledger.
Attempts link individual timing result paths and file hashes. The ledger retains
logical commands, results and exceptions; it bounds launches rather than counting
all OS descendants. A role cannot silently overwrite or retry earlier attempts.

Research timing retains the existing pair/calibration/checksum schema. The
`baseline` field identifies the declared reference rather than always O3.
`build.research` identifies the actual recipe, variant fingerprint, full source
closure and saved executable. `build.pgo` retains exact training checks/path,
fresh profile hashes and raw/merged archive locations. The workload fingerprint
identifies the common input/reference contract; use the configuration fingerprint
for the actual intervention. `promotion_eligible` is false.

Research reports retain separate observations/intervals, failed gates,
compatibility, source/build/environment/input/training/correctness identities,
attached diagnostics and statuses: observed change, validated change,
inconclusive, rejected hypothesis, unsupported environment. Readiness fields
separate controls, correctness, independent reproduction, finite search and
budgets from the pending all-ten native review. A report does not grant execution
permission for AI optimization.

Distribution controls use `control_input_design:
existing-validation-distributions-v1`. Their changed case contract creates a
separate compatible stratum; validation can match only when source closures are
identical and every argument/expected pair is already covered by all-ten
sanitizer evidence. Quality reports add descriptive CV, drift and physical-duration
distributions without pooling timing samples or changing any gate. Native
reports link their input files/hashes, per-pair failures and operator host/window
notes. Missing native evidence remains pending.

Experiment and preset documents carry `schema_version: 1`. Unknown versions are rejected on load. Numbers use seconds and bytes; percentages in reports are derived from fractions. Missing platform metrics use JSON `null`, never a fabricated zero.

Phase 2 adds `methodology_version: 2` without removing old fields. Methodology 1 measures whole-process time; methodology 2 measures compute time per unit. Their medians cannot be directly compared as a speedup.

Phase 3 adds `methodology_version: 3`, `execution_controls`, stable `host_start`/`host_end` identity plus dynamic observations, and build provenance. Each process can record the actual child PID and pre-exec affinity; measured records additionally carry in-executable affinity/CPU snapshots when available. Source/header lists and binary hashes support multi-TU builds. `gate_outcomes` records failed quality/promotion criteria without changing their thresholds. Experimental-control runs record A/A false-positive and known-slowdown diagnostics. Failed/interrupted runs retain collected samples and error metadata. Phase 2's fields/readers remain supported; missing historical host IDs are never invented.

Phase 2 also records `comparison_family_size`, selected `measurement_case`, `measurement_protocol`, per-configuration `calibration` (including all discarded pilots), and per-record `measurement` with compute/setup nanoseconds, batch count, physical seconds, and seconds per batch. Pair IDs and `pair_candidate` link each candidate to its own adjacent baseline. Baseline counts therefore multiply by successful candidate count.

Uncertainty records contain paired improvement intervals, nominal/adjusted confidence, family size, bootstrap resample count/seed, circular block length, and coverage assumptions. Summaries retain drift and outlier diagnostics; no samples are removed. `calibration_failed` is an additional terminal status. PGO build records retain instrumented build, training checks/inputs, merge process, tool version, profile hashes, and total build cost. Profiles are not portable application presets.

## Experiment

Phase 4 calibrated records use `methodology_version: 4`, `evidence_kind: primary-timing`, explicit `sample_id` and host/boot-bound `session`. Environment classification records native-Linux-no-indicator, WSL2, exposed VM/container or non-Linux observations; none proves isolation. Static scheduler/cgroup constraints join compatibility checks. Different sessions remain separate estimates. Historical session IDs are not invented; original eight source/input fingerprints and timing estimators remain unchanged.

Non-promotion kinds are `preflight`, `profiling`, `symbol-resolution`, `sanitizer-validation`, `measurement-quality` and `package-smoke`. They retain run/version/host/session provenance and `promotion_eligible: false` with distinct payloads. Registry assessment rejects them even if primary-shaped fields exist. Session files use `evidence_kind: session` and a session ID, separate from result-store run IDs.

Profiling links source JSON hashes/sample IDs, source/binary/build/PGO identities, inputs, original timing batch counts and common equal-work profile batches. Events retain type/config, errno/status, raw count, enabled/running times, running fraction and labeled scaled estimates. Invalid/missing/multiplexed ratios stay null; wait4 is separate software accounting. Sampling retains IPs, mappings, loss/overrun and object hashes. Resolution version 2 requires sized `nm` text-function ranges; older addr2line names are unverified hints. Hash-linked audits supersede hints without editing raw profiles.

Sanitizer records retain fixed flags, runtime probes, build/source hashes, per-case stdout/stderr/exit diagnostics and all checks. A separate `validation.json` broadens correctness without changing timing cases. Diagnostic ASan/UBSan virtual-address limits are explicitly null; primary defaults remain 1024 MiB. Quality records retain compatible strata, source hashes, raw-derived gates, counts/denominators, approximate Wilson intervals and readiness fields. Native control quality alone cannot certify full native ten-workload performance validation.

An experiment stores:

- `run_id`, `created_at` (UTC), `aion_version`, `purpose`, and overall `status`.
- `environment`: OS, release, architecture, CPU identity/count/features, Python version, and measurement capabilities.
- `compiler`: absolute local driver path, full first version line, major version, target, and family. The invocation name is preserved across symlinks so `clang++` keeps its C++ linking behavior.
- `settings`: iterations, warmups, measurement scheduling seed, noise threshold, improvement floor, and regression allowance.
- `limits`: wall timeout, POSIX address-space limit, and output cap.
- `configurations` and `probes`, including unsupported configuration diagnostics.
- `benchmarks`: source/input SHA-256 fingerprints, input cases, execution schedule, and per-configuration results.

Each configuration includes build success, build command/diagnostics, compilation time, binary size, correctness checks, raw warmup/measurement processes, a statistical summary, and comparison with the baseline. Process results retain command, exit status, timing, peak RSS, stdout/stderr, timeout, and output-overflow state.

Statuses are `unsupported`, `compile_failed`, `incorrect`, `execution_failed`, or `measured` after a run; `ready` is transient. Comparison classifications are `improvement`, `regression`, `no_clear_change`, and `inconclusive`. A noisy observed slowdown remains visible through `regression_observed`, even when it cannot support a reliable classification.

`improvement_fraction = 1 - candidate_median / baseline_median`; positive means faster. `speedup = baseline_median / candidate_median`. `acceptable` requires sufficiently long, repeated, non-noisy samples and no slowdown beyond the configured regression limit. Registry assessment caps regression tolerance at 5% and floors required improvement at 2%.

In Phase 2 the baseline median above uses the candidate's matched baseline subset. `uncertainty.paired_improvement_fraction` is the median of `1 - candidate_i / baseline_i`, and the confidence interval describes that paired estimand. Phase 2 reports show this paired gain beside its interval; the marginal-median ratio remains in JSON for the unchanged screening floor. Improvement requires both the existing marginal/MAD threshold and the paired interval's lower bound to clear that floor.

The result store writes a temporary sibling file and atomically replaces the destination. Reports are derived artifacts. Routine experiment evidence includes transient build paths; its executables are not retained. Phase 3 diagnostic investigations explicitly archive separate binaries, disassembly, IR, and profiles with hashes and scope labels. Confirmation and later verification always rebuild rather than reuse these diagnostic executables.

## Preset

A preset stores its name, `preset_version`, AION version, creation time, allowlisted flags, exact compiler compatibility, hardware requirements, required CPU flags, workload fingerprint mapping, and two evidence references. Each reference records the experiment ID, candidate name, and SHA-256 digest of sorted-key JSON serialization. `verification` records independent confirmation, improved workloads, and the scope of the claim.

Do not treat a copied or manually edited local JSON file as authenticated. Registry load validates the execution-sensitive flags and compatibility fields; local evidence is not signed. `aion verify` rebuilds the current sources and writes fresh correctness/performance evidence. No executable or Python callback can be embedded in a preset.
