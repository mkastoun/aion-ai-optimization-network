# AION measurement-system controls

Four real experiments retain 352 measured executions, all passing correctness, across sorting and matrix. Placement order is balanced: unpinned/pinned with scheduling seed 53100 and input seed 42, then pinned/unpinned with scheduling seed 53101 and input seed 314159. Pinned means verified guest logical CPU 0. Each control gets eleven paired measurements and two warmups.

Of eight A/A comparisons, four are consistent with no clear change and four are inconclusive. None produces a false-positive improvement signal. Of eight known slowdowns, three pass the unchanged quality gates and are detected as regressions; five remain inconclusive. This small experiment does not establish a zero false-positive rate. Pinning did not consistently remove variability.

The raw JSON and individual detailed reports are preserved in [the controls result directory](../.aion/phase3-controls/results/). All binary-identity checks pass. Controls are explicitly excluded from preset promotion, independently of the false-positive audit.

A/A uses a byte-identical baseline binary. The negative control uses the same binary and checksum plus an explicitly recorded 50 ms elapsed busy-loop delay inside each timed unit. This uses the steady clock, not a consumed-CPU-time clock. Controls can never become optimization presets.

| Run | Input seed | CPU request | Workload | Control | Identical binary | Outcome |
|---|---:|---|---|---|---|---|
| 20261030T231154-11ef27a24d | 42 | None | sorting | control-aa | True | consistent_with_AA |
| 20261030T231154-11ef27a24d | 42 | None | sorting | control-slowdown | True | verified_regression_control |
| 20261030T231154-11ef27a24d | 42 | None | matrix | control-aa | True | consistent_with_AA |
| 20261030T231154-11ef27a24d | 42 | None | matrix | control-slowdown | True | verified_regression_control |
| 20261030T231315-d0bab9b7ef | 42 | [0] | sorting | control-aa | True | consistent_with_AA |
| 20261030T231315-d0bab9b7ef | 42 | [0] | sorting | control-slowdown | True | verified_regression_control |
| 20261030T231315-d0bab9b7ef | 42 | [0] | matrix | control-aa | True | inconclusive_or_unexpected |
| 20261030T231315-d0bab9b7ef | 42 | [0] | matrix | control-slowdown | True | inconclusive |
| 20261030T231433-386e950430 | 314159 | [0] | sorting | control-aa | True | inconclusive_or_unexpected |
| 20261030T231433-386e950430 | 314159 | [0] | sorting | control-slowdown | True | inconclusive |
| 20261030T231433-386e950430 | 314159 | [0] | matrix | control-aa | True | inconclusive_or_unexpected |
| 20261030T231433-386e950430 | 314159 | [0] | matrix | control-slowdown | True | inconclusive |
| 20261030T231553-bebe4285e2 | 314159 | None | sorting | control-aa | True | consistent_with_AA |
| 20261030T231553-bebe4285e2 | 314159 | None | sorting | control-slowdown | True | inconclusive |
| 20261030T231553-bebe4285e2 | 314159 | None | matrix | control-aa | True | inconclusive_or_unexpected |
| 20261030T231553-bebe4285e2 | 314159 | None | matrix | control-slowdown | True | inconclusive |

Observed A/A false-positive improvement classifications: **0**. These classifications are audited even though publishing controls is prohibited. A lack of observed false positives does not prove an engine-wide error rate or equivalence.
Known slowdowns are called verified only when all unchanged measurement-quality and regression gates permit it. Noise, short durations, or drift remain inconclusive. Pinned/unpinned estimates are never pooled.

## Run `20261030T231154-11ef27a24d`

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Requested affinity: `disabled`; verified pinned samples: 0/88. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Noisy configuration summaries: 0/6; drifting: 0/6.
Load average at start/end: `[0.091796875, 0.0283203125, 0.0078125]` / `[0.7421875, 0.2470703125, 0.08837890625]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
Governor, turbo, and system power settings were not changed. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

## Run `20261030T231315-d0bab9b7ef`

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Requested affinity: `[0]`; verified pinned samples: 88/88. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Noisy configuration summaries: 2/6; drifting: 0/6.
Load average at start/end: `[0.7421875, 0.2470703125, 0.08837890625]` / `[1.013671875, 0.4462890625, 0.1728515625]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
Governor, turbo, and system power settings were not changed. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

## Run `20261030T231433-386e950430`

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Requested affinity: `[0]`; verified pinned samples: 88/88. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Noisy configuration summaries: 4/6; drifting: 2/6.
Load average at start/end: `[1.013671875, 0.4462890625, 0.1728515625]` / `[1.00146484375, 0.57958984375, 0.244140625]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
Governor, turbo, and system power settings were not changed. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.

## Run `20261030T231553-bebe4285e2`

## Host stability and effective controls

Evidence type: **wsl2**. WSL/hypervisor affinity controls guest logical CPUs, not verified physical host placement.
Stable host fingerprint: `b6ab3145d02cdbff021854f85b69b7f4749e79a0c6a2951f4766598082fccf0a`.
Requested affinity: `disabled`; verified pinned samples: 0/88. When disabled, an observed allowed mask does not mean CPU pinning was applied.
Noisy configuration summaries: 3/6; drifting: 3/6.
Load average at start/end: `[1.00146484375, 0.57958984375, 0.244140625]` / `[1.046875, 0.697265625, 0.3154296875]`.
Unavailable observations: sysfs frequency/governor, thermal. Available values and their sysfs/proc origins are preserved in JSON.
Governor, turbo, and system power settings were not changed. Build/linker versions, binaries, sources, and PGO profile hashes are recorded separately. No samples are pooled across runs.
