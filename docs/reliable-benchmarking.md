# Phase 2: reliable benchmarking

AION 0.2 measures computation inside the C++ process. Phase 1 wall-time reports remain readable, but their medians cannot be compared with Phase 2 medians: setup is excluded and the workload layout has changed.

## What a sample means

One **unit** runs the workload's fixed size, seed, and rounds once. Input buffers for those rounds are generated before timing. Before each timed batch, mutable inputs are restored: arrays/strings are copied, sorting gets unsorted input, matrices are zeroed, and hash maps get fresh empty containers including fresh bucket capacity. Hash-map insert/lookup/erase allocations and checksum scans are computation and remain timed. Cleanup and input generation are setup.

The C++ harness uses `std::chrono::steady_clock`, compiler memory barriers, runtime inputs, and an observable unsigned checksum. It reports integer nanoseconds for compute and setup, batch count, and checksum through a versioned JSON protocol. Process launch, exit observation, setup, and teardown are excluded from compute time. Total process wall time and peak RSS are still recorded separately. Prepared input buffers increase memory usage compared with Phase 1; peak RSS covers the whole process.

Legacy `size seed rounds` invocation still prints the same checksum. `size seed rounds --measure batches` repeats the unit and prints timing JSON. The expected repeated checksum is the independently computed unit checksum multiplied by batches modulo 2^64. AION rejects wrong output, process failures, malformed timing JSON, mismatched batches, nonpositive compute times, and internal times exceeding process wall time.

## Calibration

Every successfully compiled and verified configuration is calibrated separately. Each attempt runs three discarded pilots, scales the batch count toward 375 ms of computation, and accepts a pilot median between 250 and 500 ms. Calibration is bounded by eight attempts, 65,536 batches, process timeouts, and memory/output limits. Failure is recorded and blocks measurement/promotion. All pilot outputs must pass correctness.

Different configurations may use different batch counts to stay in the duration band; every comparison divides compute seconds by batches, so it compares equal work. No pilot enters the measured sample distribution. Calibration, warmups, and measured executions all restore the same inputs. Samples outside the target band are retained and reported; a physical median below 250 ms blocks Phase 2 promotion. A longer-than-target sample is recorded rather than discarded.

## Randomization and pairing

Each candidate gets an immediately adjacent baseline execution in every iteration. Baseline/candidate order is shuffled with balanced AB/BA counts (difference at most one), and candidate-pair order is shuffled within each round. The baseline is rerun for each candidate, rather than sharing a distant baseline measurement. Pair IDs, order, iteration, phase, and seeds are preserved. This reduces exposure to time trends but cannot eliminate background load or thermal effects.

The default is eleven measured pairs per candidate and two warmup pairs. The global baseline summary aggregates all its pairs; each candidate's comparison uses only its own matched baseline partners.

## Uncertainty and unchanged promotion limits

Results include median, MAD, CV, first-half/second-half median drift, outlier counts, physical sample duration, and paired improvement intervals. No samples or outliers are removed. A reported outlier count uses a three-scaled-MAD diagnostic (nonmedian values when MAD is zero); it is not a reason to delete measurements.

For each adjacent pair, AION calculates `1 - candidate_unit_time / baseline_unit_time`. It resamples circular blocks of these paired effects and takes the median effect, using a square-root-of-pair-count block length and 10,000 resamples by default. Keeping adjacent effects together partially accounts for serial dependence. The seed and block length are recorded. These empirical percentile intervals have approximate coverage: small samples, nonstationary behavior, and the heuristic block length limit inference. They are not a formal proof of improvement.

The declared comparison family is selected candidates × selected workloads, including unavailable candidates conservatively. A Bonferroni adjustment divides the nominal 5% error budget across that family. This arithmetic cannot make an imperfect bootstrap interval exact; the [NIST description of simultaneous intervals](https://www.itl.nist.gov/div898/handbook/prc/section4/prc463.htm) explains the adjustment when interval coverage assumptions hold.

Promotion still requires at least five measurements, a warmup, correct outputs, CV at most 5%, an observed improvement above **both 2% and twice the combined relative MAD**, and no workload regression beyond 5%. Phase 2 adds restrictions: the adjusted lower improvement bound must clear that improvement floor, the interval must exclude an unacceptable regression, and median drift above 5% blocks acceptance. Looser exploration settings cannot lower the 2% floor, raise the 5% regression/CV caps, or lower Phase 2's 250 ms minimum for promotion.

## Independent inputs and confirmation

The manifest contains independent Python-generated expectations for empty/small/alternate cases, full measurement inputs (seed 42), PGO training inputs (271828), and equally sized full confirmation inputs (314159). All configurations must pass all cases before timing.

Confirmation rebuilds in fresh temporary directories, regenerates PGO profiles when applicable, recalibrates, changes the scheduling/bootstrap seed, and uses the held-out confirmation input seed. Registry checks require matching compiler/environment/limits/flags/source fingerprints and different scheduling and input seeds. Both runs must independently satisfy promotion criteria on the same suite and improve at least one common workload.

`aion optimize --confirm-all` records fresh confirmation even for negative or inconclusive candidates. Without that flag, it retains the previous behavior of confirming candidates eligible for promotion. `aion report --result DISCOVERY.json --confirmation CONFIRMATION.json` renders both runs together and rejects reused IDs/seeds or incompatible workloads.

## LTO and PGO

The allowlist adds `-flto`. Each LTO configuration is compiled, linked, and executed before measurement. Missing linker support becomes an explicit unsupported result, as LTO requires [linker participation](https://llvm.org/docs/GoldPlugin.html).

The `pgo` and `pgo-lto` candidates use Clang's [instrument/train/merge/rebuild workflow](https://clang.llvm.org/docs/UsersManual.html#profile-guided-optimization). The adapter requires `llvm-profdata` with the same major version as Clang, generates profiles only from trusted local bundled workloads on separate training inputs, validates training output, merges fresh raw profiles, and rebuilds with the resulting profile. It records tool version, commands, training input/output, raw and merged profile hashes, and build/training costs. Unsupported runtimes or profiling tools are recorded without pretending PGO ran.

Profiling flags and file paths are internal controlled recipe arguments, not arbitrary preset flags. Instrumented binaries and training timings are never used as performance measurements. Workload-specific PGO profiles cannot become flag-only presets for unrelated applications. They remain research evidence; ordinary and LTO presets retain local reuse and independent verification.

## Reproduce

In the Ubuntu project directory:

```bash
source .aion/venv-linux/bin/activate
python -m pip install -e '.[dev]'
AION_REQUIRE_COMPILER=1 python -m pytest -q
aion optimize --benchmark all --candidate o2 --candidate lto --candidate pgo --candidate pgo-lto \
  --iterations 11 --warmups 2 --seed 42217 --confirm-all
aion report --latest
```

Use an idle machine with consistent power and cooling conditions. The runner does not set CPU affinity, governor, or turbo policy and does not isolate the host. Record and interpret noisy or inconclusive outcomes rather than rerunning until a favorable result appears. AI optimization, remote execution, and public registry updates remain outside this phase.
