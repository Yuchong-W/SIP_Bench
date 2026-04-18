# Known Limitations

## Current MVP Limits

1. The protocol focuses on `BWT/FWT-style retention` and `improvement efficiency`, not the full self-improvement problem.
2. The MVP does not yet provide a fair large-scale comparison between external-path and parameter-path adaptation.
3. The first release uses only two primary environments, which limits cross-domain generality.
4. Contamination auditing is environment-dependent and not yet unified across all adapters.
5. Long-term persistence is approximated through `T0/T1/T2`; it is not yet a full 7x24 deployment benchmark.
6. The current public release is `Linux-first`; Windows helper workflows exist but are not the primary support target.
7. `tau-bench` live execution still depends on private provider credentials and is therefore not part of the release-critical validation path.
8. Experimental `codex` prepared-suite support exists in code and config, but it is not yet a stable release asset.
9. Real `SkillsBench` Linux runs can fail for upstream reasons even when the SIP protocol path succeeds, including slow or flaky package downloads during Docker image builds and missing verifier reward files after agent execution.
10. The suite runner now supports explicit transient retries for selected `SkillsBench` failures, but retries do not guarantee success and intentionally do not mask deterministic benchmark failures.
11. The upstream `citation-check` task remains vulnerable to Ubuntu package-index instability on this machine, but the tracked prepared-copy patch now avoids that path with a validated Python-runtime fallback.

## Intended Extensions

1. add `SWE-bench-Live` as a third environment
2. add parameter-path baselines under matched budgets
3. add adapter-level contamination checks
4. add safety-side reporting alongside self-improvement metrics
5. validate experimental prepared-suite paths on a stable Linux benchmark machine
6. add a public result-visualization layer on top of protocol summaries
