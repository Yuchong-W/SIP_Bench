# SIP-Bench v0.1 Launch Materials

## GitHub Release Summary

`SIP-Bench v0.1.0` is the first public open-source release of a protocol-layer benchmark for self-improving agents.

Instead of introducing a new task world, `SIP-Bench` wraps existing benchmark environments with a shared longitudinal evaluation contract built around `T0/T1/T2`, `replay/adapt/heldout/drift`, and normalized metrics for gain, retention, and efficiency.

This release includes:

1. protocol schemas and aggregation logic
2. `SkillsBench` integration with real-suite artifacts
3. `tau-bench` historical/import-only protocol support
4. open-source release scaffolding:
   - `Apache-2.0`
   - citation metadata
   - contribution guidance
   - security policy
   - CI

Current release posture:

1. `Linux-first`
2. `SkillsBench oracle` and `tau historical` are the release-critical evidence paths
3. `codex` prepared-suite and provider-backed live runs remain experimental

## Short Public Post

Released `SIP-Bench v0.1.0`: a protocol-layer benchmark for self-improving agents.

The goal is not to add yet another benchmark world. The goal is to make improvement, retention, and cost measurable under one reusable evaluation contract across existing environments.

Current release:

1. `SkillsBench` real-suite support
2. `tau-bench` historical/import-only support
3. `Linux-first` quickstart
4. open-source release scaffolding and CI

Repo: `https://github.com/Yuchong-W/Protocol_Bench`

## Research-Oriented Summary

`SIP-Bench` asks a different question from standard agent leaderboards.

Instead of only asking "what score did the agent get on this split?", it asks:

1. did the agent improve on held-out tasks?
2. did it retain performance on previously solved tasks?
3. what cost and interaction budget did that improvement require?

The core contribution is a reusable longitudinal protocol layer:

1. `T0 / T1 / T2`
2. `replay / adapt / heldout / drift`
3. normalized run logging
4. protocol-oriented metrics such as `FG`, `BR`, and `IE`

The first release is intentionally scoped as open-source research infrastructure, not as a final large-scale empirical paper package.

## Chinese Release Post

发布了 `SIP-Bench v0.1.0`。

这不是一个新的 benchmark world，而是一层面向 `self-improving agents` 的协议层评测基础设施。核心目标是把以下问题放到同一个评测框架里：

1. agent 是否真的在 held-out 任务上提升了
2. 它是否遗忘了已经掌握的任务
3. 这种提升花了多少交互和计算成本

首个公开版本当前主打：

1. `SkillsBench` 真实协议链路
2. `tau-bench` historical/import-only 协议支持
3. `Linux-first` 的公开运行路径
4. 完整的开源发布骨架和 CI

仓库地址：

`https://github.com/Yuchong-W/Protocol_Bench`
