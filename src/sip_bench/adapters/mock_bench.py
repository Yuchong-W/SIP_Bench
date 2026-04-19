from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sip_bench.adapters.base import BenchmarkAdapter, SplitManifest, TaskDescriptor


class MockBenchAdapter(BenchmarkAdapter):
    benchmark_name = "mock-bench"

    def discover_tasks(self, source: str | Path) -> list[TaskDescriptor]:
        payload_path = Path(source)
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("tasks", payload.get("items", []))
        if not isinstance(payload, list):
            raise ValueError("Mock benchmark payload must be a list")
        if not payload:
            return []

        tasks: list[TaskDescriptor] = []
        for raw in payload:
            if isinstance(raw, str):
                item = {"task_id": raw}
            else:
                item = dict(raw)
            task_id = str(item.get("task_id") or item.get("id") or item.get("name") or "")
            if not task_id:
                raise ValueError("Each mock benchmark task must define a task_id")
            tasks.append(
                TaskDescriptor(
                    benchmark_name=self.benchmark_name,
                    task_id=task_id,
                    source_path=str(item.get("source_path", task_id)),
                    title=str(item.get("title", task_id)),
                    category=item.get("category"),
                    difficulty=item.get("difficulty"),
                    metadata={
                        "raw": item,
                        "source_type": "fixture",
                    },
                )
            )
        return tasks

    def build_run_command(
        self,
        *,
        repo_root: str | Path,
        task: TaskDescriptor,
        model: str | None = None,
        agent_import_path: str | None = None,
        python_bin: str = "python",
        extra_args: list[str] | None = None,
    ) -> list[str]:
        command = [
            python_bin,
            "-c",
            f"print(\"mock-bench task={task.task_id} model={model or 'mock'}\")",
        ]
        if agent_import_path:
            command.extend(["--agent-import-path", agent_import_path])
        if extra_args:
            command.extend(extra_args)
        return command

    def parse_result_file(
        self,
        source: str | Path,
        *,
        benchmark_split: str,
        phase: str,
        seed: int,
        path_type: str | None = None,
        model_name: str | None = None,
        agent_name: str | None = None,
        agent_version: str = "mock-bench-import",
        benchmark_version: str = "mock-bench-upstream",
        task_ids: set[str] | set[int] | None = None,
    ) -> list[dict[str, Any]]:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            if "results" in payload:
                payload = payload["results"]
            elif "items" in payload:
                payload = payload["items"]
            else:
                raise ValueError("Unsupported mock-bench result payload shape")
        if not isinstance(payload, list):
            raise ValueError("Mock-bench result payload must be a list")

        if task_ids is not None:
            requested_task_ids = {str(task_id) for task_id in task_ids}
        else:
            requested_task_ids = None

        attempt_counters: dict[tuple[str, str, str], int] = {}
        runs: list[dict[str, Any]] = []

        for item in payload:
            raw_task_id = item.get("task_id") or item.get("id") or item.get("name")
            task_id = str(raw_task_id or "mock-task")
            if requested_task_ids is not None and task_id not in requested_task_ids:
                continue

            row_model_name = model_name or str(item.get("model_name") or item.get("model") or "mock-model")
            row_agent_name = agent_name or str(item.get("agent_name") or item.get("agent") or "mock-agent")
            row_path_type = str(item.get("path_type") or path_type or "oracle")
            attempt_key = (task_id, row_model_name, row_agent_name)
            attempt_index = attempt_counters.get(attempt_key, 0)
            attempt_counters[attempt_key] = attempt_index + 1

            score = item.get("score")
            if score is None:
                score = 1.0 if bool(item.get("success")) else 0.0
            score_value = float(score)
            raw_success = item.get("success")
            if raw_success is None:
                success = score_value >= 1.0
            else:
                success = bool(raw_success)

            wall_clock_seconds = float(item.get("wall_clock_seconds") or item.get("wall_time") or 0.0)
            started_at_raw = item.get("started_at")
            finished_at_raw = item.get("finished_at")
            started_dt = self._parse_timestamp(started_at_raw) or datetime(1970, 1, 1, tzinfo=UTC)
            finished_dt = self._parse_timestamp(finished_at_raw) or (started_dt + timedelta(seconds=wall_clock_seconds))
            if finished_dt < started_dt:
                finished_dt = started_dt

            started_at = started_dt.isoformat().replace("+00:00", "Z")
            finished_at = finished_dt.isoformat().replace("+00:00", "Z")

            run_id = (
                f"mock-bench::{benchmark_split}::{phase}::{row_path_type}::{seed}::"
                f"{row_agent_name}::{row_model_name}::{task_id}::{attempt_index}"
            )
            runs.append(
                {
                    "schema_version": "0.1.0",
                    "run_id": run_id,
                    "benchmark_name": self.benchmark_name,
                    "benchmark_version": benchmark_version,
                    "benchmark_split": benchmark_split,
                    "phase": phase,
                    "path_type": row_path_type,
                    "model_name": row_model_name,
                    "agent_name": row_agent_name,
                    "agent_version": agent_version,
                    "task_id": task_id,
                    "attempt_index": attempt_index,
                    "score": score_value,
                    "success": success,
                    "token_input": int(item.get("token_input", 0) or 0),
                    "token_output": int(item.get("token_output", 0) or 0),
                    "token_total": int(item.get("token_total", 0) or 0),
                    "tool_calls_total": int(item.get("tool_calls_total", 0) or 0),
                    "memory_reads": int(item.get("memory_reads", 0) or 0),
                    "memory_writes": int(item.get("memory_writes", 0) or 0),
                    "wall_clock_seconds": wall_clock_seconds,
                    "cost_usd": float(item.get("cost_usd", 0.0) or 0.0),
                    "human_interventions": int(item.get("human_interventions", 0) or 0),
                    "seed": seed,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "metadata": {
                        "source_file": str(source),
                        "mock_payload_version": item.get("mock_payload_version", "v1"),
                        "raw": item,
                        "exception_type": item.get("exception_type"),
                        "exception_message": item.get("exception_message"),
                    },
                }
            )
        return runs

    def _parse_timestamp(self, raw: Any) -> datetime | None:
        if not raw:
            return None
        timestamp = str(raw)
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None
