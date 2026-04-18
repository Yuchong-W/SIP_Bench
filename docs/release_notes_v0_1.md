# SIP-Bench v0.1.0 Release Notes

## Summary

`SIP-Bench v0.1.0` is the first public open-source release of a protocol-layer benchmark for self-improving agents.

This release does not introduce a new benchmark world. Instead, it adds a reusable longitudinal evaluation protocol on top of existing benchmark environments so improvement, retention, and cost can be measured under one contract.

## What Is In This Release

### Protocol Layer

1. Shared lifecycle checkpoints:
   - `T0`
   - `T1`
   - `T2`
2. Shared benchmark task partitions:
   - `replay`
   - `adapt`
   - `heldout`
   - optional `drift`
3. Normalized run and summary schemas:
   - `runs.jsonl`
   - `summary.jsonl`
4. Protocol-oriented metrics:
   - `FG`
   - `BR`
   - `BR_ratio`
   - `IE`
   - `PDS`
   - `NIS`

### Implemented Integrations

1. `SkillsBench`
   - split planning
   - sparse hydration
   - Harbor execution import
   - config-driven suite orchestration
2. `tau-bench`
   - explicit plan generation
   - historical/import-only suite execution
   - live preflight path with provider-env resolution

### Open-Source Release Infrastructure

1. `Apache-2.0` licensing
2. citation metadata
3. contribution guidance
4. security policy
5. issue and pull request templates
6. minimal CI for tests and schema validation
7. one-command release validation through `python3 scripts/run_release_checks.py`

## Release-Critical Evidence Paths

The current `v0.1.0` release is anchored on:

1. validated `SkillsBench oracle` real-suite artifacts
2. validated `tau-bench historical/import-only` protocol artifacts

These were chosen because they are reproducible within the current public release posture and do not require `codex` connectivity or private provider credentials.

## Minimal Proof Of Value

`v0.1.0` is not meant to ship with only "the pipeline runs" evidence.
The smallest tracked proof of value in this release is [results/dryrun/summary.jsonl](../results/dryrun/summary.jsonl), derived from [results/dryrun/sample_runs.jsonl](../results/dryrun/sample_runs.jsonl).

| Protocol view | Value | Why it matters |
| --- | --- | --- |
| Held-out mean `T0 -> T1` | `0.250 -> 0.425` | Improvement on new tasks is real |
| Replay mean `T0 -> T1` | `0.600 -> 0.525` | The same adaptation hurts replay retention |
| Held-out mean `T1 -> T2` | `0.425 -> 0.405` | Improvement is not perfectly stable over time |
| Adapt cost mean | `75` tokens, `2` tool calls, `4.0s` | The gain is tied to explicit cost |
| Derived metrics | `FG = +0.175`, `BR = -0.075`, `PDS = -0.020`, `IE = 0.0025` | The protocol makes the tradeoff legible instead of implicit |

If this release only reported the post-adaptation held-out mean of `0.425`, the story would be "the agent improved."
The protocol view is more honest: the agent improved on held-out tasks, gave back some replay performance, softened slightly by `T2`, and spent measurable budget to do it.

That is the intended `v0.1.0` value proposition:

1. not only validating benchmark plumbing
2. also showing a concrete case where protocol structure reveals more than a single leaderboard number

## Experimental But Non-Blocking

The following paths are present in the repository but are not release blockers:

1. `SkillsBench codex external prepared suite`
2. `tau-bench` live smoke runs with provider credentials

## Support Target

The official support target for this release is `Linux-first`.

Windows helper scripts remain in the repository for local machine-specific workflows, but they are not the center of the public support story for `v0.1.0`.

## Known Limitations

1. This release is protocol infrastructure, not a complete solution to the self-improvement problem.
2. The current release does not yet provide a large-scale matched-budget comparison between external-path and parameter-path adaptation.
3. `tau-bench` live execution still depends on private provider credentials.
4. Experimental prepared-suite validation is not yet stable enough to define the public release story.
5. Some real `SkillsBench` tasks still require explicit timeout policy because Docker and environment setup remain machine-sensitive.

## Recommended Starting Points

1. Read the [README](../README.md)
2. Run the quickstart commands
3. Inspect:
   - [results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json](../results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json)
   - [results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl](../results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl)
   - [protocol/tau_bench_retail_historical_suite.json](../protocol/tau_bench_retail_historical_suite.json)

## Next Priorities

1. polish or publish a dedicated GitHub release page for `v0.1.0` if desired
2. expand the minimal proof-of-value into a richer multi-example results section
3. decide whether to add CI and license badges now that the release tag is live
4. rerun the experimental prepared-suite path with `OPENAI_API_KEY` now that the tracked suite completes end to end but currently collapses to flat-zero outputs without credentials
5. revisit `tau-bench` live execution once provider credentials and budget are explicit
