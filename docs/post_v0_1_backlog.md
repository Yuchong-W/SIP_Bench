# SIP-Bench Post-v0.1 Backlog

This backlog exists to keep the first public release tight.

Anything listed here is intentionally *not* a `v0.1.0` blocker unless it is promoted explicitly later.

For the concrete next-phase execution plan, see [post_v0_1_execution_plan.md](post_v0_1_execution_plan.md).

## Post-Tag Housekeeping

1. If desired, publish or polish a dedicated GitHub release page for `v0.1.0`.

## README And Docs Follow-Ups

1. Expand the `v0.1` minimal proof-of-value example into a richer results section once more evidence is available.
2. Consider adding CI and license badges once the release tag is live.
3. Decide whether a dedicated docs site is worth the maintenance cost after `v0.1`.
4. Add a short "how to integrate a new benchmark" walkthrough if external interest appears.
5. Tighten README and any paper-facing text now that the positioning note exists.

## Validation Hardening

1. Decide whether `scripts/run_release_checks.py` should gain an optional `smoke_adapters` step.
2. Consider a small helper for exporting release-check results into a markdown report.

## Benchmark Expansion

1. Rerun `SkillsBench codex external prepared suite` with `OPENAI_API_KEY` now that the tracked suite completes end to end and currently collapses to flat-zero outputs without credentials.
2. Add a stable public story for prepared-task comparisons only after the validation path is repeatable.
3. Track a second repeatable failure-and-recovery family so provenance evidence is not based on one case.
4. Revisit `tau-bench` live execution once provider API access is available and budget is explicit.
5. Do not add a third benchmark until the current two-environment story is stronger.

## Paper Track

1. Keep the paper claim anchored on benchmark or protocol infrastructure unless stronger empirical evidence appears.
2. Build the paper around `FG`, `BR`, and `IE` tradeoffs instead of a generic "agent got better" narrative.
3. Treat large-scale matched-budget comparisons as post-release research work, not release hygiene.
4. Grow the `v0.1` proof-of-value into a multi-environment empirical case, not just a release-facing example.
5. Prefer repo-hosted tables and figures over slide-only evidence while the empirical story is still forming.
6. Treat prepared-suite evidence as the main experimental unlock for a stronger paper claim.

## Product And Community

1. Decide later whether the project needs a logo, banner, or landing page.
2. Add issue labels and project board structure only if external traffic justifies it.
3. Keep contribution scope narrow until the release surface stabilizes.
