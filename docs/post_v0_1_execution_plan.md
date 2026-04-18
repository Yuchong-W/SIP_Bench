# SIP-Bench Post-v0.1 Execution Plan

## Purpose

`v0.1.0` solved the open-source release problem.
The next phase should solve a different problem:

1. make the protocol story sharper
2. produce stronger experimental evidence
3. turn key results into repo-hosted tables and figures instead of slide-only claims

This plan is intentionally narrower than a full paper plan and more concrete than a generic backlog.

## Working Position

The next phase should treat `SIP-Bench` as:

1. a protocol-layer evaluation framework for self-improving agents
2. complementary to benchmark-first self-evolution suites such as `EvoAgentBench`, not a direct clone of them
3. strongest when it can show not only that an agent improves, but also what it forgot, what it cost, and how stable that improvement remained

That means the work must advance on two tracks at the same time:

1. design and positioning
2. experiments and evidence

## Success Criteria

The next phase is successful only if all of the following are true:

1. the repository explains clearly what `SIP-Bench` adds beyond train/test self-evolution benchmarks
2. the repository contains a stronger results section than the current minimal proof-of-value
3. at least `2` repo-hosted figures and at least `3` compact result tables are checked into version control
4. at least one repeatable experiment bundle exists beyond the current `v0.1.0` release proof
5. the design story and the evidence story point to the same claims

## Current Status After The First Results Package

Completed so far:

1. the repository now has a positioning note that explains the protocol-first story and contrasts it with benchmark-first self-evolution evaluation
2. the repository now has a results gallery with:
   - `3` compact tables
   - `4` repo-hosted figures
3. the public-facing story is no longer dependent on only one minimal proof-of-value snippet in the README

Still missing:

1. a stronger experiment bundle beyond the tracked `v0.1.0` release artifacts
2. prepared-suite evidence that can actually test the "protocol-first versus benchmark-first" comparison story
3. a second repeatable failure-and-recovery family so provenance is not anchored on only one recovery case

Bottom line:

1. design and interpretation work are no longer the main bottleneck
2. additional experiments are still necessary
3. the highest-value remaining work is now experimental, not presentational

## Workstreams

### W1: Design And Positioning

Goal:

1. sharpen the protocol-layer story
2. make the relationship to benchmark-first self-evolution evaluation explicit

Deliverables:

1. a short related-work or positioning note that contrasts:
   - benchmark-first train/test self-evolution evaluation
   - protocol-first longitudinal evaluation
2. a cleaner explanation of why `FG`, `BR`, `IE`, `PDS`, and failure provenance are a coherent bundle
3. a simple figure showing the protocol loop from `T0` to `T1/T2`
4. a short interpretation guide for reading `summary.jsonl` like a diagnostic report instead of a leaderboard line

Candidate repo assets:

1. `docs/positioning_note_post_v0_1.md`
2. `docs/results_interpretation_guide.md`
3. `docs/figures/protocol_loop.svg`
4. `docs/figures/protocol_metric_family.svg`

### W2: Results Package Upgrade

Goal:

1. move from one minimal example to a small but credible results package
2. keep every result grounded in tracked artifacts or clearly reproducible runs

Priority evidence sources:

1. `results/dryrun/summary.jsonl`
2. `results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl`
3. tracked `tau-bench historical` artifacts
4. future `SkillsBench codex external prepared` results only after the path is repeatable

Required result tables:

1. `Protocol Value Snapshot`
   - compares held-out gain, replay retention, delayed stability, and cost in one table
2. `Environment Coverage Table`
   - states which environments are release-critical, experimental, import-only, or provider-gated
3. `Failure And Recovery Table`
   - summarizes attempts, retries, success after rerun, and what ordinary final-score reporting would hide

Required figures:

1. `Heldout vs Replay Delta`
   - paired bar or slope chart for `T0 -> T1`
2. `Cost vs Gain`
   - scatter or small multiples using `FG`, token/tool/time cost, and `IE`

Recommended additional figures:

1. `T0/T1/T2 Stability`
   - line chart showing gains that soften or hold over time
2. `Attempt Provenance`
   - bar chart for failures, retries, and recovered runs

Candidate repo assets:

1. `docs/results_gallery_post_v0_1.md`
2. `docs/figures/heldout_vs_replay_delta.svg`
3. `docs/figures/cost_vs_gain.svg`
4. `docs/figures/t0_t1_t2_stability.svg`
5. `docs/figures/attempt_provenance.svg`

### W3: Experimental Expansion

Goal:

1. add stronger evidence without exploding scope
2. prefer repeatable runs over one-off impressive numbers

Priority experiments:

1. rerun `SkillsBench codex external prepared suite` with `OPENAI_API_KEY` now that the full tracked suite completes end to end and currently collapses to a flat-zero summary without credentials
2. strengthen the current two-environment story with at least one new matched comparison that exposes a protocol tradeoff hidden by plain success reporting
3. capture a second repeatable failure-and-recovery case so attempt provenance is not based on one recovery story only
4. only then consider `tau-bench` live runs with explicit provider budget

Minimum acceptable experimental upgrade:

1. one matched comparison where the protocol reveals a tradeoff hidden by a plain success score
2. one run family that includes failure, retry, and recovery evidence
3. one cross-environment summary table that does not depend on private access to interpret

Highest-value experimental package from here:

1. one prepared-suite comparison with interpretable `FG / BR / IE` deltas after `OPENAI_API_KEY` is supplied
2. one second tracked recovery case with attempt-level provenance
3. one updated results-gallery section that combines those new artifacts into a protocol-first comparison table

Not yet a priority:

1. adding a third benchmark
2. large-scale leaderboard production
3. slide-only plots without tracked source artifacts

## Execution Order

### Phase 1: Positioning And Result Skeleton

1. add the post-`v0.1.0` positioning note
2. populate the results gallery document with the first table and figure placeholders
3. convert the current minimal proof into the first row block of that gallery

### Phase 2: Stronger Evidence On Existing Assets

1. build the three required tables from tracked artifacts
2. generate the two required figures from tracked artifacts
3. link those assets from the README and release notes

### Phase 3: New Experimental Evidence

1. rerun the prepared-suite validation with env-file-backed `OPENAI_API_KEY`
2. add comparison tables that separate:
   - held-out improvement
   - replay retention
   - stability
   - operational failure burden
3. decide whether the new evidence is strong enough to justify a paper-facing empirical section

## Repo-Hosted Asset Standard

Every future figure or table should satisfy these rules:

1. checked into the repository
2. linked from a markdown document, not buried in a notebook only
3. tied to a tracked artifact or a documented reproduction command
4. understandable without private dashboards or unpublished spreadsheets

Preferred locations:

1. figures: `docs/figures/`
2. narrative tables and interpretation: `docs/results_gallery_post_v0_1.md`
3. reproduction notes: `docs/development_log.md` or a dedicated experiment note

## Immediate Next Actions

1. rerun the prepared-suite validation with env-file-backed `OPENAI_API_KEY`
2. capture one more repeatable failure-and-recovery family and turn it into tracked provenance artifacts
3. update the results gallery with a protocol-first comparison table once those experiments exist
4. postpone broader benchmark expansion until those experimental assets exist
