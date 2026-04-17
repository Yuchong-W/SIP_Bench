# Scripts

Implemented:

1. `aggregate_metrics.py`
Read `runs.jsonl`, group records by benchmark/model/path configuration, and write `summary.jsonl`.

2. `smoke_adapters.py`
Exercise local adapter scaffolds against sample fixtures without requiring full upstream benchmark installation.

3. `run_eval.py`
Build a SkillsBench execution plan, hydrate a sparse SkillsBench checkout, execute a plan in `mock` or `subprocess` mode, import SkillsBench trajectory JSON, import Harbor job directories from real SkillsBench runs, or import tau-bench JSON results into SIP-Bench `runs.jsonl`.

4. `run_protocol.py`
Run a config-driven SkillsBench or tau-bench protocol suite that executes/imports multiple phase-split runs, combines `runs.jsonl`, and writes a validated `summary.jsonl` when the suite is complete enough to aggregate.

5. `validate_records.py`
Validate `json` or `jsonl` artifacts against the authoritative SIP schemas.

6. `harbor312.cmd`
Windows launcher for Harbor on Python `3.12`. It sets a local `UV_CACHE_DIR`, forces UTF-8 console output, and disables Docker BuildKit because the default Windows + global Harbor path on this machine is unstable.

7. `tau311.cmd`
Windows launcher for `tau-bench` on `py -3.11`. It prepends the repo-local dependency overlay `.pydeps311` and the local `benchmarks\tau-bench` checkout to `PYTHONPATH`, then forwards all arguments to Python.

Operational notes:

1. Slow real SkillsBench Docker tasks may still need explicit Harbor timeout overrides passed through `run_eval.py` or suite config `extra_args`, for example `--environment-build-timeout-multiplier 4`.
2. Suite config paths are resolved relative to the config file location.
3. The current real suite is an orchestration validation suite, not a scientific benchmark claim.
4. `run_protocol.py` now supports per-run task preparation through suite config:
   - `mode = copy`
   - `skill_mode = strip|keep`
   - explicit task patch IDs such as `offer_letter_generator_system_docx`
5. `tau-bench` on this machine should be run through `scripts\tau311.cmd`, not the ambient `python`, because the required packages are intentionally isolated into `.pydeps311`.
6. The current `tau-bench` online smoke blocker is missing provider credentials, not importability. `OPENAI_API_KEY` is absent from the resolved suite environment, while `scripts\tau311.cmd -c "import tau_bench"` already succeeds.
7. `run_protocol.py` now supports protocol-level env loading for `tau-bench`. Resolution order is:
   - run-level `env_file`
   - suite-level `execution.env_file`
   - `protocol/.env.local`
   - `protocol/.env`
   - `<repo_root>/.env.local`
   - `<repo_root>/.env`
   - current shell environment
8. The recommended local secret path is `protocol/.env.local`, which is gitignored. A checked-in template lives at `protocol/tau_openai.env.example`.

Planned next:

1. `build_leaderboard`
Render a compact markdown table from summaries.

2. `run_regression`
Execute the golden-task suite after adapter or metric changes.

## First Commands

```powershell
python scripts\aggregate_metrics.py --runs results\dryrun\sample_runs.jsonl --out results\dryrun\summary.jsonl
python scripts\smoke_adapters.py
python scripts\run_eval.py plan-skillsbench --registry tests\fixtures\skillsbench_registry_sample.json --repo-root benchmarks\skillsbench --task-id court-form-filling --replay-count 1 --adapt-count 0 --heldout-count 0 --harbor-bin scripts\harbor312.cmd --out results\dryrun\skillsbench_plan.json
python scripts\run_eval.py hydrate-skillsbench --plan results\dryrun\skillsbench_plan.json --repo-root benchmarks\skillsbench --split replay --out results\dryrun\skillsbench_hydration.json
python scripts\run_eval.py execute-plan --plan results\dryrun\skillsbench_plan.json --split replay --mode subprocess --cwd E:\Protocal_Bench --out results\dryrun\skillsbench_execution.json
python scripts\run_eval.py import-skillsbench-job --job-dir tests\fixtures\skillsbench_harbor_job_sample --out results\dryrun\skillsbench_job_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 21 --registry tests\fixtures\skillsbench_registry_sample.json --agent-version job-fixture-import --benchmark-version skillsbench-harbor-fixture
python scripts\validate_records.py --data results\dryrun\skillsbench_job_runs.jsonl --schema runs
python scripts\run_protocol.py run-skillsbench-suite --config protocol\skillsbench_oracle_real_suite.json --mode subprocess
python scripts\run_protocol.py run-tau-suite --config protocol\tau_bench_retail_historical_suite.json --mode subprocess
scripts\tau311.cmd -c "import openai, litellm, tau_bench; print('tau_runtime_ok')"
python -c "from pathlib import Path; import sys; sys.path.insert(0, str(Path('src').resolve())); from sip_bench.protocol_runner import load_protocol_suite_config; cfg = load_protocol_suite_config('protocol/skillsbench_codex_external_prepared_suite.json'); print(cfg['suite_name'], len(cfg['runs']))"
```
