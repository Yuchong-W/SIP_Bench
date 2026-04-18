# SIP-Bench Post-v0.1 Results Gallery

This document is the first repo-hosted upgrade beyond the `v0.1.0` minimal proof-of-value.
It turns already tracked artifacts into compact tables and figures that can support README, release, or paper-facing claims without relying on private slides.

See also:

1. [Positioning note: protocol-first vs benchmark-first self-evolution evaluation](positioning_note_post_v0_1.md)

## Protocol Value Snapshot

| Evidence path | T0 heldout | T1 heldout | FG | T0 replay | T1 replay | BR | T2 heldout / PDS | Cost signal | Why it matters |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `results/dryrun/summary.jsonl` | `0.250` | `0.425` | `+0.175` | `0.600` | `0.525` | `-0.075` | `0.405 / -0.020` | `75` tokens, `2` tool calls, `4.0s` | Improvement is real, but it costs budget, hurts replay retention, and softens by `T2` |
| `SkillsBench oracle real suite` | `1.000` | `1.000` | `0.000` | `1.000` | `1.000` | `0.000` | `n/a` | `184.16s` mean wall clock | The live protocol path is operationally valid, but this suite is evidence of execution correctness rather than improvement tradeoff |
| `SkillsBench codex external prepared suite` | `0.000` | `0.000` | `0.000` | `0.000` | `0.000` | `0.000` | `n/a` | `152.10s` mean wall clock | The full prepared suite now executes end to end on this host, but without `OPENAI_API_KEY` the Harbor `codex` agent collapses both strip and keep paths into flat-zero verifier outcomes |
| `tau-bench historical/import-only` | `1.000` | `1.000` | `0.000` | `0.500` | `0.500` | `0.000` | `n/a` | `$0.01292` mean cost | Gives a second environment that is interpretable without private access, even though it is not yet a strong gain/retention stress test |

Primary tracked sources:

1. `results/dryrun/summary.jsonl`
2. `results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl`
3. `results/protocol_runs/skillsbench_codex_external_prepared_suite/summary.jsonl`
4. `results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl`

## Environment Coverage Table

| Path | Current status | Release role | What it is good for right now | Current limitation |
| --- | --- | --- | --- | --- |
| `SkillsBench oracle real suite` | Supported | Release-critical | Real planning, hydration, execution import, suite aggregation, and retry-aware provenance | Current tracked suite is mostly orchestration evidence, not a strong self-improvement result |
| `tau-bench historical/import-only` | Supported | Release-critical | Stable second environment without provider credentials | Historical/import-only path is weaker than live execution for operational realism |
| `SkillsBench codex external prepared` | Experimental, but now fully executable | Optional | Best candidate for stronger protocol-vs-self-evolution comparisons | The suite now completes end to end, but without `OPENAI_API_KEY` it produces a flat-zero summary that reflects credential failure more than capability |
| `tau-bench` live provider-backed execution | Experimental | Optional | Best candidate for a more realistic second live environment | Requires provider credentials and explicit budget |

Primary tracked sources:

1. `docs/support_matrix_v0_1.md`
2. `README.md`
3. tracked suite configs under `protocol/`

## Failure And Recovery Table

| Case | Initial signal | Protocol-visible evidence | Recovery action | Final result | What a plain final score would hide |
| --- | --- | --- | --- | --- | --- |
| `SkillsBench t0_replay` rerun | Earlier rerun imported a stale failed `dialogue-parser` result because the Harbor job directory was reused | `suite_report.json` now records a distinct rerun job name: `skillsbench-oracle-real-suite-t0_replay-attempt01-rerun02` | Added fresh rerun job-name allocation and reran only `t0_replay` via `--run-name` | `t0_replay` recovered to `score = 1.0`; suite summary returned to full success | Final suite success alone would erase the stale-import hazard and the engineering work needed to recover |
| Live suite execution in general | Docker / apt / environment issues can fail for infrastructure reasons rather than protocol logic | per-run `retry_policy`, `attempts/`, `preparation/`, and run-local provenance files are all tracked | keep retry policy explicit and preserve attempt-level artifacts | live suite remains auditable instead of looking like one opaque score | ordinary benchmark reporting usually compresses infra failure burden into one terminal status |
| `tau-bench historical` release path | second environment needed to be interpretable without private credentials | tracked historical suite summary is versioned and schema-valid | use import-only historical artifacts as the public second environment | release can show two environments without gating on live provider access | a simple support matrix would not show which path is actually reproducible today |
| `SkillsBench codex external prepared` full suite | the first probe failed in `dialogue-parser` Docker build, the second exposed missing model configuration, and the final tracked suite completed with a flat-zero summary | tracked `preparation/`, `attempts/`, `suite_report.json`, and probe artifacts show the progression from apt instability to explicit `model` wiring to `env_override_keys = []` and `0.0` verifier rewards across the final suite | add `dialogue_parser_apt_retry`, make the tracked config pass `model = "gpt-5.4"`, and thread SkillsBench env resolution through `.env.local` / `env_file` | the suite is now fully executable and schema-valid, but it still needs `OPENAI_API_KEY` to produce a meaningful non-zero comparison | a flat support label would hide both the engineering recovery and the fact that the remaining blocker is now credential state rather than protocol wiring |

Primary tracked sources:

1. `docs/development_log.md`
2. `results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json`
3. `results/protocol_runs/skillsbench_codex_external_prepared_suite/suite_report.json`
4. `results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl`
5. `results/protocol_runs/skillsbench_codex_external_prepared_t0_replay_probe/runs/t0_replay.jsonl`
6. `results/protocol_runs/skillsbench_codex_external_prepared_t0_replay_retry_probe/runs/t0_replay.jsonl`
7. `results/protocol_runs/skillsbench_codex_external_prepared_t0_replay_model_probe/runs/t0_replay.jsonl`

## Figures

### Heldout vs Replay Delta

![Heldout vs Replay Delta](figures/heldout_vs_replay_delta.svg)

Source:

1. `results/dryrun/summary.jsonl`

Interpretation:

1. the held-out line rises from `0.250` to `0.425`
2. the replay line falls from `0.600` to `0.525`
3. this is the smallest tracked example of why protocol structure adds value beyond a single post-adaptation score

### Cost vs Gain Summary

![Cost vs Gain Summary](figures/cost_vs_gain.svg)

Source:

1. `results/dryrun/summary.jsonl`

Interpretation:

1. the tracked gain is small but positive
2. the gain is not free in token, tool, or time budget
3. `IE` stays visible next to raw cost signals so "improvement" is not discussed as if it were costless

### T0/T1/T2 Stability

![T0/T1/T2 Stability](figures/t0_t1_t2_stability.svg)

Source:

1. `results/dryrun/summary.jsonl`

Interpretation:

1. the tracked held-out score rises sharply from `T0` to `T1`
2. the gain remains positive at `T2`
3. `PDS = -0.020` makes the softening explicit instead of letting `T1` stand in as the whole story

### Attempt Provenance Snapshot

![Attempt Provenance Snapshot](figures/attempt_provenance.svg)

Source:

1. `docs/development_log.md`
2. `results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json`

Interpretation:

1. the `t0_replay` recovery path is now a tracked in-repo story instead of a hidden rerun
2. the suite keeps the rerun-specific job name visible: `...rerun02`
3. the final `1.0` suite summary is still useful, but no longer erases the engineering provenance behind recovery

## Remaining Gaps

1. the next high-value upgrade is to rerun the now-complete prepared suite with `OPENAI_API_KEY` so the comparison reflects capability instead of credential failure
2. once a stronger prepared-suite comparison exists, the gallery should add a protocol-first vs benchmark-first comparison table
3. the current provenance chart is based on one strong recovery case; a second tracked recovery family would make this part of the story materially stronger
