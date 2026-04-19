# Contributing To SIP-Bench

Thanks for contributing to `SIP-Bench`.

This repository is a protocol-layer benchmark project, so changes should preserve three priorities:

1. protocol correctness
2. artifact reproducibility
3. clarity about what is release-grade versus experimental

## Support Target

The current public support target is `Linux-first`.

Windows-specific helper scripts remain useful for local work, but they should not be treated as the primary public execution path for `v0.1`.

## What To Change Carefully

Please be especially careful when editing:

1. `schemas/`
2. `src/sip_bench/metrics.py`
3. `src/sip_bench/runner.py`
4. `src/sip_bench/protocol_runner.py`
5. tracked example artifacts under `results/`

Changes in these areas can silently invalidate previously documented results or break the reproducibility story.

## Local Development Workflow

Recommended baseline:

```bash
python3 scripts/run_release_checks.py
```

Useful additional checks:

```bash
python3 scripts/run_release_checks.py --skip-tests
python3 scripts/aggregate_metrics.py --runs results/dryrun/sample_runs.jsonl --out /tmp/sip_summary.jsonl
python3 scripts/run_eval.py import-skillsbench-job --job-dir tests/fixtures/skillsbench_harbor_job_sample --out /tmp/skillsbench_job_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 21 --registry tests/fixtures/skillsbench_registry_sample.json --agent-version fixture-import --benchmark-version skillsbench-harbor-fixture
```

Line-ending policy:

1. `.editorconfig` and `.gitattributes` are both part of the release surface.
2. default repository text files should stay `LF`.
3. Windows launcher files such as `.cmd` should stay `CRLF`.
4. avoid mixing formatting-only renormalization with feature changes.

## Result Artifact Policy

Tracked artifacts in `results/` are part of the project story and should be edited intentionally.

Before modifying tracked outputs, decide which category the change belongs to:

1. release asset that should stay tracked
2. local-only debug artifact that should be ignored
3. experimental output that should live outside the release surface

Do not mix cleanup, artifact regeneration, and feature changes into one commit unless the relationship is unavoidable.

## Benchmark Dependencies

This repository integrates with external benchmark ecosystems, but it does not vendor their full contents into the public release surface.

Please keep these boundaries explicit:

1. upstream benchmark code keeps its own license and terms
2. local benchmark checkouts under `benchmarks/` are not assumed to exist in every environment
3. private API access must not become a hard requirement for basic validation

## Experimental Paths

The following paths are valuable, but they are currently not release blockers:

1. `SkillsBench codex external prepared suite`
2. `tau-bench` live runs that require provider credentials

If you touch these paths, document clearly whether the change is:

1. release-critical
2. experimental
3. machine-specific

## Pull Request Guidance

A good contribution usually includes:

1. a clear statement of what changed
2. why the change matters for protocol correctness or usability
3. what commands were run to validate it
4. whether any tracked artifacts were regenerated

If a change is intentionally documentation-only or cleanup-only, say that explicitly.

## Adding a New Benchmark Adapter

SIP-Bench is benchmark-agnostic by design, so new benchmark support should enter through the adapter interface.

### 1) Add a Data Adapter

1. create a class in `src/sip_bench/adapters/` that subclasses `BenchmarkAdapter`.
2. implement the following methods:
   - `discover_tasks(source)`
   - `build_manifest(tasks, replay_count, adapt_count, heldout_count, drift_count, seed)`
   - `build_harbor_command(...)` (for command-driven adapters like SkillsBench) or the equivalent task-builder
   - `parse_result_file(...)` (for import-only adapters)
3. keep task IDs and metadata schema-consistent:
   - include `benchmark_name`, `task_id`, `source_path`, `title`, `category`, `difficulty` when available.
4. export the adapter in `src/sip_bench/adapters/__init__.py`.

### 2) Validate Schema Compatibility

1. add/extend tests in `tests/test_adapters.py` and `tests/test_protocol_runner.py`.
2. ensure suite and run records still validate:
   - `python3 scripts/validate_records.py --data <runs>.jsonl --schema runs`
   - `python3 scripts/validate_records.py --data <summary>.jsonl --schema summary`
3. keep import paths and registry assumptions explicit in docs.

### 3) Add Execution Paths

1. add example protocol suite config under `protocol/`.
2. add/extend smoke fixtures under `tests/fixtures/`.
3. update docs:
   - `docs/support_matrix_v0_1.md`
   - `docs/release_manifest.md`
   - this contributing checklist.
4. validate plan-to-path consistency with:
   - `python3 scripts/check_plan_matrix.py --config protocol/<suite>.json --strict`

### 4) Reproducibility and Release Readiness

1. define a stable default for:
   - seed
   - retry policy
   - environment/exec command path
2. run `python3 scripts/run_release_checks.py --skip-import-check` (local smoke) and
   `python3 scripts/run_release_checks.py` (with fixture import) before opening the PR.
3. include the command block in the PR description so reviewers can replay exactly.

## New Benchmark Onboarding

For a concrete end-to-end checklist with examples, use:

- `docs/new_benchmark_onboarding_checklist.md`
