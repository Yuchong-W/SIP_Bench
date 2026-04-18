# Host-Auth Prepared Experiment Design

This document defines the experimental ladder for the repo-local `codex-local-auth` path.
Its purpose is to keep the next round of prepared-suite work aligned with both:

1. high-quality open-source engineering discipline
2. paper-grade empirical design discipline

## What Is Already Proven

The following claims are already supported by tracked artifacts:

1. the repo-local host-auth custom agent works without editing the global Harbor installation
2. ChatGPT login state is sufficient for real verifier-backed prepared SkillsBench runs
3. the host-auth path now supports a full four-run `T0/T1 replay/heldout` bundle and produces a valid `summary.jsonl`

That means the next round should not spend effort re-proving account-auth viability on the same easy tasks.

## What Is Not Yet Proven

The following claims are still missing:

1. the host-auth path can produce non-ceiling protocol evidence
2. the prepared path can reveal `FG / BR / IE` tradeoffs rather than only execution correctness
3. the next prepared bundle can support a paper-facing comparison instead of only a smoke or regression story

## Experimental Standard

Every new prepared experiment should satisfy these rules:

1. it must be reproducible from a checked-in config
2. it must produce tracked run artifacts, not only terminal logs
3. it must be interpretable without private dashboards
4. it must be evaluated against a clear acceptance gate before being promoted into the public results story

## Acceptance Gates

Treat each candidate experiment as belonging to one of three classes:

1. `Smoke`
   - purpose: validate that the execution path still works
   - success condition: valid artifacts, valid runs, valid suite report
   - not sufficient for protocol-value claims
2. `Screening`
   - purpose: check whether a task or task family is likely to avoid ceiling effect
   - success condition: produces a meaningful, nontrivial score or operational signal worth promoting to a bundle
   - sufficient to justify a follow-up bundle, but not yet a headline result
3. `Evidence`
   - purpose: support protocol-first claims
   - success condition: non-ceiling results, interpretable replay/heldout behavior, tracked provenance, and stable reruns

## Current Ladder

### Stage 0: Smoke Baseline

Locked asset:

1. `protocol/skillsbench_codex_external_prepared_host_auth_bundle.json`

Interpretation:

1. this is the canonical smoke or regression bundle for account-auth prepared execution
2. it proves infrastructure viability
3. it does not yet prove protocol value because all tracked scores saturate at `1.0`

### Stage 1: Screening Probes

Immediate goal:

1. identify one or more tasks that do not collapse into the same ceiling pattern as the current easy bundle

Current screening candidate:

1. `citation-check`
   - difficulty: `medium`
   - category: `research`
   - reason to screen:
     - verifier is discrete and strict
     - likely less vulnerable to trivial saturation than the current easy pair
     - currently available in the local checkout without needing additional benchmark fetches

Screening rule:

1. do not promote a task into the next bundle solely because it is labeled `medium`
2. promote it only if the probe produces a nontrivial score, meaningful cost difference, or a clear operational failure mode worth tracking
3. if the first blocker is environment drift rather than capability, apply the least invasive hardening patch first and rerun the same screening task before escalating to a different task

Current patch ladder for `citation-check`:

1. first use `citation_check_apt_retry` to reduce transient Ubuntu package-fetch failures while preserving the original task shape
2. only if that remains too brittle should the stronger `citation_check_python_runtime` patch be used, because it rewrites more of the task bootstrap path

### Stage 2: Non-Ceiling Bundle

Target:

1. a replay-plus-heldout host-auth bundle that is not dominated by `1.0 / 1.0 / 1.0 / 1.0`

Desired structure:

1. replay side should include at least one task with meaningful room above and below perfect score
2. heldout side should come from a different category so replay-versus-heldout remains interpretable
3. the pair should be chosen for runtime practicality as well as protocol value

Promotion rule:

1. only after screening identifies at least one non-ceiling candidate should a new bundle be treated as the main prepared evidence bundle

### Stage 3: Hard Bundle

Escalation trigger:

1. if the medium bundle still saturates or is too weak to reveal protocol tradeoffs

Goal:

1. bring in at least one `hard` task while preserving reproducibility and runtime practicality

## Local Availability Constraint

The current local `benchmarks/skillsbench` checkout is not a full offline mirror of every task in the registry.

At the time of writing, the locally available task directories are:

1. `citation-check` (`medium`, `research`)
2. `court-form-filling` (`easy`, `document-processing`)
3. `dialogue-parser` (`easy`, `game`)
4. `offer-letter-generator` (`easy`, `document-generation`)
5. `powerlifting-coef-calc` (`easy`, `data-analysis`)

Implication:

1. not every registry-listed medium or hard task is currently inspectable offline from this checkout
2. screening should therefore start with locally available candidates unless the benchmark checkout is intentionally expanded first

## Fallback Policy

Use `OPENAI_API_KEY` only if at least one of the following becomes true:

1. the harder host-auth screening probes stall repeatedly for reasons specific to the host-auth path
2. the host-auth path becomes too brittle to support repeatable non-ceiling bundles
3. the benchmark checkout is ready for stronger tasks but the host-auth route is the binding operational blocker

## Reporting Standard

When a screening probe finishes, record:

1. task id
2. difficulty and category
3. phase and path type
4. score
5. token total
6. wall-clock time
7. whether the result should be classified as `Smoke`, `Screening`, or `Evidence`

This classification should be written into `docs/development_log.md` before the task is promoted into the results gallery.
