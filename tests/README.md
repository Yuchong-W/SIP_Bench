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

## First Command

```powershell
python -m unittest discover -s tests -p "test_*.py"
python scripts\validate_records.py --data results\dryrun\sample_runs.jsonl --schema runs
```
