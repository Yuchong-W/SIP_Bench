# Benchmarks

This directory is reserved for upstream benchmark repositories and development snapshots.

## Current State

Direct `git clone` to GitHub failed in this environment because outbound GitHub connections were reset or blocked on port `443`.

To avoid blocking adapter development, the repository currently uses:

1. partial upstream metadata snapshots
2. adapter scaffolds built against fetched upstream entrypoints
3. local fixtures for smoke tests

## Intended Upstreams

1. `benchflow-ai/skillsbench`
2. `sierra-research/tau-bench`

## Notes

1. `tau-bench` README currently warns that the repo tasks are outdated and points users to the newer `tau2-bench` / `tau3-bench` line.
2. The MVP remains adapter-compatible with `tau-bench` style CLI entrypoints first, then can be upgraded once a full upstream checkout is available.
