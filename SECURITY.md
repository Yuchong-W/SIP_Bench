# Security Policy

## Scope

`SIP-Bench` is research infrastructure and benchmark orchestration software. It is not designed as a hardened production service.

That said, security-relevant issues are still important, especially when they involve:

1. unsafe execution defaults
2. secret leakage through tracked files or logs
3. command-construction bugs that expand execution scope unexpectedly
4. accidental inclusion of local credentials or benchmark-private assets in the public release surface

## Supported Release Line

The current supported public line is the latest `v0.1.x` release branch or the current `main` branch before the next tagged release.

## Reporting A Vulnerability

Please do not open a public issue for a suspected security problem that could expose secrets or unsafe execution behavior.

Instead:

1. report the issue privately to the maintainer
2. include a minimal reproduction when possible
3. state whether the issue affects:
   - local secret handling
   - subprocess execution
   - benchmark job import
   - release artifact publication

## What To Expect

Best-effort response goals:

1. acknowledgment within `7` days
2. initial triage within `14` days

Because this is a research project, response times may vary, but reports that affect secret handling or unsafe execution will be prioritized.

## Operational Guidance

Until the project grows a broader maintainer base, users should assume:

1. private provider credentials belong in local gitignored env files
2. benchmark checkouts under `benchmarks/` are local dependencies and should be reviewed before execution
3. experimental suite configs should not be treated as production-safe automation
