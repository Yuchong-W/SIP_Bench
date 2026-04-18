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

7. `harbor312`
POSIX wrapper for Harbor on Python `3.12`. It mirrors the release-facing environment defaults from `harbor312.cmd` while remaining executable on the `Linux-first` path.

8. `tau311.cmd`
Windows launcher for `tau-bench` on `py -3.11`. It prepends the repo-local dependency overlay `.pydeps311` and the local `benchmarks\tau-bench` checkout to `PYTHONPATH`, then forwards all arguments to Python.

9. `run_release_checks.py`
Run the release-facing local validation path used by the public quickstart and CI. It exercises unit tests, dry-run aggregation, SkillsBench Harbor job import, and schema validation for tracked artifacts.

Release-facing guidance:

1. `Linux-first` is the current public support target.
2. The Windows `.cmd` launchers remain available for local machine-specific workflows, but they are not the center of the `v0.1` public story.
3. The current release-critical benchmark evidence path does not require `codex` connectivity or live provider credentials.

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
9. `execute-plan` and `tau_bench_preflight` now resolve bare `python` or `python3` through the current environment so Linux hosts without a `python` alias still work.
10. `run_release_checks.py` uses the current interpreter by default, so the same command works inside virtualenvs and CI without relying on an ambient `python` alias.
11. The tracked `SkillsBench oracle` real-suite config now points at `scripts/harbor312`, with automatic `.cmd` fallback on Windows so the same config works on both release-facing Linux hosts and local Windows workflows.

Planned next:

1. `build_leaderboard`
Render a compact markdown table from summaries.

2. `run_regression`
Execute the golden-task suite after adapter or metric changes.

## First Commands

```bash
python3 scripts/run_release_checks.py
python3 scripts/aggregate_metrics.py --runs results/dryrun/sample_runs.jsonl --out /tmp/sip_summary.jsonl
python3 scripts/smoke_adapters.py
python3 scripts/run_eval.py import-skillsbench-job --job-dir tests/fixtures/skillsbench_harbor_job_sample --out /tmp/skillsbench_job_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 21 --registry tests/fixtures/skillsbench_registry_sample.json --agent-version fixture-import --benchmark-version skillsbench-harbor-fixture
python3 scripts/validate_records.py --data /tmp/skillsbench_job_runs.jsonl --schema runs
python3 scripts/validate_records.py --data results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl --schema summary
```
