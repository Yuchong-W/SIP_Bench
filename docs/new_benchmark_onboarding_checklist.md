# New Benchmark Onboarding Checklist (v0.1)

## Purpose

This checklist is for adding a new benchmark to SIP-Bench without changing the protocol contract.  
Each new benchmark must remain a drop-in adapter and preserve schema-stable `runs.jsonl` / `summary.jsonl` outputs.

## 1) Adapter Contract

1. Add a new adapter class under `src/sip_bench/adapters/`.
2. Implement/verify:
   - `discover_tasks(self, source)`
   - `build_manifest(self, tasks, replay_count, adapt_count, heldout_count, drift_count=0, seed=0)`
   - `build_manifest(...)` must return `SplitManifest`
   - `build_run` helper (`build_harbor_command` for SkillsBench-style adapters or equivalent builder)
   - `parse_result_file` / import entrypoint for raw benchmark outputs
3. Export in `src/sip_bench/adapters/__init__.py` and add tests for adapter-specific behavior.

## 2) Schema and Metadata Compatibility

1. Every emitted run row must match the run schema.
2. Required stable fields to keep:
   - `benchmark_name`
   - `task_id`
   - `source_path` (or equivalent stable id)
   - `phase`
   - `benchmark_split`
   - `path_type`
   - `attempt_index`
   - `score`
   - `model_name`
   - `agent_name`
   - `agent_version`
   - `seed`
3. Reproducibility fields:
   - `started_at`
   - `finished_at`
   - `token_total`, `tool_calls_total`, `wall_clock_seconds`, `cost_usd`
4. Run `scripts/validate_records.py` with `--schema runs` and `--schema summary` for derived artifacts.

## 3) Plan Path and Reproducibility

1. Add config under `protocol/` with:
   - fixed `repo_root` and `out_root`
   - `suite_name`
   - explicit `runs` list with `run_name`, `phase`, `benchmark_split`, and `task_ids`.
2. Include retry policy and execution policy in config:
   - deterministic attempt limits
   - timeout overrides (if needed) as explicit fields
3. For each suite, keep the reproducibility bundle:
   - `plans/<run_name>.json`
   - `plans/<run_name>.source.json`
   - `hydration/<run_name>.json`
   - `execution/<run_name>.json`
   - `runs/<run_name>.jsonl`
   - suite-level `suite_report.json`, `combined_runs.jsonl`, `summary.jsonl`
4. Run `python3 scripts/check_plan_matrix.py --config <suite-config> --strict` after suite folder writes.

## 4) Plan Matrix and Evidence Readiness

1. Record suite-level evidence in `docs/release_manifest.md` and `docs/release_checklist_v0_1.md`.
2. Update `docs/support_matrix_v0_1.md` with supported environment/path requirements.
3. Add a small "results summary row" entry to `docs/results_table_data` and relevant figure generation inputs.
4. Verify `scripts/run_release_checks.py` still passes.

## 5) Gate Before PR

Before opening PR, the contributor must provide:

1. Command block proving:
   - schema validation
   - one dry-run/protocol run command
2. One failing case and one recovered case in suite artifacts (if infra-relevant).
3. A short note in PR summary describing:
   - what this benchmark adds
   - how retry/determinism is defined
   - where the evidence bundle is stored

## 6) References

- `CONTRIBUTING.md` — adapter development section  
- `scripts/check_plan_matrix.py` output  
- `scripts/run_release_checks.py`
- `docs/release_checklist_v0_1.md`
