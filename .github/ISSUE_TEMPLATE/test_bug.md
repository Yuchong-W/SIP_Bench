---
name: Test bug
about: Report a reproducible test or validation bug.
title: "[Test] "
labels: bug
assignees: ''
---

## What failed

Describe the exact test/check and expected behavior.

## Repro steps

Paste the exact command sequence.

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## Environment

- OS:
- Python:
- Docker:
- Command output:

## Evidence

- Error message:
- Output artifact (if any):

## Impact

- [ ] Unit tests
- [ ] CLI behavior
- [ ] Artifact schema
- [ ] CI
