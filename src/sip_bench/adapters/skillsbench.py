from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sip_bench.adapters.base import BenchmarkAdapter, TaskDescriptor


class SkillsBenchAdapter(BenchmarkAdapter):
    benchmark_name = "skillsbench"

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
