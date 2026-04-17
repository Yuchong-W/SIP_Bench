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

## Release-Critical Evidence Paths

The current `v0.1.0` release is anchored on:

1. validated `SkillsBench oracle` real-suite artifacts
2. validated `tau-bench historical/import-only` protocol artifacts

These were chosen because they are reproducible within the current public release posture and do not require `codex` connectivity or private provider credentials.

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

1. finish release-cleanup around tracked artifact churn
2. validate on a stable Linux benchmark machine
3. expand release-quality examples and visualizations
4. keep `tau` live and prepared-suite paths as tracked experimental follow-ups
