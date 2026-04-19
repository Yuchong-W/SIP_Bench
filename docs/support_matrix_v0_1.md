# SIP-Bench v0.1 Support Matrix (Extended)

## High-Level Support Posture

This matrix is scoped to the public `v0.1.0` release target:

1. `Linux-first` support target.
2. Release-critical paths avoid private credentials by default.
3. Additional paths are documented as optional or experimental.

## Platform and Runtime Compatibility

| Component | Version / compatibility baseline | Notes |
| --- | --- | --- |
| Python | `3.10+` | `jsonschema` runtime schema checks are required. |
| Git | `2.30+` | used for sparse-checkout on SkillsBench task hydration. |
| Docker | Local install required for SkillsBench execution; daemon must be available for real runs. | Host auth and prepared-suite flows are still Docker-reliant unless using import-only modes. |
| `harbor` | wrapper entrypoints in `scripts/harbor312`, `scripts/harbor312.cmd` | Prefer wrapper script for explicit command/timeout defaults. |
| `tau_bench` | Python package pinned by local project environment in `scripts/tau311.cmd` and `.pydeps311`. | Use wrapper to keep CLI behavior stable across machines. |

## Benchmark Support Matrix

| Benchmark path | Status | Version | Release role | Credentials | Docker dependencies | Notes |
| --- | --- | --- | --- | --- | --- |
| `SkillsBench` protocol (oracle + prepared variants) | Supported (execution) | `protocol/` JSON schema v0.1.0 | Release-critical for oracle path; prepared path is experimental | Optional for some prepared flows | Required for `subprocess` execution (`local_jobs` + task containers) | `SkillsBench` release-critical path requires only local registry/task checks and can run in import-free smoke mode with tracked fixtures. |
| `SkillsBench codex prepared (host-auth)` | Supported as experimental adapter path | `protocol/skillsbench_codex_external_prepared_*` | Experimental | Uses account-auth path by default; no global Harbor edit required | Required | Real path currently produces stable artifacts but remains ceiling-limited for some task pairs. |
| `tau-bench` historical/import-only | Supported | `protocol/` JSON schema v0.1.0 | Release-critical (interpretable second environment) | No private provider key required | Not required (import-only) | Uses local historical trajectories under benchmark checkout. |
| `tau-bench` live smoke | Experimental / optional | `protocol/tau_bench_retail_openai_smoke_suite.json` | Optional | Required if executed (`OPENAI_API_KEY` + OpenAI env) | Optional | Useful for end-to-end realism, intentionally outside release-critical path. |

## Execution Modes

| Mode | Status | Notes |
| --- | --- | --- |
| `mock` | Supported | Offline smoke for adapter and schema-level checks. |
| `subprocess` | Supported | Default for Linux-first reproducible execution. |
| import-only | Supported | Used for fixture/historical replay and for CI-friendly validation. |

## What Is Not Promised in v0.1

1. full parity between Linux and Windows execution behavior.
2. no-docker mode for prepared-suite real execution.
3. fully credential-free execution for all benchmark variants (especially `tau-bench` live).
4. guaranteed non-ceiling evidence on every new benchmark pair.

## Planned Extension

`v0.2+` should add an explicit third benchmark class and publish a strict adapter matrix across all paths (currently one of P3/P4 goals).
