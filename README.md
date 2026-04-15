# SI-Protocol Benchmark

`SI-Protocol Benchmark` (`SIP-Bench`) is a protocol-layer benchmark for measuring self-improvement in agents.

This project does not introduce a brand-new environment. It wraps existing benchmarks with a unified evaluation protocol so we can answer questions that current agent benchmarks usually miss:

1. Did the agent improve on held-out tasks?
2. Did it retain performance on old tasks?
3. How much interaction and compute did that improvement cost?

## Current Scope

The MVP targets two environments:

1. `SkillsBench`
2. `tau-bench`

An optional third environment, `SWE-bench-Live`, is reserved for a later extension if the first two adapters stabilize on schedule.

## Core Protocol

Each benchmark is evaluated under a shared three-stage protocol:

1. `T0`: initial agent, no targeted adaptation
2. `T1`: post-adaptation
3. `T2`: post-delay or post-drift

Each benchmark also defines shared task subsets:

1. `replay`
2. `adapt`
3. `heldout`
4. optional `drift`

The primary metrics are:

1. `FG`: Forward Gain
2. `BR`: Backward Retention
3. `IE`: Improvement Efficiency

## Repository Layout

1. [protocol/protocol_spec_v0.md](E:\Protocal_Bench\protocol\protocol_spec_v0.md)
2. [schemas/runs.schema.json](E:\Protocal_Bench\schemas\runs.schema.json)
3. [schemas/summary.schema.json](E:\Protocal_Bench\schemas\summary.schema.json)
4. [schemas/protocol_suite.schema.json](E:\Protocal_Bench\schemas\protocol_suite.schema.json)
5. [docs/decision_log.md](E:\Protocal_Bench\docs\decision_log.md)
6. [docs/known_limitations.md](E:\Protocal_Bench\docs\known_limitations.md)
7. [docs/technical_design.md](E:\Protocal_Bench\docs\technical_design.md)
8. [docs/development_log.md](E:\Protocal_Bench\docs\development_log.md)
9. `scripts/`
10. `results/`
11. `tests/`

## Status

This repository is now beyond pure scaffold status. The protocol, schemas, metric engine, aggregation CLI, sparse SkillsBench hydration, real SkillsBench Harbor-job import, config-driven protocol orchestration, and real upstream checkout strategy are in place. `tau-bench` is checked out locally over SSH, `SkillsBench` is maintained as a sparse SSH checkout, and the real execution path now prefers `scripts\harbor312.cmd` so Harbor runs under Python `3.12` with Docker BuildKit disabled.

The first real multi-run protocol suite has already executed end-to-end and produced a valid `combined_runs.jsonl` plus `summary.jsonl` under `results/protocol_runs/skillsbench_oracle_real_suite/`.

## Real SkillsBench Flow

The current single-run real SkillsBench smoke path is:

1. `plan-skillsbench`
2. `hydrate-skillsbench`
3. `execute-plan --mode subprocess`
4. `import-skillsbench-job`
5. `validate_records`

Notes:

1. The execution bridge now consumes real Harbor job directories even when a trial fails during Docker build or verifier setup.
2. The benchmark outcome is recorded in imported `runs.jsonl`; `execute-plan` only reports whether the command launched successfully.
3. On this machine, the global `harbor.exe` installed under Python `3.13` is not reliable for Windows subprocess orchestration, so `scripts\harbor312.cmd` is the supported launcher.
4. The first fully successful real smoke run on this machine used `dialogue-parser` with `--environment-build-timeout-multiplier 4`; the default `600` second build timeout was too low for that Docker task.

## Real Protocol Suite Flow

The current real multi-run protocol path is:

1. `run-skillsbench-suite`
2. per-run `plan`
3. per-run `hydrate`
4. per-run `execute`
5. per-run `import`
6. combined `runs.jsonl` validation
7. summary aggregation into `summary.jsonl`

Notes:

1. Suite configs are resolved relative to the config file location.
2. The suite runner also supports import-only runs for deterministic regression testing.
3. The current real suite is an `oracle` plumbing validation suite, not a meaningful self-improvement claim.

## First Commands

```powershell
python -m unittest discover -s tests -p "test_*.py"
python scripts\aggregate_metrics.py --runs results\dryrun\sample_runs.jsonl --out results\dryrun\summary.jsonl
python scripts\smoke_adapters.py
python scripts\run_eval.py plan-skillsbench --registry tests\fixtures\skillsbench_registry_sample.json --repo-root benchmarks\skillsbench --task-id court-form-filling --replay-count 1 --adapt-count 0 --heldout-count 0 --harbor-bin scripts\harbor312.cmd --out results\dryrun\skillsbench_plan.json
python scripts\run_eval.py hydrate-skillsbench --plan results\dryrun\skillsbench_plan.json --repo-root benchmarks\skillsbench --split replay --out results\dryrun\skillsbench_hydration.json
python scripts\run_eval.py execute-plan --plan results\dryrun\skillsbench_plan.json --split replay --mode subprocess --cwd E:\Protocal_Bench --out results\dryrun\skillsbench_execution.json
python scripts\run_eval.py import-skillsbench-job --job-dir tests\fixtures\skillsbench_harbor_job_sample --out results\dryrun\skillsbench_job_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 21 --registry tests\fixtures\skillsbench_registry_sample.json --agent-version job-fixture-import --benchmark-version skillsbench-harbor-fixture
python scripts\validate_records.py --data results\dryrun\skillsbench_job_runs.jsonl --schema runs
python scripts\run_protocol.py run-skillsbench-suite --config protocol\skillsbench_oracle_real_suite.json --mode subprocess
```
