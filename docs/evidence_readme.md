# Evidence Reproducibility Guide

This document defines the exact commands for reproducing all evidence in the current results gallery.

## Core Table Artifacts

1. Generate the table layer:

```bash
python3 scripts/build_results_gallery_artifacts.py \
 --summary results/dryrun/summary.jsonl \
 --summary results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl \
  --summary results/protocol_runs/skillsbench_harbor_non_ceiling_repeat_bundle/summary.jsonl \
  --summary results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl \
 --table-dir docs/results_table_data \
 --table-filename protocol_summary_snapshot
```

Output:

1. `docs/results_table_data/protocol_summary_snapshot.json`
2. `docs/results_table_data/protocol_summary_snapshot.csv`

## Core Figure Assets

The gallery is built from script-generated charts and two tracked manual SVGs.

1. Generate script-backed SVGs:

```bash
python3 scripts/build_results_gallery_artifacts.py \
 --summary results/dryrun/summary.jsonl \
 --summary results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl \
  --summary results/protocol_runs/skillsbench_harbor_non_ceiling_repeat_bundle/summary.jsonl \
  --summary results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl \
  --out-dir docs/figures \
  --table-dir docs/results_table_data \
  --table-filename protocol_summary_snapshot
```

This command regenerates:

1. `docs/figures/heldout_vs_replay_delta.svg`
2. `docs/figures/fg_br_ie.svg`
3. `docs/figures/cost_vs_gain.svg`
4. `docs/figures/t0_t1_t2_stability.svg`

2. Manual/track-only SVGs:

1. `docs/figures/attempt_provenance.svg`  
   Updated from `results/protocol_runs/skillsbench_oracle_real_suite/*` provenance artifacts (see the case entry in `docs/results_gallery_post_v0_1.md`).
2. `docs/figures/host_auth_progress.svg`  
   Updated from `results/protocol_runs/skillsbench_codex_external_prepared_host_auth_bundle/*` and related host-auth artifacts.

## Evidence Gate and Status Re-check

1. Run the protocol-level gate:

```bash
python3 scripts/evidence_gate.py --summary results/dryrun/summary.jsonl
```

2. Validate core schema compliance:

```bash
python3 scripts/validate_records.py --data results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl --schema summary
python3 scripts/validate_records.py --data results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl --schema summary
```

3. Run the release check as a baseline:

```bash
python3 scripts/run_release_checks.py
```

## One-Line Gallery Validation

From a fresh clone, run the command above, then open:

1. `docs/results_gallery_post_v0_1.md`
2. `docs/results_table_data/protocol_summary_snapshot.csv`
3. `docs/figures/*.svg`

## Family-Level Ablation Command

Run family-level failure/metric ablation across combined runs:

```bash
python3 scripts/build_task_family_ablation.py \
  --combined-runs results/protocol_runs/skillsbench_codex_external_prepared_host_auth_bundle/combined_runs.jsonl \
  --combined-runs results/protocol_runs/skillsbench_codex_external_prepared_host_auth_citation_replay_probe/combined_runs.jsonl \
  --combined-runs results/protocol_runs/skillsbench_codex_external_prepared_host_auth_citation_replay_probe_runtime_hardened/combined_runs.jsonl \
  --combined-runs results/protocol_runs/skillsbench_codex_external_prepared_t0_replay_host_agent_probe2/combined_runs.jsonl \
  --out-dir docs/results_task_family_ablation \
  --out-name task_family_ablation_host_focus_v0_1
```

The command writes:

1. `docs/results_task_family_ablation/task_family_ablation_host_focus_v0_1.json`
2. `docs/results_task_family_ablation/task_family_ablation_host_focus_v0_1.csv`
