from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sip_bench.adapters.base import BenchmarkAdapter, TaskDescriptor


class SkillsBenchAdapter(BenchmarkAdapter):
    benchmark_name = "skillsbench"
    condition_to_path_type = {
        "noskills": "frozen",
        "withskills": "external",
        "gen": "external",
    }

    def discover_tasks(self, source: str | Path) -> list[TaskDescriptor]:
        registry_path = Path(source)
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        tasks: list[TaskDescriptor] = []
        for item in payload:
            tasks.append(
                TaskDescriptor(
                    benchmark_name=self.benchmark_name,
                    task_id=item["title"],
                    source_path=item["path"],
                    title=item["title"],
                    category=item.get("category"),
                    difficulty=item.get("difficulty"),
                    metadata={
                        "tags": item.get("tags", []),
                        "author_name": item.get("author_name"),
                        "version": item.get("version"),
                        "updated_at": item.get("updatedAt"),
                    },
                )
            )
        return tasks

    def resolve_task_path(self, repo_root: str | Path, task: TaskDescriptor) -> Path:
        return Path(repo_root) / task.source_path

    def build_harbor_command(
        self,
        *,
        repo_root: str | Path,
        task: TaskDescriptor,
        agent: str,
        model: str | None = None,
        harbor_bin: str = "harbor",
        extra_args: list[str] | None = None,
    ) -> list[str]:
        command = [
            harbor_bin,
            "run",
            "-p",
            str(self.resolve_task_path(repo_root, task)),
            "-a",
            agent,
        ]
        if model:
            command.extend(["-m", model])
        if extra_args:
            command.extend(extra_args)
        return command

    def filter_tasks(
        self,
        tasks: list[TaskDescriptor],
        *,
        categories: set[str] | None = None,
        difficulties: set[str] | None = None,
    ) -> list[TaskDescriptor]:
        filtered = tasks
        if categories:
            filtered = [task for task in filtered if task.category in categories]
        if difficulties:
            filtered = [task for task in filtered if task.difficulty in difficulties]
        return filtered

    def default_registry_path(self, repo_root: str | Path) -> Path:
        return Path(repo_root) / "website" / "src" / "data" / "tasks-registry.json"

    def build_registry_index(self, source: str | Path) -> dict[str, TaskDescriptor]:
        return {
            task.task_id: task
            for task in self.discover_tasks(source)
        }

    def parse_result_file(
        self,
        source: str | Path,
        *,
        benchmark_split: str,
        phase: str,
        seed: int,
        path_type: str | None = None,
        registry_source: str | Path | None = None,
        model_name: str | None = None,
        agent_name: str | None = None,
        agent_version: str = "upstream-import",
        benchmark_version: str = "skillsbench-upstream",
        conditions: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            if "trajectories" in payload:
                payload = payload["trajectories"]
            elif "items" in payload:
                payload = payload["items"]
            else:
                raise ValueError("Unsupported SkillsBench result payload shape")
        if not isinstance(payload, list):
            raise ValueError("SkillsBench result payload must be a list")

        registry_index = self.build_registry_index(registry_source) if registry_source else {}
        attempt_counters: dict[tuple[str, str, str, str], int] = {}
        runs: list[dict[str, Any]] = []

        for item in payload:
            condition = str(item.get("condition", "unknown"))
            if conditions and condition not in conditions:
                continue

            task_name = str(item["taskName"])
            row_model_name = model_name or str(item.get("model") or "unknown-model")
            row_agent_name = agent_name or str(item.get("harness") or "skillsbench-harness")
            row_path_type = path_type or self.infer_path_type(condition)
            attempt_key = (task_name, condition, row_model_name, row_agent_name)
            attempt_index = attempt_counters.get(attempt_key, 0)
            attempt_counters[attempt_key] = attempt_index + 1

            registry_task = registry_index.get(task_name)
            verifier = item.get("verifier") or {}
            tests_total = int(verifier.get("tests") or 0)
            tests_passed = int(verifier.get("passed") or 0)
            tests_failed = int(verifier.get("failed") or 0)
            result_label = str(item.get("result") or "unknown")
            success = result_label.lower() == "pass"
            score = self._score_from_verifier(
                tests_total=tests_total,
                tests_passed=tests_passed,
                success=success,
            )

            steps = item.get("steps") or []
            started_at, finished_at = self._resolve_time_bounds(steps=steps, duration_seconds=float(item.get("duration") or 0.0))
            token_input, token_output, token_total = self._resolve_token_counts(item.get("tokens") or {})

            run_id = (
                f"skillsbench::{benchmark_split}::{phase}::{condition}::{seed}::"
                f"{row_agent_name}::{row_model_name}::{task_name}::{attempt_index}"
            )
            run_record: dict[str, Any] = {
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
                "task_id": task_name,
                "attempt_index": attempt_index,
                "score": score,
                "success": success,
                "token_input": token_input,
                "token_output": token_output,
                "token_total": token_total,
                "tool_calls_total": sum(1 for step in steps if step.get("type") == "tool_call"),
                "memory_reads": 0,
                "memory_writes": 0,
                "wall_clock_seconds": float(item.get("duration") or 0.0),
                "cost_usd": 0.0,
                "human_interventions": 0,
                "seed": seed,
                "started_at": started_at,
                "finished_at": finished_at,
                "metadata": {
                    "condition": condition,
                    "family": item.get("family"),
                    "harness": item.get("harness"),
                    "result_label": result_label,
                    "verifier": {
                        "tests": tests_total,
                        "passed": tests_passed,
                        "failed": tests_failed,
                    },
                    "steps_total": len(steps),
                    "source_file": str(source),
                },
            }
            if registry_task:
                run_record["task_template_id"] = str(registry_task.metadata.get("version") or "")
                run_record["metadata"].update(
                    {
                        "category": registry_task.category,
                        "difficulty": registry_task.difficulty,
                        "task_source_path": registry_task.source_path,
                        "task_tags": registry_task.metadata.get("tags", []),
                        "task_author_name": registry_task.metadata.get("author_name"),
                        "task_updated_at": registry_task.metadata.get("updated_at"),
                    }
                )
            runs.append(run_record)

        return runs

    def infer_path_type(self, condition: str) -> str:
        normalized = condition.strip().lower()
        try:
            return self.condition_to_path_type[normalized]
        except KeyError as exc:
            raise ValueError(f"Unsupported SkillsBench condition for path type inference: {condition}") from exc

    def _score_from_verifier(self, *, tests_total: int, tests_passed: int, success: bool) -> float:
        if tests_total > 0:
            return max(0.0, min(1.0, tests_passed / tests_total))
        return 1.0 if success else 0.0

    def _resolve_time_bounds(self, *, steps: list[dict[str, Any]], duration_seconds: float) -> tuple[str, str]:
        timestamps = [
            parsed
            for parsed in (self._parse_timestamp(step.get("timestamp")) for step in steps)
            if parsed is not None
        ]
        if timestamps:
            started = timestamps[0]
            finished = timestamps[-1]
            if finished < started:
                finished = started
            return self._format_timestamp(started), self._format_timestamp(finished)

        started = datetime(1970, 1, 1, tzinfo=UTC)
        finished = started + timedelta(seconds=max(0.0, duration_seconds))
        return self._format_timestamp(started), self._format_timestamp(finished)

    def _resolve_token_counts(self, payload: dict[str, Any]) -> tuple[int, int, int]:
        token_input = int(payload.get("input") or 0)
        token_output = int(payload.get("output") or 0)
        token_total = int(payload.get("total") or (token_input + token_output))
        return token_input, token_output, token_total

    def _parse_timestamp(self, raw: Any) -> datetime | None:
        if not raw:
            return None
        timestamp = str(raw)
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            return None

    def _format_timestamp(self, value: datetime) -> str:
        return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
