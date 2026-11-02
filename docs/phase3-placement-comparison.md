# AION independent-run comparison

Runs: `20261030T231154-11ef27a24d` / `20261030T231315-d0bab9b7ef`.
Compatible for independent confirmation: **False**.
Raw samples are never pooled. Incompatible hosts or CPU controls are side-by-side diagnostics only.
Reasons: requested CPU placement differs
Unavailable provenance: none listed

| Workload | Candidate | First classification | Second classification |
|---|---|---|---|
| sorting | control-aa | no_clear_change | no_clear_change |
| sorting | control-slowdown | regression | regression |
| matrix | control-aa | no_clear_change | inconclusive |
| matrix | control-slowdown | regression | inconclusive |

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Requested affinity: `disabled`; verified pinned samples: 0/88. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Recorded verification methods: `['actual executable sched_getaffinity before/after compute']`. Verification is a snapshot, not exclusive CPU ownership.
Different CPU endpoints observed: 3/88; equal endpoints do not prove no intermediate migration.
Noisy configuration summaries: 0/6; drifting: 0/6.
Load average at start/end: `[0.091796875, 0.0283203125, 0.0078125]` / `[0.7421875, 0.2470703125, 0.08837890625]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.


## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Requested affinity: `[0]`; verified pinned samples: 88/88. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Recorded verification methods: `['actual executable sched_getaffinity before/after compute']`. Verification is a snapshot, not exclusive CPU ownership.
Different CPU endpoints observed: 0/88; equal endpoints do not prove no intermediate migration.
Noisy configuration summaries: 2/6; drifting: 0/6.
Load average at start/end: `[0.7421875, 0.2470703125, 0.08837890625]` / `[1.013671875, 0.4462890625, 0.1728515625]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
AION changed no governor, turbo, or system power settings. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.
