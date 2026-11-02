# AION 0.4: native replication, profiling, and ten workloads

The existing Clang adapter, bounded process supervisor, calibrated paired timing, independent references, local registry, and Phase 1–3 evidence remain. Statistics and promotion thresholds are not changed. The eight existing workload sources, headers, and timing cases will remain identifiable; expanded correctness inputs live in a separate validation manifest.

Implementation sequence:

1. Extend read-only environment classification/topology/restriction observations, preflight, and explicit session provenance. Distinguish native Linux with no detected virtualization from proof of physical isolation. Keep WSL2 development supported.
2. Add optional Linux `perf_event_open` counting through a bundled trusted helper, with per-event permission/availability and enabled/running times. Preserve software resource observations separately. Profile rebuilt binaries against exact timing-result hashes/input identities; never insert profiling into primary timing. Optional perf sampling records hot regions only when available.
3. Extend control studies across independent sessions, stratify compatible evidence, report descriptive outcome rates and approximate uncertainty, and assess readiness without claiming a universal false-positive rate.
4. Add separate ASan/UBSan and independent differential validation, including edge/large inputs. Sanitizer virtual-address requirements must not silently change primary timing limits.
5. Add multi-file image filtering and variable-size in-memory key/value processing with independent references, multiple seeds/distributions, observable serialized output, PGO, and LTO.
6. Run supported real experiments, inspect records/LTO, logs/PGO, and matrix LTO/PGO+LTO against preserved evidence, run complete Linux/Windows tests, and install/smoke-test a separate 0.4 wheel. Record missing counters/native hardware/CI honestly.

Required final records are Phase 4 methodology, validation, performance, native Linux setup, and hardware-counter methodology. Native Linux performance validation remains a separate pending milestone unless real native experiments are executed. There is no AI optimizer, cloud requirement, privileged system change, or autonomous source transformation.

All supported implementation and local validation work is complete: full Linux/Windows suites, separate ten-workload differential/ASan/UBSan checks, real counter/sampling investigations, two-session controls and primary discovery/confirmation, reports, and independent wheel smoke. No independently verified improvement qualifies for a preset; records/LTO has a scoped repeated regression. Measurement quality is not yet validated and native performance evidence remains pending. See [validation and changed files](phase4-validation.md), [performance](phase4-performance.md), and [quality](phase4-quality.md). GitHub Actions was not executed in this unconfigured workspace.
