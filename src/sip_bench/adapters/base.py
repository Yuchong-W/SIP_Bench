from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskDescriptor:
    benchmark_name: str
    task_id: str
    source_path: str
    title: str
    category: str | None = None
    difficulty: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_name": self.benchmark_name,
            "task_id": self.task_id,
            "source_path": self.source_path,
            "title": self.title,
            "category": self.category,
            "difficulty": self.difficulty,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SplitManifest:
    replay: list[TaskDescriptor]
    adapt: list[TaskDescriptor]
    heldout: list[TaskDescriptor]
    drift: list[TaskDescriptor] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "replay": len(self.replay),
            "adapt": len(self.adapt),
            "heldout": len(self.heldout),
            "drift": len(self.drift),
        }

    def all_task_ids(self) -> set[str]:
        task_ids: set[str] = set()
        for bucket in (self.replay, self.adapt, self.heldout, self.drift):
            for task in bucket:
                task_ids.add(task.task_id)
        return task_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": self.counts(),
            "replay": [task.to_dict() for task in self.replay],
            "adapt": [task.to_dict() for task in self.adapt],
            "heldout": [task.to_dict() for task in self.heldout],
            "drift": [task.to_dict() for task in self.drift],
        }


class BenchmarkAdapter(ABC):
    benchmark_name: str

    @abstractmethod
    def discover_tasks(self, source: str | Path) -> list[TaskDescriptor]:
        raise NotImplementedError

    def build_manifest(
        self,
        tasks: list[TaskDescriptor],
        *,
        replay_count: int,
        adapt_count: int,
        heldout_count: int,
        drift_count: int = 0,
        seed: int = 0,
    ) -> SplitManifest:
        required = replay_count + adapt_count + heldout_count + drift_count
        if required <= 0:
            raise ValueError("At least one task must be requested")
        if len(tasks) < required:
            raise ValueError(
                f"Requested {required} tasks but only {len(tasks)} are available"
            )

        rng = random.Random(seed)
        shuffled = list(tasks)
        rng.shuffle(shuffled)

        replay_end = replay_count
        adapt_end = replay_end + adapt_count
        heldout_end = adapt_end + heldout_count
        drift_end = heldout_end + drift_count

        return SplitManifest(
            replay=shuffled[:replay_end],
            adapt=shuffled[replay_end:adapt_end],
            heldout=shuffled[adapt_end:heldout_end],
            drift=shuffled[heldout_end:drift_end],
        )

    def validate_manifest(self, manifest: SplitManifest) -> None:
        overlap = _intersections(
            replay=manifest.replay,
            adapt=manifest.adapt,
            heldout=manifest.heldout,
            drift=manifest.drift,
        )
        if overlap:
            raise ValueError(f"Manifest contains overlapping task ids: {sorted(overlap)}")


def _intersections(**buckets: list[TaskDescriptor]) -> set[str]:
    seen: set[str] = set()
    overlap: set[str] = set()
    for tasks in buckets.values():
        for task in tasks:
            if task.task_id in seen:
                overlap.add(task.task_id)
            seen.add(task.task_id)
    return overlap
