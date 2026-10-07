# SIP-Bench

![SIP-Bench Figure](cover.png)
[![CI](https://github.com/Yuchong-W/Protocol_Bench/actions/workflows/ci.yml/badge.svg)](https://github.com/Yuchong-W/Protocol_Bench/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Linux First](https://img.shields.io/badge/platform-Linux--first-2ea44f.svg)](README.md)

`SIP-Bench` turns existing benchmarks into self-improvement benchmarks.

It adds a shared longitudinal protocol on top of existing benchmarks so you can measure:

1. whether the agent improved on held-out tasks,
2. whether it retained performance on tasks it already knew,
3. what interaction, compute, and runtime cost that improvement required.

Most benchmark reports stop at a single score. `SIP-Bench` is for the questions that come after that score:

1. Did improvement on new tasks hurt replay performance?
2. Did the gain persist at a later checkpoint?
3. Was the gain operationally expensive?
4. Did the run fail for infrastructure reasons rather than capability reasons?

Protocol surface:

1. `T0 / T1 / T2` checkpoints,
2. `replay / adapt / heldout / drift` splits,
3. normalized `runs.jsonl` and `summary.jsonl` records,
4. protocol metrics such as `FG`, `BR`, `PDS`, `IE`, and `NIS`,
5. first-class tracking of failed executions and retry provenance.

## Adapter-First

`SIP-Bench` is designed around one idea: benchmark-specific logic belongs in adapters, while SI evaluation logic stays shared.

That gives you:

1. benchmark-specific logic stays inside an adapter,
2. the protocol contract stays benchmark-agnostic,
3. imported results are normalized into shared `runs.jsonl` and `summary.jsonl` schemas,
4. the same `T0 / T1 / T2` and `replay / adapt / heldout / drift` logic can be reused across very different task worlds.

If you can write an adapter for a benchmark, you can evaluate that benchmark under the SIP protocol.

## What You Get

Current repository surface:

1. an adapter layer for wrapping new benchmarks into the same SI protocol,
2. first-class support for `SkillsBench`, `EvoAgentBench`, and `tau-bench`,
3. split planning and suite orchestration,
4. normalized `runs.jsonl` and `summary.jsonl` outputs,
5. aggregation, schema validation, and evidence-gate tooling,
6. tracked dry-run and real-artifact examples.

## Benchmarks

| Benchmark path | Status | Notes |
| --- | --- | --- |
| `SkillsBench oracle` | primary | real execution and tracked suite artifacts |
| `EvoAgentBench` | primary design target | demonstrates the protocol on self-improvement-heavy agent workflows and motivates the adapter-first architecture |
| `tau-bench historical` | supplementary | import-only path with tracked suite artifacts |
| `tau-bench live` | optional | requires provider credentials |
| `SkillsBench prepared external` | experimental | useful for task-preparation and path validation |
| `medical-synthea` native | credential-free | result-only suite with tracked config and generated CI artifacts |

## Why Clone This

If you already have a benchmark and want SI evaluation instead of a single-shot score, this repository gives you the reusable pieces:

1. write an adapter,
2. map the benchmark into `replay / adapt / heldout / drift`,
3. import normalized run records,
4. compute SI-focused metrics under the same protocol as every other adapter.

That is the real product surface of `SIP-Bench`.

## Quickstart

Minimum local checks:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python3 scripts/run_release_checks.py
python3 -m unittest discover -s tests -p "test_*.py"
```

The native medical lane runs without API credentials, Docker, Harbor, or an upstream
benchmark checkout:

```bash
python scripts/run_release_checks.py --skip-import-check --plan-matrix --report /tmp/sip-release-report.json
```

Its report records the expected 12 suite runs and 24 normalized records, SHA-256
hashes for generated artifacts, aggregate cost fields, and failure-family counts.
External suites retain their plan, hydration, execution, and source-artifact checks.

Build a protocol summary from tracked sample runs:

```bash
python3 scripts/aggregate_metrics.py \
  --runs results/dryrun/sample_runs.jsonl \
  --out /tmp/sip_summary.jsonl
```

Import a fixture-format SkillsBench Harbor job:

```bash
python3 scripts/run_eval.py import-skillsbench-job \
  --job-dir tests/fixtures/skillsbench_harbor_job_sample \
  --out /tmp/skillsbench_job_runs.jsonl \
  --benchmark-split smoke \
  --phase T0 \
  --path-type oracle \
  --seed 21 \
  --registry tests/fixtures/skillsbench_registry_sample.json \
  --agent-version fixture-import \
  --benchmark-version skillsbench-harbor-fixture
```

Validate the imported records:

```bash
python3 scripts/validate_records.py \
  --data /tmp/skillsbench_job_runs.jsonl \
  --schema runs
```

## Artifacts

If you want concrete outputs before reading code, start here:

1. [results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json](results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json)
2. [results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl](results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl)
3. [results/dryrun/summary.jsonl](results/dryrun/summary.jsonl)
4. [results/protocol_runs/tau_bench_retail_historical_suite/suite_report.json](results/protocol_runs/tau_bench_retail_historical_suite/suite_report.json)
5. [results/protocol_runs/README.md](results/protocol_runs/README.md)

## Minimal Proof

This repository only needs to prove one thing: protocol-level evaluation reveals information a single post-adaptation score hides.

The smallest tracked proof is [results/dryrun/summary.jsonl](results/dryrun/summary.jsonl):

1. held-out performance improves from `T0` to `T1`,
2. replay performance regresses at the same time,
3. the gain softens again by `T2`,
4. the improvement has explicit interaction cost.

That is enough to justify the project.

Execution-backed proof:

1. [results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json](results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json)
2. [results/protocol_runs/tau_bench_retail_historical_suite/suite_report.json](results/protocol_runs/tau_bench_retail_historical_suite/suite_report.json)

Design proof:

1. `SkillsBench` shows a real execution-backed path,
2. `EvoAgentBench` shows that the same protocol ideas can target a very different self-improvement workflow,
3. `tau-bench` shows that the same normalization layer also works for import-oriented external environments.

## Protocol Model

Lifecycle checkpoints:

1. `T0`
2. `T1`
3. `T2`

Task partitions:

1. `replay`
2. `adapt`
3. `heldout`
4. optional `drift`

Primary metrics:

1. `FG`
2. `BR`
3. `BR_ratio`
4. `PDS`
5. `IE`
6. `NIS`

Protocol reference:

1. [protocol/protocol_spec_v0.md](protocol/protocol_spec_v0.md)
2. [schemas/runs.schema.json](schemas/runs.schema.json)
3. [schemas/summary.schema.json](schemas/summary.schema.json)
4. [schemas/protocol_suite.schema.json](schemas/protocol_suite.schema.json)

## Read Next

1. [docs/README.md](docs/README.md)
2. [docs/technical_design.md](docs/technical_design.md)
3. [protocol/protocol_spec_v0.md](protocol/protocol_spec_v0.md)

Main implementation:

1. `src/sip_bench/`
2. `scripts/`
3. `tests/`
4. `protocol/`
5. `results/`

Common developer entry points:

```bash
make setup
make test
make release-checks
make plan-matrix
```

## Scope

This repository is strongest as reusable evaluation infrastructure, not as a polished launcher for every upstream environment.

Core project value:

1. the protocol contract,
2. normalized schemas,
3. auditable benchmark-specific adapters,
4. import and aggregation tooling,
5. real example artifacts.

## Development

Environment posture:

1. `Linux-first`
2. local verification uses `unittest`
3. some optional benchmark paths require external credentials or upstream checkouts

If you want to contribute or extend a benchmark adapter, read:

1. [docs/technical_design.md](docs/technical_design.md)
2. [scripts/README.md](scripts/README.md)
3. [tests/README.md](tests/README.md)

## License

See [LICENSE](LICENSE) if present in this repository root. If your checkout does not yet include one, add a project license before public release.

# Medical fixture accounting

For the native `medical-synthea` fixture, `memory_reads` and `memory_writes` are
logical protocol counters. A `T1` or `T2` adapt record reports one write for its
adaptation call; all `T1`/`T2` records report one read because the phase has a
memory-enabled policy. The emergency red-flag rules can return before an exact
`RuleMemory` lookup, so these counters do not claim physical key-value-store I/O.
