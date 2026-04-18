# SI-Protocol Benchmark

`SIP-Bench` is a protocol layer for evaluating self-improving agents across improvement, retention, and cost.

It does not introduce a new task world. It wraps existing benchmark environments with a shared longitudinal evaluation contract so you can ask questions that single-shot leaderboards usually cannot answer:

1. Did the agent improve on held-out tasks?
2. Did it retain performance on tasks it already knew?
3. What interaction, compute, and operational cost did that improvement require?

## Why This Is Different

Most agent benchmarks report a score for one run on one split. `SIP-Bench` instead standardizes a reusable protocol:

1. `T0 / T1 / T2` checkpoints
2. `replay / adapt / heldout / drift` task partitions
3. normalized run records and summary records
4. metrics for gain, retention, and efficiency
5. first-class recording of failed benchmark executions

The project is best understood as research infrastructure for measuring self-improvement, not as another benchmark wrapper and not as a new benchmark environment.

## Protocol At A Glance

```mermaid
flowchart LR
    A[T0 initial agent] --> B[Replay tasks]
    A --> C[Held-out tasks]
    B --> D[T1 post-adaptation agent]
    C --> D
    D --> E[Replay evaluation]
    D --> F[Held-out evaluation]
    D --> G[Optional drift or delayed T2 evaluation]
    E --> H[BR and BR_ratio]
    F --> I[FG]
    H --> J[Protocol summary]
    I --> J
    G --> K[PDS]
    K --> J
    J --> L[IE and NIS with cost fields]
```

## Current Release Direction

The current `v0.1` release plan is optimized for a strong open-source launch:

1. official support target: `Linux-first`
2. release-critical environments:
   - `SkillsBench`
   - `tau-bench`
3. release-critical evidence:
   - real `SkillsBench oracle` suite artifacts
   - `tau-bench` historical/import-only protocol artifacts
4. experimental but non-blocking:
   - `SkillsBench codex external prepared suite`
   - `tau-bench` live runs that require provider credentials

Milestone and release-tracking docs live here:

1. [docs/milestone_plan_v0_1.md](docs/milestone_plan_v0_1.md)
2. [docs/release_checklist_v0_1.md](docs/release_checklist_v0_1.md)
3. [docs/support_matrix_v0_1.md](docs/support_matrix_v0_1.md)
4. [docs/linux_validation_runbook_v0_1.md](docs/linux_validation_runbook_v0_1.md)
5. [docs/post_v0_1_backlog.md](docs/post_v0_1_backlog.md)

## Supported Environments

| Environment | Current status | Release role |
| --- | --- | --- |
| `SkillsBench` | Real planning, hydration, execution import, and suite aggregation implemented | Primary release path |
| `tau-bench` historical | Import-only suite path implemented and aggregated | Secondary release path |
| `tau-bench` live | Runtime wrapper and preflight exist, requires provider credentials | Optional |
| `SkillsBench codex prepared` | Task preparation layer exists, validation is still experimental | Optional |

## Protocol Model

Lifecycle phases:

1. `T0`: initial agent
2. `T1`: post-adaptation checkpoint
3. `T2`: delayed or post-drift checkpoint

Task partitions:

1. `replay`
2. `adapt`
3. `heldout`
4. optional `drift`

Primary metrics:

1. `FG`: Forward Gain
2. `BR`: Backward Retention
3. `BR_ratio`
4. `IE`: Improvement Efficiency
5. `PDS`: Post-Delay Stability
6. `NIS`: Net Improvement Score

Schemas and protocol references:

1. [protocol/protocol_spec_v0.md](protocol/protocol_spec_v0.md)
2. [schemas/runs.schema.json](schemas/runs.schema.json)
3. [schemas/summary.schema.json](schemas/summary.schema.json)
4. [schemas/protocol_suite.schema.json](schemas/protocol_suite.schema.json)

## Quickstart

The commands below avoid private agent access and work with the repository's local fixtures and tracked sample outputs.

```bash
python3 scripts/run_release_checks.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/aggregate_metrics.py --runs results/dryrun/sample_runs.jsonl --out /tmp/sip_summary.jsonl
python3 scripts/run_eval.py import-skillsbench-job --job-dir tests/fixtures/skillsbench_harbor_job_sample --out /tmp/skillsbench_job_runs.jsonl --benchmark-split smoke --phase T0 --path-type oracle --seed 21 --registry tests/fixtures/skillsbench_registry_sample.json --agent-version fixture-import --benchmark-version skillsbench-harbor-fixture
python3 scripts/validate_records.py --data /tmp/skillsbench_job_runs.jsonl --schema runs
```

What this gives you:

1. local unit coverage for protocol logic
2. a generated `summary.jsonl` from sample runs
3. a real-format `SkillsBench` Harbor job imported into SIP-Bench run records
4. schema validation on the imported artifact

If you want the same checks as the release path and CI, start with:

```bash
python3 scripts/run_release_checks.py
```

## Representative Artifacts

Tracked example outputs and configs:

1. Real `SkillsBench` suite report: [results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json](results/protocol_runs/skillsbench_oracle_real_suite/suite_report.json)
2. Real `SkillsBench` summary: [results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl](results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl)
3. Successful `SkillsBench` smoke import: [results/dryrun/skillsbench_dialogue_timeout4_runs.jsonl](results/dryrun/skillsbench_dialogue_timeout4_runs.jsonl)
4. Sample `tau-bench` imported runs: [results/dryrun/tau_runs.jsonl](results/dryrun/tau_runs.jsonl)
5. Real `SkillsBench` suite config: [protocol/skillsbench_oracle_real_suite.json](protocol/skillsbench_oracle_real_suite.json)
6. Experimental prepared-suite config: [protocol/skillsbench_codex_external_prepared_suite.json](protocol/skillsbench_codex_external_prepared_suite.json)
7. Historical `tau-bench` suite config: [protocol/tau_bench_retail_historical_suite.json](protocol/tau_bench_retail_historical_suite.json)
8. Optional live `tau-bench` smoke config: [protocol/tau_bench_retail_openai_smoke_suite.json](protocol/tau_bench_retail_openai_smoke_suite.json)

## Real Benchmark Paths

### SkillsBench

Current real path:

1. build an explicit plan
2. hydrate the sparse checkout
3. execute through Harbor
4. import the Harbor job directory
5. validate `runs.jsonl`

The current multi-run suite runner supports:

1. per-run planning
2. per-run hydration
3. optional run-local task preparation
4. optional per-run `retry_policy` with attempt-level artifacts for transient infrastructure failures
5. per-run execution or import-only mode
6. combined `runs.jsonl`
7. aggregated `summary.jsonl`

The current tracked real suite is an orchestration validation suite, not a claim of meaningful self-improvement.

### tau-bench

Current supported paths:

1. `historical/import-only`
2. `live` with explicit provider credentials

The current release-safe path is the historical suite because it does not depend on private API access.

The live smoke path is configured but requires provider credentials. A checked-in template lives at [protocol/tau_openai.env.example](protocol/tau_openai.env.example).

## Task Preparation Layer

For `SkillsBench`, suite configs can optionally prepare run-local task copies instead of mutating the upstream checkout.

Supported preparation features:

1. `mode = source`
2. `mode = copy`
3. `skill_mode = strip|keep`
4. explicit task patches such as `offer_letter_generator_system_docx`

This layer is what enables frozen-style versus skill-enabled comparisons without rewriting upstream tasks in place.

## Repository Map

1. [docs/technical_design.md](docs/technical_design.md)
2. [docs/development_log.md](docs/development_log.md)
3. [docs/decision_log.md](docs/decision_log.md)
4. [docs/known_limitations.md](docs/known_limitations.md)
5. [docs/release_manifest.md](docs/release_manifest.md)
6. [docs/linux_validation_runbook_v0_1.md](docs/linux_validation_runbook_v0_1.md)
7. [docs/post_v0_1_backlog.md](docs/post_v0_1_backlog.md)
8. [scripts/README.md](scripts/README.md)
9. [src/sip_bench/](src/sip_bench)
10. [tests/README.md](tests/README.md)

## Operational Notes

1. `Linux-first` is the official support target for `v0.1`.
2. Windows-specific helpers such as `scripts/harbor312.cmd` and `scripts/tau311.cmd` remain useful local wrappers, but they are not the center of the public support story.
3. Real `SkillsBench` runs may still need explicit timeout overrides for slow Docker tasks.
4. `tau-bench` live execution depends on provider credentials and is intentionally not a release blocker.
5. Upstream benchmark checkouts under `benchmarks/` are local dependencies and are not vendored into the repository release surface.

## FAQ

### Is this a new benchmark?

No. `SIP-Bench` is a protocol layer on top of existing benchmark environments.

### Does the first release require private API access?

No. The release-critical quickstart and tracked validation path do not require private model credentials.

### Is `codex` required?

No. Experimental prepared-suite support exists, but `codex` connectivity is not part of the `v0.1` release-critical path.

### What should I use if I only want a stable second environment today?

Use the tracked `tau-bench` historical/import-only path. It exercises the protocol layer without turning provider credentials into a blocker.

## License

The SIP-Bench code in this repository is licensed under [Apache-2.0](LICENSE).

External benchmark projects, datasets, and local upstream checkouts keep their own licenses and usage terms. See [NOTICE](NOTICE) for the release-surface clarification.
