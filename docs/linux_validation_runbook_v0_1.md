# SIP-Bench v0.1 Linux Validation Runbook

This runbook is for the official `Linux-first` validation pass before or immediately after the `v0.1.0` tag.

It is intentionally scoped to the public release path:

1. no `codex` connectivity required
2. no provider credentials required
3. no live `tau-bench` execution required

## Goal

Validate that a fresh Linux machine can reproduce the release-facing local checks and inspect the tracked benchmark artifacts.

## Recommended Host

1. Linux host with Docker available
2. `git`
3. `python3`
4. outbound network access for `git clone` and `pip install`

Preferred Python version:

1. `3.12` to match CI

## Fresh Clone Setup

```bash
git clone git@github.com:Yuchong-W/Protocol_Bench.git
cd Protocol_Bench
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip jsonschema
```

## Release Validation Command

Run the shared release check entrypoint:

```bash
python3 scripts/run_release_checks.py
```

If you want to inspect generated temporary outputs, keep them:

```bash
python3 scripts/run_release_checks.py --keep-temp
```

## What This Validates

1. unit tests
2. dry-run summary aggregation
3. SkillsBench Harbor-job import from tracked fixture data
4. schema validation for tracked dry-run artifacts
5. schema validation for tracked real `SkillsBench oracle` suite artifacts

## What This Does Not Require

1. local `SkillsBench` checkout under `benchmarks/`
2. local `tau-bench` checkout under `benchmarks/`
3. `OPENAI_API_KEY`
4. `codex` access

## Optional Artifact Inspection

After the release checks pass, inspect the tracked evidence paths:

```bash
python3 scripts/validate_records.py --data results/protocol_runs/skillsbench_oracle_real_suite/combined_runs.jsonl --schema runs
python3 scripts/validate_records.py --data results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl --schema summary
sed -n '1,120p' results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json
sed -n '1,120p' results/protocol_runs/tau_bench_retail_historical_suite/suite_report.json
```

## Optional Benchmark-Machine Follow-Up

If the Linux machine also has the upstream benchmarks checked out, the next release-adjacent checks are:

1. rerun the documented quickstart exactly as written in the README
2. confirm Docker-backed `SkillsBench` behavior remains stable
3. keep `tau-bench` live execution out of scope unless provider credentials are intentionally supplied

## Exit Criteria

The Linux validation pass is good enough for `v0.1.0` if all of the following are true:

1. `python3 scripts/run_release_checks.py` exits `0`
2. the tracked real-suite artifacts still validate
3. the README commands match the repository state
4. the machine does not require `codex` connectivity to exercise the public release path

## What To Record

Capture these values in your release notes or validation log:

1. validation date
2. machine OS and Python version
3. commit SHA: `git rev-parse HEAD`
4. whether Docker was available
5. whether the release-check command passed unchanged
