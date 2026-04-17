from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sip_bench.adapters.base import BenchmarkAdapter, SplitManifest, TaskDescriptor


class TauBenchAdapter(BenchmarkAdapter):
    benchmark_name = "tau-bench"

    def discover_tasks(self, source: str | Path) -> list[TaskDescriptor]:
        manifest_path = Path(source)
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        tasks: list[TaskDescriptor] = []
        for item in payload:
            task_id = int(item["task_id"])
            env_name = item.get("env", "retail")
            task_split = item.get("task_split", "test")
            tasks.append(
                TaskDescriptor(
                    benchmark_name=self.benchmark_name,
                    task_id=f"{env_name}:{task_split}:{task_id}",
                    source_path=f"{env_name}/{task_split}/{task_id}",
                    title=f"{env_name}-{task_split}-{task_id}",
                    category=env_name,
                    difficulty=None,
                    metadata={
                        "env": env_name,
                        "task_split": task_split,
                        "numeric_task_id": task_id,
                    },
                )
            )
        return tasks

    def build_manifest_from_ids(
        self,
        *,
        env: str,
        task_split: str,
        replay_ids: list[int],
        adapt_ids: list[int],
        heldout_ids: list[int],
        drift_ids: list[int] | None = None,
    ) -> SplitManifest:
        drift_ids = drift_ids or []
        return SplitManifest(
            replay=[self._task_descriptor(env=env, task_split=task_split, task_id=i) for i in replay_ids],
            adapt=[self._task_descriptor(env=env, task_split=task_split, task_id=i) for i in adapt_ids],
            heldout=[self._task_descriptor(env=env, task_split=task_split, task_id=i) for i in heldout_ids],
            drift=[self._task_descriptor(env=env, task_split=task_split, task_id=i) for i in drift_ids],
        )

    def build_run_command(
        self,
        *,
        repo_root: str | Path,
        env: str,
        task_split: str,
        task_ids: list[int],
        model: str,
        model_provider: str,
        user_model: str,
        user_model_provider: str,
        python_bin: str = "python",
        agent_strategy: str = "tool-calling",
        user_strategy: str = "llm",
        num_trials: int = 1,
        max_concurrency: int = 1,
        seed: int = 10,
        log_dir: str = "results",
        few_shot_displays_path: str | None = None,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        command = [
            python_bin,
            str(Path(repo_root) / "run.py"),
            "--agent-strategy",
            agent_strategy,
            "--env",
            env,
            "--model",
            model,
            "--model-provider",
            model_provider,
            "--user-model",
            user_model,
            "--user-model-provider",
            user_model_provider,
            "--user-strategy",
            user_strategy,
            "--task-split",
            task_split,
            "--num-trials",
            str(num_trials),
            "--max-concurrency",
            str(max_concurrency),
            "--seed",
            str(seed),
            "--log-dir",
            log_dir,
        ]
        if task_ids:
            command.append("--task-ids")
            command.extend(str(task_id) for task_id in task_ids)
        if few_shot_displays_path:
            command.extend(["--few-shot-displays-path", few_shot_displays_path])
        if extra_args:
            command.extend(extra_args)
        return command

    def parse_result_file(
        self,
        source: str | Path,
        *,
        env: str,
        task_split: str,
        benchmark_split: str,
        phase: str,
        path_type: str,
        model_name: str,
        agent_name: str,
        agent_version: str,
        seed: int,
        benchmark_version: str = "snapshot-cli-v1",
        task_ids: set[int] | None = None,
    ) -> list[dict[str, Any]]:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
        runs: list[dict[str, Any]] = []
        for attempt_index, item in enumerate(payload):
            reward = float(item["reward"])
            task_id = int(item["task_id"])
            if task_ids is not None and task_id not in task_ids:
                continue
            info = item.get("info", {})
            run_id = f"tau::{env}::{task_split}::{phase}::{seed}::{task_id}::{attempt_index}"
            runs.append(
                {
                    "schema_version": "0.1.0",
                    "run_id": run_id,
                    "benchmark_name": self.benchmark_name,
                    "benchmark_version": benchmark_version,
                    "benchmark_split": benchmark_split,
                    "phase": phase,
                    "path_type": path_type,
                    "model_name": model_name,
                    "agent_name": agent_name,
                    "agent_version": agent_version,
                    "task_id": f"{env}:{task_split}:{task_id}",
                    "attempt_index": attempt_index,
                    "score": reward,
                    "success": reward >= 1.0 - 1e-6,
                    "token_input": 0,
                    "token_output": 0,
                    "token_total": 0,
                    "tool_calls_total": 0,
                    "memory_reads": 0,
                    "memory_writes": 0,
                    "wall_clock_seconds": 0.0,
                    "cost_usd": float(info.get("user_cost", 0.0) or 0.0),
                    "human_interventions": 0,
                    "seed": seed,
                    "started_at": "1970-01-01T00:00:00Z",
                    "finished_at": "1970-01-01T00:00:00Z",
                    "metadata": {
                        "env": env,
                        "task_split": task_split,
                        "raw_info": info,
                        "traj_length": len(item.get("traj", [])),
                        "trial": item.get("trial"),
                    },
                }
            )
        return runs

    def _task_descriptor(self, *, env: str, task_split: str, task_id: int) -> TaskDescriptor:
        return TaskDescriptor(
            benchmark_name=self.benchmark_name,
            task_id=f"{env}:{task_split}:{task_id}",
            source_path=f"{env}/{task_split}/{task_id}",
            title=f"{env}-{task_split}-{task_id}",
            category=env,
            difficulty=None,
            metadata={
                "env": env,
                "task_split": task_split,
                "numeric_task_id": task_id,
            },
        )
