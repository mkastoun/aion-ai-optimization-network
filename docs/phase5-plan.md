# Phase 5 plan: native validation and controlled research

Status: **implementation and supported local validation complete**. The final
release passes 149 Linux tests and 132 Windows-compatible tests (17 explicit
skips); the isolated 0.5 wheel passes. All 17 declared comparisons completed
discovery and confirmation, with separate counters/codegen and source/binary/
profile audits. No independently confirmed optimization qualifies. Native
scientific validation remains pending; Phase 6 is not ready. See
[validation](phase5-validation.md), [performance](phase5-performance.md),
[findings](phase5-research-findings.md) and [native instructions](phase5-native-instructions.md).

The plan below records the bounded design established before research timing.

The implementation will keep Phase 1–4 raw evidence, the ten original workloads,
their independent references, and all statistical thresholds intact. Native
scientific validation requires a physical Linux host; this workstation's WSL2
results can exercise the workflow but cannot satisfy that milestone.

Before timing, seal a finite catalog and the selected panels, source hashes,
compiler/build identity, input/training cases, scheduling seeds and computational
budgets. Run every selected panel in discovery and independent confirmation;
retain unsupported builds, incorrect outputs, interrupted attempts and negative
results. No adaptive search or automatic preset conversion is permitted.

Records interventions: O3 versus LTO; parser noinline; aggregate noinline;
vectorization disabled; loop unrolling disabled; PGO interaction; branchless
aggregation versus O3. Logs interventions: O3 versus PGO, training amount,
ordinary versus measured training path, representative mixed distributions,
and an unseen distribution. Matrix interventions: O3 versus LTO, vectorization,
unrolling, PGO interaction, and a transposed dot-product implementation versus
O3. Each panel declares its own reference. Multi-part source interventions test
that implementation as a whole, without isolating an individual microarchitectural
mechanism. The fixed family size covers the complete catalog even for a subset.

Use existing calibration, pairing, correctness, uncertainty and confirmation
gates. Keep counters/codegen/sanitizers outside primary timing. Preserve fresh
PGO profiles and binaries. Record bounded command attempts and time budgets.

Validation: research fixtures, real compiler variants and independent oracles;
full Linux and Windows-compatible suites; all-ten sanitizer/differential checks;
isolated 0.5 wheel. Run additional controls across separate observation windows
and report outcomes separately by compatible input design and environment.
Extend native replication with explicit separate-session discovery/confirmation,
controls, validation and report stages. Document exact commands and actual IDs.

Phase 6 readiness is assessed separately: measurement quality, correctness,
independent reproducibility, bounded search, budgets and preset separation must
all be established. No independently confirmed improvement is a valid outcome.
