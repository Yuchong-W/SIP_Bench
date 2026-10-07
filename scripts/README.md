# Scripts

This repository keeps most operational entry points in `scripts/`.

The public surface is intentionally centered on a small set of reproducible commands. Historical or experimental helpers still exist, but they should not be treated as the first thing a new user runs.

## Start Here

Most users only need these commands:

1. `run_release_checks.py`
   End-to-end local validation used by quickstart and CI.
2. `aggregate_metrics.py`
   Aggregate normalized `runs.jsonl` into `summary.jsonl`.
3. `validate_records.py`
   Validate `json` or `jsonl` files against SIP-Bench schemas.
4. `run_eval.py`
   Import benchmark outputs or build and execute single-run plans.
5. `run_protocol.py`
   Execute or import multi-run protocol suites from config files.
6. `evidence_gate.py`
   Evaluate whether a completed summary meets the repository's evidence thresholds.
7. `check_plan_matrix.py`
   Sanity-check protocol suite configs and expected artifact paths.

## Core Categories

### Validation And Aggregation

1. `run_release_checks.py`
2. `aggregate_metrics.py`
3. `validate_records.py`
4. `evidence_gate.py`
5. `check_plan_matrix.py`

### Benchmark Execution And Import

1. `run_eval.py`
2. `run_protocol.py`
3. `smoke_adapters.py`
4. `run_synthetic_replay.py`
   Experimental frozen synthetic diagnosis export and byte-for-byte verification.
   See [the source and artifact contract](../docs/synthetic_replay.md).

### Result Rendering

1. `build_strategy_comparison.py`
2. `build_results_gallery_artifacts.py`
3. `build_task_family_ablation.py`

### EvoAgentBench Retained Tooling

These scripts are kept because the repository still ships real OmniMath result packages and fixtures:

1. `generate_evoagentbench_omnimath_demo.py`
2. `analyze_evoagentbench_omnimath_results.py`
3. `build_evoagentbench_raw_phase_comparison.py`
4. `build_evoagentbench_failure_taxonomy.py`
5. `build_evoagentbench_verifier_sensitivity_audit.py`
6. `run_evoagentbench_omnimath_codex_real.py`

They are retained artifacts and utilities, not the primary public story of the repository.

## First Commands

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python3 scripts/run_release_checks.py
python3 scripts/check_plan_matrix.py --protocol-dir protocol
python3 scripts/aggregate_metrics.py --runs results/dryrun/sample_runs.jsonl --out /tmp/sip_summary.jsonl
```

## Notes

1. `Linux-first` is the maintained public support target.
2. Some scripts require local benchmark checkouts under `benchmarks/`.
3. Some optional paths require provider credentials, but the default validation path does not.
4. Experimental account-auth bridge scripts remain in the repository for historical completeness, but they are not part of the recommended public workflow.
