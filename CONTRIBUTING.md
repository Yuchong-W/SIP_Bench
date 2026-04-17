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
