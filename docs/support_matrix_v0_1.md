# SIP-Bench v0.1 Support Matrix

This matrix describes the intended public support posture for `v0.1.0`.

## Platform Support

| Area | Linux | Windows | Notes |
| --- | --- | --- | --- |
| Unit tests | Supported | Best effort | `Linux-first` is the official support target |
| Dry-run CLI paths | Supported | Best effort | Quickstart and CI are centered on Linux |
| `SkillsBench` protocol logic | Supported | Best effort | Real-task stability still depends on local Docker behavior |
| `tau-bench` historical/import-only | Supported | Best effort | No provider credentials required |
| `tau-bench` live preflight | Supported | Best effort | Requires provider credentials |
| `codex` prepared-suite path | Experimental | Experimental | Not release-critical |

## Benchmark Support

| Benchmark path | Status | Release role | Notes |
| --- | --- | --- | --- |
| `SkillsBench oracle real suite` | Supported | Release-critical | Main real-suite evidence path |
| `SkillsBench Harbor job import` | Supported | Release-critical | Imports both success and failure outcomes |
| `SkillsBench prepared task copies` | Experimental | Optional | Useful for frozen vs skill-enabled comparisons |
| `tau-bench historical/import-only` | Supported | Release-critical | Current second-environment evidence path |
| `tau-bench` live provider-backed execution | Experimental | Optional | Requires provider credentials |

## Execution Modes

| Mode | Status | Notes |
| --- | --- | --- |
| `mock` | Supported | Stable for dry-run protocol validation |
| `subprocess` | Supported | Officially supported on Linux-first path |
| import-only suite mode | Supported | Especially important for deterministic historical or fixture-backed runs |

## What Is Not Promised In v0.1

1. Full parity between Linux and Windows
2. Stable public `codex` validation on every machine
3. Credential-free live `tau-bench` execution
4. Large-scale matched-budget empirical comparisons across all path types
