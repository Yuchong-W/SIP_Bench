# SIP-Bench v0.1 Milestone Plan

## Scope

This plan targets a public `v0.1.0` release by `2026-05-01`.

The release is optimized for a high-quality open-source launch, not for the strongest possible paper result. The primary goal is to publish a repository that is easy to understand, easy to run, and credible as research infrastructure.

Locked decisions:

1. Positioning: `protocol-layer benchmark for self-improving agents`
2. Primary environments: `SkillsBench` and `tau-bench`
3. Official support target: `Linux-first`
4. License target: `Apache-2.0`
5. Release-critical experiment path:
   - `SkillsBench oracle real suite`
   - `tau-bench historical/import-only suite`
6. Non-blocking experimental path:
   - `SkillsBench codex external prepared suite`
   - `tau-bench` online smoke or live runs when API access becomes available

## Progress Snapshot

Current snapshot as of `2026-04-18`:

1. `M1 Release Narrative`: complete
2. `M2 Repository Hygiene`: complete for the repository-facing release path
3. `M3 Quickstart And Demo`: complete for the current public quickstart, artifact tour, and compact proof-of-value writeup
4. `M4 Release-Grade Validation`: local validation, tracked real-suite validation, and minimal proof-of-value example are in place; fresh-clone rerun and CI confirmation still pending
5. `M5 Release Cut`: release notes and launch materials are drafted and now include the compact value-proof narrative; final tag and release publication still pending

## Why This Release Can Be Novel

The core novelty is not a new task world. The novelty is a reusable longitudinal evaluation protocol for self-improving agents.

The release should consistently emphasize these value claims:

1. `SIP-Bench` evaluates improvement across time, not only single-shot task performance.
2. It makes `forward gain`, `backward retention`, and `improvement efficiency` comparable across existing benchmarks.
3. It records operational failures as first-class benchmark outcomes instead of silently dropping failed runs.
4. It separates protocol logic from benchmark-specific integration so new benchmarks can be added without rewriting the metric layer.

## Release Goals

By `v0.1.0`, the repository should satisfy all of the following:

1. A new visitor can understand the project from the README in under `3` minutes.
2. A user can run the documented quickstart on a supported machine without private access to `codex`.
3. A researcher can inspect real example artifacts for both `SkillsBench` and `tau-bench`.
4. The repository contains the legal and engineering files expected from a serious open-source project.
5. The published claims match what has actually been executed and stored in versioned artifacts.
6. The release includes at least one compact example that shows why the protocol is useful beyond a single-shot benchmark score.

## Minimum Value Proof For v0.1

`v0.1.0` should not ship with only "the pipeline runs" evidence.
It should also ship with one small but concrete proof that the protocol adds value.

The minimum acceptable form is:

1. one compact table or figure, typically `3` to `6` rows
2. one short explanatory passage in the README, release notes, or both
3. evidence derived from tracked artifacts or a clearly described small targeted run

That proof may emphasize either or both of:

1. engineering value:
   - retries, failures, and attempt provenance are visible instead of being silently collapsed into one final score
2. research value:
   - `FG`, `BR`, `IE`, or related protocol fields reveal something a single-shot leaderboard number would miss

This is intentionally smaller than a paper-ready study.
`v0.1.0` needs an honest proof-of-value, not a large-scale empirical campaign.

## Non-Goals For v0.1

These items should not block the first public release:

1. A polished docs website
2. `codex`-dependent validation on the release machine
3. A paper-ready large-scale statistical study
4. A third benchmark environment
5. Perfect cross-platform parity between Linux and Windows

## Milestones

### M1: Release Narrative

Target window: `2026-04-17` to `2026-04-19`

Deliverables:

1. Finalize the high-level positioning in the README.
2. Add `LICENSE`, `NOTICE`, and `CITATION.cff`.
3. Add this milestone plan and the release checklist.
4. Decide which result artifacts are public release assets and which are local-only.

Exit criteria:

1. The public story is coherent and consistent across README and docs.
2. The release no longer looks like an internal experiment dump.

### M2: Repository Hygiene

Target window: `2026-04-19` to `2026-04-22`

Deliverables:

1. Resolve the current working-tree noise caused by formatting and platform-specific output churn.
2. Fix `python` vs `python3` subprocess assumptions so the documented test path is portable on Linux.
3. Review `.gitignore` so run-local caches and generated prepared-task copies do not pollute status.
4. Confirm which `results/` directories are intended for version control.

Exit criteria:

1. A release branch can be reviewed without unrelated noise.
2. The supported local workflow is documented and reproducible.

### M3: Quickstart And Demo

Target window: `2026-04-22` to `2026-04-25`

Deliverables:

1. Rewrite the README quickstart around a minimal reproducible path.
2. Add a simple end-to-end demo path from suite config to summary artifact.
3. Point users to representative example outputs already present in the repository.
4. Ensure all README commands map to real files and real commands in the repo.

Exit criteria:

1. A new user can reach a successful run path in roughly `15` minutes.
2. The repository contains one signature walkthrough that is easy to share.

### M4: Release-Grade Validation

Target window: `2026-04-25` to `2026-04-29`

Deliverables:

1. Re-run the supported local validation path on a Linux Docker machine.
2. Confirm `SkillsBench oracle real suite` artifacts remain valid.
3. Confirm `tau-bench historical` protocol artifacts remain valid.
4. Add minimal CI for tests and schema validation.
5. Produce one compact proof-of-value result derived from tracked artifacts or a small targeted release-side run.

Exit criteria:

1. The repository has at least one clean validation report on the official support environment.
2. The release does not depend on access to a closed agent endpoint.
3. The release can point to one concrete example of protocol value, not only protocol correctness.

### M5: Release Cut

Target window: `2026-04-29` to `2026-05-01`

Deliverables:

1. Final README pass
2. Final release checklist pass
3. `v0.1.0` changelog or release note
4. Tag and publish the release
5. Draft one short launch post and one short research-oriented summary
6. Integrate the compact proof-of-value example into the release-facing narrative.

Exit criteria:

1. `main` is in a releasable state.
2. The first public tag can be shared without caveats about repository mess.
3. A skeptical reader can see at least one concrete reason this protocol is worth using.

## Deliverable Matrix

### Required

1. Clear README with project positioning, scope, and quickstart
2. `Apache-2.0` licensing files
3. Stable CLI entrypoints for planning, importing, and protocol execution
4. Example artifacts for:
   - `SkillsBench oracle real suite`
   - `tau-bench historical suite`
5. Passing local validation flow on the official support environment
6. A public release tag and release notes
7. One small proof-of-value result that demonstrates what SIP-Bench reveals beyond "final score"

### Strongly Recommended

1. A simple protocol diagram
2. A benchmark support matrix
3. A short FAQ section in the README
4. A dedicated section that explains why this is not just another wrapper repo

### Optional

1. Experimental `codex` prepared-suite artifacts
2. A richer visualization script or notebook
3. Social launch assets such as a banner or GIF

## Risks

### R1: Repository Churn Obscures Real Changes

Impact:

1. Review becomes noisy.
2. Release diffs become hard to trust.

Mitigation:

1. Separate content cleanup from feature work.
2. Keep generated result directories explicitly classified as tracked or ignored.

### R2: `codex` Cannot Be Used On The Release Validation Machine

Impact:

1. The experimental prepared-suite path cannot be release-critical.

Mitigation:

1. Keep `codex` support documented but optional.
2. Anchor the release on `oracle` and historical result paths.

### R3: Online API Access Is Not Available

Impact:

1. `tau-bench` live smoke cannot block release.

Mitigation:

1. Use `tau-bench historical/import-only` as the official second environment for `v0.1`.

### R4: Docker Or Upstream Task Instability

Impact:

1. Real benchmark execution may fail for reasons unrelated to protocol logic.

Mitigation:

1. Treat failure artifacts as first-class results.
2. Keep the release claims aligned to executed evidence, not idealized plans.

## Release Acceptance Criteria

`v0.1.0` is ready when all of the following are true:

1. The README matches the actual repository state.
2. The repository has clear legal metadata and citation metadata.
3. The official support environment is documented as `Linux-first`.
4. The release does not rely on `codex` connectivity.
5. The tracked example artifacts validate against the repository schemas.
6. The working tree can be explained without hidden local conventions.

## Immediate Next Actions

1. Add the release-structure files required for open-source launch.
2. Clean up working-tree noise before more features are added.
3. Rewrite the README around a public user journey rather than an internal lab log.
4. Prepare a Linux validation pass for the final release branch.
5. Draft the smallest credible value-proof table and explanatory note for the release surface.
