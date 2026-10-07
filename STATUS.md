# PR #1 status

Checked 2026-09-12 from `navilia-medical-adapter`.

- PR #1 targets `main` and is based directly on `origin/main` (`a0c826f`).
- `.github/workflows/ci.yml` exists and is configured for `pull_request`; it runs
  `make ci` on Ubuntu with Python 3.12.
- GitHub reports an empty `statusCheckRollup` and the PR is shown as `UNSTABLE`.
  No failed check or workflow run is exposed to diagnose or rerun from this
  checkout, so the likely blocker is repository/Actions scheduling rather than
  a missing workflow file.
- Local `make ci` reaches the checks but cannot complete in this environment:
  `jsonschema` is not installed and the optional `EvoAgentBench` module is not
  present. These predate the medical adapter changes and require dependency or
  upstream checkout availability to resolve.

No PR-scoped code change was made for this infrastructure-only blocker.

Follow-up check: GitHub now reports `headRefOid=acf0a98ff101b8d26a630a24f86e84d69a5019a5`, matching the latest local commit. The PR remains open, has no reviews, and still has an empty `statusCheckRollup`; no new CI or review information is available.

Latest API check: workflow run `34692897466` for this SHA completed with
`conclusion=action_required`; it did not create any check runs. The PR is
`MERGEABLE` but `mergeStateStatus=UNSTABLE`. This is consistent with GitHub
requiring workflow approval for a fork-originated pull request. A neutral
maintainer note would be: “The CI workflow is present and the PR is mergeable;
the run is waiting on GitHub’s action approval and has not produced test
results yet. Once approved, the existing `make ci` workflow can report the
actual checks.”

Repair update, 2026-09-14: PR branch code head `a3d8006` rejects Navilia
timeline event-prediction rows on JSON, JSONL, and unsupported FHIR Bundle
paths instead of treating their resource-type answers as diagnoses. The
dependency environment ran 99 tests: 94 passed and 5 optional EvoAgentBench
integration tests skipped. `run_release_checks.py --plan-matrix` completed 9
steps with zero failures. The matrix retains 85 non-strict warnings for
optional historical artifacts. GitHub Actions approval remains the only
external CI blocker.
