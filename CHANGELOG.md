# Changelog

All notable changes to `SIP-Bench` will be documented in this file.

## v0.1.0

Initial public open-source release track.

Highlights:

1. protocol-layer benchmark framing for self-improving agents
2. normalized `runs.jsonl` and `summary.jsonl` schemas
3. metric aggregation for gain, retention, and efficiency
4. `SkillsBench` integration with planning, hydration, execution import, and suite orchestration
5. `tau-bench` integration with historical/import-only protocol support and live preflight support
6. release scaffolding for open-source use:
   - `Apache-2.0` license
   - citation metadata
   - contribution guidance
   - security policy
   - issue and PR templates
   - minimal CI
7. consolidated release validation:
   - `scripts/run_release_checks.py`
   - CI now uses the shared release-check entrypoint
   - `.editorconfig` complements `.gitattributes` for line-ending discipline
8. suite recovery hardening:
   - `run_protocol.py --run-name ...` can rerun a subset of suite runs and rebuild the suite summary from mixed old-plus-new results
   - real SkillsBench reruns now allocate a fresh Harbor job directory so stale job outputs cannot be re-imported accidentally

Known release posture:

1. `Linux-first` official support target
2. `SkillsBench oracle` and `tau-bench historical` are the release-critical evidence paths
3. `codex` prepared-suite and provider-backed live runs remain experimental
