# Release Manifest

## Release Intent

This manifest is now scoped to the first public open-source release, not to every local experiment.

Release priorities:

1. present `SIP-Bench` as protocol-layer research infrastructure
2. keep the public surface reviewable and reproducible
3. anchor the release on validated artifacts that do not require `codex` connectivity or private API access

Current release-critical evidence:

1. `SkillsBench oracle real suite`
2. `tau-bench historical/import-only suite`

Current experimental but non-blocking areas:

1. `SkillsBench codex external prepared suite`
2. `tau-bench` live smoke

## Target Repository

1. `Yuchong-W/Protocol_Bench`

## Local Release State

1. local git repository repaired on `2026-04-15`
2. local history includes the initial scaffold commit `cb19fed`
3. release-engineering documentation updates are also committed locally
4. remote is configured as `origin = git@github.com:Yuchong-W/Protocol_Bench.git`
5. release branch `main` has been pushed successfully
6. HTTPS transport is still blocked locally, so future publishing from this machine should prefer SSH
7. the local working tree is clean after refreshing line-ending-only files through the git index

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
2. `CONTRIBUTING.md`
3. `SECURITY.md`
4. `CHANGELOG.md`
5. `scripts/README.md`
6. `scripts/aggregate_metrics.py`
7. `scripts/run_eval.py`
8. `scripts/run_protocol.py`
9. `scripts/run_release_checks.py`
10. `scripts/smoke_adapters.py`
11. `scripts/validate_records.py`
12. `scripts/harbor312`
13. `scripts/harbor312.cmd`
14. `scripts/tau311.cmd`
15. `.gitignore`
16. `.gitattributes`
17. `.editorconfig`
18. `LICENSE`
19. `NOTICE`
20. `CITATION.cff`
21. `.github/workflows/ci.yml`
22. `.github/ISSUE_TEMPLATE/bug_report.md`
23. `.github/ISSUE_TEMPLATE/feature_request.md`
24. `.github/ISSUE_TEMPLATE/config.yml`
25. `.github/PULL_REQUEST_TEMPLATE.md`

Engineering docs:

1. `06_protocol_benchmark_plan.md`
2. `docs/technical_design.md`
3. `docs/development_log.md`
4. `docs/decision_log.md`
5. `docs/known_limitations.md`
6. `docs/upstream_surface_notes.md`
7. `docs/release_manifest.md`
8. `docs/milestone_plan_v0_1.md`
9. `docs/release_checklist_v0_1.md`
10. `docs/release_notes_v0_1.md`
11. `docs/launch_materials_v0_1.md`
12. `docs/support_matrix_v0_1.md`
13. `docs/linux_validation_runbook_v0_1.md`
14. `docs/post_v0_1_backlog.md`

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
12. `tests/fixtures/skillsbench_harbor_job_sample/result.json`
13. `tests/fixtures/skillsbench_harbor_job_sample/citation-check__fixture001/result.json`
14. `tests/fixtures/skillsbench_harbor_job_sample/court-form-filling__fixture002/result.json`
15. `protocol/skillsbench_codex_external_prepared_suite.json`
16. `protocol/tau_bench_retail_historical_suite.json`
17. `protocol/tau_bench_retail_openai_smoke_suite.json`
18. `protocol/tau_openai.env.example`

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
12. `results/dryrun/skillsbench_dialogue_timeout4_runs.jsonl`

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
10. partial outputs under `results/protocol_runs/skillsbench_codex_external_prepared_suite/`
11. `results/protocol_runs/**/prepared/`
12. `.codex/`

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

## Experimental Outputs

These should be kept reviewable but are not part of the `v0.1` release-critical surface:

1. `protocol/skillsbench_codex_external_prepared_suite.json`
2. `protocol/tau_bench_retail_openai_smoke_suite.json`
3. any provider-backed live smoke outputs
4. any incomplete prepared-suite outputs


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
4. `protocol/tau_openai.env.example`

Additional local-only exclusions:

1. `.pydeps311/`
2. `results/dryrun/pip_probe/`
3. transient tau smoke preflight outputs under `results/protocol_runs/tau_bench_retail_openai_smoke_suite/`
4. `protocol/.env`
5. `protocol/.env.local`
6. `protocol/*.env.local`
7. `results/protocol_runs/skillsbench_codex_external_prepared_suite/`
