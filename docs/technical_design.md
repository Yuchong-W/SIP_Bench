# Technical Design

## Goal

`SIP-Bench` is a protocol-layer benchmark for self-improvement. The project does not define a new world simulator. It wraps existing agent benchmarks with a shared longitudinal protocol so improvement, retention, and cost can be measured under one contract.

The MVP focuses on two benchmark families:

1. `SkillsBench`
2. `tau-bench`

The current `v0.1` release direction is `Linux-first` and open-source-release-oriented. The release-critical evidence path is:

1. real `SkillsBench oracle` suite artifacts
2. `tau-bench historical/import-only` suite artifacts

Experimental paths such as `SkillsBench codex external prepared` and `tau-bench` live provider-backed runs remain useful, but they are not release blockers.

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
5. real runtime on this machine should use a wrapper that injects repo-local dependencies rather than relying on the ambient Python installation

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
5. `tau_bench_preflight`
Checks local importability plus required provider environment variables before any online tau run is attempted.

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
4. `scripts/run_protocol.py`
4. `scripts/validate_records.py`

`run_eval.py` currently supports:

1. `plan-skillsbench`
2. `execute-plan`
3. `import-tau-results`
4. `import-skillsbench-results`
5. `hydrate-skillsbench`
6. `import-skillsbench-job`

`run_protocol.py` currently supports:

1. `run-skillsbench-suite`
2. `run-tau-suite`

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
11. config-driven suite orchestration
12. env-file loading and protocol-level env override wiring
13. task-preparation helpers for copied SkillsBench tasks

Primary test command:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## Environment Constraints

Current release-facing constraints:

1. `Linux-first` is the official support target for `v0.1`.
2. Windows helper scripts remain available, but they are not the primary public execution path.
3. `tau-bench` live execution requires model-provider credentials and is not required for the first public release.
4. Upstream benchmark checkouts under `benchmarks/` are local dependencies, not vendored release contents.
5. Real `SkillsBench` Docker tasks may need explicit timeout policy because environment setup instability is still machine-dependent.

## Release Surface

Tracked release assets should focus on protocol code, schemas, CLI entrypoints, docs, tests, and representative validated artifacts.

The following are intentionally not part of the current release-critical surface:

1. local caches and local dependency overlays
2. local secret files
3. run-local prepared task copies
4. incomplete experimental `codex` prepared-suite outputs

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
5. task-level Dockerfile hardening is still incomplete even though the suite runner now supports explicit transient-failure retries
6. first fully successful non-`oracle` suite with stable Docker service behavior on this machine

## Next Engineering Steps

1. Add a leaderboard builder from `summary.jsonl`.
2. Add a regression suite over frozen Harbor job fixtures.
3. Add multi-phase real-run orchestration so `FG/BR/IE` can be computed from imported job outputs.
4. Expand the failure taxonomy and task-specific mitigations for Docker build and dependency-download errors beyond the current suite-level retry policy.

## Update: Real SkillsBench Bridge

Resolved in the current revision:

1. `SkillsBench` plans can now be constrained by explicit `task_id` values.
2. Sparse checkout hydration is now a first-class CLI step driven from the generated plan.
3. Dedicated repository-local Harbor launchers now exist for both Windows and Linux:
   - `scripts/harbor312`
   - `scripts/harbor312.cmd`
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
4. launcher: repository-local `harbor312` wrapper
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

## Update: Publication Sync

The repository state has been re-checked after the real smoke-chain work and is currently synchronized with GitHub.

Observed publication state:

1. local branch: `main`
2. working tree: clean
3. remote publication path: `git@github.com:Yuchong-W/Protocol_Bench.git`
4. supported transport on this machine: SSH

Operational note:

1. `gh` is not installed in this environment, so repository publication currently uses direct `git` push over SSH rather than a PR-oriented GitHub CLI flow
2. this does not block repository synchronization, but it does mean PR automation should not be treated as part of the local MVP release path

## Update: Real Protocol Suite Runner

The project now has a config-driven multi-run orchestrator for real `SkillsBench` protocol tests.

New capability:

1. a suite config can declare multiple phase/split runs explicitly
2. each run is materialized into its own `plan`, `hydrate`, `execute`, and `import` outputs
3. the suite runner combines imported run records into a shared `combined_runs.jsonl`
4. when the suite is complete enough, it automatically aggregates `summary.jsonl`

Engineering choices:

1. suite config paths are resolved relative to the config file location
2. the runner supports an import-only mode so regression tests do not need live Docker execution
3. explicit split assignment is now a first-class plan-construction path, rather than overloading random split sampling

## Update: First Real Multi-Run Protocol Test

The first real multi-run protocol test has now completed successfully.

Suite:

1. config: `protocol/skillsbench_oracle_real_suite.json`
2. benchmark: `skillsbench`
3. path type: `oracle`
4. phases: `T0`, `T1`
5. splits executed: `replay`, `heldout`

Observed output:

1. `combined_runs.jsonl` was generated and validates against `runs.schema.json`
2. `summary.jsonl` was generated and validates against `summary.schema.json`
3. `dialogue-parser` succeeded in both `T0 replay` and `T1 replay`
4. `citation-check` failed in both `heldout` runs, but those failures were still imported correctly into protocol records

Engineering implication:

1. the project has moved from single-run real smoke testing to true multi-run protocol execution
2. the remaining bottleneck is no longer orchestration glue
3. it is benchmark-task stability and adaptation-path implementation for non-oracle runs

## Update: Task Preparation Layer

The suite runner now supports a run-local task-preparation phase before execution.

Current capabilities:

1. copy only the selected `SkillsBench` tasks into a per-run prepared root
2. strip `environment/skills` for `T0`-style frozen runs without mutating the upstream checkout
3. rewrite Dockerfiles when skills are stripped so `COPY skills ...` and skill-only `PYTHONPATH` lines do not break Docker build
4. apply explicit task patches by task ID

Current built-in patch set:

1. `offer_letter_generator_system_docx`
Rewrites `offer-letter-generator` to use `python3-docx` from the system package manager instead of the unstable `pip python-docx` dependency chain observed on this machine.
2. `dialogue_parser_apt_retry`
Hardens the `dialogue-parser` Dockerfile with apt retry and timeout flags for the Graphviz system package install.
3. `citation_check_apt_retry`
Hardens the `citation-check` Dockerfile with apt retry and timeout flags for the Ubuntu package install step.
4. `citation_check_python_runtime`
Rewrites `citation-check` to use a Python slim base image plus pip-installed verifier dependencies, and emits `reward.txt` directly from the verifier script so Harbor can import the result as a successful run.

Why this exists:

1. several upstream `SkillsBench` tasks currently fail here because transitive `pip` dependencies intermittently resolve as unavailable during Docker build
2. we need a way to separate protocol logic from machine-local environment noise
3. preparation happens in a run-local copy and is therefore auditable and reversible

Additional prepared-copy hardening now in place:

1. shell scripts under prepared `SkillsBench` tasks are normalized from CRLF to LF before execution
2. this avoids Linux false negatives where Harbor reports `required file not found` for existing `*.sh` files with Windows line endings

## Update: First Non-Oracle Probe

`Harbor + codex` is now confirmed to be reachable on this machine.

Observed probes:

1. `dialogue-parser` with `-a codex` reaches real task execution setup rather than failing immediately on missing credentials
2. the first non-`oracle` failure mode was `AgentSetupTimeoutError` at `360.0` seconds, not agent absence
3. a later retry with increased setup timeout was blocked by Docker environment instability rather than protocol logic

Engineering implication:

1. non-`oracle` execution is now a runtime-stability problem, not a missing-integration problem
2. timeout policy must remain a first-class suite config input
3. a prepared external-path suite can now be expressed cleanly even if this machine still needs Docker stabilization for consistent completion

## Update: tau-bench Local Runtime Overlay

`tau-bench` no longer depends on the ambient Windows Python environment on this machine.

Implemented path:

1. repo-local dependency overlay: `.pydeps311`
2. local wrapper: `scripts\tau311.cmd`
3. upstream checkout on `PYTHONPATH`: `benchmarks\tau-bench`
4. interpreter: `py -3.11`

Why this was needed:

1. direct `pip install` under the default Anaconda-backed `python` path repeatedly hung or failed
2. user-site installs eventually failed with `WinError 5` under `C:\Users\22793\AppData\Roaming\Python`
3. mixing `Anaconda`, `py -3.11`, `uv`, and Harbor runtimes made global dependency debugging noisy and non-reproducible

Current verified behavior:

1. `scripts\tau311.cmd -c "import openai, litellm, tenacity"` succeeds
2. `scripts\tau311.cmd -c "import tau_bench"` succeeds
3. the protocol preflight now verifies dependency importability independently from provider credentials

Engineering implication:

1. future `tau-bench` execution on this machine should go through `scripts\tau311.cmd`
2. local dependency overlays are a safer default than user-site installs for single-researcher benchmark workspaces

## Update: tau-bench Protocol Status

`tau-bench` now has a protocol path that is operationally distinct from its provider-credential path.

Current status:

1. historical import suite: `protocol/tau_bench_retail_historical_suite.json`
2. online smoke suite: `protocol/tau_bench_retail_openai_smoke_suite.json`
3. suite runner command: `python scripts\run_protocol.py run-tau-suite --config <suite>`

Observed results:

1. the historical suite executes end-to-end and generates a valid `summary.jsonl`
2. the online smoke suite now fails fast in preflight rather than hanging in package installation
3. the remaining online blocker is `OPENAI_API_KEY` absence, not dependency import failure

Engineering implication:

1. `tau-bench` protocol integration is ready for real execution once one provider credential is supplied
2. the next failure to expect is benchmark/runtime behavior, not environment bootstrap

## Update: tau-bench Protocol-Level Env Resolution

`tau-bench` no longer depends on ad-hoc shell exports for provider credentials.

Implemented path:

1. suite schema now supports `env_file` at both `execution` and per-run level
2. the runner loads dotenv-style `KEY=VALUE` files without external dependencies
3. the same resolved env overrides are applied to both preflight and real subprocess execution
4. `execute_command_plan` now accepts explicit `env_overrides` and records only the override keys, not secret values

Resolution order:

1. run-level `env_file`
2. suite-level `execution.env_file`
3. config-directory `.env.local`
4. config-directory `.env`
5. benchmark repo `.env.local`
6. benchmark repo `.env`
7. inherited shell environment

Why this was needed:

1. VSCode or local tooling can have working provider setup that is invisible to a new shell launched for protocol execution
2. relying only on shell exports makes smoke runs non-reproducible and hard to hand off
3. benchmark execution should be config-driven, including secret-source resolution, even if secret values themselves are never committed

Current verified behavior:

1. unit coverage now includes dotenv parsing and subprocess env injection
2. `run_tau_bench_suite(...)` passes resolved env overrides into preflight
3. `protocol/.env.local` is now the recommended gitignored local credential location, with `protocol/tau_openai.env.example` as the checked-in template
4. Windows UTF-8 env files with BOM are handled via `utf-8-sig`, so PowerShell-written local env files resolve correctly

## Update: Structured SkillsBench Retry Policy

`SkillsBench` real suites now support explicit transient-failure retries without hiding retry provenance.

Implemented path:

1. `protocol_suite.schema.json` now supports `retry_policy` at both suite-execution and per-run level
2. `run-skillsbench-suite(...)` now records each attempt under `attempts/<run_name>/`
3. every attempt gets its own `plan`, `execution`, `runs`, and execution-artifact directory
4. the final run report records both the full attempt list and the selected final attempt

Why this was needed:

1. the Linux real probe proved the protocol loop was sound, but upstream Docker builds still fail intermittently on package downloads
2. hidden reruns would make benchmark evidence harder to audit
3. the release-critical real suite needs a way to absorb transient infra failures without pretending deterministic benchmark failures succeeded

Current verified behavior:

1. unit coverage now exercises a transient failure on attempt 1 followed by a successful final attempt
2. the tracked `SkillsBench oracle` real suite enables a conservative two-attempt policy for timeout-style failures and known apt/network fetch errors
3. deterministic failures such as the observed `RewardFileNotFoundError` remain non-retriable by default
4. a real Linux `dialogue-parser` probe triggered a retry from `attempt01` to `attempt02`, with both Harbor jobs imported into valid attempt-level `runs.jsonl` artifacts and the retry reason recorded as `exception_message:e: failed to fetch`
5. after enabling run-local task preparation with apt hardening and shell normalization, a second real `dialogue-parser` probe completed successfully with `score = 1.0` and no retry
6. after switching `citation-check` to the Python-runtime prepared patch, a real Linux heldout probe also completed successfully with `score = 1.0` and no exception

Engineering implication:

1. retry is now part of the protocol artifact model, not an undocumented shell habit
2. remaining robustness work should focus on task-level Docker hardening and a sharper failure taxonomy
