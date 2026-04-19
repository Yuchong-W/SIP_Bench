# Figures

This directory is reserved for repo-hosted visual assets used by:

1. `docs/results_gallery_post_v0_1.md`
2. `README.md`
3. future post-`v0.1.0` experiment notes

Each figure includes a stable filename, a one-line caption, and a reproducible source command.

Preferred formats:

1. `svg` for lightweight tracked charts and diagrams
2. `png` only when vector output is impractical

Current standard outputs:

1. `heldout_vs_replay_delta.svg`  
   Caption: `Heldout and Replay Mean Score Snapshot`
   Source: one or more `summary.jsonl`, recommended `results/dryrun/summary.jsonl`.
2. `fg_br_ie.svg`  
   Caption: `FG / BR / IE Profile`
   Source: one or more `summary.jsonl`, recommended `results/dryrun/summary.jsonl`.
3. `cost_vs_gain.svg`  
   Caption: `Cost and Metric Delta Summary`
   Source: one or more `summary.jsonl`, recommended `results/dryrun/summary.jsonl`.
4. `t0_t1_t2_stability.svg`  
   Caption: `T0/T1/T2 Stability Snapshot`
   Source: one or more `summary.jsonl`, recommended `results/dryrun/summary.jsonl`.
5. `attempt_provenance.svg`  
   Caption: `Attempt Provenance Snapshot`
   Source: `results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json` plus run-name-resolved rerun artifacts.
6. `host_auth_progress.svg`  
   Caption: `Host-Auth Progress`
   Source: `results/protocol_runs/skillsbench_codex_external_prepared_host_auth_bundle/*` and `results/protocol_runs/skillsbench_codex_external_prepared_host_auth_citation_replay_probe*/*`.

Recommended generation pipeline:

1. generate/update chart + table output:

```bash
python3 scripts/build_results_gallery_artifacts.py --summary results/dryrun/summary.jsonl --out-dir docs/figures --table-dir docs/results_table_data
```

2. `attempt_provenance.svg` and `host_auth_progress.svg` are currently maintained as tracked SVGs produced from `results/protocol_runs/*` narratives and listed in `docs/results_gallery_post_v0_1.md`.

Every checked-in figure should have:

1. a clear source artifact or reproduction note
2. a stable filename
3. a markdown document that explains why the figure exists
