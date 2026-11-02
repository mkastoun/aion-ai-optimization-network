# AION 0.6 MVP Preview

AION helps investigate whether a compiler policy or a trusted program variant
actually improves a workload. The preview provides a complete local workflow:
select a workload, propose approved experiment IDs, inspect a sealed plan,
validate correctness, compile, benchmark, independently confirm and report.

This is an engineering prototype. It is **not completed Phase 6 scientific
validation**. Native Linux validation remains pending, WSL measurement conditions
remain unvalidated, and research cannot create production presets.

All ten existing workloads are selectable. The preview catalog contains the
original 17 research panels and 14 explicitly approved O2/LTO comparisons for the
remaining seven workloads. The original research command still defaults to its
17-panel catalog. The preview retains a conservative family of 31 comparisons,
even for a smaller selected subset; the statistical implementation and gates
remain unchanged.

The offline deterministic strategy prioritizes standard O3 anchors, source
interventions against O3, then targeted policies and more expensive profile
experiments. Static cost estimates and a seeded stable tie break make selection
reproducible. It is a heuristic, not an AI model.

The optional AI strategy imports a strictly validated JSON response from an
external LLM or coding assistant. It can rank catalog IDs and explain hypotheses.
It cannot supply recipes, source paths, commands, LLVM passes, source code,
statistics or preset approvals. AION has no required model API, key, paid service
or automatic provider request. Imported model identity/authorship is declared by
the caller; AION does not authenticate the external generation.

Candidate IDs and order freeze before discovery. Separate ASan, UBSan and
differential validation precede primary measurements. The existing research
adapter, calibration, pairing, output verification and uncertainty machinery
execute real C++ builds. Distinct sequential observation windows and held-out
input/scheduling seeds support independent confirmation; they do not prove
independent physical host conditions. No retry-until-success behavior or
automatic candidate replacement occurs.

Each run produces intermediate JSON evidence, archived sources/executables/PGO
profiles, a Markdown report and a standalone local HTML report. Functionality,
correctness, local quality, exploratory signals, regressions and native
scientific readiness are separate fields. A completed demo can have no reliable
improvement. If no scientifically qualified optimization exists, the report
prominently states **“No independently verified improvement found.”**

See [quickstart](mvp-quickstart.md), [architecture](mvp-architecture.md),
[validation](mvp-validation.md), and [actual demo results](mvp-demo-results.md).
