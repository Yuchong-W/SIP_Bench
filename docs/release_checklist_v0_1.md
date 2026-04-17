# SIP-Bench v0.1 Release Checklist

This checklist is for the first public open-source release. It assumes:

1. `Linux-first` official support
2. `Apache-2.0` license
3. `codex` connectivity is not required on the release machine
4. `tau-bench` live runs are optional

## 1. Release Narrative

- [ ] README headline states the protocol-layer positioning clearly.
- [ ] README explains the novelty beyond "benchmark wrapper".
- [ ] README describes the currently supported environments.
- [ ] README distinguishes release-critical paths from experimental paths.
- [ ] README quickstart uses commands that exist and have been tested.

## 2. Legal And Metadata Files

- [ ] `LICENSE` is present and correct.
- [ ] `NOTICE` is present and correct.
- [ ] `CITATION.cff` is present and references the release repository.
- [ ] README explains that upstream benchmark code keeps its own licenses.

## 3. Repository Hygiene

- [ ] `.gitignore` covers local caches, local secrets, and run-local prepared task copies.
- [ ] Experimental local metadata files are not left unignored.
- [ ] The working tree no longer contains accidental formatting churn.
- [ ] The tracked files intended for release have been reviewed intentionally.

## 4. Validation

- [ ] Unit tests pass on the supported environment.
- [ ] Schema validation passes for the tracked example artifacts.
- [ ] `python3 scripts/run_release_checks.py` passes on the release branch.
- [ ] The documented quickstart has been re-run from a clean checkout.
- [ ] `python` vs `python3` assumptions are explicit and consistent.

## 5. Benchmark Artifact Set

- [ ] `SkillsBench oracle real suite` artifacts are present and valid.
- [ ] `tau-bench historical suite` artifacts are present and valid.
- [ ] Experimental `codex` prepared-suite outputs are either:
  - [ ] intentionally excluded from release, or
  - [ ] intentionally validated and documented
- [ ] The repository documents which `results/` directories are tracked release assets.

## 6. Documentation Quality

- [ ] `docs/technical_design.md` matches the current code paths.
- [ ] `docs/development_log.md` reflects the real chronology of key milestones.
- [ ] `docs/release_manifest.md` matches intended tracked assets.
- [ ] `docs/known_limitations.md` reflects the release boundary honestly.

## 7. CI And Automation

- [ ] Minimal CI is configured for tests and schema validation.
- [ ] CI does not depend on unavailable private services.
- [ ] CI status is green on the release branch.

## 8. Release Packaging

- [ ] Version number is fixed to `v0.1.0`.
- [ ] Release notes summarize:
  - [ ] protocol contribution
  - [ ] supported benchmarks
  - [ ] known limitations
  - [ ] next planned steps
- [ ] A tag is ready to publish from a reviewed commit.

## 9. Launch Materials

- [ ] A short GitHub release summary is drafted.
- [ ] A short public launch post is drafted.
- [ ] A short research-oriented summary is drafted.

## 10. Post-Release Backlog

- [ ] README follow-ups are captured separately from the release branch.
- [ ] `tau-bench` live integration remains a tracked follow-up, not a release blocker.
- [ ] `codex` prepared-suite validation remains a tracked follow-up, not a release blocker.
- [ ] Paper-writing work is tracked separately from open-source release hygiene.
