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

1. Keep the current host-auth easy-task bundle as a smoke or regression artifact, not as the main evidence bundle.
2. Build a medium-difficulty host-auth prepared bundle that is explicitly chosen to avoid ceiling effect.
3. Escalate to a hard-task host-auth bundle if the medium bundle still saturates at `1.0`.
4. Rerun `SkillsBench codex external prepared suite` with `OPENAI_API_KEY` only if the harder host-auth bundles stall or become too brittle.
5. Add a stable public story for prepared-task comparisons only after the non-ceiling validation path is repeatable.
6. Track a second repeatable failure-and-recovery family so provenance evidence is not based on one case.
7. Revisit `tau-bench` live execution once provider API access is available and budget is explicit.
8. Do not add a third benchmark until the current two-environment story is stronger.

## Paper Track

1. Keep the paper claim anchored on benchmark or protocol infrastructure unless stronger empirical evidence appears.
2. Build the paper around `FG`, `BR`, and `IE` tradeoffs instead of a generic "agent got better" narrative.
3. Treat the new host-auth smoke bundle as infrastructure evidence, not as the centerpiece empirical claim.
4. Treat large-scale matched-budget comparisons as post-release research work, not release hygiene.
5. Grow the `v0.1` proof-of-value into a multi-environment empirical case, not just a release-facing example.
6. Prefer repo-hosted tables and figures over slide-only evidence while the empirical story is still forming.
7. Treat non-ceiling prepared-suite evidence as the main experimental unlock for a stronger paper claim.

## Product And Community

1. Decide later whether the project needs a logo, banner, or landing page.
2. Add issue labels and project board structure only if external traffic justifies it.
3. Keep contribution scope narrow until the release surface stabilizes.
