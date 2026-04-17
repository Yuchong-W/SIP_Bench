# Release Manifest

## Target Repository

1. `Yuchong-W/Protocol_Bench`

## Local Release State

1. local git repository repaired on `2026-04-15`
2. local history includes the initial scaffold commit `cb19fed`
3. release-engineering documentation updates are also committed locally
4. remote is configured as `origin = git@github.com:Yuchong-W/Protocol_Bench.git`
5. release branch `main` has been pushed successfully
6. HTTPS transport is still blocked locally, so future publishing from this machine should prefer SSH

## Files Intended For Upload

Core protocol and schemas:

1. `protocol/protocol_spec_v0.md`
2. `schemas/runs.schema.json`
3. `schemas/summary.schema.json`
4. `schemas/protocol_suite.schema.json`

Core source:

1. `src/sip_bench/__init__.py`
2. `src/sip_bench/metrics.py`
3. `src/sip_bench/runner.py`
4. `src/sip_bench/validation.py`
5. `src/sip_bench/protocol_runner.py`
6. `src/sip_bench/adapters/__init__.py`
7. `src/sip_bench/adapters/base.py`
8. `src/sip_bench/adapters/skillsbench.py`
9. `src/sip_bench/adapters/tau_bench.py`

CLI and repository docs:

1. `README.md`
2. `scripts/README.md`
3. `scripts/aggregate_metrics.py`
4. `scripts/run_eval.py`
5. `scripts/run_protocol.py`
6. `scripts/smoke_adapters.py`
7. `scripts/validate_records.py`
8. `scripts/tau311.cmd`
9. `.gitignore`

Engineering docs:

1. `06_protocol_benchmark_plan.md`
2. `docs/technical_design.md`
3. `docs/development_log.md`
4. `docs/decision_log.md`
5. `docs/known_limitations.md`
6. `docs/upstream_surface_notes.md`
7. `docs/release_manifest.md`

Tests and fixtures:

1. `tests/README.md`
2. `tests/metric_cases.json`
3. `tests/test_metrics.py`
4. `tests/test_adapters.py`
5. `tests/test_runner.py`
6. `tests/test_validation.py`
7. `tests/fixtures/echo_task.py`
8. `tests/fixtures/mock_execute_plan.json`
9. `tests/fixtures/skillsbench_registry_sample.json`
10. `tests/fixtures/tau_results_sample.json`
11. `tests/test_protocol_runner.py`
12. `protocol/skillsbench_codex_external_prepared_suite.json`
13. `protocol/tau_bench_retail_historical_suite.json`
14. `protocol/tau_bench_retail_openai_smoke_suite.json`

Sample outputs:

1. `results/dryrun/sample_runs.jsonl`
2. `results/dryrun/summary.jsonl`
3. `results/dryrun/skillsbench_plan.json`
4. `results/dryrun/skillsbench_execution.json`
5. `results/dryrun/tau_runs.jsonl`
6. `results/dryrun/mock_subprocess_execution.json`
7. `results/dryrun/skillsbench_runs_sample.jsonl`
8. `results/dryrun/skillsbench_upstream_withskills.jsonl`
9. `results/protocol_runs/skillsbench_oracle_real_suite/combined_runs.jsonl`
10. `results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl`
11. `results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json`

## Files Intentionally Excluded From Upload

1. `__pycache__/`
2. `results/dryrun/artifacts/`
3. transient mock text outputs under `results/dryrun/`
4. local upstream checkouts under `benchmarks/skillsbench/` and `benchmarks/tau-bench/`
5. broken local `.git/` residue
6. `results/prepared_probes/`
7. `.pydeps311/`
8. `results/dryrun/pip_probe/`
9. ad-hoc tau protocol smoke outputs under `results/protocol_runs/tau_bench_retail_openai_smoke_suite/`


## Update 2026-04-15

Additional source and script files now intended for upload:

1. `scripts/harbor312.cmd`
2. `tests/fixtures/skillsbench_harbor_job_sample/result.json`
3. `tests/fixtures/skillsbench_harbor_job_sample/citation-check__fixture001/result.json`
4. `tests/fixtures/skillsbench_harbor_job_sample/court-form-filling__fixture002/result.json`
5. `protocol/skillsbench_codex_external_prepared_suite.json`

Additional sample outputs expected after the next real smoke run:

1. `results/dryrun/skillsbench_hydration.json`
2. `results/dryrun/skillsbench_execution.json`
3. `results/dryrun/skillsbench_job_runs.jsonl`

Additional local-only exclusions:

1. `.uv-cache/`
2. `results/real_jobs*/`
3. `results/prepared_probes/`


## Real Smoke Outputs

Generated and suitable for upload:

1. `results/dryrun/skillsbench_real_smoke_plan.json`
2. `results/dryrun/skillsbench_real_smoke_hydration.json`
3. `results/dryrun/skillsbench_real_smoke_execution.json`
4. `results/dryrun/skillsbench_real_smoke_runs.jsonl`
5. `results/dryrun/skillsbench_job_runs.jsonl`


## Real Successful Smoke Outputs

Generated and suitable for upload:

1. `results/dryrun/skillsbench_dialogue_smoke_plan.json`
2. `results/dryrun/skillsbench_dialogue_smoke_hydration.json`
3. `results/dryrun/skillsbench_dialogue_smoke_execution.json`
4. `results/dryrun/skillsbench_dialogue_smoke_runs.jsonl`
5. `results/dryrun/skillsbench_dialogue_timeout4_plan.json`
6. `results/dryrun/skillsbench_dialogue_timeout4_hydration.json`
7. `results/dryrun/skillsbench_dialogue_timeout4_execution.json`
8. `results/dryrun/skillsbench_dialogue_timeout4_runs.jsonl`


## Real Protocol Suite Outputs

Generated and suitable for upload:

1. `protocol/skillsbench_oracle_real_suite.json`
2. `results/protocol_runs/skillsbench_oracle_real_suite/combined_runs.jsonl`
3. `results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl`
4. `results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json`
5. `results/protocol_runs/skillsbench_oracle_real_suite/plans/t0_replay.json`
6. `results/protocol_runs/skillsbench_oracle_real_suite/plans/t0_heldout.json`
7. `results/protocol_runs/skillsbench_oracle_real_suite/plans/t1_replay.json`
8. `results/protocol_runs/skillsbench_oracle_real_suite/plans/t1_heldout.json`
9. `results/protocol_runs/skillsbench_oracle_real_suite/hydration/t0_replay.json`
10. `results/protocol_runs/skillsbench_oracle_real_suite/hydration/t0_heldout.json`
11. `results/protocol_runs/skillsbench_oracle_real_suite/hydration/t1_replay.json`
12. `results/protocol_runs/skillsbench_oracle_real_suite/hydration/t1_heldout.json`
13. `results/protocol_runs/skillsbench_oracle_real_suite/execution/t0_replay.json`
14. `results/protocol_runs/skillsbench_oracle_real_suite/execution/t0_heldout.json`
15. `results/protocol_runs/skillsbench_oracle_real_suite/execution/t1_replay.json`
16. `results/protocol_runs/skillsbench_oracle_real_suite/execution/t1_heldout.json`
17. `results/protocol_runs/skillsbench_oracle_real_suite/runs/t0_replay.jsonl`
18. `results/protocol_runs/skillsbench_oracle_real_suite/runs/t0_heldout.jsonl`
19. `results/protocol_runs/skillsbench_oracle_real_suite/runs/t1_replay.jsonl`
20. `results/protocol_runs/skillsbench_oracle_real_suite/runs/t1_heldout.jsonl`


## Publication Sync Note

Current publication expectation:

1. push directly from local `main` to `origin/main`
2. use SSH transport on this machine
3. do not assume GitHub CLI or PR automation is available locally

## Update 2026-04-17

Additional runtime and protocol files now intended for upload:

1. `scripts/tau311.cmd`
2. `protocol/tau_bench_retail_historical_suite.json`
3. `protocol/tau_bench_retail_openai_smoke_suite.json`

Additional local-only exclusions:

1. `.pydeps311/`
2. `results/dryrun/pip_probe/`
3. transient tau smoke preflight outputs under `results/protocol_runs/tau_bench_retail_openai_smoke_suite/`
