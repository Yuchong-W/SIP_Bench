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
