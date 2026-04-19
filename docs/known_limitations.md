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

## Threat Model

The current evidence set is strongest for infrastructure and protocol behavior, not for universal improvement claims.

Current bias and noise risks:

1. task reuse and local checkpointing can amplify repeated effects in a narrow family,
2. benchmark fixture layout and local cache reuse can influence repeated runs in ways not tied to model learning,
3. transient environment failures (Docker/image/tooling/credentials/network) can cause false-negative failures that are not protocol regressions,
4. current limited task families make capability inference sensitive to task selection and local data availability.

Mitigation in the current release:

1. separate runs by suite name, split, phase, and attempt,
2. preserve all `run_status`, `attempt`, and provenance artifacts instead of only aggregate final scores,
3. run `scripts/evidence_gate.py` and `scripts/build_task_family_ablation.py` as independent checks,
4. limit cross-suite claims to reproducibly tracked release-critical environments.

## Why No Full-Scale Sweep Yet

At this stage the priority is protocol correctness and repeatability under constrained budget:

1. keep reproducible execution and rerun paths fixed,
2. validate that non-ceiling gates and family-level evidence are stable over repeats,
3. establish that recovery provenance is preserved when infra failures occur.

The large-scale matched-budget comparison can be added later as a separate study stage without weakening the current release claims.
