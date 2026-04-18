# SIP-Bench Post-v0.1 Results Gallery

This document is the planned home for repo-hosted tables and figures that extend the `v0.1.0` minimal proof-of-value into a stronger empirical package.

Until the assets are fully populated, it should act as a stable target for links and future result drops.

## Planned Tables

### Protocol Value Snapshot

Target content:

1. held-out gain
2. replay retention
3. delayed stability
4. adapt cost
5. derived protocol metrics

Primary source candidates:

1. `results/dryrun/summary.jsonl`
2. `results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl`

### Environment Coverage Table

Target content:

1. `SkillsBench oracle`
2. `tau-bench historical`
3. `SkillsBench codex external prepared`
4. `tau-bench` live

Primary source candidates:

1. `README.md`
2. `docs/support_matrix_v0_1.md`
3. tracked suite configs under `protocol/`

### Failure And Recovery Table

Target content:

1. initial failure mode
2. retry or rerun action
3. recovered outcome
4. what the final score alone would have hidden

Primary source candidates:

1. `docs/development_log.md`
2. `results/protocol_runs/skillsbench_oracle_real_suite/`

## Planned Figures

### Heldout vs Replay Delta

Planned path:

1. `docs/figures/heldout_vs_replay_delta.svg`

### Cost vs Gain

Planned path:

1. `docs/figures/cost_vs_gain.svg`

### T0/T1/T2 Stability

Planned path:

1. `docs/figures/t0_t1_t2_stability.svg`

### Attempt Provenance

Planned path:

1. `docs/figures/attempt_provenance.svg`

## Asset Rules

1. every figure should link back to tracked artifacts or a documented reproduction command
2. every table should be understandable without an external spreadsheet
3. every asset should support a protocol claim, not only a cosmetic summary
