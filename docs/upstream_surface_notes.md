# Upstream Surface Notes

This file records the upstream surfaces currently used by the adapters.

## SkillsBench

Public repo:

1. `https://github.com/benchflow-ai/skillsbench`

Current local checkout strategy:

1. sparse SSH checkout
2. real metadata materialized under `website/src/data/`
3. full `tasks/` tree not materialized yet

Observed surfaces:

1. Uses `harbor` as the execution framework.
2. Requires Python `>=3.12`.
3. Task directories follow Harbor task format under `tasks/<task-id>/`.
4. Task metadata is exposed in `website/src/data/tasks-registry.json`.
5. Real trajectory examples are exposed in `website/src/data/sample-trajectories.json`.
6. Core task files:
   - `instruction.md`
   - `task.toml`
   - `environment/Dockerfile`
   - `solution/solve.sh`
   - `tests/test.sh`
   - `tests/test_outputs.py`

Importer-relevant trajectory fields:

1. `taskName`
2. `condition`
3. `result`
4. `duration`
5. `tokens.input`
6. `tokens.output`
7. `steps[*].type`
8. `steps[*].timestamp`
9. `verifier.tests`
10. `verifier.passed`
11. `verifier.failed`

Representative command:

```bash
uv run harbor run -p tasks/<task-id> -a oracle
```

## tau-bench

Public repo:

1. `https://github.com/sierra-research/tau-bench`

Current local checkout strategy:

1. full SSH checkout

Observed surfaces:

1. Primary CLI entrypoint is `run.py`.
2. Python package name is `tau_bench`.
3. Supported environments in the checked entrypoint:
   - `retail`
   - `airline`
4. Supported splits:
   - `train`
   - `dev`
   - `test`
5. Results are written as JSON arrays of `EnvRunResult`.

Importer note:

1. upstream `task_split` and SIP `benchmark_split` are different concepts and must be supplied separately

Representative command:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --user-model gpt-4o --user-model-provider openai --user-strategy llm --task-split test --task-ids 2 4 6
```
