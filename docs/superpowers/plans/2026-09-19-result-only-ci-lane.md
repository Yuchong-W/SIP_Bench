# Result-Only Suite CI Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a credential-free release/CI lane that runs and validates the checked-in native medical suite while keeping external benchmark artifact checks separate.

**Architecture:** Mark protocol configs with an explicit `suite_kind` (`external` or `result-only`) and a result-only artifact contract. The release checker will execute the native medical CLI in a temporary output directory, validate its 12 run artifacts and 24 records, hash the generated artifacts, and emit a failure/cost summary. The plan-matrix checker will require only declared artifacts for result-only suites and retain the existing plan/hydration/execution requirements for external suites.

**Tech Stack:** Python 3.11+, jsonschema, unittest, GitHub Actions, existing `run_protocol.py`, `run_release_checks.py`, and `check_plan_matrix.py`.

## Global Constraints

- Do not change scores, retry policy, or the four split names.
- Do not require provider credentials, Docker, Harbor, or upstream benchmark checkouts for the native lane.
- Do not push `main` or merge PR #1; push only an independent fork branch and open a PR associated with PR #1.
- Preserve existing external suite behavior and current release artifact requirements.

---

### Task 1: Define the result-only config contract

**Files:**
- Modify: `schemas/protocol_suite.schema.json`
- Modify: `protocol/medical_synthetic_suite.json`
- Test: `tests/test_protocol_runner.py`

**Interfaces:**
- Configs accept top-level `suite_kind` with `external` and `result-only` values.
- Result-only configs may declare `expected_artifacts` containing `runs_per_suite`, `records`, and artifact names.
- Existing configs without `suite_kind` normalize to `external`.

- [ ] **Step 1: Add a failing config-contract test.**

```python
def test_result_only_config_declares_expected_artifacts(self):
    config = load_protocol_suite_config(ROOT / "protocol" / "medical_synthetic_suite.json")
    self.assertEqual(config["suite_kind"], "result-only")
    self.assertEqual(config["expected_artifacts"]["runs_per_suite"], 12)
    self.assertEqual(config["expected_artifacts"]["records"], 24)
```

- [ ] **Step 2: Extend the JSON schema and semantic normalization.**

Add `suite_kind` and an `expected_artifacts` object with non-negative integer fields and an artifact-name array. Normalize missing `suite_kind` to `external`; reject `result-only` configs without expected artifact counts.

- [ ] **Step 3: Update the medical config.**

Set `suite_kind` to `result-only` and declare `runs_per_suite: 12`, `records: 24`, and `combined_runs.jsonl`, `summary.jsonl`, `suite_report.json`.

- [ ] **Step 4: Run the focused config test.**

Run: `.venv/bin/python -m unittest tests.test_protocol_runner.ProtocolRunnerTests.test_result_only_config_declares_expected_artifacts`

Expected: PASS.

- [ ] **Step 5: Commit the contract.**

```bash
git add schemas/protocol_suite.schema.json protocol/medical_synthetic_suite.json tests/test_protocol_runner.py
git commit -m "feat: declare result-only suite artifacts"
```

### Task 2: Make plan-matrix checks honor suite kind

**Files:**
- Modify: `scripts/check_plan_matrix.py`
- Test: `tests/test_check_plan_matrix.py`

**Interfaces:**
- `_run_suite_check` reads `suite_kind`.
- `result-only` checks only `runs/<run>.jsonl` plus declared suite artifacts; `external` keeps current checks.

- [ ] **Step 1: Add a failing result-only matrix test.**

Use a temporary result-only config with one run and pre-create only its JSONL, combined, summary, and suite report files. Assert zero failed checks and no plan/hydration/execution requirements.

- [ ] **Step 2: Implement conditional artifact expectations.**

For `result-only`, skip source plan, plan, hydration, and execution checks. Require each run JSONL and only the names in `expected_artifacts.artifacts`; keep the current behavior unchanged for external configs.

- [ ] **Step 3: Run focused matrix tests.**

Run: `.venv/bin/python -m unittest tests.test_check_plan_matrix`

Expected: PASS.

- [ ] **Step 4: Commit the matrix behavior.**

```bash
git add scripts/check_plan_matrix.py tests/test_check_plan_matrix.py
git commit -m "fix: support result-only plan matrix suites"
```

### Task 3: Add a credential-free release check and failure/cost report

**Files:**
- Modify: `scripts/run_release_checks.py`
- Modify: `tests/test_release_checks.py`
- Test artifact: temporary directory only

**Interfaces:**
- `run_release_checks.py` runs `run-medical-suite` for result-only configs in a temporary output root.
- The report includes `result_only_suites`, generated artifact SHA-256 values, record/run counts, cost totals, and failure-family totals.

- [ ] **Step 1: Add a failing release-check test.**

Invoke the release checker with `--skip-import-check --plan-matrix --report <tmp/report.json>` and assert the report contains a passed native-suite step, 12 runs, 24 records, and non-empty cost/failure fields without reading credentials.

- [ ] **Step 2: Implement native suite execution.**

Discover result-only configs, execute each via `scripts/run_protocol.py run-medical-suite --config ... --out-root <temp>`, validate combined runs and summary with existing validators, count records/runs, hash `combined_runs.jsonl`, `summary.jsonl`, and `suite_report.json`, and aggregate `wall_clock_seconds`, `token_total`, `tool_calls_total`, and failure families from records.

- [ ] **Step 3: Preserve external checks.**

Leave required dry-run and SkillsBench artifact gates and optional historical artifact classification unchanged. A native failure marks release checks failed; missing external optional artifacts remain warnings/metadata.

- [ ] **Step 4: Run focused release tests.**

Run: `.venv/bin/python -m unittest tests.test_release_checks`

Expected: PASS.

- [ ] **Step 5: Commit release checks.**

```bash
git add scripts/run_release_checks.py tests/test_release_checks.py
git commit -m "feat: validate native suites in release checks"
```

### Task 4: Wire GitHub Actions and documentation

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `docs/technical_design.md`
- Modify: `protocol/protocol_spec_v0.md`
- Test: full unittest and release checks

**Interfaces:**
- CI runs the credential-free native lane on every pull request and uploads its JSON report/artifacts.
- Documentation distinguishes result-only and external suites and explains failure/cost report fields.

- [ ] **Step 1: Add a CI step.**

Run the release checker with `--skip-import-check --plan-matrix --report ci-artifacts/release-report.json`, then upload `ci-artifacts` with `actions/upload-artifact@v4`.

- [ ] **Step 2: Document the lane and boundary.**

State that native result-only suites require no API key, Docker, Harbor, or upstream checkout; external suites retain their existing requirements.

- [ ] **Step 3: Run all checks.**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/run_release_checks.py --skip-import-check --plan-matrix --report /tmp/sip-release-report.json
.venv/bin/python scripts/validate_records.py --data /tmp/medical-suite/combined_runs.jsonl --schema runs
```

Expected: all tests pass; native result-only report passes; generated runs and summary validate.

- [ ] **Step 4: Commit docs and CI.**

```bash
git add .github/workflows/ci.yml README.md docs/technical_design.md protocol/protocol_spec_v0.md
git commit -m "ci: add credential-free native suite lane"
```

### Task 5: Push an independent branch and open an associated PR

**Files:**
- No source files; GitHub metadata only.

- [ ] **Step 1: Verify branch divergence.**

Confirm the branch is based on `medical-native-suite`, does not target upstream `main`, and has no merge action.

- [ ] **Step 2: Push only the fork branch.**

```bash
git push fork medical-native-ci
```

- [ ] **Step 3: Open a PR against the fork’s native branch and associate PR #1.**

Use `gh pr create --repo Frankie-Xu/SIP_Bench --base medical-native-suite --head medical-native-ci --body-file ...` with `Closes #1` omitted; reference PR #1 in the body as a dependency/background link so it does not close or modify PR #1.

- [ ] **Step 4: Verify remote SHA, PR URL, and CI status.**

Report commit SHA, PR URL, test result, and any `action_required` status. Do not merge or push upstream `main`.

## Completion

Implemented in four commits on `medical-native-ci`: `ab3b99a`, `e84d3f3`,
`790e054`, and `e15e92e`. Full tests passed (104 total, 99 passed, 5 skipped).
The credential-free release lane produced 12 runs and 24 records, validated both
schemas, and emitted artifact hashes, cost totals, and failure-family counts.
