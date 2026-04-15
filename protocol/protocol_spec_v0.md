# SIP-Bench Protocol Spec v0

## Purpose

`SIP-Bench` measures self-improvement as a longitudinal property rather than a point-in-time score. The protocol is designed to sit on top of existing agent benchmarks and expose three quantities that are usually missing:

1. held-out improvement
2. old-task retention
3. improvement efficiency

This document defines the MVP protocol for the first release.

## Benchmark Targets

The MVP protocol supports:

1. `skillsbench`
2. `tau-bench`

Optional later extension:

3. `swe-bench-live`

## Protocol Units

The protocol has three units:

1. `benchmark`
Current environment and task family.

2. `phase`
Current lifecycle checkpoint of the agent.

3. `split`
Task subset used for replay, adaptation, held-out evaluation, or drift.

## Phases

### `T0`

Initial agent before benchmark-specific adaptation.

Rules:

1. No targeted updates using `adapt` tasks.
2. Only generic prompting and default harness configuration are allowed.

### `T1`

Agent after one adaptation cycle.

Allowed updates:

1. external-path updates:
- skill insertion
- memory write/read support
- retrieval or prompt-library updates

2. optional parameter-path updates:
- LoRA-lite
- small SFT

### `T2`

Agent after delay, drift, or additional task exposure.

Purpose:

1. measure stability after improvement
2. check whether gains survive time or environment changes

## Task Splits

Each benchmark adapter must export the following named subsets:

### `replay`

Old tasks used to measure retention.

### `adapt`

Tasks or trajectories the agent may use during adaptation.

### `heldout`

New tasks used to measure forward gain.

### `drift`

Optional shifted-distribution tasks used at `T2`.

## Split Rules

Adapters must satisfy the following:

1. `adapt` and `heldout` cannot overlap by task ID.
2. `adapt` and `heldout` should not contain near-duplicate templates when metadata is available.
3. `replay` must contain tasks that were already solvable or attempted before adaptation.
4. If `drift` exists, it must preserve task format while changing evidence, user state, policy, or environment conditions.

## Path Types

Every run must declare one path type:

1. `frozen`
No improvement mechanism.

2. `external`
Only harness-layer adaptation.

3. `parameter`
Parameter update such as LoRA or SFT.

4. `oracle`
Upper-bound or debugging mode. Not for the main leaderboard.

## Required Metrics

### `FG`

`FG = score(T1, heldout) - score(T0, heldout)`

### `BR`

`BR = score(T1, replay) - score(T0, replay)`

### `BR_ratio`

`BR_ratio = score(T1, replay) / max(score(T0, replay), eps)`

### `IE`

`IE = FG / cost`

Recommended cost fields:

1. total tokens
2. wall-clock time
3. tool calls
4. optional human interventions

If cost is `0`, `IE` must be recorded as `null` instead of forcing a fake finite value.

### `PDS`

`PDS = score(T2, heldout_or_drift) - score(T1, heldout)`

If `T2` has not been run yet, `PDS`-related summary fields remain `null`.

### `NIS`

`NIS = FG - lambda * max(0, -BR)`

This is a reporting convenience metric, not a replacement for the main metrics.

## Scoring

Each adapter must output a scalar `score` in `[0, 1]` when possible.

If a benchmark natively uses pass rate:

1. success maps to `1.0`
2. failure maps to `0.0`

If a benchmark uses partial credit:

1. adapter must document the normalization rule
2. normalized output must still be recorded as `score`

## Repeats

MVP requirement:

1. each main result must be repeated at least `3` times
2. reports must include mean and standard deviation
3. high-variance results should not enter the main comparison table without an explicit warning

## Logging Contract

Each benchmark execution must emit one JSON object per attempt to `runs.jsonl`.

Required fields are defined in:

1. [runs.schema.json](E:\Protocal_Bench\schemas\runs.schema.json)

Aggregated outputs must conform to:

1. [summary.schema.json](E:\Protocal_Bench\schemas\summary.schema.json)

## Benchmark-Specific Adapter Contract

Each adapter must implement:

1. task export for `replay`, `adapt`, `heldout`, optional `drift`
2. a `run(task, phase, path_type, seed)` interface
3. a normalized `score`
4. cost logging
5. stable task IDs

## MVP Acceptance Criteria

The protocol is considered operational when:

1. `skillsbench` can run `T0 -> T1` with valid logs
2. `tau-bench` can run `T0 -> T1` with valid logs
3. `FG`, `BR`, and `IE` are computed automatically
4. at least one result shows a non-trivial tradeoff between forward gain and backward retention

## Out of Scope for v0

1. full parameter-path fairness
2. large-scale third-environment support
3. unified contamination auditing across all environments
4. safety-improvement joint evaluation
