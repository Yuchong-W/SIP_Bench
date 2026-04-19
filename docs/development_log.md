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

### Local Repository Repair and Push Attempt

Work completed:

1. Removed the broken local `.git` residue under `E:\Protocal_Bench`.
2. Re-initialized the workspace as a clean git repository on branch `main`.
3. Re-ran the current regression and schema validation suite.
4. Created root commit `cb19fed` with the current MVP scaffold.
5. Added remote `origin = https://github.com/Yuchong-W/Protocol_Bench.git`.
6. Attempted normal and escalated `git push origin main`.

Tests run:

1. `python -m unittest discover -s tests -p "test_*.py"`
2. `python scripts\validate_records.py --data results\dryrun\sample_runs.jsonl --schema runs`
3. `python scripts\validate_records.py --data results\dryrun\summary.jsonl --schema summary`
4. `git push origin main`
5. escalated retry of `git push origin main`

Observed result:

1. local git state is now healthy
2. the repository has a valid root commit and remote binding
3. both push attempts fail with `Failed to connect to github.com port 443`

Current blocker:

1. final publication is blocked only by outbound GitHub connectivity from this environment

Follow-up note:

1. a documentation-only follow-up commit was added after the initial scaffold commit so the recorded publish state and release manifest are part of local history
2. a later retry of `git push origin main` still failed with the same `github.com:443` connectivity error

### Network Retry and SSH Publication

Work completed:

1. Re-tested direct HTTPS connectivity to `github.com`.
2. Verified that `github.com:443` still times out while `github.com:22` is reachable.
3. Verified SSH authentication with `git@github.com`.
4. Switched `origin` from HTTPS to SSH.
5. Fetched remote `main`, inspected the remote initial commit, merged it without rewriting history, and pushed successfully.

Tests run:

1. `curl.exe -I --max-time 20 https://github.com`
2. `git ls-remote https://github.com/Yuchong-W/Protocol_Bench.git`
3. `Test-NetConnection github.com -Port 443`
4. `Test-NetConnection github.com -Port 22`
5. `ssh -T git@github.com`
6. `git fetch origin main`
7. `git push origin main`

Observed result:

1. HTTPS transport remains blocked from this environment.
2. SSH transport works and authenticates as `Yuchong-W`.
3. Remote `main` already contained a single `Initial commit` with a one-line `README.md`.
4. The local branch was merged with `origin/main` and pushed successfully.

Current status:

1. `E:\Protocal_Bench` is now published to `Yuchong-W/Protocol_Bench`.
2. The active publication path for this machine should use SSH, not HTTPS.

### Real Upstream Checkout and SkillsBench Importer

Work completed:

1. Replaced the placeholder `tau-bench` directory with a real SSH checkout.
2. Replaced the placeholder `SkillsBench` directory with a real sparse SSH checkout.
3. Materialized `SkillsBench` metadata under `website/src/data/`.
4. Added a real SkillsBench importer that consumes trajectory/result JSON and writes SIP `runs.jsonl`.
5. Fixed the tau importer contract so upstream `task_split` and SIP `benchmark_split` are no longer conflated.
6. Added test fixtures and regression coverage for SkillsBench result import.
7. Imported a real upstream SkillsBench sample trajectory file into `results/dryrun/skillsbench_upstream_withskills.jsonl`.

Tests run:

1. `python -m unittest discover -s tests -p "test_*.py"`
2. `python scripts\run_eval.py import-skillsbench-results --source tests\fixtures\skillsbench_results_sample.json --out results\dryrun\skillsbench_runs_sample.jsonl --benchmark-split golden --phase T1 --seed 3 --registry tests\fixtures\skillsbench_registry_sample.json --agent-version fixture-import --benchmark-version skillsbench-fixture`
3. `python scripts\run_eval.py import-tau-results --source tests\fixtures\tau_results_sample.json --out results\dryrun\tau_runs.jsonl --env retail --task-split test --benchmark-split heldout --phase T1 --path-type external --model-name gpt-5-mini --agent-name tau-import --agent-version 0.1.0 --seed 9`
4. `python scripts\validate_records.py --data results\dryrun\skillsbench_runs_sample.jsonl --schema runs`
5. `python scripts\validate_records.py --data results\dryrun\tau_runs.jsonl --schema runs`
6. `python scripts\run_eval.py import-skillsbench-results --source benchmarks\skillsbench\website\src\data\sample-trajectories.json --out results\dryrun\skillsbench_upstream_withskills.jsonl --benchmark-split golden --phase T1 --seed 0 --repo-root benchmarks\skillsbench --agent-version upstream-sample --condition withskills`
7. `python scripts\validate_records.py --data results\dryrun\skillsbench_upstream_withskills.jsonl --schema runs`

Observed result:

1. The SkillsBench importer now consumes real upstream trajectory format.
2. Imported rows preserve registry metadata and derive score, timestamps, token counts, and tool-call counts from upstream fields.
3. The local machine can maintain upstream checkouts through SSH even though GitHub HTTPS remains blocked.

Open follow-up:

1. The sparse SkillsBench checkout still needs a task-hydration helper before real task execution can be driven from a plan.


### Real SkillsBench End-to-End Wiring

Work completed:

1. Added explicit `task_id` filtering to `plan-skillsbench` so a single known task can be selected deterministically.
2. Added `hydrate-skillsbench` to expand the sparse checkout based on a concrete manifest before execution.
3. Added `scripts\harbor312.cmd` so Harbor runs under Python `3.12` with local cache, UTF-8 output, and Docker BuildKit disabled.
4. Added a Harbor job importer for SkillsBench so real `result.json` directories can be translated into SIP `runs.jsonl`.
5. Added regression fixtures for Harbor job import and extended unit coverage for hydration plus Harbor-job parsing.

Tests and probes run during implementation:

1. `harbor run -p benchmarks\skillsbench	asks\court-form-filling -a oracle --job-name skillsbench-oracle-court-form-filling --jobs-dir results
eal_jobs --n-concurrent 1 --artifact /logs/verifier --debug`
2. `uvx --python 3.12 harbor --version`
3. `uvx --python 3.12 harbor run -p benchmarks\skillsbench	asks\court-form-filling -a oracle --job-name skillsbench-oracle-court-form-filling-py312 --jobs-dir results
eal_jobs_py312 --n-concurrent 1 --artifact /logs/verifier --debug`
4. `uvx --python 3.12 harbor run -p benchmarks\skillsbench	asks\offer-letter-generator -a oracle --job-name skillsbench-oracle-offer-letter-generator-py312 --jobs-dir results
eal_jobs_py312 --n-concurrent 1 --artifact /logs/verifier`

Observed result:

1. The global `harbor.exe` on Python `3.13` fails before Docker build with `NotImplementedError` during Windows subprocess orchestration.
2. Harbor on Python `3.12` clears that runtime bug and reaches real Docker environment setup.
3. Real SkillsBench runs are still vulnerable to Docker builder and external package-network failures on this machine, which now appear as importable Harbor job errors instead of disappearing outside the protocol.
4. The remaining engineering gap is no longer "how to import Harbor output" but "how to stabilize real task execution under local Docker/network conditions".


### Real SkillsBench Smoke Run Outcome

Work completed:

1. Built a real SkillsBench plan around `offer-letter-generator` using the repository-local `scripts\harbor312.cmd` launcher.
2. Hydrated the sparse checkout for the selected task.
3. Ran `execute-plan --mode subprocess` against the real upstream checkout and produced a Harbor job directory under `results\real_jobs_e2e\skillsbench-e2e-offer-letter`.
4. Imported that real Harbor job into `results\dryrun\skillsbench_real_smoke_runs.jsonl` and validated it against `runs.schema.json`.
5. Hardened the subprocess executor to capture bytes and decode with UTF-8 replacement, because Harbor output contained non-GBK bytes on Windows.

Commands run:

1. `python scripts\run_eval.py plan-skillsbench --registry benchmarks\skillsbench\website\src\data\tasks-registry.json --repo-root benchmarks\skillsbench --task-id offer-letter-generator --replay-count 1 --adapt-count 0 --heldout-count 0 --harbor-bin scripts\harbor312.cmd --extra-arg=--jobs-dir --extra-arg=results\real_jobs_e2e --extra-arg=--job-name --extra-arg=skillsbench-e2e-offer-letter --extra-arg=--artifact --extra-arg=/logs/verifier --out results\dryrun\skillsbench_real_smoke_plan.json`
2. `python scripts\run_eval.py hydrate-skillsbench --plan results\dryrun\skillsbench_real_smoke_plan.json --repo-root benchmarks\skillsbench --split replay --out results\dryrun\skillsbench_real_smoke_hydration.json`
3. `python scripts\run_eval.py execute-plan --plan results\dryrun\skillsbench_real_smoke_plan.json --split replay --mode subprocess --cwd E:\Protocal_Bench --out results\dryrun\skillsbench_real_smoke_execution.json`
4. `python scripts\run_eval.py import-skillsbench-job --job-dir results\real_jobs_e2e\skillsbench-e2e-offer-letter --out results\dryrun\skillsbench_real_smoke_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 0 --repo-root benchmarks\skillsbench --agent-version harbor312-smoke`
5. `python scripts\validate_records.py --data results\dryrun\skillsbench_real_smoke_runs.jsonl --schema runs`

Observed result:

1. The protocol chain is now fully wired on real upstream data: plan, hydrate, execute, import, and schema validation all completed.
2. The execution report shows the Harbor command launched successfully and wrote a real job directory.
3. The imported SIP run shows the benchmark trial itself failed before agent execution because Docker build hit a `pip` download timeout while installing `python-docx` dependencies inside the task image.
4. This failure is now visible as a first-class protocol record instead of being lost in ad-hoc logs.


### Real SkillsBench Successful Smoke Run

Work completed:

1. Reused the real upstream `dialogue-parser` task as the first candidate for a fully successful end-to-end run.
2. Confirmed that the initial run failed at environment startup because the default Harbor build timeout of `600` seconds was too low for this machine.
3. Rebuilt the plan with `--environment-build-timeout-multiplier 4`.
4. Re-ran the real chain through `plan`, `hydrate`, `execute`, `import`, and `validate`.
5. Produced a successful SIP record in `results/dryrun/skillsbench_dialogue_timeout4_runs.jsonl`.

Commands run:

1. `scripts\harbor312.cmd run --help`
2. `python scripts\run_eval.py plan-skillsbench --registry benchmarks\skillsbench\website\src\data\tasks-registry.json --repo-root benchmarks\skillsbench --task-id dialogue-parser --replay-count 1 --adapt-count 0 --heldout-count 0 --harbor-bin scripts\harbor312.cmd --extra-arg=--jobs-dir --extra-arg=results\real_jobs_e2e --extra-arg=--job-name --extra-arg=skillsbench-e2e-dialogue-parser --extra-arg=--artifact --extra-arg=/logs/verifier --out results\dryrun\skillsbench_dialogue_smoke_plan.json`
3. `python scripts\run_eval.py execute-plan --plan results\dryrun\skillsbench_dialogue_smoke_plan.json --split replay --mode subprocess --cwd E:\Protocal_Bench --out results\dryrun\skillsbench_dialogue_smoke_execution.json`
4. `python scripts\run_eval.py import-skillsbench-job --job-dir results\real_jobs_e2e\skillsbench-e2e-dialogue-parser --out results\dryrun\skillsbench_dialogue_smoke_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 0 --repo-root benchmarks\skillsbench --agent-version harbor312-smoke`
5. `python scripts\run_eval.py plan-skillsbench --registry benchmarks\skillsbench\website\src\data\tasks-registry.json --repo-root benchmarks\skillsbench --task-id dialogue-parser --replay-count 1 --adapt-count 0 --heldout-count 0 --harbor-bin scripts\harbor312.cmd --extra-arg=--jobs-dir --extra-arg=results\real_jobs_e2e --extra-arg=--job-name --extra-arg=skillsbench-e2e-dialogue-parser-timeout4 --extra-arg=--artifact --extra-arg=/logs/verifier --extra-arg=--environment-build-timeout-multiplier --extra-arg=4 --out results\dryrun\skillsbench_dialogue_timeout4_plan.json`
6. `python scripts\run_eval.py hydrate-skillsbench --plan results\dryrun\skillsbench_dialogue_timeout4_plan.json --repo-root benchmarks\skillsbench --split replay --out results\dryrun\skillsbench_dialogue_timeout4_hydration.json`
7. `python scripts\run_eval.py execute-plan --plan results\dryrun\skillsbench_dialogue_timeout4_plan.json --split replay --mode subprocess --cwd E:\Protocal_Bench --out results\dryrun\skillsbench_dialogue_timeout4_execution.json`
8. `python scripts\run_eval.py import-skillsbench-job --job-dir results\real_jobs_e2e\skillsbench-e2e-dialogue-parser-timeout4 --out results\dryrun\skillsbench_dialogue_timeout4_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 0 --repo-root benchmarks\skillsbench --agent-version harbor312-timeout4`
9. `python scripts\validate_records.py --data results\dryrun\skillsbench_dialogue_timeout4_runs.jsonl --schema runs`

Observed result:

1. The first `dialogue-parser` run imported cleanly but recorded `EnvironmentStartTimeoutError`, which isolated the failure to Harbor build timeout policy rather than protocol glue.
2. The second run with `--environment-build-timeout-multiplier 4` completed successfully and imported as a valid SIP `runs.jsonl` row.
3. The end-to-end chain is now confirmed on real upstream data for both failure and success cases.
4. The next meaningful work item is multi-phase orchestration, not additional one-off import debugging.


### Publication Sync Check

Work completed:

1. Re-checked the repository publication state after the real smoke-chain work.
2. Confirmed that the local branch is clean and already synchronized with remote `main`.
3. Recorded the current publication constraint that this machine uses SSH `git push`, not GitHub CLI / PR automation.
4. Updated the technical design and release tracking docs so the publication path is documented in-repo.

Commands run:

1. `git status --short --branch`
2. `gh --version`
3. `gh auth status`

Observed result:

1. `E:\Protocal_Bench` had no uncommitted code changes before the documentation sync.
2. `gh` is not installed in this environment.
3. Direct repository synchronization is still possible through `git` over SSH, which is the active supported publication path for this machine.
4. A documentation-only follow-up commit is therefore the correct way to reflect the current published state.


### Config-Driven Protocol Runner

Work completed:

1. Added `src/sip_bench/protocol_runner.py` for config-driven multi-run execution.
2. Added `scripts\run_protocol.py` as the CLI entrypoint.
3. Added `schemas\protocol_suite.schema.json` for suite config validation.
4. Added `protocol\skillsbench_oracle_real_suite.json` as the first real suite config.
5. Added `tests\test_protocol_runner.py` for explicit-plan and import-only suite regression coverage.

Tests run:

1. `python -m unittest tests.test_protocol_runner -v`
2. `python -m unittest discover -s tests -p "test_*.py"`

Observed result:

1. The orchestrator can build explicit split plans instead of relying on random manifest sampling.
2. The suite runner can aggregate imported records into a valid `summary.jsonl`.
3. Import-only mode gives deterministic regression coverage without requiring live Docker execution.


### First Real Protocol Suite Run

Work completed:

1. Hydrated `citation-check` as a second real task candidate.
2. Fixed suite-config path handling by expressing repo paths relative to `protocol\`.
3. Fixed orchestrator execution so local launchers are resolved correctly and real runs execute from the repository root.
4. Ran the first real multi-run suite with `T0 replay`, `T0 heldout`, `T1 replay`, and `T1 heldout`.
5. Produced `combined_runs.jsonl`, `summary.jsonl`, and `suite_report.json` under `results\protocol_runs\skillsbench_oracle_real_suite`.

Commands run:

1. `git -C benchmarks\skillsbench sparse-checkout add tasks/citation-check`
2. `python -m unittest tests.test_protocol_runner -v`
3. `python -m unittest discover -s tests -p "test_*.py"`
4. `python scripts\run_protocol.py run-skillsbench-suite --config protocol\skillsbench_oracle_real_suite.json --mode subprocess`

Observed result:

1. The suite completed with `4` imported records and valid combined-run schema validation.
2. `summary.jsonl` was generated and validated successfully.
3. `dialogue-parser` succeeded in both replay runs.
4. `citation-check` did not pass in the heldout runs, but both outcomes were still imported correctly and contributed to the protocol summary.


### Task Preparation Layer

Work completed:

1. Extended `protocol_suite.schema.json` with per-run `task_preparation`.
2. Added run-local task copying to the protocol runner.
3. Added `skill_mode = strip|keep` handling for copied `SkillsBench` tasks.
4. Added Dockerfile rewriting so stripped-skill tasks no longer keep broken `COPY skills ...` or skill-only `PYTHONPATH` lines.
5. Added the first explicit task patch, `offer_letter_generator_system_docx`.
6. Added a first non-`oracle` suite config: `protocol\skillsbench_codex_external_prepared_suite.json`.

Tests run:

1. `python -m unittest discover -s tests -p "test_*.py"`
2. `python -c "from pathlib import Path; import sys; sys.path.insert(0, str(Path('src').resolve())); from sip_bench.protocol_runner import load_protocol_suite_config; cfg = load_protocol_suite_config('protocol/skillsbench_codex_external_prepared_suite.json'); print(cfg['suite_name'], len(cfg['runs']))"`

Observed result:

1. Unit-test coverage increased to `29`.
2. The suite schema accepts copy-mode task preparation, skill stripping, and patch declarations.
3. The new prepared external-path suite is loadable through the real runner entrypoint.


### Real Task Stability Probes

Work completed:

1. Screened additional upstream `SkillsBench` tasks with `oracle`.
2. Probed the real `codex` agent on `dialogue-parser`.
3. Generated a local prepared task copy for `offer-letter-generator` using the new patch path.

Commands run:

1. `scripts\harbor312.cmd run -y -p benchmarks\skillsbench\tasks\court-form-filling -a oracle --jobs-dir results\real_jobs_screen --job-name screen-court-form-filling --artifact /logs/verifier --environment-build-timeout-multiplier 4 -n 1`
2. `scripts\harbor312.cmd run -y -p benchmarks\skillsbench\tasks\offer-letter-generator -a oracle --jobs-dir results\real_jobs_screen --job-name screen-offer-letter-generator --artifact /logs/verifier --environment-build-timeout-multiplier 4 -n 1`
3. `scripts\harbor312.cmd run -y -p benchmarks\skillsbench\tasks\dialogue-parser -a codex --jobs-dir results\real_jobs_screen --job-name screen-codex-dialogue-parser --artifact /logs/verifier --environment-build-timeout-multiplier 4 -n 1`
4. `python -c "from pathlib import Path; import sys; sys.path.insert(0, str(Path('src').resolve())); from sip_bench.protocol_runner import prepare_skillsbench_tasks; report = prepare_skillsbench_tasks(source_repo_root=Path('benchmarks/skillsbench').resolve(), registry_path=Path('benchmarks/skillsbench/website/src/data/tasks-registry.json').resolve(), split_task_ids={'replay': [], 'adapt': [], 'heldout': ['offer-letter-generator'], 'drift': []}, prepared_root=Path('results/prepared_probes/offer_letter_generator_keep').resolve(), skill_mode='keep', patches={'offer-letter-generator': ['offer_letter_generator_system_docx']}); print(report['prepared_root'])"`

Observed result:

1. `court-form-filling` fails during Docker build because `fillpdf` transitively requires `Pillow`, which the container could not resolve from `pip`.
2. `offer-letter-generator` fails during Docker build because `python-docx` transitively requires `lxml`, which the container could not resolve from `pip`.
3. `codex` is reachable through Harbor and does not fail on missing credentials; the first real non-`oracle` failure was `AgentSetupTimeoutError` after `360.0` seconds.
4. Subsequent Harbor runs also exposed intermittent Docker availability and overlay filesystem instability on this machine, so current blocking risk is runtime stability rather than missing protocol glue.

## 2026-04-17

### tau-bench Protocol Runner Completion

Work completed:

1. Extended `protocol_suite.schema.json` from `SkillsBench`-only to `SkillsBench + tau-bench`.
2. Added `run_tau_bench_suite(...)` plus explicit tau plan construction in `src\sip_bench\protocol_runner.py`.
3. Added `run-tau-suite` to `scripts\run_protocol.py`.
4. Added two tau suite configs:
   - `protocol\tau_bench_retail_historical_suite.json`
   - `protocol\tau_bench_retail_openai_smoke_suite.json`
5. Added protocol-runner regression coverage for tau import-only aggregation and config validation.

Tests run:

1. `python -m unittest discover -s tests -p "test_*.py"`
2. `python scripts\run_protocol.py run-tau-suite --config protocol\tau_bench_retail_historical_suite.json --mode subprocess`

Observed result:

1. The full test suite passed with `32` tests.
2. The historical tau suite executed end-to-end and generated a valid `summary.jsonl`.
3. `tau-bench` is now on the same protocol footing as `SkillsBench` for import-only and aggregation flows.

### tau-bench Runtime Isolation

Work completed:

1. Created repo-local dependency overlay directory `.pydeps311`.
2. Added `scripts\tau311.cmd` to force `py -3.11` plus local `PYTHONPATH` injection.
3. Re-pointed both tau suite configs to `scripts\tau311.cmd` instead of ambient `python`.

Commands run:

1. `scripts\tau311.cmd -c "import openai, litellm, tenacity; print('core_wrapper_ok')"`
2. `scripts\tau311.cmd -c "import tau_bench; from litellm import provider_list; print('tau_wrapper_ok', len(provider_list))"`

Observed result:

1. Core OpenAI/LiteLLM imports succeed from the repo-local overlay.
2. `tau_bench` imports succeed from the wrapper path.
3. The machine no longer needs a successful global or user-site `pip install` to run tau preflight.

### Package Installation Diagnosis

Work completed:

1. Confirmed that direct HTTPS access from Python works against both `pypi.org` and the Tsinghua mirror.
2. Confirmed that `pip download` succeeds when cache is disabled.
3. Identified two separate installation hazards:
   - hanging `pip` commands when multiple probes share `E:\pip_cache`
   - `WinError 5` when `pip` attempts to write user-site packages under `C:\Users\22793\AppData\Roaming\Python`
4. Recovered by avoiding user-site install and using the repo-local overlay instead.

Commands run:

1. `py -3.11 -c "import urllib.request ..."`
2. `py -3.11 -m pip download --no-deps --retries 0 --timeout 10 -d results\dryrun\pip_probe openai`
3. targeted installs into `.pydeps311`

Observed result:

1. The problem is not global TLS failure.
2. The reliable path is: no shared pip cache, no user-site install, local overlay only.

### tau Online Smoke Preflight

Work completed:

1. Ran the online tau smoke suite through the new wrapper-backed protocol path.
2. Collected both suite-level and per-run preflight reports.

Commands run:

1. `python scripts\run_protocol.py run-tau-suite --config protocol\tau_bench_retail_openai_smoke_suite.json --mode subprocess`

Observed result:

1. The command now fails fast instead of hanging in environment bootstrap.
2. Preflight dependency import succeeds.
3. The only remaining online blocker is `OPENAI_API_KEY` absence.
4. `tau-bench` is therefore real-test-ready from an engineering standpoint, pending one provider credential.

### tau-bench Env Resolution Hardening

Work completed:

1. Added `env_file` support to the protocol suite schema for both suite-level execution defaults and per-run overrides.
2. Added dotenv-style env-file loading to the runner without introducing a new dependency.
3. Threaded resolved env overrides through tau preflight and real subprocess execution.
4. Added a checked-in template at `protocol\tau_openai.env.example` and gitignored local secret paths under `protocol\`.

Tests run:

1. `python -m unittest discover -s tests -p "test_*.py"`

Observed result:

1. Unit coverage now includes env-file parsing, subprocess env override injection, and tau-suite preflight wiring.
2. `tau-bench` no longer depends on the launching shell having exported `OPENAI_API_KEY` if a suite-adjacent `.env.local` or explicit `env_file` is present.
3. The remaining blocker for a true live smoke run is possession of a valid provider key, not discovering that key inside the protocol runner.
4. Windows-written UTF-8 env files with BOM are now accepted; preflight correctly recognizes `OPENAI_API_KEY` from a temporary probe file written by PowerShell.

### Open-Source Release Packaging

Work completed:

1. Repositioned the repository around a public `protocol-layer benchmark` story instead of an internal milestone log.
2. Added release-engineering files for a real open-source launch:
   - `LICENSE`
   - `NOTICE`
   - `CITATION.cff`
   - `CONTRIBUTING.md`
   - `SECURITY.md`
   - GitHub issue templates
   - GitHub pull request template
   - GitHub Actions CI workflow
3. Added `docs/milestone_plan_v0_1.md` and `docs/release_checklist_v0_1.md`.
4. Rewrote the README around `Linux-first` quickstart, representative artifacts, and release-critical versus experimental paths.
5. Updated release-facing docs so `SkillsBench oracle` and `tau-bench historical` are the explicit `v0.1` evidence path.

Validation run:

1. `python3 -m unittest discover -s tests -p "test_*.py"`
2. `python3 scripts/aggregate_metrics.py --runs results/dryrun/sample_runs.jsonl --out /tmp/sip_summary.jsonl`
3. `python3 scripts/run_eval.py import-skillsbench-job --job-dir tests/fixtures/skillsbench_harbor_job_sample --out /tmp/skillsbench_job_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 21 --registry tests/fixtures/skillsbench_registry_sample.json --agent-version fixture-import --benchmark-version skillsbench-harbor-fixture`
4. `python3 scripts/validate_records.py --data /tmp/skillsbench_job_runs.jsonl --schema runs`
5. `python3 scripts/validate_records.py --data results/protocol_runs/skillsbench_oracle_real_suite/combined_runs.jsonl --schema runs`
6. `python3 scripts/validate_records.py --data results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl --schema summary`

Observed result:

1. The repository now has a credible public release surface instead of only internal implementation notes.
2. The first public quickstart no longer depends on `codex` connectivity or private model credentials.
3. The Linux path is now materially stronger because bare `python` subprocess calls fall back to the active interpreter when needed.
4. The remaining release-cleanup problem is mostly line-ending churn in tracked files rather than missing release structure.

### Release Validation Consolidation

Work completed:

1. Added `scripts/run_release_checks.py` as a single local entrypoint for the public `v0.1` validation path.
2. Rewired GitHub Actions CI to call that script instead of duplicating release checks inline.
3. Added `.editorconfig` so normal repository text files default to `LF` while Windows launchers keep `CRLF`.
4. Updated the README, contributing guide, script docs, and release checklist to point at the shared validation command.

Validation run:

1. `python3 scripts/run_release_checks.py`

Observed result:

1. Release validation is now easier to rerun locally and less likely to drift between docs, CI, and the actual release branch.
2. The repository now has both Git-level and editor-level line-ending policy, which should reduce future formatting churn.

### Working Tree Cleanup

Work completed:

1. Verified that the remaining tracked-file noise after release packaging was line-ending-only, not semantic content drift.
2. Refreshed those files through the git index instead of rewriting tracked artifacts by hand.
3. Reached a fully clean working tree again after the release-validation and doc commits were pushed.

Observed result:

1. The release branch is now back to a reviewable baseline with no hidden local dirt.
2. Future release work can be measured against real changes instead of CRLF-only churn.

### Linux Runbook And Post-Release Backlog

Work completed:

1. Added a dedicated Linux validation runbook for machines that cannot use `codex`.
2. Added a post-`v0.1` backlog so README polish, live `tau`, and prepared-suite work stay outside the release-critical path.
3. Linked both docs from the README and release manifest.

Observed result:

1. The remaining unchecked release items are now explicit and operational, not just implied in conversation.
2. The release branch has a cleaner boundary between `v0.1` scope and follow-up work.

### Real SkillsBench Linux Probe

Work completed:

1. Confirmed Docker was actually usable on the Linux host, not just installed.
2. Ran a real four-run `SkillsBench oracle` Linux probe suite through `run-skillsbench-suite` with Docker-backed Harbor execution.
3. Observed and recorded the full protocol loop:
   - `plan`
   - `hydrate`
   - `execute`
   - `import`
   - `aggregate`
4. Added a POSIX `scripts/harbor312` wrapper and switched the tracked `SkillsBench oracle` suite config to a cross-platform Harbor entrypoint.

Observed result:

1. The Linux probe produced valid `combined_runs.jsonl`, `summary.jsonl`, and `suite_report.json`.
2. The SIP protocol runner correctly recorded multiple classes of real operational failure instead of dropping them:
   - Docker build failures caused by upstream apt/network instability
   - `RewardFileNotFoundError` after agent execution
3. The release-critical protocol path is therefore real on Linux, even though the upstream benchmark tasks remain operationally flaky.

### Structured SkillsBench Retry Policy

Work completed:

1. Added `retry_policy` to `schemas/protocol_suite.schema.json` for suite-level and per-run configuration.
2. Extended `run-skillsbench-suite(...)` so each retry attempt writes separate `plan`, `execution`, and `runs` artifacts under `attempts/<run_name>/`.
3. Updated the tracked `protocol/skillsbench_oracle_real_suite.json` config to allow one explicit retry for transient Docker timeout and package-fetch failures.
4. Added regression coverage for the case where attempt 1 imports a transient failure and attempt 2 becomes the selected final artifact set.

Observed result:

1. Retry provenance now stays visible in the suite report instead of being hidden behind overwritten output files.
2. The release-critical `SkillsBench oracle` suite can now distinguish "protocol is fine, infra was flaky once" from deterministic benchmark failures.
3. `RewardFileNotFoundError` remains outside the default retry set until there is evidence that rerunning the same task reliably fixes it.
4. A real Linux `dialogue-parser` retry probe executed `attempt01` and `attempt02` Harbor jobs end to end, and both attempts were preserved as valid `runs.jsonl` artifacts with the retry trigger recorded as `exception_message:e: failed to fetch`.

### Hardened Prepared SkillsBench Tasks

Work completed:

1. Added task-preparation patches for `dialogue-parser` and `citation-check` Dockerfiles so prepared copies can harden apt installs with retry and timeout flags.
2. Normalized prepared `*.sh` files from CRLF to LF during task preparation so Linux Harbor runs do not fail on shell-script line endings copied from upstream task files.
3. Switched the tracked `SkillsBench oracle` suite to `task_preparation.mode = copy` with explicit patches for the two release-critical tasks.

Observed result:

1. A hardened real `dialogue-parser` Linux probe completed successfully on the first attempt with a valid imported SIP run record and `score = 1.0`.
2. The previous `RewardFileNotFoundError` on `dialogue-parser` was traced to prepared-copy shell scripts using CRLF line endings; once normalized, the task progressed through environment setup, agent execution, and verifier completion.
3. A hardened real `citation-check` probe now reaches an explicit retryable Docker build failure under the prepared copy, which narrows the remaining blocker to Ubuntu package index reliability rather than to protocol glue or script execution.
4. A stronger Python-runtime patch for `citation-check` then removed the Ubuntu apt dependency and verifier bootstrap drift, and a follow-up real heldout probe completed successfully with a valid imported SIP run record and `score = 1.0`.

## 2026-04-18

### Suite Recovery Rerun

Work completed:

1. Added `--run-name` support to `scripts/run_protocol.py` so a config-driven suite can rerun only the named run or runs.
2. Extended `run_skillsbench_suite(...)` and `run_tau_bench_suite(...)` to reuse existing suite reports for unselected runs while rebuilding `combined_runs.jsonl` and `summary.jsonl` from the mixed old-plus-new run set.
3. Fixed Harbor rerun job naming so recovery runs always allocate a fresh job directory instead of reusing a stale prior `result.json`.
4. Added regression coverage for targeted suite reruns and fresh rerun job-name allocation.
5. Re-ran the failed `SkillsBench oracle real suite` `t0_replay` run through the new recovery path and restored the tracked suite to a fully successful `T0/T1 replay + heldout` state.

Tests run:

1. `python3 -m unittest tests.test_protocol_runner -v`
2. `python3 -m unittest discover -s tests -p "test_*.py"`
3. `python3 scripts/run_protocol.py run-skillsbench-suite --config protocol/skillsbench_oracle_real_suite.json --mode subprocess --run-name t0_replay`
4. escalated rerun of the same command outside the sandbox so Harbor and Docker could use normal network access

Observed result:

1. The local green test result is now `45` tests and represents real local regression coverage for protocol logic, fixture-backed import paths, and controlled integration seams; it is not the same thing as re-running every live benchmark path end to end.
2. The recovery rerun first exposed a real stale-import hazard: reusing an existing Harbor job directory caused the protocol to re-import an older failed `dialogue-parser` job.
3. After fresh job-name allocation was added, the next real rerun wrote to `skillsbench-oracle-real-suite-t0_replay-attempt01-rerun02` and imported a successful `dialogue-parser` Harbor result with `score = 1.0`.
4. The tracked `SkillsBench oracle real suite` summary is now back to the intended release-facing shape:
   - `t0_replay_mean = 1.0`
   - `t1_replay_mean = 1.0`
   - `t0_heldout_mean = 1.0`
   - `t1_heldout_mean = 1.0`
   - `br_ratio_mean = 1.0`

### Fresh-Clone Release Validation

Work completed:

1. Created a fresh clone of the current reviewed tree at `/tmp/protocol_bench_fresh_validate_620713f`.
2. Re-ran the documented release validation command from inside that clean checkout instead of from the original working tree.
3. Updated the release plan and checklist so fresh-clone validation is no longer tracked as an unfinished blocker.

Tests run:

1. `git clone /home/yuchong/Protocal_Bench /tmp/protocol_bench_fresh_validate_620713f`
2. `python3 scripts/run_release_checks.py`

Observed result:

1. The clean-checkout validation passed `8/8` checks at commit `620713f0a42d1b956217d950c239183038551dd3`.
2. The documented public validation path does not rely on hidden local working-tree state.
3. The remaining release-gating uncertainty is now remote CI confirmation and final tag publication, not quickstart drift.

### CI-Like Python 3.12 Validation

Work completed:

1. Inspected the repository workflow and confirmed the GitHub Actions job is just `Python 3.12`, `pip install --upgrade pip jsonschema`, and `python scripts/run_release_checks.py`.
2. Recreated that workflow in a new clean clone at `/tmp/protocol_bench_ci_validate_be81239`.
3. Used a dedicated target directory for `pip` dependencies after `venv` creation failed locally because `python3.12-venv` is not installed on this machine.

Tests run:

1. `git clone /home/yuchong/Protocal_Bench /tmp/protocol_bench_ci_validate_be81239`
2. `python3 -m pip install --upgrade pip jsonschema --target /tmp/protocol_bench_ci_validate_be81239/.pydeps`
3. `PYTHONPATH=/tmp/protocol_bench_ci_validate_be81239/.pydeps python3 scripts/run_release_checks.py`

Observed result:

1. The CI-equivalent validation passed `45` tests and `8/8` release-check steps at commit `be81239e47dbcffa619905e79ca1581129db7e20`.
2. The repository's workflow logic appears healthy on the same Python major/minor version used by `.github/workflows/ci.yml`.
3. The remaining uncertainty is specifically GitHub-side workflow visibility and status reporting, not whether the scripted CI path itself works.

### v0.1.0 Tag Publication

Work completed:

1. Received manual confirmation that GitHub Actions was green on reviewed commit `f1472f0f945890f5939253846b4ecd08185dbcc5`.
2. Published annotated tag `v0.1.0` from that reviewed commit.
3. Kept the release anchor on the reviewed green commit instead of moving the tag to a newer bookkeeping-only documentation commit.

Tests run:

1. `git push origin v0.1.0`

Observed result:

1. GitHub accepted the new `v0.1.0` tag.
2. The first public release now has a stable remote reference even though this session still lacks repository-level Actions and release-page visibility.

### SkillsBench Codex External Prepared Probe

Work completed:

1. Built isolated single-run `t0_replay` probe configs under `/tmp` so the prepared external path could be tested without colliding with the tracked suite outputs.
2. Ran a real prepared `dialogue-parser` probe through `run-skillsbench-suite` with `harbor312`, `codex`, and Docker-backed task preparation.
3. Re-ran the same probe with the tracked `dialogue_parser_apt_retry` patch plus the suite retry policy after the first run failed on transient Debian package fetch errors.
4. Confirmed the installed Harbor `codex` agent now requires an explicit model name instead of inheriting the local Codex CLI default from `~/.codex/config.toml`.
5. Updated the tracked `SkillsBench codex external prepared` suite config to use explicit model selection, prepared-task hardening for `dialogue-parser`, and env-file-backed execution overrides.
6. Extended the SkillsBench suite runner so it resolves `.env.local` / `env_file` the same way `tau-bench` already does and passes only the override keys into execution provenance.
7. Ran a third single-run probe with `model = "gpt-5.4"` and then reran the full tracked `protocol/skillsbench_codex_external_prepared_suite.json` to completion.

Tests run:

1. `python3 scripts/run_protocol.py run-skillsbench-suite --config /tmp/skillsbench_codex_external_prepared_t0_replay_probe.json --mode subprocess`
2. `python3 scripts/run_protocol.py run-skillsbench-suite --config /tmp/skillsbench_codex_external_prepared_t0_replay_retry_probe.json --mode subprocess`
3. `python3 scripts/run_protocol.py run-skillsbench-suite --config /tmp/skillsbench_codex_external_prepared_t0_replay_model_probe.json --mode subprocess`
4. `python3 scripts/run_protocol.py run-skillsbench-suite --config protocol/skillsbench_codex_external_prepared_suite.json --mode subprocess`

Observed result:

1. The prepared external path is real on this machine: it reaches task preparation, Harbor job creation, Docker environment startup, and imported SIP run artifacts.
2. The first probe failed in `dialogue-parser` environment build because `apt-get` hit transient package-fetch failures; the second probe hardened that layer and moved the failure boundary upward.
3. After the Docker build issue was mitigated, the next real blocker became `ValueError: Model name is required`, which came from the installed Harbor `codex` agent rather than from SIP-Bench glue code; adding `model = "gpt-5.4"` removed that failure mode.
4. The full tracked prepared suite now completes end to end and generates a valid summary on this host, with:
   - `t0_replay_mean = 0.0`
   - `t1_replay_mean = 0.0`
   - `t0_heldout_mean = 0.0`
   - `t1_heldout_mean = 0.0`
   - `fg_mean = 0.0`
   - `br_mean = 0.0`
5. Agent-side `codex.txt` logs for both `dialogue-parser` and `offer-letter-generator` show repeated `401 Unauthorized` failures because the inherited `OPENAI_API_KEY` is empty, while the final imported SIP records collapse that state into verifier-backed `0.0` scores.
6. The prepared-suite path therefore no longer belongs in the vague category of "maybe inaccessible on this host"; it is now a concrete experimental path whose remaining blocker is specifically credential state, not protocol wiring or task preparation.

### Isolated Harbor Codex Login Bridge Probe

Work completed:

1. Added a repository-local Harbor-to-Codex auth bridge in `src/sip_bench/harbor_codex_bridge.py` plus `tools/harbor_codex_bridge/sitecustomize.py`.
2. Updated `scripts/harbor312` and `scripts/harbor312.cmd` so only this repository's Harbor wrapper prepends the local bridge to `PYTHONPATH` and points `SIP_HARBOR_CODEX_AUTH_SOURCE` at the host `~/.codex/auth.json`.
3. Kept the installed Harbor package untouched; no files under the global `harbor` installation were modified.
4. Added unit coverage for:
   - preferring repo-local login auth when no API key is present
   - omitting empty `OPENAI_API_KEY` values from the agent environment
5. Ran an isolated single-run `t0_replay` probe for prepared `dialogue-parser` against the local bridge path.
6. Re-ran the same probe outside the Codex sandbox so Docker could access the host daemon and the result would not be confounded by sandbox-only `docker.sock` restrictions.

Tests run:

1. `python3 -m unittest tests.test_protocol_runner -v`
2. `python3 scripts/run_protocol.py run-skillsbench-suite --config /tmp/skillsbench_codex_external_prepared_t0_replay_login_bridge_probe.json --mode subprocess`

Observed result:

1. The repo-local bridge works as intended from an isolation standpoint: Harbor is patched only through this repository's wrapper, not by editing any global Harbor file.
2. The sandboxed probe first failed at Docker build time because the sandbox could not cleanly access the host daemon; rerunning outside the sandbox removed that ambiguity.
3. The outside-sandbox rerun advanced through environment setup, agent setup, agent execution, and verifier execution, producing a full Harbor trial artifact under `results/real_jobs_protocol_prepared_t0_replay_login_bridge_probe/...-rerun02/`.
4. Even with the local bridge in place, `agent/codex.txt` still shows repeated `401 Unauthorized` failures that report `Incorrect API key provided: ''`.
5. The local ChatGPT/Codex login state therefore still does not substitute for `OPENAI_API_KEY` on the current Harbor `codex` noninteractive execution path, at least not with this bridge approach.
6. The practical experimental conclusion is unchanged: the next full prepared-suite comparison should still be run with an env-file-backed `OPENAI_API_KEY`, while the repo-local bridge remains useful as contained infrastructure for future auth experiments.

### Repo-Local Host-Auth Custom Agent Probe

Work completed:

1. Confirmed on the host that `codex exec --skip-git-repo-check --model gpt-5.4 --json -- 'Reply with exactly OK'` succeeds using the local ChatGPT login state, so the account itself is not the bottleneck.
2. Extended the SkillsBench command builder and protocol suite schema to accept `agent_import_path`, allowing Harbor to instantiate repo-local custom agents without modifying the global Harbor installation.
3. Added `src/sip_bench/harbor_codex_host_agent.py`, a repo-local `CodexLocalAuthAgent` that:
   - runs `codex exec` on the host instead of inside the task container
   - stages a host workspace mirror for the task
   - syncs outputs back into the Harbor-managed container before verification
   - records host-side token usage and execution metadata in the imported Harbor result
4. Fixed a Harbor integration subtlety: if both `-a codex` and `--agent-import-path ...` are passed, Harbor still prefers the built-in agent name. The command builder now omits `-a` when a custom import path is present.
5. Added helper coverage for:
   - host-workspace instruction rewriting
   - Docker `WORKDIR` inference
   - usage extraction from `codex --json` output
   - repo-local helper script generation for future container-aware host-auth tasks
6. Ran a new prepared single-run `dialogue-parser` probe through the repo-local custom agent path.

Tests run:

1. `codex exec --skip-git-repo-check --model gpt-5.4 --json -- 'Reply with exactly OK'`
2. `python3 scripts/run_protocol.py run-skillsbench-suite --config /tmp/skillsbench_codex_external_prepared_t0_replay_host_agent_probe2.json --mode subprocess`
3. `python3 -m unittest discover -s tests -p 'test_*.py'`

Observed result:

1. The host-side account-auth path is real on this machine; the direct host `codex exec` check succeeded before any Harbor integration work.
2. The repo-local custom-agent probe produced a real Harbor trial result under `results/real_jobs_protocol_prepared_t0_replay_host_agent_probe2/.../dialogue-parser__Uyj6XK4/result.json`.
3. The imported SIP record at `results/protocol_runs/skillsbench_codex_external_prepared_t0_replay_host_agent_probe2/runs/t0_replay.jsonl` is no longer a flat credential failure:
   - `agent_name = codex-local-auth`
   - `score = 0.667`
   - `success = true`
   - `token_input = 416082`
   - `token_output = 9759`
4. The custom agent created `solution.py`, `dialogue.json`, and `dialogue.dot` in the tracked host workspace and synchronized those outputs into the Harbor verifier path before test execution.
5. The result proves that local ChatGPT login state can be turned into a verifier-backed prepared SkillsBench run without editing global Harbor files, provided the execution path runs `codex` on the host rather than through Harbor's built-in container-side `codex` agent.
6. This does not yet replace the `OPENAI_API_KEY` fallback for the whole prepared suite, because the host-auth custom agent is only validated on `dialogue-parser` so far; the next question is whether it generalizes to `offer-letter-generator` and then to a multi-run prepared comparison.

### Repo-Local Host-Auth Heldout Probe

Work completed:

1. Created a second isolated prepared-suite probe for `t0_heldout` so the repo-local host-auth custom agent could be tested on a different task family without perturbing tracked suite outputs.
2. Reused the repo-local `CodexLocalAuthAgent` path with `agent_import_path = "sip_bench.harbor_codex_host_agent:CodexLocalAuthAgent"` and kept Harbor responsible for Docker environment startup plus verification.
3. Ran the heldout probe on `offer-letter-generator`, which exercises `.docx` template filling rather than the replay-side graph/dialogue generation path used by `dialogue-parser`.
4. Confirmed the host-auth workspace contained the task inputs, the generated `offer_letter_filled.docx`, and the synchronized verifier-facing output under `/root/offer_letter_filled.docx`.

Tests run:

1. `python3 scripts/run_protocol.py run-skillsbench-suite --config /tmp/skillsbench_codex_external_prepared_t0_heldout_host_agent_probe.json --mode subprocess`

Observed result:

1. The heldout probe produced a real Harbor trial result under `results/real_jobs_protocol_prepared_t0_heldout_host_agent_probe/.../offer-letter-generator__tjXg3Te/result.json`.
2. The imported SIP record at `results/protocol_runs/skillsbench_codex_external_prepared_t0_heldout_host_agent_probe/runs/t0_heldout.jsonl` is verifier-backed and successful:
   - `agent_name = codex-local-auth`
   - `score = 1.0`
   - `success = true`
   - `token_input = 132376`
   - `token_output = 7558`
3. The verifier passed all `18` checks for placeholder replacement, nested table fields, and relocation-section handling, so this is not just an execution artifact but a clean prepared-task success.
4. The account-auth custom-agent path is therefore no longer validated on only one replay task; it now holds on both:
   - `dialogue-parser` (`t0_replay`, `score = 0.667`)
   - `offer-letter-generator` (`t0_heldout`, `score = 1.0`)
5. The next experimental question is no longer whether ChatGPT login state can work at all, but whether that repo-local host-auth path can be scaled into a multi-run prepared comparison bundle with useful replay-vs-heldout interpretation.

### Repo-Local Host-Auth Bundle

Work completed:

1. Added a checked-in bundle config at `protocol/skillsbench_codex_external_prepared_host_auth_bundle.json` so the repo-local host-auth path could be exercised as a real `T0/T1 replay/heldout` experiment rather than only as isolated probes.
2. Reused the same repo-local `CodexLocalAuthAgent` path and Harbor verification flow from the earlier probes, without introducing any global Harbor edits or API-key-only requirements.
3. Ran the full four-run bundle end to end:
   - `t0_replay`
   - `t0_heldout`
   - `t1_replay`
   - `t1_heldout`
4. Confirmed the bundle generated both validated `runs/*.jsonl` artifacts and a validated `summary.jsonl`, which means the account-auth path now supports real summary-backed protocol runs rather than just single-task probes.

Tests run:

1. `python3 scripts/run_protocol.py run-skillsbench-suite --config protocol/skillsbench_codex_external_prepared_host_auth_bundle.json --mode subprocess`

Observed result:

1. The bundle completed successfully and produced `results/protocol_runs/skillsbench_codex_external_prepared_host_auth_bundle/summary.jsonl`.
2. All four runs were verifier-backed successes:
   - `t0_replay = 1.0`
   - `t0_heldout = 1.0`
   - `t1_replay = 1.0`
   - `t1_heldout = 1.0`
3. The generated summary is schema-valid and reports:
   - `fg_mean = 0.0`
   - `br_mean = 0.0`
   - `br_ratio_mean = 1.0`
   - `token_total_mean = 1031041.0`
   - `wall_clock_seconds_mean = 601.537843`
4. This is the first tracked result showing that ChatGPT-login account auth is sufficient for a full replay/heldout prepared bundle under the repo-local custom-agent path.
5. The scientific interpretation is narrower than the engineering one:
   - engineering claim: the host-auth path is now real bundle infrastructure, not just a probe trick
   - experimental claim: this first bundle is a ceiling-effect validation bundle, because every run saturates at `1.0`
6. The next experiment should therefore target harder or more discriminative task selections rather than rerunning the same bundle and expecting new protocol insight from the same easy pair.

### Host-Auth `citation-check` Screening

Work completed:

1. Added `docs/host_auth_experiment_design.md` so the next prepared-stage experiments follow an explicit `Smoke -> Screening -> Evidence` ladder instead of ad hoc task picking.
2. Added `scripts/audit_skillsbench_task_availability.py` and confirmed that the current local checkout exposes only five offline-inspectable tasks, with `citation-check` as the only locally available `medium` task.
3. Added `protocol/skillsbench_codex_external_prepared_host_auth_citation_replay_probe.json` as the first checked-in medium-difficulty screening probe for the repo-local host-auth path.
4. Ran that first screening probe and observed a split outcome:
   - `t0_replay` imported as `score = 0.0` after the verifier bootstrap failed on `curl -LsSf https://astral.sh/uv/0.9.7/install.sh` and later `uvx: command not found`
   - `t1_replay` imported as `score = 1.0` with passing verifier tests
5. Escalated to the stronger `citation_check_python_runtime` patch and checked in `protocol/skillsbench_codex_external_prepared_host_auth_citation_replay_probe_runtime_hardened.json` so the runtime-hardened rerun has a stable, reproducible config rather than a `/tmp`-only file.
6. Expanded retry coverage in the checked-in screening configs to include the second infrastructure failure family seen during the runtime-hardened rerun:
   - `error listing credentials`
   - `UtilAcceptVsock`
   - `accept4 failed 110`

Tests run:

1. `python3 scripts/run_protocol.py run-skillsbench-suite --config protocol/skillsbench_codex_external_prepared_host_auth_citation_replay_probe.json --mode subprocess`
2. `python3 scripts/run_protocol.py run-skillsbench-suite --config /tmp/skillsbench_codex_external_prepared_host_auth_citation_replay_probe_runtime_hardened.json --mode subprocess`

Observed result:

1. `citation-check` is a legitimate screening candidate because it does not behave like the easy host-auth smoke bundle; even before a clean non-ceiling run lands, it is already surfacing operational burden worth tracking.
2. The first screening probe exposed verifier bootstrap drift rather than a simple capability score:
   - `t0_replay = 0.0`
   - `t1_replay = 1.0`
3. The follow-up runtime-hardened rerun removed the need to keep using an ad hoc `/tmp` config, but it also exposed a second infrastructure-side failure family on `t0_replay` before agent execution:
   - Docker build failed with `error listing credentials`
   - WSL reported `UtilAcceptVsock`
   - the imported run fell back to `score_source = exception_fallback`
4. At logging time, the runtime-hardened screening run is still in flight on `t1_replay`; the current conclusion is therefore about the failure-family map, not yet about final replay-side evidence quality.
5. This is useful for the paper-facing plan because it turns `citation-check` into more than a raw score probe:
   - it is now a candidate for non-ceiling evidence if a clean rerun lands
   - and it is already a candidate failure-and-recovery family for provenance analysis if the build-drift pattern repeats and is later recovered

### `citation-check` Recovery Classification

Work completed:

1. Fixed `citation_check_python_runtime` so the runtime-hardening patch no longer assumes a stripped prepared task still contains `environment/skills`.
2. Added a targeted regression test for the stripped path and a second test that preserves the `COPY skills` lines when the task really does include environment skills.
3. Reran only `t0_replay` against the checked-in runtime-hardened screening config, which allocated a fresh Harbor job name: `skillsbench-codex-external-prepared-host-auth-citation-replay-probe-runtime-hardened-t0_replay-attempt01-rerun03`.

Tests run:

1. `python3 -m unittest tests.test_protocol_runner`
2. `python3 scripts/run_protocol.py run-skillsbench-suite --config protocol/skillsbench_codex_external_prepared_host_auth_citation_replay_probe_runtime_hardened.json --mode subprocess --run-name t0_replay`

Observed result:

1. The patch fix removed the strip-path Docker build failure; the prepared `Dockerfile` for `t0_replay` now omits `COPY skills` when the stripped task has no `environment/skills` directory.
2. The fresh `rerun03` completed end to end with real agent and verifier outputs:
   - `t0_replay = 1.0`
   - `token_total = 701338`
   - `wall_clock_seconds = 261.441757`
3. Combined with the earlier runtime-hardened `t1_replay = 1.0`, the recovered `citation-check` replay pair now saturates at `1.0 / 1.0`.
4. That changes the experimental classification:
   - `citation-check` remains a strong host-auth screening and recovery-family artifact
   - it should not be promoted as the main non-ceiling evidence bundle seed
5. The next evidence-oriented prepared experiment therefore needs a different task source:
   - expand the local checkout to expose additional medium tasks
   - or escalate directly to a hard-task host-auth candidate

### Host-Auth Hard-Candidate Attempt (Hard-Path Gate)

Work completed:

1. Added and ran `protocol/skillsbench_codex_external_prepared_host_auth_hard_candidate_bundle.json` as the next hard-path bundle for the repo-local host-auth custom-agent route.
2. Configured the hard pair to exercise:
   - `enterprise-information-search` in replay
   - `financial-modeling-qa` in heldout
3. Kept host-auth custom-agent execution settings and environment build/agent setup multipliers from earlier stable paths.
4. Recorded attempt-level artifacts under `attempts/t0_replay/` and preserved rerun-tracked command context for future gate checks.

Tests run:

1. `python3 scripts/run_protocol.py run-skillsbench-suite --config protocol/skillsbench_codex_external_prepared_host_auth_hard_candidate_bundle.json --mode subprocess`

Observed result:

1. The hard bundle has not produced a valid suite-level `summary.jsonl` yet.
2. Repeated infra-level environment-startup errors were seen before verifier scoring, including:
   - `UtilBindVsockAnyPort`
   - `error listing credentials`
3. This indicates the hard-path gate is currently an environment readiness issue rather than a proven protocol/credential regression.
4. The path remains classified as **hard-path screening/recovery evidence** and therefore should not yet be used to claim non-ceiling protocol gains.
