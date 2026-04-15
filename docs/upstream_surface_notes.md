# Upstream Surface Notes

This file records the minimal upstream surfaces currently used to build adapters while full repository clone is unavailable.

## SkillsBench

Public repo:

1. `https://github.com/benchflow-ai/skillsbench`

Observed surfaces:

1. Uses `harbor` as the execution framework.
2. Requires Python `>=3.12`.
3. Task directories follow Harbor task format under `tasks/<task-id>/`.
4. Task metadata is exposed in `website/src/data/tasks-registry.json`.
5. Core task files:
   - `instruction.md`
   - `task.toml`
   - `environment/Dockerfile`
   - `solution/solve.sh`
   - `tests/test.sh`
   - `tests/test_outputs.py`

Representative command:

```bash
uv run harbor run -p tasks/<task-id> -a oracle
```

## tau-bench

Public repo:

1. `https://github.com/sierra-research/tau-bench`

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

Representative command:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --user-model gpt-4o --user-model-provider openai --user-strategy llm --task-split test --task-ids 2 4 6
```
