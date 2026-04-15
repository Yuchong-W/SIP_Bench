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
4. [docs/decision_log.md](E:\Protocal_Bench\docs\decision_log.md)
5. [docs/known_limitations.md](E:\Protocal_Bench\docs\known_limitations.md)
6. [docs/technical_design.md](E:\Protocal_Bench\docs\technical_design.md)
7. [docs/development_log.md](E:\Protocal_Bench\docs\development_log.md)
8. `scripts/`
9. `results/`
10. `tests/`

## Immediate Milestones

1. Finalize `protocol_spec_v0`.
2. Implement `SkillsBench` adapter.
3. Implement `tau-bench` adapter.
4. Produce the first `runs.jsonl` and `summary.jsonl`.

## Status

This repository is in Week 1 setup. The protocol, schemas, metric engine, aggregation CLI, and benchmark adapter scaffolds are in place. The next milestone is wiring these adapters to full upstream checkouts or installable benchmark environments.

## First Commands

```powershell
python -m unittest discover -s tests -p "test_*.py"
python scripts\aggregate_metrics.py --runs results\dryrun\sample_runs.jsonl --out results\dryrun\summary.jsonl
python scripts\smoke_adapters.py
python scripts\run_eval.py plan-skillsbench --registry tests\fixtures\skillsbench_registry_sample.json --repo-root benchmarks\skillsbench --replay-count 2 --adapt-count 1 --heldout-count 2 --out results\dryrun\skillsbench_plan.json
python scripts\run_eval.py execute-plan --plan results\dryrun\skillsbench_plan.json --out results\dryrun\skillsbench_execution.json --mode mock
python scripts\run_eval.py import-tau-results --source tests\fixtures\tau_results_sample.json --out results\dryrun\tau_runs.jsonl --env retail --task-split test --phase T1 --path-type external --model-name gpt-5-mini --agent-name tau-import --agent-version 0.1.0 --seed 9
python scripts\validate_records.py --data results\dryrun\sample_runs.jsonl --schema runs
python scripts\validate_records.py --data results\dryrun\summary.jsonl --schema summary
```
