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
        task_ids: set[str] | None = None,
    ) -> list[TaskDescriptor]:
        filtered = tasks
        if categories:
            filtered = [task for task in filtered if task.category in categories]
        if difficulties:
            filtered = [task for task in filtered if task.difficulty in difficulties]
        if task_ids:
            filtered = [task for task in filtered if task.task_id in task_ids]
            found = {task.task_id for task in filtered}
            missing = sorted(task_ids - found)
            if missing:
                raise ValueError(
                    f"Requested SkillsBench task ids are not available after filtering: {missing}"
                )
        return filtered

    def default_registry_path(self, repo_root: str | Path) -> Path:
        return Path(repo_root) / "website" / "src" / "data" / "tasks-registry.json"

    def build_registry_index(self, source: str | Path) -> dict[str, TaskDescriptor]:
        return {task.task_id: task for task in self.discover_tasks(source)}

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
            started_at, finished_at = self._resolve_time_bounds(
                steps=steps,
                duration_seconds=float(item.get("duration") or 0.0),
            )
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
                task_version = registry_task.metadata.get("version")
                if task_version is not None:
                    run_record["task_template_id"] = str(task_version)
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

    def parse_harbor_job_dir(
        self,
        source: str | Path,
        *,
        benchmark_split: str,
        phase: str,
        path_type: str,
        seed: int,
        registry_source: str | Path | None = None,
        model_name: str | None = None,
        agent_name: str | None = None,
        agent_version: str = "harbor-job-import",
        benchmark_version: str = "skillsbench-upstream",
    ) -> list[dict[str, Any]]:
        job_dir = Path(source)
        trial_files = sorted(path for path in job_dir.glob("*/result.json") if path.is_file())
        if not trial_files:
            raise ValueError(f"No trial result.json files found under {job_dir}")

        registry_index = self.build_registry_index(registry_source) if registry_source else {}
        attempt_counters: dict[tuple[str, str, str, str], int] = {}
        runs: list[dict[str, Any]] = []

        for result_path in trial_files:
            item = json.loads(result_path.read_text(encoding="utf-8"))
            config = item.get("config") or {}
            config_agent = config.get("agent") or {}
            config_environment = config.get("environment") or {}
            task_path = str((config.get("task") or {}).get("path") or "")
            task_name = str(item.get("task_name") or Path(task_path).name or "unknown-task")
            registry_task = registry_index.get(task_name)

            agent_info = item.get("agent_info") or {}
            model_info = agent_info.get("model_info") or {}
            row_agent_name = agent_name or str(agent_info.get("name") or config_agent.get("name") or "harbor-agent")
            row_model_name = model_name or str(model_info.get("name") or config_agent.get("model_name") or row_agent_name)

            attempt_key = (task_name, row_model_name, row_agent_name, path_type)
            attempt_index = attempt_counters.get(attempt_key, 0)
            attempt_counters[attempt_key] = attempt_index + 1

            verifier_result = item.get("verifier_result") or {}
            rewards = verifier_result.get("rewards") or {}
            exception_info = item.get("exception_info") or {}
            success, score, score_source = self._resolve_harbor_outcome(
                rewards=rewards,
                exception_info=exception_info,
            )
            started_at, finished_at, wall_clock_seconds = self._resolve_explicit_bounds(
                started_at_raw=item.get("started_at"),
                finished_at_raw=item.get("finished_at"),
            )
            agent_result = item.get("agent_result") or {}
            token_input, token_output, token_total, cost_usd = self._resolve_agent_usage(agent_result)
            tool_calls_total = self._resolve_harbor_tool_calls(agent_result)

            metadata: dict[str, Any] = {
                "source_format": "harbor_job",
                "job_dir": str(job_dir),
                "source_file": str(result_path),
                "trial_name": item.get("trial_name"),
                "trial_uri": item.get("trial_uri"),
                "task_checksum": item.get("task_checksum"),
                "task_source_path": task_path or None,
                "environment_type": config_environment.get("type"),
                "job_id": config.get("job_id"),
                "rewards": rewards,
                "score_source": score_source,
                "exception_type": exception_info.get("exception_type"),
                "exception_message": exception_info.get("exception_message"),
            }
            if agent_result:
                metadata["agent_metadata_keys"] = sorted((agent_result.get("metadata") or {}).keys())
                metadata["cache_tokens"] = self._coerce_int(agent_result.get("n_cache_tokens"))
            if registry_task:
                task_version = registry_task.metadata.get("version")
                if task_version is not None:
                    metadata["task_version"] = task_version
                metadata.update(
                    {
                        "category": registry_task.category,
                        "difficulty": registry_task.difficulty,
                        "task_source_path": registry_task.source_path,
                        "task_tags": registry_task.metadata.get("tags", []),
                        "task_author_name": registry_task.metadata.get("author_name"),
                        "task_updated_at": registry_task.metadata.get("updated_at"),
                    }
                )

            run_id = (
                f"skillsbench::harbor::{benchmark_split}::{phase}::{path_type}::{seed}::"
                f"{row_agent_name}::{row_model_name}::{task_name}::{attempt_index}"
            )
            run_record: dict[str, Any] = {
                "schema_version": "0.1.0",
                "run_id": run_id,
                "benchmark_name": self.benchmark_name,
                "benchmark_version": benchmark_version,
                "benchmark_split": benchmark_split,
                "phase": phase,
                "path_type": path_type,
                "model_name": row_model_name,
                "agent_name": row_agent_name,
                "agent_version": agent_version or str(agent_info.get("version") or "harbor-job-import"),
                "task_id": task_name,
                "attempt_index": attempt_index,
                "score": score,
                "success": success,
                "token_input": token_input,
                "token_output": token_output,
                "token_total": token_total,
                "tool_calls_total": tool_calls_total,
                "memory_reads": 0,
                "memory_writes": 0,
                "wall_clock_seconds": wall_clock_seconds,
                "cost_usd": cost_usd,
                "human_interventions": 0,
                "seed": seed,
                "started_at": started_at,
                "finished_at": finished_at,
                "metadata": metadata,
            }
            if registry_task and registry_task.metadata.get("version") is not None:
                run_record["task_template_id"] = str(registry_task.metadata["version"])
            runs.append(run_record)

        return runs

    def infer_path_type(self, condition: str) -> str:
        normalized = condition.strip().lower()
        try:
            return self.condition_to_path_type[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported SkillsBench condition for path type inference: {condition}"
            ) from exc

    def _score_from_verifier(self, *, tests_total: int, tests_passed: int, success: bool) -> float:
        if tests_total > 0:
            return max(0.0, min(1.0, tests_passed / tests_total))
        return 1.0 if success else 0.0

    def _resolve_harbor_outcome(
        self,
        *,
        rewards: dict[str, Any],
        exception_info: dict[str, Any],
    ) -> tuple[bool, float, str]:
        reward_value = self._reward_value(rewards)
        if reward_value is not None:
            score = max(0.0, reward_value)
            return (not bool(exception_info)) and score > 0.0, score, "verifier_rewards"
        success = not bool(exception_info)
        return success, (1.0 if success else 0.0), "exception_fallback"

    def _reward_value(self, rewards: dict[str, Any]) -> float | None:
        if not rewards:
            return None
        if "reward" in rewards:
            return self._coerce_float(rewards.get("reward"))
        numeric_values = [
            value
            for value in (self._coerce_float(raw_value) for raw_value in rewards.values())
            if value is not None
        ]
        if not numeric_values:
            return None
        return sum(numeric_values) / len(numeric_values)

    def _resolve_harbor_tool_calls(self, agent_result: dict[str, Any]) -> int:
        metadata = agent_result.get("metadata") or {}
        for key in ("tool_calls_total", "n_tool_calls", "tool_call_count"):
            coerced = self._coerce_int(metadata.get(key))
            if coerced is not None:
                return coerced
        tool_calls = metadata.get("tool_calls")
        if isinstance(tool_calls, list):
            return len(tool_calls)
        return 0

    def _resolve_explicit_bounds(
        self,
        *,
        started_at_raw: Any,
        finished_at_raw: Any,
    ) -> tuple[str, str, float]:
        started = self._parse_timestamp(started_at_raw) or datetime(1970, 1, 1, tzinfo=UTC)
        finished = self._parse_timestamp(finished_at_raw) or started
        if finished < started:
            finished = started
        duration_seconds = (finished - started).total_seconds()
        return self._format_timestamp(started), self._format_timestamp(finished), duration_seconds

    def _resolve_agent_usage(self, agent_result: dict[str, Any]) -> tuple[int, int, int, float]:
        token_input = self._coerce_int(agent_result.get("n_input_tokens")) or 0
        token_output = self._coerce_int(agent_result.get("n_output_tokens")) or 0
        token_total = token_input + token_output
        cost_usd = self._coerce_float(agent_result.get("cost_usd")) or 0.0
        return token_input, token_output, token_total, cost_usd

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

    def _coerce_int(self, raw: Any) -> int | None:
        if raw is None or raw == "":
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def _coerce_float(self, raw: Any) -> float | None:
        if raw is None or raw == "":
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
