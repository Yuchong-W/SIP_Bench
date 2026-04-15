# Technical Design

## Goal

`SIP-Bench` is a protocol-layer benchmark for self-improvement. The project does not define a new world simulator. It wraps existing agent benchmarks with a shared longitudinal protocol so improvement, retention, and cost can be measured under one contract.

The MVP focuses on two benchmark families:

1. `SkillsBench`
2. `tau-bench`

## Design Principles

1. Reuse existing benchmark environments instead of building a new environment stack.
2. Keep the first version CPU-friendly and single-researcher maintainable.
3. Separate protocol logic from benchmark-specific integration.
4. Treat logs and schemas as first-class interfaces.
5. Make every step runnable in dry-run mode before wiring to expensive real execution.

## Protocol Model

The protocol has three lifecycle phases:

1. `T0`
Initial agent before benchmark-specific adaptation.
2. `T1`
Post-adaptation checkpoint.
3. `T2`
Delayed or post-drift checkpoint.

Each benchmark is partitioned into shared splits:

1. `replay`
2. `adapt`
3. `heldout`
4. optional `drift`

This gives a benchmark-agnostic way to measure:

1. held-out improvement
2. old-task retention
3. improvement efficiency
4. post-drift stability

## Metric Layer

Implemented metric definitions:

1. `FG`
`score(T1, heldout) - score(T0, heldout)`
2. `BR`
`score(T1, replay) - score(T0, replay)`
3. `BR_ratio`
`score(T1, replay) / max(score(T0, replay), eps)`
4. `IE`
`FG / cost`, with `null` when cost is zero
5. `PDS`
`score(T2, heldout_or_drift) - score(T1, heldout)`
6. `NIS`
`FG - lambda * max(0, -BR)`

Implementation lives in:

1. `src/sip_bench/metrics.py`

The metric engine takes normalized `runs.jsonl` records and produces aggregated `summary.jsonl` output. It groups by benchmark, version, path type, model, and agent version, then computes mean and variance across seeds or repeats.

## Schema Layer

Two schemas are authoritative:

1. `schemas/runs.schema.json`
2. `schemas/summary.schema.json`

They define:

1. required run-level fields
2. allowed split and phase values
3. normalized score range
4. summary-level metric and cost fields
5. nullable fields for `T2` or zero-cost edge cases

Validation is implemented in:

1. `src/sip_bench/validation.py`
2. `scripts/validate_records.py`

## Adapter Abstraction

The adapter layer is defined in:

1. `src/sip_bench/adapters/base.py`

Core types:

1. `TaskDescriptor`
Portable task metadata record.
2. `SplitManifest`
Protocol split container with overlap checking.
3. `BenchmarkAdapter`
Base class for task discovery and split construction.

This keeps benchmark-specific knowledge out of the metric engine and out of the CLI.

## SkillsBench Adapter

Implemented in:

1. `src/sip_bench/adapters/skillsbench.py`

Current responsibilities:

1. discover tasks from registry JSON
2. filter tasks by category and difficulty
3. build Harbor execution commands
4. support split planning for `replay/adapt/heldout/drift`
5. import trajectory/result JSON into normalized SIP run records

Current upstream assumptions:

1. task registry is available as JSON
2. task directories follow Harbor task layout
3. execution is performed through `harbor run -p <task> -a <agent>`
4. trajectory exports contain stable fields such as `taskName`, `condition`, `result`, `duration`, `tokens`, `steps`, and `verifier`

Current importer behavior:

1. joins result rows back to the task registry for category, difficulty, tags, and task version
2. infers SIP `path_type` from SkillsBench condition labels by default:
   - `noskills -> frozen`
   - `withskills -> external`
   - `gen -> external`
3. derives `score` from verifier pass ratio when test counts are present
4. derives `tool_calls_total` from `steps[*].type == tool_call`
5. derives `started_at` and `finished_at` from step timestamps when available

## tau-bench Adapter

Implemented in:

1. `src/sip_bench/adapters/tau_bench.py`

Current responsibilities:

1. build split manifests from explicit task IDs
2. generate `run.py` execution commands
3. import upstream result JSON into normalized `runs.jsonl`

Current upstream assumptions:

1. benchmark is organized by `env` and `task_split`
2. result file is a JSON array of upstream `EnvRunResult`
3. reward can be normalized directly into SIP `score`
4. upstream `task_split` must stay in metadata, while SIP `benchmark_split` must be passed explicitly by the caller

## Runner Layer

Implemented in:

1. `src/sip_bench/runner.py`

Current functions:

1. `build_skillsbench_plan`
Creates a plan JSON with manifest plus per-task execution commands.
2. `import_tau_results`
Converts upstream tau results to SIP runs.
3. `import_skillsbench_results`
Converts SkillsBench trajectories or evaluation rows to SIP runs.
4. `execute_command_plan`
Executes or mock-executes plan commands and produces an execution report.

Execution modes:

1. `mock`
Writes fake success artifacts without calling external tools.
2. `subprocess`
Runs real commands and stores stdout/stderr per task.

The runner stores one execution report per plan. The report includes:

1. execution summary
2. per-task status
3. stdout path
4. stderr path
5. mode
6. wall-clock duration

## CLI Layer

Current CLI entrypoints:

1. `scripts/aggregate_metrics.py`
2. `scripts/smoke_adapters.py`
3. `scripts/run_eval.py`
4. `scripts/validate_records.py`

`run_eval.py` currently supports:

1. `plan-skillsbench`
2. `execute-plan`
3. `import-tau-results`
4. `import-skillsbench-results`

This is enough to exercise a dry-run end-to-end workflow:

1. build a plan
2. execute the plan in mock mode
3. import upstream-style results
4. aggregate runs into summaries
5. validate logs and summaries against schemas

## Artifact Model

Main artifact classes:

1. `plan JSON`
Manifest plus commands.
2. `execution JSON`
Per-task execution report.
3. `runs.jsonl`
Normalized run records.
4. `summary.jsonl`
Aggregated benchmark summary.
5. `artifacts/`
Per-task stdout/stderr folders.

Representative generated files:

1. `results/dryrun/skillsbench_plan.json`
2. `results/dryrun/skillsbench_execution.json`
3. `results/dryrun/tau_runs.jsonl`
4. `results/dryrun/summary.jsonl`

## Testing Strategy

The test suite currently covers:

1. metric formulas
2. aggregation logic
3. edge cases for `T2` and zero-cost `IE`
4. adapter discovery and command generation
5. tau result import
6. SkillsBench result import
7. runner planning
8. mock execution
9. subprocess execution via a local fixture program
10. schema validation

Primary test command:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

## Environment Constraints

Observed engineering constraints:

1. current machine is not GPU-first
2. GitHub HTTPS on port `443` is blocked from this environment
3. `gh` CLI is not installed
4. current workspace was not originally a git repository
5. Windows subprocess output cleanup can hit transient file-lock timing if tests reuse fixed output paths

As a result, upstream integration currently uses:

1. SSH for repository publishing and upstream checkout
2. a sparse checkout for `SkillsBench`
3. a full checkout for `tau-bench`
4. local fixtures for deterministic regression tests

## Known Gaps

Not finished yet:

1. direct subprocess execution against a real `tau-bench` checkout with live model credentials
2. leaderboard rendering
3. regression test harness over a frozen real-run corpus
4. automatic aggregation over real `T0/T1/T2` SkillsBench jobs once multiple phases have been collected
5. environment-level retries for flaky Docker build and package-network failures during real Harbor runs

## Next Engineering Steps

1. Add a leaderboard builder from `summary.jsonl`.
2. Add a regression suite over frozen Harbor job fixtures.
3. Add multi-phase real-run orchestration so `FG/BR/IE` can be computed from imported job outputs.
4. Add retry and failure-taxonomy reporting for Docker build and dependency-download errors.

## Update: Real SkillsBench Bridge

Resolved in the current revision:

1. `SkillsBench` plans can now be constrained by explicit `task_id` values.
2. Sparse checkout hydration is now a first-class CLI step driven from the generated plan.
3. A dedicated `scripts\harbor312.cmd` launcher now runs Harbor on Python `3.12`, forces UTF-8 console output, and disables Docker BuildKit on this machine.
4. Harbor job directories are now importable into SIP `runs.jsonl`, including failed trials that never reached agent execution.

Current environment-specific blockers:

1. The globally installed `harbor.exe` still uses a Python `3.13` runtime that fails during Windows subprocess orchestration with `NotImplementedError`.
2. Some real SkillsBench Docker builds still fail due network or Docker-builder instability, so the importer must treat Harbor job output as the source of truth instead of assuming successful benchmark completion.

## Publication State

The intended remote repository is:

1. `Yuchong-W/Protocol_Bench`

Current publication constraints:

1. Direct `git` and `curl` access to `github.com:443` fails from this environment even under escalated execution.
2. The connected GitHub app does not currently expose `Yuchong-W/Protocol_Bench`, so direct connector-side file commits are unavailable.
3. SSH transport to `github.com:22` works and is the current publication path for this repository.

As a result, the publication workflow is currently split into two layers:

1. keep repository content in a clean upload-ready shape locally
2. prefer SSH remote publishing when HTTPS transport is blocked


## Update: Execution Output Decoding

A real Harbor smoke run exposed an additional Windows-specific issue in the generic executor: `subprocess.run(..., text=True)` can fail when the child emits bytes that are not decodable under the local GBK code page. The executor now captures raw bytes and decodes with UTF-8 replacement before writing stdout and stderr artifacts. This keeps the execution report path stable even when third-party tools print mixed or invalid console encodings.

## Update: First Real Successful SkillsBench Run

The real `SkillsBench` chain has now produced a fully successful imported SIP record on this machine.

Successful path:

1. selected task: `dialogue-parser`
2. protocol steps: `plan -> hydrate -> execute -> import -> validate`
3. agent path: `oracle`
4. launcher: `scripts\harbor312.cmd`
5. additional Harbor override: `--environment-build-timeout-multiplier 4`

Observed outcome:

1. the original `dialogue-parser` smoke run failed with `EnvironmentStartTimeoutError` after the default `600` second build timeout
2. rerunning the same task with an explicit environment-build timeout multiplier completed successfully
3. the imported SIP record in `results/dryrun/skillsbench_dialogue_timeout4_runs.jsonl` validates against `runs.schema.json`
4. the protocol bridge is therefore no longer only "able to import failed Harbor jobs"; it can now import a real successful upstream run as well

Engineering implication:

1. the primary remaining blocker is not missing glue code
2. it is task-level runtime stability and timeout tuning across different SkillsBench environments
3. future orchestration should therefore treat timeout overrides as benchmark execution policy, not as ad-hoc manual recovery
