# Development Log

## 2026-04-14

### Scope Lock

Work completed:

1. Locked MVP scope to `SkillsBench + tau-bench`.
2. Deferred parameter-path baselines by default.
3. Defined Week 1 goal as protocol correctness before benchmark scale.

Key outputs:

1. `06_protocol_benchmark_plan.md`
2. `protocol/protocol_spec_v0.md`
3. `schemas/runs.schema.json`
4. `schemas/summary.schema.json`

### Metric Engine

Work completed:

1. Implemented normalized protocol metrics in `src/sip_bench/metrics.py`.
2. Added `aggregate_metrics.py` for converting `runs.jsonl` to `summary.jsonl`.
3. Added metric unit tests and toy cases.

Tests run:

1. `python -m unittest discover -s tests -p "test_*.py"`

Observed result:

1. Initial metric and aggregation suite passed.

### Adapter Scaffolding

Work completed:

1. Added adapter abstraction layer.
2. Added `SkillsBenchAdapter`.
3. Added `TauBenchAdapter`.
4. Added `smoke_adapters.py` and local fixtures.

Tests run:

1. `python scripts\smoke_adapters.py`
2. `python -m unittest discover -s tests -p "test_*.py"`

Observed result:

1. Local adapter smoke path worked.
2. Command generation and tau import path worked.

### Environment Issues

Observed issues:

1. `git clone` to GitHub public repos failed with connection reset / blocked `443`.
2. Partial clone cleanup required escalated deletion because a broken `.git` directory was left behind.

Mitigation:

1. Switched to upstream surface snapshots and local fixtures.
2. Created placeholder directories under `benchmarks/`.

## 2026-04-15

### Runner and CLI Expansion

Work completed:

1. Added `run_eval.py` planning and import subcommands.
2. Added execution mode support:
   - `mock`
   - `subprocess`
3. Added execution report generation with per-task stdout/stderr artifacts.
4. Added real timing capture for each execution record.

Generated artifacts:

1. `results/dryrun/skillsbench_plan.json`
2. `results/dryrun/skillsbench_execution.json`
3. `results/dryrun/tau_runs.jsonl`
4. `results/dryrun/mock_subprocess_execution.json`

Tests run:

1. `python scripts\run_eval.py plan-skillsbench --registry tests\fixtures\skillsbench_registry_sample.json --repo-root benchmarks\skillsbench --replay-count 2 --adapt-count 1 --heldout-count 2 --out results\dryrun\skillsbench_plan.json`
2. `python scripts\run_eval.py execute-plan --plan results\dryrun\skillsbench_plan.json --out results\dryrun\skillsbench_execution.json --mode mock`
3. `python scripts\run_eval.py import-tau-results --source tests\fixtures\tau_results_sample.json --out results\dryrun\tau_runs.jsonl --env retail --task-split test --phase T1 --path-type external --model-name gpt-5-mini --agent-name tau-import --agent-version 0.1.0 --seed 9`
4. `python scripts\run_eval.py execute-plan --plan tests\fixtures\mock_execute_plan.json --out results\dryrun\mock_subprocess_execution.json --mode subprocess --cwd E:\Protocal_Bench`
5. `python -m unittest discover -s tests -p "test_*.py"`

Observed result:

1. End-to-end dry-run planning, execution, import, and aggregation path works.
2. Test suite count increased to `14`.

### Schema Validation

Work completed:

1. Added `src/sip_bench/validation.py`.
2. Added `scripts/validate_records.py`.
3. Added validation tests for `runs` and `summary`.

Tests run:

1. `python scripts\validate_records.py --data results\dryrun\sample_runs.jsonl --schema runs`
2. `python scripts\validate_records.py --data results\dryrun\summary.jsonl --schema summary`

Expected result:

1. Both commands should return valid reports and exit code `0`.

### Environment Issues

Observed issues:

1. `gh` CLI is not installed.
2. Current workspace is not attached to any git remote.
3. No matching existing GitHub repository for this project was found through the connected repository list.
4. A Windows cleanup issue appeared when subprocess tests wrote to fixed output paths and the test immediately deleted them.

Mitigation:

1. Switched subprocess test outputs to temporary directories.
2. Decoupled test editing from fixed positional command indices and now rewrite `--out` arguments by flag lookup.
3. Prepared to initialize local git separately from remote publishing.

### Open Blockers

Current blockers:

1. No target GitHub remote repository has been specified or created for this project.
2. Full upstream benchmark checkout is still blocked by GitHub network connectivity.

### Remote Publishing Attempt

Work completed:

1. Confirmed the target repository URL as `https://github.com/Yuchong-W/Protocol_Bench`.
2. Checked GitHub app visibility for the repository.
3. Retried remote Git probing with escalated shell permissions.

Tests run:

1. `git ls-remote https://github.com/Yuchong-W/Protocol_Bench.git`
2. escalated retry of the same command
3. GitHub repository search through the connected connector

Observed result:

1. direct shell access to `github.com:443` still fails
2. the connected GitHub app cannot currently see `Yuchong-W/Protocol_Bench`
3. remote push is therefore blocked by transport and connector binding, not by project state

Mitigation:

1. keep the workspace in upload-ready shape
2. record the exact publish blockers in docs
3. prepare a file manifest so the final push step is mechanical once transport is available
