# Tests

The first test target is protocol correctness, not benchmark scale.

## Priority Order

1. metric unit tests
2. split integrity tests
3. adapter smoke tests
4. regression tests on golden tasks

## First Artifacts

1. `metric_cases.json`
Toy cases for `FG`, `BR`, `BR_ratio`, `IE`, `PDS`, and `NIS`.

## Rule

No benchmark result should enter the main table unless:

1. schema validation passes
2. metric unit tests pass
3. adapter smoke tests pass
4. importer regression tests pass

## First Commands

```bash
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/validate_records.py --data results/dryrun/sample_runs.jsonl --schema runs
python3 scripts/run_release_checks.py
```

## Notes

1. `Linux-first` is the maintained path for public validation.
2. Tests are written against tracked fixtures so they do not require private benchmark credentials.
3. If you add a new adapter or importer path, include at least one fixture-backed regression test.
4. `test_synthetic_replay.py` checks frozen source/output hashes, deterministic replay,
   patient isolation, held-out label independence and FHIR patient alias resolution
   with original synthetic fixtures. It requires no model or simulator runtime.
