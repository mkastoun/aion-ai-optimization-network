# AION measurement-quality evidence

Run: `20261031T074352-80f556d13d`; status: **completed**.
Session: `5237af24cc3b4d3ca125761e096d9238`; environment: **wsl2**.
This diagnostic record cannot create optimization presets. No primary timing samples are pooled.

disabled: no timing samples or effect estimates are pooled; outcome counts are stratified by compatible environment/design
Intervals describe observed control outcomes using a binomial approximation, not a universal false-positive rate. Workloads and runs within sessions are correlated.

## Benchmark readiness

- validation_passed_on_available_environment: True
- native_linux_evidence_available: False
- measurement_quality_checks_passed: False
- assessment: measurement environment not yet validated
- native_linux_control_study_passed: False
- native_linux_performance_validated: False
- native_linux_performance_status: pending: no native Linux measurements in this study
- insufficient_or_inconclusive_evidence: True
- note: Readiness is scoped to selected control workloads, hosts, placements, sessions and inputs. It is not proof of a universal error rate or blanket permission for AI optimization.

## Stratum 0: wsl2, CPUs None
Sessions: 2; runs: 4; cross-session design complete: True.
Measurement quality checks passed: **False**.

| Descriptive rate | Count/total | Fraction | Approximate 95% interval |
|---|---:|---:|---|
| aa_false_positive_all | 0/12 | 0.0% | [0.0%, 24.2%] |
| aa_false_positive_quality_valid | 0/8 | 0.0% | [0.0%, 32.4%] |
| slowdown_detected_all | 9/12 | 75.0% | [46.8%, 91.1%] |
| slowdown_detected_quality_valid | 9/9 | 100.0% | [70.1%, 100.0%] |
| inconclusive_all | 7/24 | 29.2% | [14.9%, 49.2%] |

| Run | Session | Workload | Control | Outcome | Failed gates | CV baseline/candidate % | Paired interval % |
|---|---|---|---|---|---|---|---|
| 20261031T024808-16604ed1ec | a407629a605c4cbd88e960d19ca09b87 | matrix | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 3.77/2.58 | [-1.11, 1.44] |
| 20261031T024808-16604ed1ec | a407629a605c4cbd88e960d19ca09b87 | matrix | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 4.00/0.51 | [-704.93, -646.93] |
| 20261031T024808-16604ed1ec | a407629a605c4cbd88e960d19ca09b87 | records | control-aa | inconclusive | variability, drift, improvement_floor_and_uncertainty | 9.04/8.84 | [-4.20, 0.27] |
| 20261031T024808-16604ed1ec | a407629a605c4cbd88e960d19ca09b87 | records | control-slowdown | inconclusive | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | 17.81/1.56 | [-704.94, -602.64] |
| 20261031T024808-16604ed1ec | a407629a605c4cbd88e960d19ca09b87 | logs | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 4.17/2.05 | [-0.48, 1.84] |
| 20261031T024808-16604ed1ec | a407629a605c4cbd88e960d19ca09b87 | logs | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 3.43/2.20 | [-324.47, -317.67] |
| 20261031T025446-d8c3d617f2 | a407629a605c4cbd88e960d19ca09b87 | matrix | control-aa | inconclusive | variability, drift, improvement_floor_and_uncertainty | 13.96/7.28 | [-2.13, 1.30] |
| 20261031T025446-d8c3d617f2 | a407629a605c4cbd88e960d19ca09b87 | matrix | control-slowdown | inconclusive | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | 15.43/7.23 | [-569.31, -517.06] |
| 20261031T025446-d8c3d617f2 | a407629a605c4cbd88e960d19ca09b87 | records | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 2.51/2.41 | [-1.79, 1.09] |
| 20261031T025446-d8c3d617f2 | a407629a605c4cbd88e960d19ca09b87 | records | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.16/0.27 | [-668.21, -635.59] |
| 20261031T025446-d8c3d617f2 | a407629a605c4cbd88e960d19ca09b87 | logs | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 1.51/1.44 | [-0.28, 1.27] |
| 20261031T025446-d8c3d617f2 | a407629a605c4cbd88e960d19ca09b87 | logs | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 1.71/0.52 | [-327.37, -317.24] |
| 20261031T031311-377df4b714 | 8ebc2d20d2d44e1aab1f49b496c4e39e | matrix | control-aa | inconclusive | variability, improvement_floor_and_uncertainty | 11.10/14.01 | [-3.74, 2.91] |
| 20261031T031311-377df4b714 | 8ebc2d20d2d44e1aab1f49b496c4e39e | matrix | control-slowdown | inconclusive | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | 12.85/1.56 | [-591.39, -446.63] |
| 20261031T031311-377df4b714 | 8ebc2d20d2d44e1aab1f49b496c4e39e | records | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 3.03/2.19 | [-0.96, 2.74] |
| 20261031T031311-377df4b714 | 8ebc2d20d2d44e1aab1f49b496c4e39e | records | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.71/0.27 | [-706.39, -678.76] |
| 20261031T031311-377df4b714 | 8ebc2d20d2d44e1aab1f49b496c4e39e | logs | control-aa | inconclusive | drift, improvement_floor_and_uncertainty | 3.13/4.32 | [-0.49, 0.59] |
| 20261031T031311-377df4b714 | 8ebc2d20d2d44e1aab1f49b496c4e39e | logs | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.25/0.43 | [-352.05, -336.12] |
| 20261031T031931-623d6784e6 | 8ebc2d20d2d44e1aab1f49b496c4e39e | matrix | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 0.76/1.55 | [-1.89, -0.04] |
| 20261031T031931-623d6784e6 | 8ebc2d20d2d44e1aab1f49b496c4e39e | matrix | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 1.81/0.78 | [-603.26, -584.23] |
| 20261031T031931-623d6784e6 | 8ebc2d20d2d44e1aab1f49b496c4e39e | records | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 0.81/0.79 | [-1.43, 1.70] |
| 20261031T031931-623d6784e6 | 8ebc2d20d2d44e1aab1f49b496c4e39e | records | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 1.58/0.16 | [-701.63, -695.24] |
| 20261031T031931-623d6784e6 | 8ebc2d20d2d44e1aab1f49b496c4e39e | logs | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 0.78/1.06 | [-0.81, 0.20] |
| 20261031T031931-623d6784e6 | 8ebc2d20d2d44e1aab1f49b496c4e39e | logs | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 1.14/0.37 | [-348.10, -339.48] |

## Stratum 1: wsl2, CPUs [0]
Sessions: 2; runs: 4; cross-session design complete: True.
Measurement quality checks passed: **False**.

| Descriptive rate | Count/total | Fraction | Approximate 95% interval |
|---|---:|---:|---|
| aa_false_positive_all | 0/12 | 0.0% | [0.0%, 24.2%] |
| aa_false_positive_quality_valid | 0/6 | 0.0% | [0.0%, 39.0%] |
| slowdown_detected_all | 9/12 | 75.0% | [46.8%, 91.1%] |
| slowdown_detected_quality_valid | 9/9 | 100.0% | [70.1%, 100.0%] |
| inconclusive_all | 9/24 | 37.5% | [21.2%, 57.3%] |

| Run | Session | Workload | Control | Outcome | Failed gates | CV baseline/candidate % | Paired interval % |
|---|---|---|---|---|---|---|---|
| 20261031T025021-78a97a7f38 | a407629a605c4cbd88e960d19ca09b87 | matrix | control-aa | inconclusive | variability, improvement_floor_and_uncertainty | 14.68/5.14 | [-1.89, 0.95] |
| 20261031T025021-78a97a7f38 | a407629a605c4cbd88e960d19ca09b87 | matrix | control-slowdown | inconclusive | variability, acceptable_regression_bound, improvement_floor_and_uncertainty | 9.13/2.06 | [-584.68, -536.10] |
| 20261031T025021-78a97a7f38 | a407629a605c4cbd88e960d19ca09b87 | records | control-aa | inconclusive | variability, improvement_floor_and_uncertainty | 15.52/3.56 | [-1.43, 6.36] |
| 20261031T025021-78a97a7f38 | a407629a605c4cbd88e960d19ca09b87 | records | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 4.04/0.57 | [-670.40, -640.41] |
| 20261031T025021-78a97a7f38 | a407629a605c4cbd88e960d19ca09b87 | logs | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 1.39/1.60 | [-0.74, -0.02] |
| 20261031T025021-78a97a7f38 | a407629a605c4cbd88e960d19ca09b87 | logs | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.09/0.58 | [-333.21, -315.03] |
| 20261031T025231-216c95c3e1 | a407629a605c4cbd88e960d19ca09b87 | matrix | control-aa | inconclusive | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | 19.97/24.82 | [-9.61, 13.22] |
| 20261031T025231-216c95c3e1 | a407629a605c4cbd88e960d19ca09b87 | matrix | control-slowdown | inconclusive | variability, drift, acceptable_regression_bound, improvement_floor_and_uncertainty | 17.51/3.94 | [-589.96, -370.67] |
| 20261031T025231-216c95c3e1 | a407629a605c4cbd88e960d19ca09b87 | records | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 2.68/3.52 | [-3.80, 3.93] |
| 20261031T025231-216c95c3e1 | a407629a605c4cbd88e960d19ca09b87 | records | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.17/0.65 | [-669.01, -657.16] |
| 20261031T025231-216c95c3e1 | a407629a605c4cbd88e960d19ca09b87 | logs | control-aa | inconclusive | variability, improvement_floor_and_uncertainty | 7.61/5.21 | [-2.06, 2.21] |
| 20261031T025231-216c95c3e1 | a407629a605c4cbd88e960d19ca09b87 | logs | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.15/0.31 | [-324.59, -320.86] |
| 20261031T031521-f68e44950b | 8ebc2d20d2d44e1aab1f49b496c4e39e | matrix | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 1.82/2.31 | [-2.00, 1.11] |
| 20261031T031521-f68e44950b | 8ebc2d20d2d44e1aab1f49b496c4e39e | matrix | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 1.98/0.25 | [-610.68, -588.80] |
| 20261031T031521-f68e44950b | 8ebc2d20d2d44e1aab1f49b496c4e39e | records | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 1.55/2.25 | [-1.03, 0.91] |
| 20261031T031521-f68e44950b | 8ebc2d20d2d44e1aab1f49b496c4e39e | records | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.56/0.37 | [-704.88, -680.79] |
| 20261031T031521-f68e44950b | 8ebc2d20d2d44e1aab1f49b496c4e39e | logs | control-aa | inconclusive | variability, improvement_floor_and_uncertainty | 3.30/5.38 | [-1.99, 1.47] |
| 20261031T031521-f68e44950b | 8ebc2d20d2d44e1aab1f49b496c4e39e | logs | control-slowdown | inconclusive | drift, acceptable_regression_bound, improvement_floor_and_uncertainty | 3.06/1.14 | [-348.10, -328.44] |
| 20261031T031726-86a927c090 | 8ebc2d20d2d44e1aab1f49b496c4e39e | matrix | control-aa | inconclusive | variability, improvement_floor_and_uncertainty | 5.58/6.09 | [-0.80, 1.44] |
| 20261031T031726-86a927c090 | 8ebc2d20d2d44e1aab1f49b496c4e39e | matrix | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.55/0.54 | [-599.66, -568.28] |
| 20261031T031726-86a927c090 | 8ebc2d20d2d44e1aab1f49b496c4e39e | records | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 4.47/1.80 | [-0.24, 5.15] |
| 20261031T031726-86a927c090 | 8ebc2d20d2d44e1aab1f49b496c4e39e | records | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 2.47/0.18 | [-701.80, -684.35] |
| 20261031T031726-86a927c090 | 8ebc2d20d2d44e1aab1f49b496c4e39e | logs | control-aa | consistent_with_AA | improvement_floor_and_uncertainty | 1.51/1.55 | [-1.63, 1.24] |
| 20261031T031726-86a927c090 | 8ebc2d20d2d44e1aab1f49b496c4e39e | logs | control-slowdown | detected_slowdown | acceptable_regression_bound, improvement_floor_and_uncertainty | 1.32/0.37 | [-343.64, -334.08] |

Descriptive outcome counts do not establish equivalence, a universal false-positive rate, or validated physical isolation. Start/end host observations and source JSON hashes remain in the audit.
