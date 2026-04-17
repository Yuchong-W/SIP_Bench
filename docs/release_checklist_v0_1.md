# SIP-Bench v0.1 Release Checklist

This checklist is for the first public open-source release. It assumes:

1. `Linux-first` official support
2. `Apache-2.0` license
3. `codex` connectivity is not required on the release machine
4. `tau-bench` live runs are optional

## 1. Release Narrative

- [x] README headline states the protocol-layer positioning clearly.
- [x] README explains the novelty beyond "benchmark wrapper".
- [x] README describes the currently supported environments.
- [x] README distinguishes release-critical paths from experimental paths.
- [x] README quickstart uses commands that exist and have been tested.

## 2. Legal And Metadata Files

- [x] `LICENSE` is present and correct.
- [x] `NOTICE` is present and correct.
- [x] `CITATION.cff` is present and references the release repository.
- [x] README explains that upstream benchmark code keeps its own licenses.

## 3. Repository Hygiene

- [x] `.gitignore` covers local caches, local secrets, and run-local prepared task copies.
- [x] Experimental local metadata files are not left unignored.
- [x] The working tree no longer contains accidental formatting churn.
- [x] The tracked files intended for release have been reviewed intentionally.

## 4. Validation

- [x] Unit tests pass on the supported environment.
- [x] Schema validation passes for the tracked example artifacts.
- [x] `python3 scripts/run_release_checks.py` passes on the release branch.
- [ ] The documented quickstart has been re-run from a clean checkout.
- [x] `python` vs `python3` assumptions are explicit and consistent.

## 5. Benchmark Artifact Set

- [x] `SkillsBench oracle real suite` artifacts are present and valid.
- [x] `tau-bench historical suite` artifacts are present and valid.
- [ ] Experimental `codex` prepared-suite outputs are either:
  - [x] intentionally excluded from release, or
  - [ ] intentionally validated and documented
- [x] The repository documents which `results/` directories are tracked release assets.

## 6. Documentation Quality

- [x] `docs/technical_design.md` matches the current code paths.
- [x] `docs/development_log.md` reflects the real chronology of key milestones.
- [x] `docs/release_manifest.md` matches intended tracked assets.
- [x] `docs/known_limitations.md` reflects the release boundary honestly.

## 7. CI And Automation

- [x] Minimal CI is configured for tests and schema validation.
- [x] CI does not depend on unavailable private services.
- [ ] CI status is green on the release branch.

## 8. Release Packaging

- [x] Version number is fixed to `v0.1.0`.
- [ ] Release notes summarize:
  - [x] protocol contribution
  - [x] supported benchmarks
  - [x] known limitations
  - [x] next planned steps
- [ ] A tag is ready to publish from a reviewed commit.

## 9. Launch Materials

- [x] A short GitHub release summary is drafted.
- [x] A short public launch post is drafted.
- [x] A short research-oriented summary is drafted.

## 10. Post-Release Backlog

- [ ] README follow-ups are captured separately from the release branch.
- [x] `tau-bench` live integration remains a tracked follow-up, not a release blocker.
- [x] `codex` prepared-suite validation remains a tracked follow-up, not a release blocker.
- [x] Paper-writing work is tracked separately from open-source release hygiene.
