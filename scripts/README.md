# Scripts

Implemented:

1. `aggregate_metrics.py`
Read `runs.jsonl`, group records by benchmark/model/path configuration, and write `summary.jsonl`.

2. `smoke_adapters.py`
Exercise local adapter scaffolds against sample fixtures without requiring full upstream benchmark installation.

3. `run_eval.py`
Build a SkillsBench execution plan, hydrate a sparse SkillsBench checkout, execute a plan in `mock` or `subprocess` mode, import SkillsBench trajectory JSON, import Harbor job directories from real SkillsBench runs, or import tau-bench JSON results into SIP-Bench `runs.jsonl`.

4. `validate_records.py`
Validate `json` or `jsonl` artifacts against the authoritative SIP schemas.

5. `harbor312.cmd`
Windows launcher for Harbor on Python `3.12`. It sets a local `UV_CACHE_DIR`, forces UTF-8 console output, and disables Docker BuildKit because the default Windows + global Harbor path on this machine is unstable.

Operational note:

1. Slow real SkillsBench Docker tasks may still need explicit Harbor timeout overrides passed through `run_eval.py`, for example `--extra-arg=--environment-build-timeout-multiplier --extra-arg=4`.

Planned next:

1. `build_leaderboard`
Render a compact markdown table from summaries.

2. `run_regression`
Execute the golden-task suite after adapter or metric changes.

## First Command

```powershell
python scriptsggregate_metrics.py --runs results\dryrun\sample_runs.jsonl --out results\dryrun\summary.jsonl
python scripts\smoke_adapters.py
python scriptsun_eval.py plan-skillsbench --registry testsixtures\skillsbench_registry_sample.json --repo-root benchmarks\skillsbench --task-id court-form-filling --replay-count 1 --adapt-count 0 --heldout-count 0 --harbor-bin scripts\harbor312.cmd --out results\dryrun\skillsbench_plan.json
python scriptsun_eval.py hydrate-skillsbench --plan results\dryrun\skillsbench_plan.json --repo-root benchmarks\skillsbench --split replay --out results\dryrun\skillsbench_hydration.json
python scriptsun_eval.py execute-plan --plan results\dryrun\skillsbench_plan.json --split replay --mode subprocess --cwd E:\Protocal_Bench --out results\dryrun\skillsbench_execution.json
python scriptsun_eval.py import-skillsbench-job --job-dir testsixtures\skillsbench_harbor_job_sample --out results\dryrun\skillsbench_job_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 21 --registry testsixtures\skillsbench_registry_sample.json --agent-version job-fixture-import --benchmark-version skillsbench-harbor-fixture
python scriptsalidate_records.py --data results\dryrun\skillsbench_job_runs.jsonl --schema runs
```
