# Known Limitations

## Current MVP Limits

1. The protocol focuses on `BWT/FWT-style retention` and `improvement efficiency`, not the full self-improvement problem.
2. The MVP does not yet provide a fair large-scale comparison between external-path and parameter-path adaptation.
3. The first release uses only two primary environments, which limits cross-domain generality.
4. Contamination auditing is environment-dependent and not yet unified across all adapters.
5. Long-term persistence is approximated through `T0/T1/T2`; it is not yet a full 7x24 deployment benchmark.

## Intended Extensions

1. add `SWE-bench-Live` as a third environment
2. add parameter-path baselines under matched budgets
3. add adapter-level contamination checks
4. add safety-side reporting alongside self-improvement metrics
