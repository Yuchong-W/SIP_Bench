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
