# SIP-Bench v0.1 Release Checklist

This checklist is for the first public open-source release. It assumes:

1. `Linux-first` official support
2. `Apache-2.0` license
3. `codex` connectivity is not required on the release machine
4. `tau-bench` live runs are optional

## 0. Release-Check Mapping (Executable Audit)

`scripts/run_release_checks.py` now emits a JSON report with per-step status.  
Use this mapping when reviewing the output:

| Run-release step | Mapping | Command |
| --- | --- | --- |
| `unit-tests` | Validation section: "Unit tests pass on the supported environment." | `python3 -m unittest discover -s tests -p test_*.py` |
| `aggregate-dryrun-sample` | Validation section: dry-run aggregation and schema path preparation | `python3 scripts/aggregate_metrics.py --runs results/dryrun/sample_runs.jsonl --out <temp>/sip_summary.jsonl` |
| `import-skillsbench-harbor-job` | Validation section: import smoke path (fixture-backed) | `python3 scripts/run_eval.py import-skillsbench-job ...` |
| `validate-imported-skillsbench-runs` | Validation section: imported fixture schema check | `python3 scripts/validate_records.py --data <temp>/skillsbench_job_runs.jsonl --schema runs` |
| `validate-dryrun-runs` | Validation section: schema validation on tracked dry-run runs | `python3 scripts/validate_records.py --data results/dryrun/sample_runs.jsonl --schema runs` |
| `validate-dryrun-summary` | Validation section: schema validation on tracked dry-run summary | `python3 scripts/validate_records.py --data results/dryrun/summary.jsonl --schema summary` |
| `validate-real-suite-runs` | Validation section: real suite schema check | `python3 scripts/validate_records.py --data results/protocol_runs/skillsbench_oracle_real_suite/combined_runs.jsonl --schema runs` |
| `validate-real-suite-summary` | Validation section: real suite summary validation | `python3 scripts/validate_records.py --data results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl --schema summary` |
| `artifact_hashes` / `artifact_gate` | Release package stability evidence | `python3 scripts/run_release_checks.py` |
| `plan-matrix` | Protocol suite configuration consistency evidence | `python3 scripts/check_plan_matrix.py --protocol-dir protocol --out /tmp/plan_matrix_report.json` |
| `plan-matrix (strict)` | Release blocker variant for missing critical artifacts | `python3 scripts/run_release_checks.py --plan-matrix --plan-matrix-strict --plan-matrix-protocol-dir protocol --plan-matrix-config protocol/skillsbench_oracle_real_suite.json --plan-matrix-config protocol/tau_bench_retail_historical_suite.json --report /tmp/release_check.json` |

## 1. Release Narrative

- [x] README headline states the protocol-layer positioning clearly.
- [x] README explains the novelty beyond "benchmark wrapper".
- [x] README describes the currently supported environments.
- [x] README distinguishes release-critical paths from experimental paths.
- [x] README quickstart uses commands that exist and have been tested.

## 2. Legal And Metadata Files

- [x] `LICENSE` is present and correct.
- [x] `NOTICE` is present and correct.
- [x] `CITATION.cff` is present and references the release repository.
- [x] README explains that upstream benchmark code keeps its own licenses.

## 3. Repository Hygiene

- [x] `.gitignore` covers local caches, local secrets, and run-local prepared task copies.
- [x] Experimental local metadata files are not left unignored.
- [x] The working tree no longer contains accidental formatting churn.
- [x] The tracked files intended for release have been reviewed intentionally.

## 4. Validation

- [x] Unit tests pass on the supported environment.
- [x] Schema validation passes for the tracked example artifacts.
- [x] `python3 scripts/run_release_checks.py` passes on the release branch.
- [x] The documented quickstart has been re-run from a clean checkout.
- [x] `python` vs `python3` assumptions are explicit and consistent.

## 5. Benchmark Artifact Set

- [x] `SkillsBench oracle real suite` artifacts are present and valid.
- [x] `tau-bench historical suite` artifacts are present and valid.
- [x] The release includes one compact proof-of-value result:
  - [x] table, figure, or similarly compact artifact
  - [x] grounded in tracked artifacts or an explicitly documented small run
  - [x] showing what SIP-Bench reveals beyond a single-shot benchmark score
- [x] Experimental `codex` prepared-suite outputs are either:
  - [x] intentionally excluded from release, or
  - [ ] intentionally validated and documented
- [x] The repository documents which `results/` directories are tracked release assets.

## 6. Documentation Quality

- [x] `docs/technical_design.md` matches the current code paths.
- [x] `docs/development_log.md` reflects the real chronology of key milestones.
- [x] `docs/release_manifest.md` matches intended tracked assets.
- [x] `docs/known_limitations.md` reflects the release boundary honestly.

## 7. CI And Automation

- [x] Minimal CI is configured for tests and schema validation.
- [x] CI does not depend on unavailable private services.
- [x] CI status was confirmed green on the reviewed release commit `f1472f0`.

## 8. Release Packaging

- [x] Version number is fixed to `v0.1.0`.
- [x] Release notes summarize:
  - [x] protocol contribution
  - [x] supported benchmarks
  - [x] known limitations
  - [x] next planned steps
- [x] The `v0.1.0` tag was published from reviewed commit `f1472f0`.

## 9. Launch Materials

- [x] A short GitHub release summary is drafted.
- [x] A short public launch post is drafted.
- [x] A short research-oriented summary is drafted.

## 10. Post-Release Backlog

- [x] README follow-ups are captured separately from the release branch.
- [x] `tau-bench` live integration remains a tracked follow-up, not a release blocker.
- [x] `codex` prepared-suite validation remains a tracked follow-up, not a release blocker.
- [x] Paper-writing work is tracked separately from open-source release hygiene.
