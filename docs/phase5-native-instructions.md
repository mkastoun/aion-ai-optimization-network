# Exact native Linux replication instructions

Use a physical Linux computer that you own or have permission to benchmark.
WSL2, Docker, cloud VMs and GitHub-hosted runners do not satisfy this milestone.
Detection is observational; confirm the physical host separately. Record power
source, background work, ambient/thermal conditions, SMT/CPU placement and
observation windows. AION records exposed policies and constraints; it does not
change governors, priorities, cgroups, turbo, SMT, privileges or PMU permissions.

On Ubuntu 24.04, install prerequisites manually if missing:

```bash
sudo apt-get update
sudo apt-get install python3-venv clang llvm g++
python3 -m venv .venv-native
.venv-native/bin/python -m pip install -e '.[dev]'
.venv-native/bin/python -m pytest -q
```

From the checkout, choose and document a CPU. `auto` selects an allowed logical
CPU; it does not promise physical isolation. Replace `auto` consistently with a
chosen CPU ID when appropriate. Optional counters may be unavailable without
affecting ordinary correctness execution; retain their errors. Do not run other
builds/tests/profiling alongside measured studies.

In observation window A:

```bash
.venv-native/bin/python tools/replicate_linux.py \
  --store .aion/native5/a --seed 71000 --cpus auto --role discovery \
  --require-native --label 'physical Linux window A' \
  --native-host-note 'Physical machine identity, power/thermal/background conditions and window A details' \
  --stage all
```

This runs strict native preflight; two original controls on matrix/records/logs;
two distribution controls on image/kv; all ten O3/O2/LTO/PGO/PGO+LTO discovery
timings; and separate all-ten sanitizers/differential checks. Failed control or
correctness stages remain in the command/exit journal. Investigate a failed
stage before deliberately continuing; keep every earlier result. Individual
stages can be run with the same store/session, without changing stored evidence.

Declare the bounded research matrix before observing its timing:

```bash
.venv-native/bin/aion research declare --output .aion/native5/research-plan.json \
  --seed 71300 --confirmation-seed 72300 --cpus auto \
  --iterations 11 --warmups 2 --commands 2500 --seconds 3600
.venv-native/bin/python tools/replicate_linux.py \
  --store .aion/native5/a --seed 71000 --cpus auto --role discovery \
  --require-native --stage research --research-store .aion/native5/research \
  --research-declaration .aion/native5/research-plan.json
.venv-native/bin/aion --store .aion/native5/research-validation research validate \
  --session-file .aion/native5/a/session.json --cpus auto
```

Close window A. In a genuinely separate observation window B, document the new
conditions and use a new store/session. Different IDs created back-to-back are
not by themselves evidence of independent host conditions. Do not overlap runs.

```bash
.venv-native/bin/python tools/replicate_linux.py \
  --store .aion/native5/b --seed 72000 --cpus auto --role confirmation \
  --require-native --label 'physical Linux window B' \
  --native-host-note 'Physical machine identity, power/thermal/background conditions and window B details' \
  --stage all
.venv-native/bin/python tools/replicate_linux.py \
  --store .aion/native5/b --seed 72000 --cpus auto --role confirmation \
  --require-native --stage research --research-store .aion/native5/research \
  --research-declaration .aion/native5/research-plan.json
.venv-native/bin/python tools/replicate_linux.py \
  --store .aion/native5/b --peer-store .aion/native5/a --seed 72000 --stage report
```

The native report preserves individual estimates, recomputes relevant control
quality, checks all-ten coverage/validation, separate documented observation
windows, held-out seeds, provenance, duration/CV/drift/correctness/uncertainty
gates and compatibility. A completed command does not imply native validation
passed. Inspect `native_performance_validated`, `failed_gates` and each stratum.
Known candidate regressions may be valid findings; they never qualify presets.

For research reports, find actual study/validation/quality IDs in `results/`;
do not substitute the latest individual panel for the study journal. Produce a
source-linked quality record first, then attach separate diagnostics if wanted:

```bash
.venv-native/bin/aion --store .aion/native5/quality quality \
  --directory .aion/native5/a/results --directory .aion/native5/b/results \
  --validation .aion/native5/b/results/VALIDATION_ID.json
.venv-native/bin/aion --store .aion/native5/diagnostics research diagnose \
  --study .aion/native5/research/results/DISCOVERY_STUDY_ID.json \
  --session-file .aion/native5/b/session.json \
  --panel records-lto --panel logs-pgo --panel matrix-lto
.venv-native/bin/aion --store .aion/native5/reports research report \
  --discovery .aion/native5/research/results/DISCOVERY_STUDY_ID.json \
  --confirmation .aion/native5/research/results/CONFIRMATION_STUDY_ID.json \
  --quality .aion/native5/quality/results/QUALITY_ID.json \
  --validation .aion/native5/research-validation/results/RESEARCH_VALIDATION_ID.json \
  --diagnostic .aion/native5/diagnostics/results/DIAGNOSTIC_ID.json
```

Do not promote program-specific PGO or research sources into universal flag
presets. Retain unsupported/inconclusive outcomes and all attempts. Review Phase
6 readiness separately; a control-only report cannot certify all-ten native
timing or authorize AI optimization.
