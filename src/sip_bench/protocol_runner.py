from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from sip_bench.adapters import SkillsBenchAdapter
from sip_bench.adapters.base import SplitManifest, TaskDescriptor
from sip_bench.metrics import aggregate_runs, load_jsonl, write_jsonl
from sip_bench.runner import execute_command_plan, hydrate_skillsbench_checkout, import_skillsbench_job, write_json
from sip_bench.validation import load_schema, validate_data_file
from jsonschema import Draft202012Validator

SUITE_SCHEMA_VERSION = "0.1.0"
DEFAULT_SPLITS = ("replay", "adapt", "heldout", "drift")
DEFAULT_TASK_PREPARATION = {
    "mode": "source",
    "skill_mode": "keep",
    "patches": {},
}


def run_skillsbench_suite(
    *,
    config_path: str | Path,
    out_root: str | Path | None = None,
    execute_mode: str = "subprocess",
    aggregate: bool = True,
) -> dict[str, Any]:
    config_file = Path(config_path).resolve()
    config = load_protocol_suite_config(config_file)
    base_dir = config_file.parent

    repo_root = _resolve_path(base_dir, config["repo_root"])
    registry_path = _resolve_path(base_dir, config["registry_path"])
    suite_root = _resolve_path(base_dir, out_root) if out_root else _resolve_path(base_dir, config["out_root"])
    suite_root.mkdir(parents=True, exist_ok=True)

    execution_defaults = config["execution"]
    combined_runs: list[dict[str, Any]] = []
    run_reports: list[dict[str, Any]] = []

    for run_spec in config["runs"]:
        run_report = _run_skillsbench_spec(
            suite_name=config["suite_name"],
            base_dir=base_dir,
            suite_root=suite_root,
            repo_root=repo_root,
            registry_path=registry_path,
            execution_defaults=execution_defaults,
            run_spec=run_spec,
            execute_mode=execute_mode,
        )
        run_reports.append(run_report)
        if run_report.get("records_path"):
            combined_runs.extend(load_jsonl(run_report["records_path"]))

    combined_runs_path = suite_root / "combined_runs.jsonl"
    write_jsonl(combined_runs_path, combined_runs)

    runs_validation = validate_data_file(
        data_path=combined_runs_path,
        schema_path=Path(__file__).resolve().parents[2] / "schemas" / "runs.schema.json",
    )

    summary_path = suite_root / "summary.jsonl"
    summary_report = _aggregate_suite_records(
        records=combined_runs,
        out_path=summary_path,
        aggregate=aggregate,
    )

    report = {
        "schema_version": SUITE_SCHEMA_VERSION,
        "suite_name": config["suite_name"],
        "benchmark_name": config["benchmark_name"],
        "config_path": str(config_file),
        "out_root": str(suite_root),
        "execute_mode": execute_mode,
        "run_count": len(run_reports),
        "runs": run_reports,
        "combined_runs_path": str(combined_runs_path),
        "runs_validation": runs_validation,
        "summary": summary_report,
    }
    write_json(suite_root / "suite_report.json", report)
    return report


def build_skillsbench_explicit_plan(
    *,
    registry_path: str | Path,
    repo_root: str | Path,
    split_task_ids: dict[str, list[str]],
    agent: str = "oracle",
    model: str | None = None,
    harbor_bin: str = "harbor",
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    adapter = SkillsBenchAdapter()
    tasks = adapter.discover_tasks(registry_path)
    task_index = {task.task_id: task for task in tasks}

    manifest = SplitManifest(
        replay=_resolve_explicit_tasks(task_index=task_index, task_ids=split_task_ids.get("replay", [])),
        adapt=_resolve_explicit_tasks(task_index=task_index, task_ids=split_task_ids.get("adapt", [])),
        heldout=_resolve_explicit_tasks(task_index=task_index, task_ids=split_task_ids.get("heldout", [])),
        drift=_resolve_explicit_tasks(task_index=task_index, task_ids=split_task_ids.get("drift", [])),
    )
    adapter.validate_manifest(manifest)

    commands: dict[str, list[list[str]]] = {}
    for split_name in DEFAULT_SPLITS:
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
            "filtered_tasks": len(manifest.all_task_ids()),
            "categories": [],
            "difficulties": [],
            "task_ids": {split: split_task_ids.get(split, []) for split in DEFAULT_SPLITS},
            "seed": None,
            "selection_mode": "explicit",
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


def load_protocol_suite_config(config_path: str | Path) -> dict[str, Any]:
    config_file = Path(config_path)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "protocol_suite.schema.json"
    validator = Draft202012Validator(load_schema(schema_path))
    errors = sorted(validator.iter_errors(config), key=lambda error: list(error.absolute_path))
    if errors:
        message = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        raise ValueError(f"Invalid protocol suite config: {message}")
    return config


def _run_skillsbench_spec(
    *,
    suite_name: str,
    base_dir: Path,
    suite_root: Path,
    repo_root: Path,
    registry_path: Path,
    execution_defaults: dict[str, Any],
    run_spec: dict[str, Any],
    execute_mode: str,
) -> dict[str, Any]:
    run_name = run_spec["run_name"]
    split_name = run_spec["benchmark_split"]
    phase = run_spec["phase"]
    path_type = run_spec.get("path_type", execution_defaults["path_type"])
    seed = int(run_spec.get("seed", execution_defaults.get("seed", 0)))
    agent = run_spec.get("agent", execution_defaults["agent"])
    model = run_spec.get("model", execution_defaults.get("model"))
    harbor_bin = _resolve_command_value(base_dir, run_spec.get("harbor_bin", execution_defaults["harbor_bin"]))
    job_name = run_spec.get("job_name", f"{suite_name}-{run_name}")
    jobs_dir_value = run_spec.get("jobs_dir", execution_defaults["jobs_dir"])
    jobs_dir = _resolve_path(base_dir, jobs_dir_value)
    extra_args = [*execution_defaults.get("extra_args", []), *run_spec.get("extra_args", [])]
    agent_version = run_spec.get("agent_version", execution_defaults["agent_version"])
    agent_name = run_spec.get("agent_name")
    model_name = run_spec.get("model_name")
    task_preparation = _merge_task_preparation(
        execution_defaults.get("task_preparation"),
        run_spec.get("task_preparation"),
    )

    split_task_ids = {name: [] for name in DEFAULT_SPLITS}
    split_task_ids[split_name] = list(run_spec["task_ids"])

    plan_path = suite_root / "plans" / f"{run_name}.json"
    hydration_path = suite_root / "hydration" / f"{run_name}.json"
    preparation_path = suite_root / "preparation" / f"{run_name}.json"
    execution_path = suite_root / "execution" / f"{run_name}.json"
    records_path = suite_root / "runs" / f"{run_name}.jsonl"

    source_job_dir_value = run_spec.get("source_job_dir")
    hydration_report: dict[str, Any] | None = None
    preparation_report: dict[str, Any] | None = None
    job_dir = _resolve_path(base_dir, source_job_dir_value) if source_job_dir_value else jobs_dir / job_name
    execution_report: dict[str, Any] | None = None

    if source_job_dir_value:
        execution_repo_root = repo_root
        hydration_report = {
            "schema_version": SUITE_SCHEMA_VERSION,
            "action": "skipped_hydration",
            "reason": "import-only run",
            "hydrated_paths": [],
        }
        plan_payload = build_skillsbench_explicit_plan(
            registry_path=registry_path,
            repo_root=execution_repo_root,
            split_task_ids=split_task_ids,
            agent=agent,
            model=model,
            harbor_bin=harbor_bin,
            extra_args=[
                "--jobs-dir",
                str(jobs_dir),
                "--job-name",
                job_name,
                *extra_args,
            ],
        )
    else:
        source_plan_payload = build_skillsbench_explicit_plan(
            registry_path=registry_path,
            repo_root=repo_root,
            split_task_ids=split_task_ids,
            agent=agent,
            model=model,
            harbor_bin=harbor_bin,
            extra_args=[
                "--jobs-dir",
                str(jobs_dir),
                "--job-name",
                job_name,
                *extra_args,
            ],
        )
        source_plan_path = suite_root / "plans" / f"{run_name}.source.json"
        write_json(source_plan_path, source_plan_payload)
        hydration_report = hydrate_skillsbench_checkout(
            plan_source=source_plan_path,
            repo_root=repo_root,
            out=hydration_path,
            split=split_name,
        )
        execution_repo_root = repo_root
        if task_preparation["mode"] == "copy":
            execution_repo_root = suite_root / "prepared" / run_name
            preparation_report = prepare_skillsbench_tasks(
                source_repo_root=repo_root,
                registry_path=registry_path,
                split_task_ids=split_task_ids,
                prepared_root=execution_repo_root,
                skill_mode=task_preparation["skill_mode"],
                patches=task_preparation["patches"],
            )
            write_json(preparation_path, preparation_report)
        plan_payload = build_skillsbench_explicit_plan(
            registry_path=registry_path,
            repo_root=execution_repo_root,
            split_task_ids=split_task_ids,
            agent=agent,
            model=model,
            harbor_bin=harbor_bin,
            extra_args=[
                "--jobs-dir",
                str(jobs_dir),
                "--job-name",
                job_name,
                *extra_args,
            ],
        )
        write_json(plan_path, plan_payload)
        execution_report = execute_command_plan(
            plan_source=plan_path,
            out=execution_path,
            split=split_name,
            mode=execute_mode,
            cwd=repo_root.parent.parent,
        )
        if not job_dir.exists():
            raise RuntimeError(f"Expected Harbor job directory does not exist after execution: {job_dir}")
    if source_job_dir_value:
        write_json(plan_path, plan_payload)

    imported_runs = import_skillsbench_job(
        source=job_dir,
        out=records_path,
        benchmark_split=split_name,
        phase=phase,
        path_type=path_type,
        seed=seed,
        registry_source=registry_path,
        repo_root=repo_root,
        model_name=model_name,
        agent_name=agent_name,
        agent_version=agent_version,
    )
    records_validation = validate_data_file(
        data_path=records_path,
        schema_path=Path(__file__).resolve().parents[2] / "schemas" / "runs.schema.json",
    )

    return {
        "run_name": run_name,
        "phase": phase,
        "benchmark_split": split_name,
        "path_type": path_type,
        "seed": seed,
        "plan_path": str(plan_path),
        "hydration_path": str(hydration_path),
        "execution_path": str(execution_path) if execution_report else None,
        "records_path": str(records_path),
        "job_dir": str(job_dir),
        "task_ids": list(run_spec["task_ids"]),
        "hydrated_paths": hydration_report["hydrated_paths"] if hydration_report else [],
        "task_preparation": task_preparation,
        "preparation_path": str(preparation_path) if preparation_report else None,
        "execution_mode": execute_mode if execution_report else "import-only",
        "execution_summary": execution_report["summary"] if execution_report else None,
        "imported_records": len(imported_runs),
        "success_count": sum(1 for record in imported_runs if record["success"]),
        "failure_count": sum(1 for record in imported_runs if not record["success"]),
        "records_validation": records_validation,
    }


def prepare_skillsbench_tasks(
    *,
    source_repo_root: Path,
    registry_path: Path,
    split_task_ids: dict[str, list[str]],
    prepared_root: Path,
    skill_mode: str,
    patches: dict[str, list[str]],
) -> dict[str, Any]:
    adapter = SkillsBenchAdapter()
    task_index = adapter.build_registry_index(registry_path)
    task_ids = sorted({task_id for task_ids in split_task_ids.values() for task_id in task_ids})
    prepared_root.mkdir(parents=True, exist_ok=True)

    prepared_tasks: list[dict[str, Any]] = []
    patched_files: list[str] = []
    for task_id in task_ids:
        task = task_index[task_id]
        source_task_path = source_repo_root / task.source_path
        destination_task_path = prepared_root / task.source_path
        if destination_task_path.exists():
            shutil.rmtree(destination_task_path)
        destination_task_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_task_path, destination_task_path)

        if skill_mode == "strip":
            stripped_files = _strip_skills_from_task(destination_task_path)
            patched_files.extend(stripped_files)

        for patch_name in patches.get(task_id, []):
            patched_files.extend(_apply_task_patch(task_id=task_id, patch_name=patch_name, task_root=destination_task_path))

        prepared_tasks.append(
            {
                "task_id": task_id,
                "source_path": str(source_task_path),
                "prepared_path": str(destination_task_path),
                "skill_mode": skill_mode,
                "patches": patches.get(task_id, []),
            }
        )

    return {
        "schema_version": SUITE_SCHEMA_VERSION,
        "action": "skillsbench_task_preparation",
        "prepared_root": str(prepared_root),
        "skill_mode": skill_mode,
        "patched_files": patched_files,
        "tasks": prepared_tasks,
    }


def _aggregate_suite_records(
    *,
    records: list[dict[str, Any]],
    out_path: Path,
    aggregate: bool,
) -> dict[str, Any]:
    if not aggregate:
        return {
            "attempted": False,
            "summary_path": str(out_path),
        }

    try:
        summaries = aggregate_runs(records)
    except ValueError as exc:
        return {
            "attempted": True,
            "summary_path": str(out_path),
            "generated": False,
            "error": str(exc),
        }

    write_jsonl(out_path, summaries)
    validation_report = validate_data_file(
        data_path=out_path,
        schema_path=Path(__file__).resolve().parents[2] / "schemas" / "summary.schema.json",
    )
    return {
        "attempted": True,
        "summary_path": str(out_path),
        "generated": True,
        "records": len(summaries),
        "validation": validation_report,
    }


def _resolve_explicit_tasks(
    *,
    task_index: dict[str, TaskDescriptor],
    task_ids: list[str],
) -> list[TaskDescriptor]:
    missing = [task_id for task_id in task_ids if task_id not in task_index]
    if missing:
        raise ValueError(f"Unknown SkillsBench task ids in explicit split assignment: {missing}")
    return [task_index[task_id] for task_id in task_ids]


def _resolve_path(base_dir: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _resolve_command_value(base_dir: Path, command_value: str) -> str:
    if any(token in command_value for token in ("\\", "/")) or command_value.lower().endswith(
        (".cmd", ".bat", ".exe", ".ps1")
    ):
        return str(_resolve_path(base_dir, command_value))
    return command_value


def _merge_task_preparation(
    execution_defaults: dict[str, Any] | None,
    run_override: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = {
        "mode": DEFAULT_TASK_PREPARATION["mode"],
        "skill_mode": DEFAULT_TASK_PREPARATION["skill_mode"],
        "patches": dict(DEFAULT_TASK_PREPARATION["patches"]),
    }
    if execution_defaults:
        merged.update({key: value for key, value in execution_defaults.items() if key != "patches"})
        if execution_defaults.get("patches"):
            merged["patches"] = dict(execution_defaults["patches"])
    if run_override:
        merged.update({key: value for key, value in run_override.items() if key != "patches"})
        if run_override.get("patches"):
            merged["patches"] = dict(run_override["patches"])
    return merged


def _strip_skills_from_task(task_root: Path) -> list[str]:
    patched_files: list[str] = []
    skills_root = task_root / "environment" / "skills"
    if skills_root.exists():
        shutil.rmtree(skills_root)
        patched_files.append(str(skills_root))

    dockerfile_path = task_root / "environment" / "Dockerfile"
    if dockerfile_path.exists():
        dockerfile_text = dockerfile_path.read_text(encoding="utf-8")
        updated_text = _strip_skills_from_dockerfile_text(dockerfile_text)
        if updated_text != dockerfile_text:
            dockerfile_path.write_text(updated_text, encoding="utf-8")
            patched_files.append(str(dockerfile_path))
    return patched_files


def _strip_skills_from_dockerfile_text(dockerfile_text: str) -> str:
    filtered_lines = []
    for line in dockerfile_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("COPY skills "):
            continue
        if stripped.startswith("ENV PYTHONPATH=") and "/skills/" in stripped:
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines).rstrip() + "\n"


def _apply_task_patch(*, task_id: str, patch_name: str, task_root: Path) -> list[str]:
    if patch_name == "offer_letter_generator_system_docx":
        if task_id != "offer-letter-generator":
            raise ValueError(f"Patch {patch_name} is only valid for offer-letter-generator, not {task_id}")
        dockerfile_path = task_root / "environment" / "Dockerfile"
        dockerfile_text = dockerfile_path.read_text(encoding="utf-8")
        dockerfile_text = dockerfile_text.replace(
            "RUN apt-get update && apt-get install -y \\\n    python3 \\\n    python3-pip \\\n    curl \\\n    && rm -rf /var/lib/apt/lists/*\n\n# Install Python packages\nRUN pip3 install --break-system-packages \\\n    python-docx==1.1.2\n",
            "RUN apt-get update && apt-get install -y \\\n    python3 \\\n    python3-pip \\\n    python3-docx \\\n    curl \\\n    && rm -rf /var/lib/apt/lists/*\n",
        )
        dockerfile_path.write_text(dockerfile_text, encoding="utf-8")
        return [str(dockerfile_path)]
    raise ValueError(f"Unsupported task patch: {patch_name}")
