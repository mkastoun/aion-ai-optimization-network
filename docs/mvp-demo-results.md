# Actual MVP demo results

These are the original retained 0.6 MVP executions. Later release preparation
does not replace their raw evidence or relabel them as Mac/native validation.
Create fresh contexts/plans after source/catalog changes; old sealed plans are
not silently migrated. See [release readiness](release-readiness.md) for the
new compatibility run and package checks.

**No independently verified improvement found.**

Both actual WSL2 demos completed on October 31, 2026 using Ubuntu Clang 18.1.3,
target `x86_64-pc-linux-gnu`, and requested CPU affinity `[0]`. Functionality and
correctness passed. Measurement quality remains unvalidated; native scientific
validation is pending. These runs do not qualify Phase 6 or create presets.

## Executed commands and evidence

From Ubuntu in this checkout:

```bash
.aion/venv-linux/bin/python -m aion mvp demo --workload records \
  --strategy deterministic --output .aion/mvp-preview/demo-records

.aion/venv-linux/bin/python -m aion mvp context --workload array \
  --output .aion/mvp-preview/ai-context.json
# The coding assistant read this context and authored ai-proposals.json.
.aion/venv-linux/bin/python -m aion mvp demo --workload array \
  --strategy ai-import --context .aion/mvp-preview/ai-context.json \
  --proposals .aion/mvp-preview/ai-proposals.json \
  --output .aion/mvp-preview/demo-ai-array
```

| Demo | Actual strategy | Selected before discovery | Run ID | Reports |
|---|---|---|---|---|
| Records | deterministic; AI unused | `records-lto`, `records-branchless` | `mvp-7258660bcfdd4a12a62c7f5748cb5d7b` | [HTML](../.aion/mvp-preview/demo-records/report.html), [Markdown](../.aion/mvp-preview/demo-records/report.md), [JSON](../.aion/mvp-preview/demo-records/report.json) |
| Array | genuine imported coding-assistant proposals | `array-o2`, `array-lto` | `mvp-ff99863f0f414b01b408bdd32d411981` | [HTML](../.aion/mvp-preview/demo-ai-array/report.html), [Markdown](../.aion/mvp-preview/demo-ai-array/report.md), [JSON](../.aion/mvp-preview/demo-ai-array/report.json) |

Each demo used two fixed candidates, seven measured baseline/candidate pairs and
one warmup per arm per role, with discovery seed `76000` and confirmation seed
`76100`. Confirmation used fresh session IDs and held-out inputs. Neither run
adapted the selected set or retried candidates based on results. The separate
automatic windows do not establish independent physical host conditions.

## Actual local estimates

Positive gain means faster than that panel's Clang O3 reference. Intervals are
the existing empirical, family-adjusted intervals across all **31 approved MVP
comparisons**, including unselected entries. Discovery and confirmation remain
separate; nothing is pooled or ranked using held-out results.

| Candidate | Discovery gain [interval] | Confirmation gain [interval] | Overall status |
|---|---:|---:|---|
| records-lto | -8.753% [-13.461%, -4.342%] | -13.560% [-14.160%, -10.222%] | Inconclusive across roles |
| records-branchless | +4.982% [+1.515%, +6.530%] | +1.727% [-2.639%, +5.710%] | Inconclusive |
| array-o2 | -0.185% [-3.703%, +0.978%] | +1.539% [-3.830%, +3.707%] | Inconclusive |
| array-lto | -1.689% [-9.416%, -0.379%] | -0.218% [-4.459%, +0.503%] | Inconclusive |

Records LTO's discovery failed variability and drift gates, while confirmation
classified a local regression. The branchless candidate failed the improvement
floor/uncertainty gate in both roles, and confirmation also failed variability.
Array O2 failed variability in both roles and drift in discovery. Array LTO
failed variability, drift and the regression bound in discovery; confirmation
was `no_clear_change`. All four candidates failed the improvement/uncertainty
gate. Full per-role gate objects remain in the JSON reports.

For this array workload, the O2 and O3 recipes produced **identical binary
SHA-256 values** in both roles. They were separately built and executed; the
small measured differences cannot establish an optimization. LTO produced a
different binary. The report retains these identities instead of implying that
different compiler recipes must create different machine code.

## Correctness and cost

| Demo | Separate correctness validation | Primary measured executions | Execution budget used |
|---|---|---:|---|
| Records | 6 differential/ASan/UBSan builds; 60/60 checks passed | 56/56 output-correct | 269/2,000 logical commands; 198.07/1,800 s |
| Array AI import | 3 differential/ASan/UBSan builds; 30/30 checks passed | 56/56 output-correct | 236/2,000 logical commands; 182.64/1,800 s |

Each demo additionally ran eight warmups, calibration pilots, build checks and
ordinary independent output verification. Source variants are deduplicated only
for the separate sanitizer validation; every selected panel still receives both
primary roles. Nested role commands also count against the global budget.
Planning used 5/100 commands and 7.82 s (records) or 7.97 s (array), under its
separate 120 s cap. Sanitizers are separate from primary timing.

The table uses the elapsed budget snapshot in each report; the final job
journals include report-writing overhead (198.50 s and 183.08 s respectively).
Each demo also passed 48 ordinary independent verification checks across eight
primary builds. All 56 records measured compute samples were within 250–500 ms;
55/56 array samples were within that band, with one 576.61 ms outlier retained.
The [final audit](../.aion/mvp-preview/final-audit.json) records exact counts and
duration ranges. Outliers were not discarded or silently remeasured.

## Actual AI use and fallback

The [exported context](../.aion/mvp-preview/ai-context.json) contained only the
array workload description, approved O2/LTO IDs and recipes, budget and rules;
there was no prior discovery evidence or confirmation evidence. This OpenAI
coding assistant read that context and authored the
[actual proposal file](../.aion/mvp-preview/ai-proposals.json) at
`2026-10-31T16:16:58Z`, hypothesizing O2 first and LTO second. The proposals were
not copied from the deterministic ranking function. The exact model identifier
was not exposed, so provenance records `not-exposed` rather than an invented ID.

AION imported and validated that real response. It made **no model API call**,
sent no context or source to a provider, executed no model-generated commands or
source, and cannot authenticate caller-declared external authorship. The two
available array experiments fit the budget, so this example validates import and
execution, not the superiority of AI ranking or its predictive accuracy.

An actual `--strategy auto` plan with no proposal file also succeeded:
[fallback plan](../.aion/mvp-preview/fallback-plan/plan.json). It records actual
strategy `deterministic`, AI used `false` and an explicit unavailable-provider
reason. It was inspected as a planning example, not executed as another study.

## What remains

The [validation record](mvp-validation.md) covers automated tests and independent
installed-wheel execution. Prior Phase 1–5 records remain preserved.
WSL2 correctness and engineering completion do not validate measurement quality,
native performance, source equivalence for arbitrary inputs or universal gains.
No new measurement-control readiness claim is made by these demos.

Eventual scientific validation requires the existing native Linux readiness and
control protocol, explicit physical-host conditions, separately delimited A/B
windows with fresh seeds, independent confirmation and unchanged promotion
thresholds. Follow [native instructions](phase5-native-instructions.md); the
preview cannot substitute its WSL evidence for that milestone.
