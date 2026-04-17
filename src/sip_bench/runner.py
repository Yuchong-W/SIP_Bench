from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from sip_bench.adapters import SkillsBenchAdapter, TauBenchAdapter
from sip_bench.metrics import write_jsonl


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_skillsbench_plan(
    *,
    registry_path: str | Path,
    repo_root: str | Path,
    replay_count: int,
    adapt_count: int,
    heldout_count: int,
    drift_count: int = 0,
    seed: int = 0,
    agent: str = "oracle",
    model: str | None = None,
    harbor_bin: str = "harbor",
    categories: set[str] | None = None,
    difficulties: set[str] | None = None,
    task_ids: set[str] | None = None,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    adapter = SkillsBenchAdapter()
    tasks = adapter.discover_tasks(registry_path)
    filtered_tasks = adapter.filter_tasks(
        tasks,
        categories=categories,
        difficulties=difficulties,
        task_ids=task_ids,
    )
    manifest = adapter.build_manifest(
        filtered_tasks,
        replay_count=replay_count,
        adapt_count=adapt_count,
        heldout_count=heldout_count,
        drift_count=drift_count,
        seed=seed,
    )
    adapter.validate_manifest(manifest)

    commands: dict[str, list[list[str]]] = {}
    for split_name in ("replay", "adapt", "heldout", "drift"):
        tasks_for_split = getattr(manifest, split_name)
        commands[split_name] = [
            adapter.build_harbor_command(
                repo_root=repo_root,
                task=task,
                agent=agent,
                model=model,
                harbor_bin=harbor_bin,
                extra_args=extra_args,
            )
            for task in tasks_for_split
        ]

    return {
        "benchmark_name": adapter.benchmark_name,
        "registry_path": str(registry_path),
        "repo_root": str(repo_root),
        "selection": {
            "total_tasks": len(tasks),
            "filtered_tasks": len(filtered_tasks),
            "categories": sorted(categories) if categories else [],
            "difficulties": sorted(difficulties) if difficulties else [],
            "task_ids": sorted(task_ids) if task_ids else [],
            "seed": seed,
        },
        "execution": {
            "agent": agent,
            "model": model,
            "harbor_bin": harbor_bin,
            "extra_args": extra_args or [],
        },
        "manifest": manifest.to_dict(),
        "commands": commands,
    }


def hydrate_skillsbench_checkout(
    *,
    plan_source: str | Path,
    repo_root: str | Path,
    out: str | Path,
    split: str = "all",
    git_bin: str = "git",
    include_registry: bool = True,
) -> dict[str, Any]:
    plan = load_json(plan_source)
    if plan.get("benchmark_name") != "skillsbench":
        raise ValueError("hydrate_skillsbench_checkout expects a SkillsBench plan")

    selected_splits = _select_splits_from_manifest(plan["manifest"], split)
    task_records = _unique_manifest_tasks(plan["manifest"], selected_splits)
    if not task_records:
        raise ValueError("No SkillsBench tasks were selected for hydration")

    patterns: list[str] = []
    if include_registry:
        patterns.append("website/src/data")
    patterns.extend(sorted({str(task["source_path"]).replace("\\", "/") for task in task_records}))

    before_patterns = _read_sparse_patterns(repo_root=repo_root, git_bin=git_bin)
    command = [git_bin, "-C", str(repo_root), "sparse-checkout", "add", *patterns]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    after_patterns = _read_sparse_patterns(repo_root=repo_root, git_bin=git_bin)
    report = {
        "schema_version": "0.1.0",
        "action": "skillsbench_hydration",
        "plan_source": str(plan_source),
        "repo_root": str(repo_root),
        "split": split,
        "selected_splits": selected_splits,
        "git_bin": git_bin,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "before_patterns": before_patterns,
        "after_patterns": after_patterns,
        "hydrated_paths": patterns,
        "tasks": [
            {
                "task_id": task["task_id"],
                "title": task.get("title"),
                "source_path": task["source_path"],
                "exists": (Path(repo_root) / task["source_path"]).exists(),
            }
            for task in task_records
        ],
        "generated_at": _now_utc(),
    }
    write_json(out, report)
    if completed.returncode != 0:
        raise RuntimeError(
            f"SkillsBench sparse hydration failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )
    return report


def import_tau_results(
    *,
    source: str | Path,
    out: str | Path,
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
    adapter = TauBenchAdapter()
    runs = adapter.parse_result_file(
        source,
        env=env,
        task_split=task_split,
        benchmark_split=benchmark_split,
        phase=phase,
        path_type=path_type,
        model_name=model_name,
        agent_name=agent_name,
        agent_version=agent_version,
        seed=seed,
        benchmark_version=benchmark_version,
        task_ids=task_ids,
    )
    write_jsonl(out, runs)
    return runs


def tau_bench_preflight(
    *,
    repo_root: str | Path,
    python_bin: str = "python",
    model_provider: str,
    user_model_provider: str,
    env_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    repo_path = Path(repo_root)
    resolved_env = _merge_env(env_overrides)
    dependency_command = [
        python_bin,
        "-c",
        (
            "import sys; "
            f"sys.path.insert(0, r'{repo_path}'); "
            "import litellm; import openai; print('tau_preflight_import_ok')"
        ),
    ]
    dependency_check = subprocess.run(
        dependency_command,
        capture_output=True,
        text=True,
        check=False,
        env=resolved_env,
    )
    required_env_vars = sorted(
        {
            env_var
            for env_var in (
                _provider_env_var(model_provider),
                _provider_env_var(user_model_provider),
            )
            if env_var is not None
        }
    )
    env_status = {env_var: bool(resolved_env.get(env_var)) for env_var in required_env_vars}
    return {
        "schema_version": "0.1.0",
        "action": "tau_bench_preflight",
        "repo_root": str(repo_path),
        "python_bin": python_bin,
        "env_override_keys": sorted(env_overrides.keys()) if env_overrides else [],
        "dependency_command": dependency_command,
        "dependency_returncode": dependency_check.returncode,
        "dependency_stdout": dependency_check.stdout,
        "dependency_stderr": dependency_check.stderr,
        "required_env_vars": required_env_vars,
        "env_status": env_status,
        "ready": dependency_check.returncode == 0 and all(env_status.values()),
        "generated_at": _now_utc(),
    }


def import_skillsbench_results(
    *,
    source: str | Path,
    out: str | Path,
    benchmark_split: str,
    phase: str,
    seed: int,
    registry_source: str | Path | None = None,
    repo_root: str | Path | None = None,
    path_type: str | None = None,
    model_name: str | None = None,
    agent_name: str | None = None,
    agent_version: str = "upstream-import",
    benchmark_version: str | None = None,
    conditions: set[str] | None = None,
) -> list[dict[str, Any]]:
    adapter = SkillsBenchAdapter()
    resolved_registry_source = registry_source
    if resolved_registry_source is None and repo_root is not None:
        resolved_registry_source = adapter.default_registry_path(repo_root)

    resolved_benchmark_version = benchmark_version
    if resolved_benchmark_version is None:
        resolved_benchmark_version = _resolve_git_revision(repo_root) if repo_root else None
    if resolved_benchmark_version is None:
        resolved_benchmark_version = "skillsbench-upstream"

    runs = adapter.parse_result_file(
        source,
        benchmark_split=benchmark_split,
        phase=phase,
        seed=seed,
        path_type=path_type,
        registry_source=resolved_registry_source,
        model_name=model_name,
        agent_name=agent_name,
        agent_version=agent_version,
        benchmark_version=resolved_benchmark_version,
        conditions=conditions,
    )
    write_jsonl(out, runs)
    return runs


def import_skillsbench_job(
    *,
    source: str | Path,
    out: str | Path,
    benchmark_split: str,
    phase: str,
    path_type: str,
    seed: int,
    registry_source: str | Path | None = None,
    repo_root: str | Path | None = None,
    model_name: str | None = None,
    agent_name: str | None = None,
    agent_version: str = "harbor-job-import",
    benchmark_version: str | None = None,
) -> list[dict[str, Any]]:
    adapter = SkillsBenchAdapter()
    resolved_registry_source = registry_source
    if resolved_registry_source is None and repo_root is not None:
        resolved_registry_source = adapter.default_registry_path(repo_root)

    resolved_benchmark_version = benchmark_version
    if resolved_benchmark_version is None:
        resolved_benchmark_version = _resolve_git_revision(repo_root) if repo_root else None
    if resolved_benchmark_version is None:
        resolved_benchmark_version = "skillsbench-upstream"

    runs = adapter.parse_harbor_job_dir(
        source,
        benchmark_split=benchmark_split,
        phase=phase,
        path_type=path_type,
        seed=seed,
        registry_source=resolved_registry_source,
        model_name=model_name,
        agent_name=agent_name,
        agent_version=agent_version,
        benchmark_version=resolved_benchmark_version,
    )
    write_jsonl(out, runs)
    return runs


def execute_command_plan(
    *,
    plan_source: str | Path,
    out: str | Path,
    split: str = "all",
    mode: str = "mock",
    artifacts_dir: str | Path | None = None,
    fail_fast: bool = False,
    cwd: str | Path | None = None,
    max_tasks: int | None = None,
    env_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    if mode not in {"mock", "subprocess"}:
        raise ValueError(f"Unsupported mode: {mode}")

    plan = load_json(plan_source)
    selected_splits = _select_splits(plan, split)
    output_path = Path(out)
    artifacts_root = Path(artifacts_dir) if artifacts_dir else output_path.parent / "artifacts"
    execution_root = Path(cwd) if cwd else None
    resolved_env = _merge_env(env_overrides)

    records: list[dict[str, Any]] = []
    executed = 0
    halted = False

    for split_name in selected_splits:
        tasks = plan["manifest"][split_name]
        commands = plan["commands"][split_name]
        if len(tasks) != len(commands):
            raise ValueError(
                f"Split {split_name} has {len(tasks)} tasks but {len(commands)} commands"
            )
        for index, (task, command) in enumerate(zip(tasks, commands)):
            if max_tasks is not None and executed >= max_tasks:
                halted = True
                break
            record = _execute_one(
                split_name=split_name,
                index=index,
                task=task,
                command=command,
                mode=mode,
                artifacts_root=artifacts_root,
                cwd=execution_root,
                env=resolved_env,
            )
            records.append(record)
            executed += 1
            if fail_fast and record["status"] != "success":
                halted = True
                break
        if halted:
            break

    report = {
        "schema_version": "0.1.0",
        "plan_source": str(plan_source),
        "benchmark_name": plan["benchmark_name"],
        "mode": mode,
        "split": split,
        "cwd": str(execution_root) if execution_root else None,
        "artifacts_dir": str(artifacts_root),
        "env_override_keys": sorted(env_overrides.keys()) if env_overrides else [],
        "summary": _summarize_execution(records, halted=halted),
        "records": records,
        "generated_at": _now_utc(),
    }
    write_json(out, report)
    return report


def _select_splits(plan: dict[str, Any], split: str) -> list[str]:
    available = ["replay", "adapt", "heldout", "drift"]
    if split == "all":
        return [name for name in available if plan["commands"].get(name)]
    if split not in available:
        raise ValueError(f"Unknown split: {split}")
    return [split]


def _select_splits_from_manifest(manifest: dict[str, Any], split: str) -> list[str]:
    available = ["replay", "adapt", "heldout", "drift"]
    if split == "all":
        return [name for name in available if manifest.get(name)]
    if split not in available:
        raise ValueError(f"Unknown split: {split}")
    return [split]


def _unique_manifest_tasks(manifest: dict[str, Any], splits: list[str]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for split_name in splits:
        for task in manifest.get(split_name, []):
            task_id = str(task["task_id"])
            if task_id in seen:
                continue
            seen.add(task_id)
            unique.append(task)
    return unique


def _execute_one(
    *,
    split_name: str,
    index: int,
    task: dict[str, Any],
    command: list[str],
    mode: str,
    artifacts_root: Path,
    cwd: Path | None,
    env: dict[str, str] | None,
) -> dict[str, Any]:
    task_stub = _safe_slug(task["task_id"])
    task_dir = artifacts_root / split_name / f"{index:03d}_{task_stub}"
    task_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = task_dir / "stdout.txt"
    stderr_path = task_dir / "stderr.txt"

    started_at = _now_utc()
    start_time = perf_counter()
    if mode == "mock":
        stdout_path.write_text(
            "MOCK EXECUTION\n" + " ".join(command) + "\n",
            encoding="utf-8",
        )
        stderr_path.write_text("", encoding="utf-8")
        finished_at = _now_utc()
        duration_seconds = perf_counter() - start_time
        return {
            "split": split_name,
            "task_id": task["task_id"],
            "task_title": task["title"],
            "command": command,
            "mode": mode,
            "status": "success",
            "exit_code": 0,
            "duration_seconds": duration_seconds,
            "started_at": started_at,
            "finished_at": finished_at,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "error": None,
        }

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=False,
            check=False,
            env=env,
        )
        stdout_text = completed.stdout.decode("utf-8", errors="replace") if completed.stdout is not None else ""
        stderr_text = completed.stderr.decode("utf-8", errors="replace") if completed.stderr is not None else ""
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")
        finished_at = _now_utc()
        duration_seconds = perf_counter() - start_time
        return {
            "split": split_name,
            "task_id": task["task_id"],
            "task_title": task["title"],
            "command": command,
            "mode": mode,
            "status": "success" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "duration_seconds": duration_seconds,
            "started_at": started_at,
            "finished_at": finished_at,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "error": None,
        }
    except FileNotFoundError as exc:
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(str(exc), encoding="utf-8")
        finished_at = _now_utc()
        duration_seconds = perf_counter() - start_time
        return {
            "split": split_name,
            "task_id": task["task_id"],
            "task_title": task["title"],
            "command": command,
            "mode": mode,
            "status": "missing_executable",
            "exit_code": None,
            "duration_seconds": duration_seconds,
            "started_at": started_at,
            "finished_at": finished_at,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "error": str(exc),
        }


def _summarize_execution(records: list[dict[str, Any]], *, halted: bool) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for record in records:
        status = record["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "executed": len(records),
        "status_counts": status_counts,
        "halted_early": halted,
    }


def _safe_slug(value: str) -> str:
    return "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in value
    )


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _provider_env_var(provider: str | None) -> str | None:
    if provider is None:
        return None
    normalized = provider.lower()
    mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "anyscale": "ANYSCALE_API_KEY",
    }
    return mapping.get(normalized)


def load_env_file(path: str | Path) -> dict[str, str]:
    env_path = Path(path)
    entries: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        entries[key] = value
    return entries


def _merge_env(env_overrides: dict[str, str] | None = None) -> dict[str, str]:
    merged = dict(os.environ)
    if env_overrides:
        merged.update(env_overrides)
    return merged


def _resolve_git_revision(repo_root: str | Path | None) -> str | None:
    if repo_root is None:
        return None
    candidate = Path(repo_root)
    if not candidate.exists():
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    revision = completed.stdout.strip()
    return revision or None


def _read_sparse_patterns(*, repo_root: str | Path, git_bin: str = "git") -> list[str]:
    try:
        completed = subprocess.run(
            [git_bin, "-C", str(repo_root), "sparse-checkout", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]
