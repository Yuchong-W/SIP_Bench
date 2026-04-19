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

## Current Status After The Host-Auth Bundle

Completed so far:

1. the repository now has a positioning note that explains the protocol-first story and contrasts it with benchmark-first self-evolution evaluation
2. the repository now has a results gallery with:
   - `3` compact tables
   - `5` repo-hosted figures
3. the public-facing story is no longer dependent on only one minimal proof-of-value snippet in the README
4. the host-auth hard-candidate probe is now executed through 3 independent prepared attempts, giving a stable infra-failure lineage for hard tasks

Still missing:

1. a stronger non-ceiling experiment bundle beyond the tracked `v0.1.0` release artifacts
2. prepared-suite evidence that can actually test the "protocol-first versus benchmark-first" comparison story instead of only execution viability
3. a second repeatable failure-and-recovery family that includes a successful recovery branch, not only infrastructure-only failures
4. a protocol-first comparison table that separates Smoke, Screening, Hard, and Evidence stages with explicit stage criteria

New constraint learned from the latest probe work:

1. a repo-local Harbor-to-Codex login bridge now exists and avoids editing the global Harbor installation
2. that isolated bridge is useful engineering infrastructure, but it still does not remove the effective credential requirement on the current Harbor `codex` noninteractive path
3. a repo-local custom agent path now exists that runs `codex exec` on the host with the user's ChatGPT login state and synchronizes outputs back into Harbor-managed verification
4. that host-auth custom agent has already produced real verifier-backed prepared probe results on both `dialogue-parser` and `offer-letter-generator`, so `OPENAI_API_KEY` is no longer the only plausible route to stronger prepared-suite evidence
5. that host-auth path now also has a real four-run `T0/T1 replay/heldout` bundle with a valid `summary.jsonl`, so it has crossed from probe infrastructure into usable experiment infrastructure
6. however, the first summary-backed host-auth bundle saturates at `1.0` on every tracked task, so it demonstrates viability better than it demonstrates protocol tradeoffs
7. the first medium screening task, `citation-check`, has already revealed two distinct infrastructure-side failure families:
   - verifier bootstrap drift (`curl` or `uvx` bootstrap failures)
   - Docker build or credential-helper drift (`error listing credentials`, `UtilBindVsockAnyPort`)
8. that means the screening program now has value even before a clean non-ceiling score lands, because it is surfacing repeatable operational burden that ordinary final-score reporting would flatten away
9. after the strip-path runtime patch was fixed and `t0_replay` was rerun successfully, `citation-check` recovered to a clean `1.0 / 1.0` replay pair, so it is now better classified as a recovery-family artifact than as the main non-ceiling evidence candidate
10. the hard-candidate path (`enterprise-information-search`) now has 3 consecutive attempts with identical environment-build failure in Docker compose (`UtilBindVsockAnyPort`, `error listing credentials`)
11. the hard-candidate bundle has not produced a valid suite-level summary yet, so the path remains in a screened recovery stage, not Evidence

Latest hard-path decision snapshot (2026-04-19):

1. attempted pair: `enterprise-information-search` + `financial-modeling-qa` under host-auth custom agent
2. latest repeated outcome: pre-verifier infra/build failure before any stable success path
3. consequence: no new `fg`, `br`, or `ie` protocol metrics from this bundle
4. active bottleneck is now container startup consistency rather than protocol orchestration logic

Current interpretation:

1. the short-term bottleneck is no longer account-auth feasibility but repeatable hard-task environment readiness
2. infra-failure provenance is now sufficiently stable to support the next decision gate in the plan
3. the next decision gate is whether infra hardening or keyed fallback is needed before the next hard candidate can be used for protocol claims

Bottom line:

1. design and interpretation work are no longer the main bottleneck
2. additional experiments are still necessary
3. the highest-value remaining work is now experimental, not presentational
4. the next experimental bottleneck is not "can account auth work at all?" but "can account auth produce non-ceiling protocol evidence on hard tasks?"

## Locked Decisions From The Latest Round

The plan should now assume all of the following unless new evidence overturns them:

1. do not edit the global Harbor installation
2. treat the repo-local host-auth custom agent as the primary prepared-suite path
3. treat `OPENAI_API_KEY` as a contingency path, not the default next step
4. keep the current easy-task host-auth bundle as a smoke or regression asset, not as the main evidence bundle

5. add a hard-candidate infra-readiness gate before any hard-task capability claim is made public

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
6. `docs/host_auth_experiment_design.md`

### W3: Experimental Expansion

Goal:

1. add stronger evidence without exploding scope
2. prefer repeatable runs over one-off impressive numbers

Priority experiments:

1. freeze the current easy-task host-auth bundle as the canonical smoke or regression bundle for account-auth prepared execution
2. build a medium-difficulty host-auth bundle that is explicitly chosen to reduce ceiling effect
   - candidate replay-like medium tasks can come from the current registry, but `citation-check` should now be treated as a screened recovery case rather than the default evidence candidate
   - candidate heldout-like medium tasks should be chosen from a different category so replay versus heldout remains interpretable
3. if the medium bundle still saturates or is too weak to reveal tradeoffs, escalate to a hard-task host-auth bundle
   - likely candidates should come from the current hard pool such as `enterprise-information-search`, `financial-modeling-qa`, or `fix-visual-stability`, depending on runtime practicality
4. keep `OPENAI_API_KEY` as the fallback route only if the host-auth path stalls on those harder bundles or becomes operationally too brittle
5. strengthen the current two-environment story with at least one new matched comparison that exposes a protocol tradeoff hidden by plain success reporting
6. capture a second repeatable failure-and-recovery case so attempt provenance is not based on one recovery story only
7. only then consider `tau-bench` live runs with explicit provider budget

Design note:

1. `docs/host_auth_experiment_design.md` is the operational guide for screening-versus-evidence classification, local task availability constraints, and patch escalation policy

Minimum acceptable experimental upgrade:

1. one matched comparison where the protocol reveals a tradeoff hidden by a plain success score
2. one run family that includes failure, retry, and recovery evidence
3. one cross-environment summary table that does not depend on private access to interpret

Highest-value experimental package from here:

1. one non-ceiling prepared-suite comparison with interpretable `FG / BR / IE` deltas using the repo-local host-auth custom agent
2. if that path stalls on harder bundles, one equivalent comparison with `OPENAI_API_KEY` as a contingency
3. one second tracked recovery case with attempt-level provenance
4. one updated results-gallery section that combines those new artifacts into a protocol-first comparison table

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

1. keep the current easy host-auth bundle only as a smoke or regression check
2. run a medium-difficulty replay-plus-heldout host-auth bundle that is less likely to saturate
3. if that still saturates, escalate to a hard-task host-auth bundle rather than immediately switching credential mode
4. if the harder host-auth bundles stall operationally, rerun the same comparison with env-file-backed `OPENAI_API_KEY`
5. add comparison tables that separate:
   - held-out improvement
   - replay retention
   - stability
   - operational failure burden
6. decide whether the new evidence is strong enough to justify a paper-facing empirical section

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

1. freeze the current easy-task host-auth bundle as the tracked smoke baseline and stop treating it as the main evidence target
2. treat the checked-in `citation-check` screening configs as the canonical recovery-family harness, not as the main evidence bundle seed
3. decide whether to continue the hard path with:
   - a targeted retry hardening pass for `enterprise-information-search`, or
   - a controlled comparator run with `OPENAI_API_KEY` on the same hard pair
4. if hard infra is reproduced, keep the hard path as Screening/Recovery status and avoid protocol Evidence claims
5. if hard infra clears and non-ceiling scores emerge, move to next-stage protocol Evidence row in the gallery
6. capture one more repeatable failure-and-recovery family and turn it into tracked provenance artifacts
7. publish the updated results gallery row and gate changes on explicit table+figure updates
