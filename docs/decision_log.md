# Decision Log

## 2026-04-14

### D001

Decision:

MVP uses exactly two primary environments:

1. `SkillsBench`
2. `tau-bench`

Why:

1. They are complementary.
2. They are close to self-improvement without requiring a new environment.
3. They keep the single-researcher scope realistic.

### D002

Decision:

`SWE-bench-Live` is extension-only and cannot block Week 1 or Week 2 progress.

Why:

1. It is valuable for dynamic refresh and contamination resistance.
2. It is too heavy to be a hard dependency for the MVP.

### D003

Decision:

Parameter-path baselines are deferred by default.

Why:

1. Local execution is CPU-first.
2. GPU is not guaranteed.
3. The MVP should prove protocol value before adding expensive training.

### D004

Decision:

Main leaderboard results require:

1. at least 3 repeats
2. complete logs
3. variance that is small enough to interpret

Why:

Single-run best scores are not credible for a protocol benchmark about self-improvement.

### D005

Decision:

Execution infrastructure uses two runner modes:

1. `mock`
2. `subprocess`

Why:

1. `mock` gives a deterministic dry-run path without external benchmark installation.
2. `subprocess` keeps the interface close to real upstream execution.
3. This allows CLI and artifact contracts to stabilize before expensive benchmark runs.

### D006

Decision:

Until GitHub connectivity allows full upstream checkout, benchmark integration will use:

1. upstream surface notes
2. local fixtures
3. placeholder benchmark directories

Why:

1. public `git clone` is currently failing in this environment
2. protocol and adapter work should not stop on network instability
3. the fallback preserves interface progress while deferring full benchmark execution

### D007

Decision:

Remote publishing will target `Yuchong-W/Protocol_Bench`, but release engineering must not depend on immediate GitHub availability.

Why:

1. the target repository is now known
2. this environment still cannot reach `github.com` over direct git transport
3. the connected GitHub app does not currently expose the target repository
4. local documentation and release manifests still need to be maintained so publication can happen with minimal manual recovery

### D008

Decision:

Publishing from this machine should use SSH remotes for GitHub instead of HTTPS.

Why:

1. repeated tests show `github.com:443` is blocked from this environment
2. `github.com:22` is reachable
3. SSH authentication for `git@github.com` succeeds for `Yuchong-W`
4. the repository push succeeded immediately after switching `origin` to SSH and merging the remote initial commit

### D009

Decision:

`SkillsBench` should be maintained as a sparse SSH checkout rather than a full local clone.

Why:

1. the repository is heavier than `tau-bench`
2. the importer only needs real registry and trajectory metadata at this stage
3. sparse checkout keeps the local dependency real without forcing the full task tree into the MVP path
4. task directories can be hydrated later on demand for selected manifests

### D010

Decision:

Importer contracts must separate upstream dataset splits from SIP protocol splits.

Why:

1. `tau-bench` `train/dev/test` are upstream task splits, not SIP `replay/adapt/heldout`
2. conflating the two would silently write semantically wrong `runs.jsonl`
3. the same principle applies to SkillsBench condition labels versus SIP `path_type` and protocol `phase`


### D011

Decision:

Real SkillsBench execution should use a repository-local Harbor wrapper instead of relying directly on the ambient global Harbor install.

Why:

1. the global Harbor install currently runs on Python `3.13` and fails on Windows during subprocess-based Docker orchestration
2. `uvx --python 3.12 harbor` clears that runtime bug and reaches real environment setup
3. a repository-local launcher lets plans encode a single stable executable path without teaching the protocol about multi-token shell prefixes
4. the launcher is also the right place to pin local cache location and Docker-related environment workarounds
5. the same tracked suite config should be able to resolve to `scripts/harbor312` on Linux and `scripts/harbor312.cmd` on Windows

### D012

Decision:

Harbor job directories should be treated as first-class import inputs for SkillsBench, even when a trial fails before verifier completion.

Why:

1. real local execution is flaky enough that dropping failed trials would hide the operational bottlenecks this benchmark infrastructure must surface
2. the Harbor `TrialResult` schema carries enough metadata to write protocol-compliant `runs.jsonl` rows for both successes and failures
3. separating command execution from job import keeps the execution layer generic and pushes benchmark outcome semantics into the adapter where they belong

### D013

Decision:

Real `SkillsBench` smoke execution on this machine should treat Harbor timeout multipliers as explicit run policy, not as incidental CLI tweaks.

Why:

1. `dialogue-parser` failed under the default environment build timeout but succeeded immediately when rerun with `--environment-build-timeout-multiplier 4`
2. the failure mode was environmental and machine-specific, not protocol-specific
3. if timeout policy remains implicit, repeated real-run failures will look like unstable benchmark logic instead of a reproducible execution configuration issue
4. future orchestration code should therefore surface timeout overrides as first-class plan inputs for slow Docker tasks

### D014

Decision:

Multi-run protocol testing should be driven by an explicit suite config instead of by ad-hoc shell choreography.

Why:

1. real protocol tests require multiple coordinated runs across `phase` and `benchmark_split`
2. that coordination needs stable metadata so the final aggregation step can produce a valid `summary.jsonl`
3. explicit suite configs make run intent reviewable and reproducible
4. the same format also enables an import-only regression mode for deterministic tests

### D015

Decision:

`SkillsBench` real suites may use run-local prepared task copies, including skill stripping and explicit task patches, instead of mutating the upstream checkout.

Why:

1. several upstream tasks currently fail on this machine for environment reasons that are orthogonal to the SIP protocol
2. `T0` frozen-style runs need a clean way to remove benchmark-provided skills without rewriting upstream sources in place
3. run-local copies make any deviation explicit, reviewable, and disposable
4. this keeps the protocol runner honest about what was executed while avoiding accidental contamination of the sparse upstream checkout

### D016

Decision:

`tau-bench` should run through a repo-local Python dependency overlay plus wrapper script instead of through user-site or ambient Python installs.

Why:

1. direct `pip install` under the default machine Python path repeatedly produced non-deterministic hangs
2. user-site installs failed with `WinError 5` under `C:\Users\22793\AppData\Roaming\Python`
3. a repo-local overlay keeps the runtime reproducible and visible inside the benchmark workspace
4. once imports are isolated, online smoke failures can be attributed cleanly to missing provider credentials rather than to Python environment drift

### D017

Decision:

Provider credentials for `tau-bench` should be resolved at the protocol layer from explicit env files or local `.env` discovery, not only from the parent shell environment.

Why:

1. shell-export-only credentials make real smoke runs non-reproducible across terminals and editors
2. benchmark execution should be fully config-driven except for the secret values themselves
3. applying the same resolved env to both preflight and execution removes a class of false-negative setup failures
4. a gitignored `protocol/.env.local` gives a stable local convention without leaking secrets into the repository

### D018

Decision:

The first public `SIP-Bench` release should use `Apache-2.0` and present itself as `Linux-first` research infrastructure.

Why:

1. the project is closer to reusable benchmark infrastructure than to a throwaway experiment repository
2. `Apache-2.0` gives a clearer public release posture for reuse, attribution, and contribution than an ad-hoc or missing license state
3. the current public support story is materially stronger on Linux than on Windows
4. narrowing the official support target reduces release ambiguity and avoids overpromising cross-platform stability

### D019

Decision:

The `v0.1` release-critical evidence path should be limited to validated `SkillsBench oracle` and `tau-bench historical/import-only` artifacts, while `codex` prepared-suite and provider-backed live runs remain experimental.

Why:

1. the repository already contains credible validated artifacts for those two release-critical paths
2. `codex` connectivity is not available on every intended validation machine
3. `tau-bench` live execution still depends on private provider credentials
4. separating release-critical from experimental paths improves the open-source launch quality without blocking future research experiments
