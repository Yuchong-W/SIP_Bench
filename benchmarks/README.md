# Benchmarks

This directory is reserved for upstream benchmark repositories and development snapshots.

## Current State

Direct HTTPS `git clone` to GitHub fails in this environment because outbound connections on port `443` are blocked.

The current workaround is:

1. publish and fetch this repository over SSH
2. use a sparse SSH checkout for `SkillsBench`
3. use a full SSH checkout for `tau-bench`

## Intended Upstreams

1. `benchflow-ai/skillsbench`
2. `sierra-research/tau-bench`

## Notes

1. `benchmarks/skillsbench` is intentionally treated as a local dependency checkout and is ignored by the main repository.
2. `benchmarks/tau-bench` is also treated as a local dependency checkout and is ignored by the main repository.
3. `SkillsBench` currently materializes real metadata under `website/src/data/` first; task trees can be expanded later via sparse checkout if execution requires them.
4. `tau-bench` README currently warns that the repo tasks are outdated and points users to the newer `tau2-bench` / `tau3-bench` line.
