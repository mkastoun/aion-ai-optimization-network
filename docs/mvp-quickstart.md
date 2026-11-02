# MVP quickstart

Execute C++ experiments inside Ubuntu on WSL2/Linux or the experimental macOS
path in the [Apple Silicon guide](install-macos-apple-silicon.md). Actual Mac
verification is pending. A physical Linux host is
not required for this preview. WSL results remain experimental; they cannot
satisfy the separate native-validation milestone.

For a shared Windows/WSL checkout, use a separate Ubuntu environment from inside
the repository in Ubuntu:

```bash
source .venv-linux/bin/activate
aion mvp list
aion mvp demo --workload records --strategy deterministic
```

For a new Ubuntu checkout, install the ordinary local toolchain manually:

```bash
sudo apt-get update
sudo apt-get install python3-venv clang llvm lld g++
python3 -m venv .venv-linux
.venv-linux/bin/python -m pip install -e '.[dev]'
.venv-linux/bin/aion mvp demo --workload records --strategy deterministic
```

The default demo selects at most two candidates, uses seven measured pairs and
one warmup per arm in each role, and caps all execution stages together at 2,000
logical external commands / 1,800 elapsed seconds. These defaults are preview
runtime choices; the existing minimum samples/warmups, duration, CV, drift,
2%/combined-MAD floor, regression bound and uncertainty gates are not relaxed.
Compiler/setup costs vary. A complete demo can still be noisy or regress.

The command prints the artifact directory and JSON/Markdown/HTML report paths.
Open `report.html` locally. It needs no server, JavaScript, network connection,
fonts or external resources. Source hashes, output checks, raw timing samples,
failed gates, compiler identities, profiles and command budgets remain in the
adjacent evidence.

## Inspect before execution

```bash
aion mvp list --json
aion mvp plan --workload records --strategy deterministic --output .aion/my-preview
aion mvp inspect --plan .aion/my-preview/plan.json
aion mvp run --plan .aion/my-preview/plan.json --approve
aion mvp report --run .aion/my-preview/job.json --output .aion/my-preview-rerender
```

`plan` performs bounded compiler identity checks but no workload measurements.
`run --approve` authorizes that exact sealed plan. `demo` is the explicit
one-command authorization for its generated bounded plan. Every new attempt
needs a fresh output directory. Reusing a completed/failed execution is rejected;
keep earlier evidence and create an intentional new plan when needed.

## Supply genuine external AI proposals

First export a bounded, discovery-only context. AION does not transmit it:

```bash
aion mvp context --workload array --output .aion/array-context.json
```

Give **only that context file** to your external LLM/coding assistant. Ask it to
return the schema below with the exported fingerprint and approved panel IDs.
It may rank experiments and state hypotheses; it cannot add execution content or
claim a verified improvement. Save the actual response as a new JSON file.

```json
{
  "schema_version": 1,
  "evidence_kind": "mvp-proposals",
  "context_sha256": "REPLACE_WITH_EXPORTED_CONTEXT_SHA256",
  "provenance": {
    "kind": "external-llm",
    "origin": "coding-assistant",
    "provider": "ACTUAL_PROVIDER",
    "model": "ACTUAL_MODEL_OR_NOT_EXPOSED",
    "generated_at": "2026-10-31T00:00:00+00:00",
    "evidence_scope": "discovery-only"
  },
  "proposals": [
    {
      "workload_id": "array",
      "panel_id": "array-o2",
      "reason": "Test whether the simpler optimization level changes this workload relative to O3.",
      "priority": 1,
      "estimated_cost": null
    }
  ]
}
```

The snippet documents the schema; do not label it as a model-generated result.
Use actual caller-supplied provenance, timestamp and fingerprint. Optional cost
is exactly `{"commands":100,"seconds":120}`; it is advisory and cannot raise
execution limits. Lower numeric priorities rank first. Reasons are bounded
single-paragraph text; shell syntax, paths, executable markup, unknown flags,
extra fields, duplicate keys/IDs and unapproved panels are rejected.

```bash
aion mvp demo --workload array --strategy ai-import \
  --context .aion/array-context.json --proposals .aion/actual-ai-response.json \
  --output .aion/array-ai-preview
```

Context options and plan/demo options must match: candidate count, iterations,
warmups, total budget, prior inputs and installed catalog. Changed source bytes
require a fresh export/plan. Accepted input is preserved before execution;
invalid input is retained with a rejection receipt and never executed.

`--strategy auto` or `--strategy ai-import` without a proposal file explicitly
falls back to the deterministic strategy. Reports show **AI used: false** and
the fallback reason. A malformed supplied file is an error, not a silent fallback.
No API service is configured by this preview.

Optional `--prior PATH` inputs must be individual discovery research records
matching the selected workload and source/input contract. Optional
`--diagnostic PATH` inputs must link to those same discovery run IDs. Confirmation
records, confirmation-linked diagnostics and changed contracts are rejected.
Exports include bounded summary numbers and static inline counts; source text,
raw stderr, credentials and filesystem paths are not exported. Local plans and
reports retain provenance paths and should not be sent as AI context.

The [demo results](mvp-demo-results.md) document actual executions, including the
provenance and limitations of the imported example used during development.
