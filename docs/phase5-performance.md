# Phase 5 performance and measurement quality

**Native Linux scientific validation is pending. No native-validated optimization improvement is available. Phase 6 is not ready.**

The local implementation was exercised under WSL2. Native-required preflight rejected this environment. The study retains all 17 predeclared comparisons in discovery and held-out confirmation; these results cannot establish bare-metal improvements or universal compiler presets.

Records/LTO repeats as a per-comparison WSL regression. No intervention clears
independent improvement requirements in both roles. Both source optimization
candidates remain inconclusive/no-clear-change. The additional controls retain
zero false A/A improvement signals and many inconclusive slowdowns; the
measurement environment is still unvalidated.

## Provenance and scope

Declaration seal: `9baa6754247284b326984df4d14ec2abc8d8e7ed6bf9293c97d22255e5727258`; [study.json](../.aion/phase5/study.json). The complete declared source snapshot is retained beside it.

Discovery: [research-a160d6c442944390b9da3212a2c16adb](../.aion/phase5/research/results/research-a160d6c442944390b9da3212a2c16adb.json); confirmation: [research-27b8a36e23554511bbf515199fd01d0a](../.aion/phase5/research/results/research-27b8a36e23554511bbf515199fd01d0a.json).
Sessions: `a9d29069bb1740fbbafef4b3aa3b17e6` and `93d58cc5886e4f438f125be52e462771`. Discovery was followed by isolated package validation before session B. Distinct IDs/windows do not prove independent physical host conditions.

Scheduling seeds: 65000 / 65100; ordinary measured input seeds: 42 / 314159; malformed-heavy logs use the declared tagged counterparts. Training seeds/cases remain separately recorded.

748/748 measured executions pass checksum/protocol checks; 732/748 (97.86%) lie in 250–500 ms. There are 136/136 correct warmups, 408/408 correct discarded pilots and 596/596 independent premeasurement output checks. All calibrations passed: True.
There are 68 final application builds, including 22 fresh program-specific PGO builds. Every archived executable matches its timing hash; every recorded source hash matches the declared snapshot; every archived merged profile matches its recorded hash. [Audit](../.aion/phase5/evidence-audit.json).

Noisy configurations: 34/68; drifting configurations: 17/68. These failures remain part of the evidence.

The research timings cover records, logs and matrix. All ten original workloads were recompiled, validated and exercised in installed-wheel smoke; its single samples are package checks. The unchanged all-ten Phase 4 performance study remains separate. The native workflow covers all ten original workloads with O3/O2/LTO/PGO/PGO+LTO. No samples are pooled across phases, roles, sessions, placements or input contracts.

## Individual research estimates

The table shows the median paired improvement and its empirical family-adjusted interval in percent; positive means faster than the declared reference. Each role has 11 randomized adjacent pairs and two warmups per arm. The family contains 17 comparisons, with a 95% family target. The marginal matched-median ratio, combined-MAD floor, strict classifications and all gates remain in raw JSON. Empirical bootstrap coverage is limited by short dependent series and possible nonstationarity. No outliers are removed.

| Panel | Discovery paired gain [interval] % | Confirmation paired gain [interval] % | Raw classifications |
|---|---:|---:|---|
| records-lto | -13.328 [-18.183, -10.870] | -11.112 [-17.238, -9.298] | regression / regression |
| records-parser-noinline | +6.343 [+4.958, +9.832] | +4.778 [-0.943, +8.835] | inconclusive / no_clear_change |
| records-aggregate-noinline | +10.896 [+7.350, +12.000] | +8.494 [-15.277, +14.763] | improvement / inconclusive |
| records-scalar | +11.811 [+6.679, +15.431] | +11.550 [+10.928, +13.545] | inconclusive / inconclusive |
| records-no-unroll | +11.601 [+8.992, +20.809] | +12.714 [+10.513, +14.337] | inconclusive / inconclusive |
| records-pgo-lto | +10.087 [+5.153, +12.744] | +7.569 [+1.806, +11.751] | no_clear_change / inconclusive |
| records-branchless | +1.234 [+0.326, +6.050] | +3.817 [-4.859, +11.572] | inconclusive / inconclusive |
| logs-pgo | +8.612 [+4.192, +11.897] | +6.021 [+4.194, +11.543] | inconclusive / no_clear_change |
| logs-training-rounds | -3.347 [-9.172, -1.748] | -5.444 [-7.517, -2.747] | inconclusive / inconclusive |
| logs-training-path | +1.235 [-7.509, +2.420] | -0.724 [-1.040, +0.637] | inconclusive / inconclusive |
| logs-training-mix | -4.228 [-5.810, -2.357] | -6.758 [-16.893, -0.310] | no_clear_change / inconclusive |
| logs-unseen | +0.849 [-5.319, +2.828] | -1.999 [-3.157, +0.022] | inconclusive / inconclusive |
| matrix-lto | -35.876 [-42.255, -29.503] | -39.523 [-44.837, -34.665] | inconclusive / inconclusive |
| matrix-scalar | -59.094 [-62.692, -52.867] | -57.744 [-70.557, -52.222] | regression / inconclusive |
| matrix-no-unroll | -3.488 [-9.544, +0.532] | -0.708 [-5.258, +10.922] | inconclusive / inconclusive |
| matrix-pgo-lto | -1.468 [-10.427, +9.702] | -2.063 [-2.768, -0.950] | inconclusive / no_clear_change |
| matrix-transposed | +0.086 [-2.844, +5.130] | -0.949 [-11.916, +2.893] | no_clear_change / inconclusive |

All native hypothesis statuses are **unsupported environment** in the reproducible research report. A positive point estimate or repeated local classification does not override native readiness or a failed gate.

## Failed gates and independent evidence

| Panel | Discovery failed gates | Confirmation failed gates | Compatible independent contracts |
|---|---|---|---|
| records-lto | acceptable_regression_bound, improvement_floor_and_uncertainty | acceptable_regression_bound, improvement_floor_and_uncertainty | True |
| records-parser-noinline | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty | True |
| records-aggregate-noinline | none | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | True |
| records-scalar | variability, improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty | True |
| records-no-unroll | variability, drift, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty | True |
| records-pgo-lto | improvement_floor_and_uncertainty | variability, improvement_floor_and_uncertainty | True |
| records-branchless | variability, improvement_floor_and_uncertainty | variability, drift, improvement_floor_and_uncertainty | True |
| logs-pgo | variability, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty | True |
| logs-training-rounds | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | True |
| logs-training-path | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | drift, improvement_floor_and_uncertainty | True |
| logs-training-mix | acceptable_regression_bound, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | True |
| logs-unseen | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | drift, improvement_floor_and_uncertainty | True |
| matrix-lto | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | True |
| matrix-scalar | acceptable_regression_bound, improvement_floor_and_uncertainty | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | True |
| matrix-no-unroll | drift, acceptable_regression_bound, improvement_floor_and_uncertainty | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | True |
| matrix-pgo-lto | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | improvement_floor_and_uncertainty | True |
| matrix-transposed | improvement_floor_and_uncertainty | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | True |

Regression/improvement gates differ from quality gates: a valid regression is an important negative result, not a failed correctness check. All exact input cases, configurations, source/binary/compiler/build identities, CPU/power/scheduler/cgroup observations, comparison intervals and compatibility reasons remain in the [research report](../.aion/phase5/reports/results/research-report-65d872468cb144149ab2fa6a629d662d.json).

## Additional control study

[Quality report](../.aion/phase5/quality/results/20261031T132551-3ee9029c88.json) recomputes outcomes from eight saved control runs in two explicit sessions. Ordinary matrix/records/logs and image/kv distribution designs remain separate strata. A/A uses exact baseline copies; known-slowdown controls execute the same correct computation plus the existing 50 ms elapsed delay per unit.

| Stratum | Runs / sessions | A/A false signals / all | Known slowdowns detected / all | Inconclusive / all | In-band measured executions | Quality passed |
|---|---:|---:|---:|---:|---:|---|
| 0: logs, matrix, records | 4/2 | 0/12 | 5/12 | 16/24 | 504/528 | False |
| 1: image, kv | 4/2 | 0/8 | 2/8 | 13/16 | 341/352 | False |

All-attempt and quality-valid denominators, approximate Wilson intervals, every CV/drift value, duration validity and environment observations stay in the quality JSON/Markdown. They are descriptive correlated observations, not a universal false-positive rate or proof of A/A equivalence. Inconclusive outcomes are retained.

| Stratum | CV minimum / median / maximum % | Drift minimum / median / maximum % | Drifting summaries |
|---|---|---|---:|
| 0 | +0.634 / +3.816 / +29.463 | -7.766 / +0.449 / +20.356 | 7 |
| 1 | +0.004 / +5.741 / +15.583 | -4.177 / +0.008 / +8.733 | 5 |

Readiness: validation passed on the available environment = True; measurement-quality checks passed = False; native evidence available = False.
[Native replication assessment](../.aion/phase5/native-report/results/native-report-f2c357364a074361804477e399f6df56.json) remains pending; control-only WSL evidence cannot certify independent all-ten native performance.

## Computational budget and readiness

| Role | Logical commands / limit | Elapsed seconds / limit | Status |
|---|---:|---:|---|
| discovery | 1147/2500 | 646.62/3600 | completed |
| confirmation | 1147/2500 | 652.03/3600 | completed |

Phase 6 assessment:

- validated_native_measurement_conditions: False
- research_correctness_validation: True
- compatible_independent_experiments: True
- bounded_auditable_catalog: True
- explicit_compute_budgets: True
- research_separate_from_presets: True
- independent_all_ten_native_validation_reviewed: False

**Decision: not ready for Phase 6.** Native measurement conditions and a separate all-ten independent native review remain required. Correct fixed variants and bounded execution do not establish arbitrary source-transformation correctness. Research cannot create presets.

Use the [exact native instructions](../docs/phase5-native-instructions.md) for the pending milestone. Tests/package results are in [validation](../docs/phase5-validation.md); causal limits and diagnostics are in [research findings](../docs/phase5-research-findings.md).
