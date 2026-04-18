from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load_registry(registry_path: Path) -> list[dict]:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("SkillsBench registry must be a list of task records")
    return data


def build_report(*, registry_path: Path, repo_root: Path) -> dict:
    registry = load_registry(registry_path)
    tasks_root = repo_root / "tasks"
    local_task_ids = sorted(path.name for path in tasks_root.iterdir() if path.is_dir())

    records = []
    for task in registry:
        task_id = str(task["path"]).split("/")[-1]
        records.append(
            {
                "task_id": task_id,
                "title": task.get("title"),
                "difficulty": task.get("difficulty"),
                "category": task.get("category"),
                "locally_available": task_id in local_task_ids,
            }
        )

    available_records = [record for record in records if record["locally_available"]]
    available_by_difficulty = Counter(record["difficulty"] for record in available_records)
    available_by_category = Counter(record["category"] for record in available_records)

    return {
        "registry_path": str(registry_path),
        "repo_root": str(repo_root),
        "total_registry_tasks": len(records),
        "locally_available_tasks": len(available_records),
        "available_by_difficulty": dict(sorted(available_by_difficulty.items())),
        "available_by_category": dict(sorted(available_by_category.items())),
        "available_tasks": available_records,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# SkillsBench Local Availability Snapshot",
        "",
        f"- Registry tasks: `{report['total_registry_tasks']}`",
        f"- Locally available tasks: `{report['locally_available_tasks']}`",
        "",
        "## Available By Difficulty",
        "",
        "| Difficulty | Count |",
        "| --- | ---: |",
    ]
    for difficulty, count in report["available_by_difficulty"].items():
        lines.append(f"| `{difficulty}` | `{count}` |")
    lines.extend(
        [
            "",
            "## Available Tasks",
            "",
            "| Task | Difficulty | Category |",
            "| --- | --- | --- |",
        ]
    )
    for record in report["available_tasks"]:
        lines.append(
            f"| `{record['task_id']}` | `{record['difficulty']}` | `{record['category']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit locally available SkillsBench tasks against the registry.")
    parser.add_argument(
        "--registry",
        default="benchmarks/skillsbench/website/src/data/tasks-registry.json",
        help="Path to the SkillsBench task registry JSON.",
    )
    parser.add_argument(
        "--repo-root",
        default="benchmarks/skillsbench",
        help="Path to the local SkillsBench repository root.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Output format.",
    )
    args = parser.parse_args()

    report = build_report(
        registry_path=Path(args.registry),
        repo_root=Path(args.repo_root),
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
