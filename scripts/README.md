# Scripts

Implemented:

1. `aggregate_metrics.py`
Read `runs.jsonl`, group records by benchmark/model/path configuration, and write `summary.jsonl`.

2. `smoke_adapters.py`
Exercise local adapter scaffolds against sample fixtures without requiring full upstream benchmark installation.

3. `run_eval.py`
Build a SkillsBench execution plan, execute a plan in `mock` or `subprocess` mode, or import tau-bench JSON results into SIP-Bench `runs.jsonl`.

4. `validate_records.py`
Validate `json` or `jsonl` artifacts against the authoritative SIP schemas.

Planned next:

1. `build_leaderboard`
Render a compact markdown table from summaries.

2. `run_regression`
Execute the golden-task suite after adapter or metric changes.

## First Command

```powershell
python scripts\aggregate_metrics.py --runs results\dryrun\sample_runs.jsonl --out results\dryrun\summary.jsonl
python scripts\smoke_adapters.py
python scripts\run_eval.py plan-skillsbench --registry tests\fixtures\skillsbench_registry_sample.json --repo-root benchmarks\skillsbench --replay-count 2 --adapt-count 1 --heldout-count 2 --out results\dryrun\skillsbench_plan.json
python scripts\run_eval.py execute-plan --plan results\dryrun\skillsbench_plan.json --out results\dryrun\skillsbench_execution.json --mode mock
python scripts\validate_records.py --data results\dryrun\sample_runs.jsonl --schema runs
```
