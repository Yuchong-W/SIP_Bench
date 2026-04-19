# Top Conference Readiness (v0.1)

## Objective

This document tracks the "paper-ready trajectory" for SIP-Bench under the current repository state.  
It separates (a) what is already implemented from (b) what remains as research follow-up.

## Current Readiness Statement

SIP-Bench currently has a strong open-source baseline (protocol contract + reproducibility tooling), but not yet a full top-tier publication-level experiment set.

## 55) Third Environment Adapter Integration

- Status: **planned**
- Current anchor: `skillsbench` + `tau-bench` deliver two environments.
- Practical unblocker: add/verify a third concrete adapter under `src/sip_bench/adapters/` and corresponding protocol config in `protocol/`.
- Reuse: `scripts/check_plan_matrix.py` and the same suite-run contract to validate adapter stability once added.

## 56) Cross-Benchmark Protocol Match

- Status: **implemented at table level**
- Cross-benchmark alignment is already represented in existing artifacts:
  - `results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl`
  - `results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl`
  - `docs/results_table_data/protocol_summary_snapshot.csv`
- Planned next: lock a canonical paired protocol suite name convention to make this a direct chart template.

## 57) Statistical Robustness Description

- Status: **implemented**
- Built into metrics pipeline:
  - `fg_std`, `br_std`, `ie_std`, `pds_std`, `nis_std`, `wall_clock_seconds_mean`
- `docs/results_gallery_post_v0_1.md` and `docs/results_table_data/*` retain mean/std rows for reviewer-visible reporting.

## 58) Multiple FG/BR/IE Directions

- Status: **implemented with tracked examples, pending stronger contrast**
- Existing artifacts include replay-only, replay/heldout and repeat bundles that separate infra recovery from protocol effects.
- Action: keep at least two protocol-comparable contrast families in the gallery when next non-ceiling bundle is finalized.

## 59) Reproducible Small-Scale Baseline

- Status: **implemented**
- Current baseline is documented in:
  - `docs/release_checklist_v0_1.md`
  - `docs/evidence_readme.md`
  - `scripts/run_protocol.py` and `scripts/aggregate_metrics.py`
- Requirement: any new baseline must include fixed seed + fixed artifact directory + retry policy.

## 60) Why Not Full-Scale Sweep

- Status: **implemented as policy**
- Full sweeps are deferred to reduce infrastructure variance and preserve reviewer-visible reproducibility.
- For protocol claims, reproducibility of controlled suites is higher value than noisy full-scale averages.

## 61) Paper Structure

- Status: **implemented draft**
- `paper` sections mapped to repo outputs:
  - Introduction: protocol contract and non-clone positioning.
  - Method: protocol contract, suite schema, adapter contract.
  - Evaluation: protocol metrics (FG/BR/IE), reproducibility tables, infra failure signatures.
  - Limitations: ceiling effects, infra bottlenecks, credential sensitivity.

## 62) Leaderboard vs Protocol Baseline Comparison

- Status: **implemented**
- `docs/positioning_note_post_v0_1.md` contains a direct protocol-first vs benchmark-first comparison narrative.
- Required follow-up: one non-ceiling pair with a clearer benchmark-first competitor baseline when available.

## 63) Experimental Limitations and Threat Model

- Status: **implemented**
- `docs/known_limitations.md` and `docs/host_auth_experiment_design.md` hold reproducibility and threat-model assumptions.

## 64) Security and Ethics

- Status: **implemented**
- Credential guidance is explicit:
  - secret files remain `.gitignore` and local
  - `protocol/.env.local` recommendation
  - optional provider-gated paths marked as experimental.

## 65) Contribution Summary Narrative

- Status: **implemented**
- Contribution articulation exists in:
  - `README.md`
  - `launch_materials_v0_1.md`
  - `release_notes_v0_1.md`

## 66) Benchmark-Agnostic Adapter Acceptance Test

- Status: **implemented**
- `tests/test_adapters.py` now includes a benchmark-agnostic contract test that verifies all exported adapters expose the required protocol-facing methods (`discover_tasks`, manifest + validation path, and execution/import entrypoints) as a reusable acceptance gate.

## 67) Reproducibility Protocol

- Status: **implemented for current environments**
- Fixed defaults now included in:
  - suite configs (`seed`, `retry_policy`, explicit env wrappers)
  - `protocol_runner` execution options
  - `scripts/run_protocol.py` command outputs.

## 68) Non-Ceiling Example Description

- Status: **implemented**
- Non-ceiling handling and interpretation are documented in:
  - `docs/known_limitations.md`
  - `docs/host_auth_experiment_design.md`
  - `docs/results_gallery_post_v0_1.md`

## 69) Extra-Routine Posterity Paths

- Status: **not yet implemented**
- Potential submission targets (ICLR/NeurIPS/ACL/EMNLP) should decide whether additional ablations are needed after non-ceiling evidence expands.

## 69) Submission-Target Ablation Matrix

- Status: **implemented**
- A practical pre-submission matrix is now defined to avoid late surprises:

| Venue | Extra ablations likely expected | Current status in this repo |
| --- | --- | --- |
| ICLR | strict ablation against protocol-only vs leaderboard-only baselines; larger repeat sample with confidence intervals | Partially: baseline vs protocol contrast and repeat path have local evidence; larger repeats pending |
| NeurIPS | third-benchmark ablation, robustness to infra variance, and reproducibility reproducibility script audit | Partially: third benchmark protocol path is in scope; infra variance logs are captured; reproducibility script coverage is in place |
| ACL/EMNLP | stronger natural-language interpretation section and task-family breakdown in intro/eval | Partially: task-family breakdown is available; manuscript-ready narrative is pending |

Action: when planning external submission, close this matrix by expanding rows where "Current status" is not fully satisfied.

## 70) Not-Yet Milestones (Release-Neutral)

- Status: **tracked**
- Keep publication-scale experiments as post-release milestones so current release can remain clean and reproducible.
