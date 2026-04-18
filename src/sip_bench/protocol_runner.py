from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path
from typing import Any

from sip_bench.adapters import SkillsBenchAdapter, TauBenchAdapter
from sip_bench.adapters.base import SplitManifest, TaskDescriptor
from sip_bench.metrics import aggregate_runs, load_jsonl, write_jsonl
from sip_bench.runner import (
    execute_command_plan,
    hydrate_skillsbench_checkout,
    import_skillsbench_job,
    import_tau_results,
    load_env_file,
    tau_bench_preflight,
    write_json,
)
from sip_bench.validation import load_schema, validate_data_file
from jsonschema import Draft202012Validator

SUITE_SCHEMA_VERSION = "0.1.0"
DEFAULT_SPLITS = ("replay", "adapt", "heldout", "drift")
DEFAULT_TASK_PREPARATION = {
    "mode": "source",
    "skill_mode": "keep",
    "patches": {},
}
DEFAULT_RETRY_POLICY = {
    "max_attempts": 1,
    "require_all_records_failed": True,
    "retry_on_execution_statuses": [],
    "retry_on_exception_types": [],
    "retry_on_message_substrings": [],
}


def run_skillsbench_suite(
    *,
    config_path: str | Path,
    out_root: str | Path | None = None,
    execute_mode: str = "subprocess",
    aggregate: bool = True,
    selected_run_names: set[str] | None = None,
) -> dict[str, Any]:
    config_file = Path(config_path).resolve()
    config = load_protocol_suite_config(config_file)
    base_dir = config_file.parent

    repo_root = _resolve_path(base_dir, config["repo_root"])
    registry_path = _resolve_path(base_dir, config["registry_path"])
    suite_root = _resolve_path(base_dir, out_root) if out_root else _resolve_path(base_dir, config["out_root"])
    suite_root.mkdir(parents=True, exist_ok=True)

    execution_defaults = config["execution"]
    selected_run_specs, selected_names = _select_suite_run_specs(
        config["runs"],
        selected_run_names,
    )
    existing_run_reports = _load_existing_suite_run_reports(suite_root / "suite_report.json")
    unselected_names = {
        str(run_spec["run_name"]) for run_spec in config["runs"] if str(run_spec["run_name"]) not in selected_names
    }
    if unselected_names:
        missing_reports = sorted(name for name in unselected_names if name not in existing_run_reports)
        if missing_reports:
            missing_text = ", ".join(missing_reports)
            raise ValueError(
                "Cannot update only part of the suite without reusable prior run reports. "
                f"Missing existing runs in {suite_root / 'suite_report.json'}: {missing_text}. "
                "Run the full suite first or use a different out_root for the subset run."
            )

    combined_runs: list[dict[str, Any]] = []
    run_reports_by_name = dict(existing_run_reports)
    for run_spec in selected_run_specs:
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
        run_reports_by_name[str(run_report["run_name"])] = run_report

    run_reports: list[dict[str, Any]] = []
    for run_spec in config["runs"]:
        run_name = str(run_spec["run_name"])
        run_report = run_reports_by_name.get(run_name)
        if run_report is None:
            continue
        run_reports.append(run_report)
        combined_runs.extend(load_jsonl(_resolve_suite_records_path(run_report, suite_root=suite_root, run_name=run_name)))

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


def run_tau_bench_suite(
    *,
    config_path: str | Path,
    out_root: str | Path | None = None,
    execute_mode: str = "subprocess",
    aggregate: bool = True,
    selected_run_names: set[str] | None = None,
) -> dict[str, Any]:
    config_file = Path(config_path).resolve()
    config = load_protocol_suite_config(config_file)
    if config["benchmark_name"] != "tau-bench":
        raise ValueError("run_tau_bench_suite expects a tau-bench config")
    base_dir = config_file.parent

    repo_root = _resolve_path(base_dir, config["repo_root"])
    suite_root = _resolve_path(base_dir, out_root) if out_root else _resolve_path(base_dir, config["out_root"])
    suite_root.mkdir(parents=True, exist_ok=True)

    execution_defaults = config["execution"]
    selected_run_specs, selected_names = _select_suite_run_specs(
        config["runs"],
        selected_run_names,
    )
    existing_run_reports = _load_existing_suite_run_reports(suite_root / "suite_report.json")
    unselected_names = {
        str(run_spec["run_name"]) for run_spec in config["runs"] if str(run_spec["run_name"]) not in selected_names
    }
    if unselected_names:
        missing_reports = sorted(name for name in unselected_names if name not in existing_run_reports)
        if missing_reports:
            missing_text = ", ".join(missing_reports)
            raise ValueError(
                "Cannot update only part of the suite without reusable prior run reports. "
                f"Missing existing runs in {suite_root / 'suite_report.json'}: {missing_text}. "
                "Run the full suite first or use a different out_root for the subset run."
            )

    suite_env_overrides = _resolve_suite_env(
        base_dir=base_dir,
        repo_root=repo_root,
        env_file_value=execution_defaults.get("env_file"),
    )
    preflight_report = tau_bench_preflight(
        repo_root=repo_root,
        python_bin=_resolve_command_value(base_dir, execution_defaults.get("python_bin", "python")),
        model_provider=execution_defaults["model_provider"],
        user_model_provider=execution_defaults["user_model_provider"],
        env_overrides=suite_env_overrides,
    )
    write_json(suite_root / "preflight.json", preflight_report)

    combined_runs: list[dict[str, Any]] = []
    run_reports_by_name = dict(existing_run_reports)
    for run_spec in selected_run_specs:
        run_report = _run_tau_spec(
            suite_name=config["suite_name"],
            base_dir=base_dir,
            suite_root=suite_root,
            repo_root=repo_root,
            execution_defaults=execution_defaults,
            run_spec=run_spec,
            execute_mode=execute_mode,
        )
        run_reports_by_name[str(run_report["run_name"])] = run_report

    run_reports: list[dict[str, Any]] = []
    for run_spec in config["runs"]:
        run_name = str(run_spec["run_name"])
        run_report = run_reports_by_name.get(run_name)
        if run_report is None:
            continue
        run_reports.append(run_report)
        combined_runs.extend(load_jsonl(_resolve_suite_records_path(run_report, suite_root=suite_root, run_name=run_name)))

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
        "preflight": preflight_report,
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


def build_tau_explicit_plan(
    *,
    repo_root: str | Path,
    env: str,
    task_split: str,
    split_task_ids: dict[str, list[int]],
    python_bin: str = "python",
    model: str,
    model_provider: str,
    user_model: str,
    user_model_provider: str,
    agent_strategy: str = "tool-calling",
    user_strategy: str = "llm",
    num_trials: int = 1,
    max_concurrency: int = 1,
    seed: int = 10,
    log_dir: str = "results",
    few_shot_displays_path: str | None = None,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    adapter = TauBenchAdapter()
    manifest = adapter.build_manifest_from_ids(
        env=env,
        task_split=task_split,
        replay_ids=split_task_ids.get("replay", []),
        adapt_ids=split_task_ids.get("adapt", []),
        heldout_ids=split_task_ids.get("heldout", []),
        drift_ids=split_task_ids.get("drift", []),
    )
    adapter.validate_manifest(manifest)

    commands: dict[str, list[list[str]]] = {}
    for split_name in DEFAULT_SPLITS:
        tasks_for_split = getattr(manifest, split_name)
        numeric_task_ids = [int(task.metadata["numeric_task_id"]) for task in tasks_for_split]
        commands[split_name] = []
        if numeric_task_ids:
            commands[split_name].append(
                adapter.build_run_command(
                    repo_root=repo_root,
                    env=env,
                    task_split=task_split,
                    task_ids=numeric_task_ids,
                    python_bin=python_bin,
                    model=model,
                    model_provider=model_provider,
                    user_model=user_model,
                    user_model_provider=user_model_provider,
                    agent_strategy=agent_strategy,
                    user_strategy=user_strategy,
                    num_trials=num_trials,
                    max_concurrency=max_concurrency,
                    seed=seed,
                    log_dir=log_dir,
                    few_shot_displays_path=few_shot_displays_path,
                    extra_args=extra_args,
                )
            )

    return {
        "benchmark_name": adapter.benchmark_name,
        "repo_root": str(repo_root),
        "selection": {
            "env": env,
            "task_split": task_split,
            "seed": seed,
            "selection_mode": "explicit",
            "task_ids": {split: split_task_ids.get(split, []) for split in DEFAULT_SPLITS},
        },
        "execution": {
            "python_bin": python_bin,
            "model": model,
            "model_provider": model_provider,
            "user_model": user_model,
            "user_model_provider": user_model_provider,
            "agent_strategy": agent_strategy,
            "user_strategy": user_strategy,
            "num_trials": num_trials,
            "max_concurrency": max_concurrency,
            "log_dir": log_dir,
            "few_shot_displays_path": few_shot_displays_path,
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
    _validate_protocol_suite_semantics(config)
    return _normalize_protocol_suite_config(config)


def _select_suite_run_specs(
    run_specs: list[dict[str, Any]],
    selected_run_names: set[str] | None,
) -> tuple[list[dict[str, Any]], set[str]]:
    if not selected_run_names:
        return list(run_specs), {str(run_spec["run_name"]) for run_spec in run_specs}

    requested_names = {str(name) for name in selected_run_names if str(name)}
    available_names = {str(run_spec["run_name"]) for run_spec in run_specs}
    unknown_names = sorted(requested_names - available_names)
    if unknown_names:
        raise ValueError(f"Unknown suite run name(s): {', '.join(unknown_names)}")
    return [
        run_spec for run_spec in run_specs if str(run_spec["run_name"]) in requested_names
    ], requested_names


def _load_existing_suite_run_reports(report_path: Path) -> dict[str, dict[str, Any]]:
    if not report_path.exists():
        return {}
    report = json.loads(report_path.read_text(encoding="utf-8"))
    return {
        str(run_report["run_name"]): run_report
        for run_report in report.get("runs", [])
        if run_report.get("run_name")
    }


def _resolve_suite_records_path(
    run_report: dict[str, Any],
    *,
    suite_root: Path,
    run_name: str,
) -> Path:
    records_path_value = run_report.get("records_path")
    candidate_paths: list[Path] = []
    if records_path_value:
        candidate_paths.append(Path(records_path_value))
    candidate_paths.append(suite_root / "runs" / f"{run_name}.jsonl")
    for candidate in candidate_paths:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Expected records for suite run {run_name} but found none in {candidate_paths}")


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
    retry_policy = _merge_retry_policy(
        execution_defaults.get("retry_policy"),
        run_spec.get("retry_policy"),
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
    effective_retry_policy = dict(retry_policy)
    if source_job_dir_value:
        effective_retry_policy["max_attempts"] = 1

    attempts_root = suite_root / "attempts" / run_name
    attempt_reports: list[dict[str, Any]] = []
    final_plan_payload: dict[str, Any] | None = None
    final_execution_report: dict[str, Any] | None = None
    final_imported_runs: list[dict[str, Any]] | None = None
    final_job_dir = job_dir
    final_job_name = job_name

    for attempt_number in range(1, effective_retry_policy["max_attempts"] + 1):
        attempt_label = _format_attempt_label(attempt_number)
        attempt_plan_path = attempts_root / f"{attempt_label}.plan.json"
        attempt_execution_path = attempts_root / f"{attempt_label}.execution.json"
        attempt_records_path = attempts_root / f"{attempt_label}.runs.jsonl"
        attempt_job_name = _allocate_attempt_job_name(
            jobs_dir=jobs_dir,
            base_job_name=job_name,
            attempt_number=attempt_number,
            max_attempts=effective_retry_policy["max_attempts"],
        )
        attempt_job_dir = job_dir if source_job_dir_value else jobs_dir / attempt_job_name
        attempt_plan_payload = build_skillsbench_explicit_plan(
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
                attempt_job_name,
                *extra_args,
            ],
        )
        write_json(attempt_plan_path, attempt_plan_payload)

        attempt_execution_report: dict[str, Any] | None = None
        if not source_job_dir_value:
            attempt_execution_report = execute_command_plan(
                plan_source=attempt_plan_path,
                out=attempt_execution_path,
                split=split_name,
                mode=execute_mode,
                cwd=repo_root.parent.parent,
                artifacts_dir=attempts_root / "artifacts" / attempt_label,
            )
            if not attempt_job_dir.exists():
                raise RuntimeError(f"Expected Harbor job directory does not exist after execution: {attempt_job_dir}")

        attempt_imported_runs = import_skillsbench_job(
            source=attempt_job_dir,
            out=attempt_records_path,
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
        attempt_records_validation = validate_data_file(
            data_path=attempt_records_path,
            schema_path=Path(__file__).resolve().parents[2] / "schemas" / "runs.schema.json",
        )
        retry_decision = _plan_skillsbench_retry(
            attempt_number=attempt_number,
            execution_report=attempt_execution_report,
            imported_runs=attempt_imported_runs,
            retry_policy=effective_retry_policy,
        )
        attempt_report = {
            "attempt_number": attempt_number,
            "attempt_label": attempt_label,
            "job_name": attempt_job_name,
            "job_dir": str(attempt_job_dir),
            "plan_path": str(attempt_plan_path),
            "execution_path": str(attempt_execution_path) if attempt_execution_report else None,
            "records_path": str(attempt_records_path),
            "execution_mode": execute_mode if attempt_execution_report else "import-only",
            "execution_summary": attempt_execution_report["summary"] if attempt_execution_report else None,
            "imported_records": len(attempt_imported_runs),
            "success_count": sum(1 for record in attempt_imported_runs if record["success"]),
            "failure_count": sum(1 for record in attempt_imported_runs if not record["success"]),
            "records_validation": attempt_records_validation,
            "retry_decision": retry_decision,
        }
        attempt_reports.append(attempt_report)

        final_plan_payload = attempt_plan_payload
        final_execution_report = attempt_execution_report
        final_imported_runs = attempt_imported_runs
        final_job_dir = attempt_job_dir
        final_job_name = attempt_job_name
        if not retry_decision["retry"]:
            break

    if final_plan_payload is None or final_imported_runs is None:
        raise RuntimeError(f"SkillsBench run {run_name} did not produce any attempt output")

    write_json(plan_path, final_plan_payload)
    if final_execution_report:
        write_json(execution_path, final_execution_report)
        execution_report = final_execution_report
    write_jsonl(records_path, final_imported_runs)
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
        "job_dir": str(final_job_dir),
        "job_name": final_job_name,
        "task_ids": list(run_spec["task_ids"]),
        "hydrated_paths": hydration_report["hydrated_paths"] if hydration_report else [],
        "task_preparation": task_preparation,
        "retry_policy": effective_retry_policy,
        "attempt_count": len(attempt_reports),
        "selected_attempt": attempt_reports[-1]["attempt_number"],
        "attempts": attempt_reports,
        "preparation_path": str(preparation_path) if preparation_report else None,
        "execution_mode": execute_mode if execution_report else "import-only",
        "execution_summary": execution_report["summary"] if execution_report else None,
        "imported_records": len(final_imported_runs),
        "success_count": sum(1 for record in final_imported_runs if record["success"]),
        "failure_count": sum(1 for record in final_imported_runs if not record["success"]),
        "records_validation": records_validation,
    }


def _run_tau_spec(
    *,
    suite_name: str,
    base_dir: Path,
    suite_root: Path,
    repo_root: Path,
    execution_defaults: dict[str, Any],
    run_spec: dict[str, Any],
    execute_mode: str,
) -> dict[str, Any]:
    run_name = run_spec["run_name"]
    split_name = run_spec["benchmark_split"]
    phase = run_spec["phase"]
    path_type = run_spec.get("path_type", execution_defaults["path_type"])
    seed = int(run_spec.get("seed", execution_defaults.get("seed", 0)))
    env = run_spec.get("env", execution_defaults["env"])
    task_split = run_spec.get("task_split", execution_defaults["task_split"])
    python_bin = _resolve_command_value(base_dir, run_spec.get("python_bin", execution_defaults.get("python_bin", "python")))
    model = run_spec.get("model", execution_defaults["model"])
    model_provider = run_spec.get("model_provider", execution_defaults["model_provider"])
    user_model = run_spec.get("user_model", execution_defaults["user_model"])
    user_model_provider = run_spec.get("user_model_provider", execution_defaults["user_model_provider"])
    agent_strategy = run_spec.get("agent_strategy", execution_defaults.get("agent_strategy", "tool-calling"))
    user_strategy = run_spec.get("user_strategy", execution_defaults.get("user_strategy", "llm"))
    num_trials = int(run_spec.get("num_trials", execution_defaults.get("num_trials", 1)))
    max_concurrency = int(run_spec.get("max_concurrency", execution_defaults.get("max_concurrency", 1)))
    agent_version = run_spec.get("agent_version", execution_defaults["agent_version"])
    agent_name = run_spec.get("agent_name", agent_strategy)
    model_name = run_spec.get("model_name", model)
    few_shot_displays_value = run_spec.get("few_shot_displays_path", execution_defaults.get("few_shot_displays_path"))
    few_shot_displays_path = _resolve_path(base_dir, few_shot_displays_value) if few_shot_displays_value else None
    extra_args = [*execution_defaults.get("extra_args", []), *run_spec.get("extra_args", [])]
    source_result_value = run_spec.get("source_result_file")
    env_overrides = _resolve_suite_env(
        base_dir=base_dir,
        repo_root=repo_root,
        env_file_value=run_spec.get("env_file", execution_defaults.get("env_file")),
    )

    split_task_ids: dict[str, list[int]] = {name: [] for name in DEFAULT_SPLITS}
    split_task_ids[split_name] = [int(task_id) for task_id in run_spec["task_ids"]]

    run_log_dir = _resolve_path(base_dir, run_spec["log_dir"]) if run_spec.get("log_dir") else suite_root / "tau_logs" / run_name
    plan_path = suite_root / "plans" / f"{run_name}.json"
    execution_path = suite_root / "execution" / f"{run_name}.json"
    records_path = suite_root / "runs" / f"{run_name}.jsonl"
    preflight_path = suite_root / "preflight_runs" / f"{run_name}.json"

    run_preflight = tau_bench_preflight(
        repo_root=repo_root,
        python_bin=python_bin,
        model_provider=model_provider,
        user_model_provider=user_model_provider,
        env_overrides=env_overrides,
    )
    write_json(preflight_path, run_preflight)

    plan_payload = build_tau_explicit_plan(
        repo_root=repo_root,
        env=env,
        task_split=task_split,
        split_task_ids=split_task_ids,
        python_bin=python_bin,
        model=model,
        model_provider=model_provider,
        user_model=user_model,
        user_model_provider=user_model_provider,
        agent_strategy=agent_strategy,
        user_strategy=user_strategy,
        num_trials=num_trials,
        max_concurrency=max_concurrency,
        seed=seed,
        log_dir=str(run_log_dir),
        few_shot_displays_path=str(few_shot_displays_path) if few_shot_displays_path else None,
        extra_args=extra_args,
    )
    write_json(plan_path, plan_payload)

    if source_result_value:
        result_file = _resolve_path(base_dir, source_result_value)
        execution_mode_value = "import-only"
        execution_summary = None
        imported_runs = import_tau_results(
            source=result_file,
            out=records_path,
            env=env,
            task_split=task_split,
            benchmark_split=split_name,
            phase=phase,
            path_type=path_type,
            model_name=model_name,
            agent_name=agent_name,
            agent_version=agent_version,
            seed=seed,
            benchmark_version=_resolve_git_or_default(repo_root, "tau-bench-upstream"),
            task_ids=set(split_task_ids[split_name]),
        )
    else:
        if not run_preflight["ready"]:
            raise RuntimeError(
                f"tau-bench preflight failed for run {run_name}: missing dependencies or provider credentials"
            )
        before_files = _list_json_files(run_log_dir)
        execution_report = execute_command_plan(
            plan_source=plan_path,
            out=execution_path,
            split=split_name,
            mode=execute_mode,
            cwd=repo_root,
            env_overrides=env_overrides,
        )
        result_file = _resolve_tau_result_file(run_log_dir=run_log_dir, before_files=before_files)
        imported_runs = import_tau_results(
            source=result_file,
            out=records_path,
            env=env,
            task_split=task_split,
            benchmark_split=split_name,
            phase=phase,
            path_type=path_type,
            model_name=model_name,
            agent_name=agent_name,
            agent_version=agent_version,
            seed=seed,
            benchmark_version=_resolve_git_or_default(repo_root, "tau-bench-upstream"),
            task_ids=set(split_task_ids[split_name]),
        )
        execution_mode_value = execute_mode
        execution_summary = execution_report["summary"]

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
        "env": env,
        "task_split": task_split,
        "plan_path": str(plan_path),
        "execution_path": str(execution_path) if not source_result_value else None,
        "records_path": str(records_path),
        "result_file": str(result_file),
        "run_log_dir": str(run_log_dir),
        "task_ids": list(split_task_ids[split_name]),
        "preflight_path": str(preflight_path),
        "env_override_keys": sorted(env_overrides.keys()),
        "preflight_ready": run_preflight["ready"],
        "execution_mode": execution_mode_value,
        "execution_summary": execution_summary,
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
            _safe_rmtree(destination_task_path)
        destination_task_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_task_path, destination_task_path)
        patched_files.extend(_normalize_shell_scripts(destination_task_path))

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


def _validate_protocol_suite_semantics(config: dict[str, Any]) -> None:
    benchmark_name = config["benchmark_name"]
    execution = config["execution"]
    if benchmark_name == "skillsbench":
        missing: list[str] = []
        for field in ("agent", "harbor_bin", "jobs_dir", "path_type", "agent_version"):
            if not execution.get(field):
                missing.append(field)
        if not config.get("registry_path"):
            missing.append("registry_path")
        if missing:
            raise ValueError(f"Invalid SkillsBench suite config, missing fields: {missing}")
    elif benchmark_name == "tau-bench":
        missing = [
            field
            for field in (
                "env",
                "task_split",
                "model",
                "model_provider",
                "user_model",
                "user_model_provider",
                "path_type",
                "agent_version",
            )
            if not execution.get(field)
        ]
        if missing:
            raise ValueError(f"Invalid tau-bench suite config, missing execution fields: {missing}")
        if any("source_job_dir" in run_spec for run_spec in config["runs"]):
            raise ValueError("tau-bench suite runs do not support source_job_dir; use source_result_file")
    else:
        raise ValueError(f"Unsupported benchmark_name in protocol suite config: {benchmark_name}")


def _normalize_protocol_suite_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(config))
    benchmark_name = normalized["benchmark_name"]
    for run_spec in normalized["runs"]:
        if benchmark_name == "skillsbench":
            run_spec["task_ids"] = [str(task_id) for task_id in run_spec["task_ids"]]
        elif benchmark_name == "tau-bench":
            run_spec["task_ids"] = [int(task_id) for task_id in run_spec["task_ids"]]
    return normalized


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


def _resolve_git_or_default(repo_root: Path, default_value: str) -> str:
    revision_file = repo_root / ".git"
    if revision_file.exists():
        from sip_bench.runner import _resolve_git_revision  # local import to avoid widening public surface

        revision = _resolve_git_revision(repo_root)
        if revision:
            return revision
    return default_value


def _resolve_command_value(base_dir: Path, command_value: str) -> str:
    if any(token in command_value for token in ("\\", "/")) or command_value.lower().endswith(
        (".cmd", ".bat", ".exe", ".ps1", ".sh")
    ):
        resolved = _resolve_path(base_dir, command_value)
        if os.name == "nt" and not resolved.suffix:
            for suffix in (".cmd", ".bat"):
                candidate = resolved.with_suffix(suffix)
                if candidate.exists():
                    return str(candidate)
        if os.name != "nt" and resolved.suffix.lower() in {".cmd", ".bat", ".ps1"}:
            for candidate in (resolved.with_suffix(""), resolved.with_suffix(".sh")):
                if candidate.exists():
                    return str(candidate)
        return str(resolved)
    return command_value


def _resolve_suite_env(
    *,
    base_dir: Path,
    repo_root: Path,
    env_file_value: str | None,
) -> dict[str, str]:
    candidate_paths: list[Path] = []
    if env_file_value:
        candidate_paths.append(_resolve_path(base_dir, env_file_value))
    else:
        candidate_paths.extend(
            [
                base_dir / ".env.local",
                base_dir / ".env",
                repo_root / ".env.local",
                repo_root / ".env",
            ]
        )
    for candidate in candidate_paths:
        if candidate.exists():
            return load_env_file(candidate)
    return {}


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


def _merge_retry_policy(
    execution_defaults: dict[str, Any] | None,
    run_override: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = {
        "max_attempts": DEFAULT_RETRY_POLICY["max_attempts"],
        "require_all_records_failed": DEFAULT_RETRY_POLICY["require_all_records_failed"],
        "retry_on_execution_statuses": list(DEFAULT_RETRY_POLICY["retry_on_execution_statuses"]),
        "retry_on_exception_types": list(DEFAULT_RETRY_POLICY["retry_on_exception_types"]),
        "retry_on_message_substrings": list(DEFAULT_RETRY_POLICY["retry_on_message_substrings"]),
    }
    for source in (execution_defaults, run_override):
        if not source:
            continue
        if "max_attempts" in source:
            merged["max_attempts"] = int(source["max_attempts"])
        if "require_all_records_failed" in source:
            merged["require_all_records_failed"] = bool(source["require_all_records_failed"])
        for key in (
            "retry_on_execution_statuses",
            "retry_on_exception_types",
            "retry_on_message_substrings",
        ):
            if key in source:
                merged[key] = [str(item) for item in source[key]]
    return merged


def _format_attempt_label(attempt_number: int) -> str:
    return f"attempt{attempt_number:02d}"


def _format_attempt_job_name(*, base_job_name: str, attempt_number: int, max_attempts: int) -> str:
    if max_attempts <= 1:
        return base_job_name
    return f"{base_job_name}-{_format_attempt_label(attempt_number)}"


def _allocate_attempt_job_name(
    *,
    jobs_dir: Path,
    base_job_name: str,
    attempt_number: int,
    max_attempts: int,
) -> str:
    base_attempt_job_name = _format_attempt_job_name(
        base_job_name=base_job_name,
        attempt_number=attempt_number,
        max_attempts=max_attempts,
    )
    candidate_job_name = base_attempt_job_name
    rerun_index = 2
    while (jobs_dir / candidate_job_name).exists():
        candidate_job_name = f"{base_attempt_job_name}-rerun{rerun_index:02d}"
        rerun_index += 1
    return candidate_job_name


def _plan_skillsbench_retry(
    *,
    attempt_number: int,
    execution_report: dict[str, Any] | None,
    imported_runs: list[dict[str, Any]],
    retry_policy: dict[str, Any],
) -> dict[str, Any]:
    remaining_attempts = max(0, int(retry_policy["max_attempts"]) - attempt_number)
    decision = {
        "eligible": False,
        "retry": False,
        "reason": "retry_policy_disabled",
        "remaining_attempts": remaining_attempts,
        "matched_failures": [],
    }
    if int(retry_policy["max_attempts"]) <= 1:
        return decision

    execution_statuses = set(retry_policy["retry_on_execution_statuses"])
    if execution_report and execution_statuses:
        status_counts = execution_report.get("summary", {}).get("status_counts", {})
        matched_statuses = [status for status in sorted(execution_statuses) if status_counts.get(status)]
        if matched_statuses:
            decision.update(
                {
                    "eligible": True,
                    "retry": remaining_attempts > 0,
                    "reason": f"execution_status:{matched_statuses[0]}",
                    "matched_failures": [
                        {
                            "kind": "execution_status",
                            "status": status,
                        }
                        for status in matched_statuses
                    ],
                }
            )
            return decision

    if retry_policy["require_all_records_failed"] and any(record.get("success") for record in imported_runs):
        decision["reason"] = "non_failed_record_present"
        return decision

    exception_types = set(retry_policy["retry_on_exception_types"])
    message_substrings = [item.lower() for item in retry_policy["retry_on_message_substrings"]]
    matched_failures: list[dict[str, Any]] = []
    for record in imported_runs:
        metadata = record.get("metadata") or {}
        exception_type = str(metadata.get("exception_type") or "")
        exception_message = str(metadata.get("exception_message") or "")
        matched_reason: str | None = None
        if exception_type and exception_type in exception_types:
            matched_reason = f"exception_type:{exception_type}"
        if matched_reason is None and exception_message and message_substrings:
            normalized_message = exception_message.lower()
            for needle in message_substrings:
                if needle and needle in normalized_message:
                    matched_reason = f"exception_message:{needle}"
                    break
        if matched_reason is None:
            continue
        matched_failures.append(
            {
                "kind": "import_failure",
                "run_id": record.get("run_id"),
                "task_id": record.get("task_id"),
                "exception_type": exception_type or None,
                "reason": matched_reason,
            }
        )
    if matched_failures:
        decision.update(
            {
                "eligible": True,
                "retry": remaining_attempts > 0,
                "reason": matched_failures[0]["reason"],
                "matched_failures": matched_failures,
            }
        )
        return decision

    decision["reason"] = "no_retry_match"
    return decision


def _list_json_files(root: Path) -> set[Path]:
    if not root.exists():
        return set()
    return {path.resolve() for path in root.glob("*.json")}


def _resolve_tau_result_file(*, run_log_dir: Path, before_files: set[Path]) -> Path:
    after_files = _list_json_files(run_log_dir)
    new_files = sorted(after_files - before_files, key=lambda path: path.stat().st_mtime)
    if len(new_files) == 1:
        return new_files[0]
    if len(new_files) > 1:
        return new_files[-1]
    existing_files = sorted(after_files, key=lambda path: path.stat().st_mtime)
    if existing_files:
        return existing_files[-1]
    raise RuntimeError(f"Could not locate tau-bench result JSON in {run_log_dir}")


def _strip_skills_from_task(task_root: Path) -> list[str]:
    patched_files: list[str] = []
    skills_root = task_root / "environment" / "skills"
    if skills_root.exists():
        _safe_rmtree(skills_root)
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


def _normalize_shell_scripts(task_root: Path) -> list[str]:
    patched_files: list[str] = []
    for script_path in sorted(task_root.rglob("*.sh")):
        original_bytes = script_path.read_bytes()
        normalized_bytes = original_bytes.replace(b"\r\n", b"\n")
        if normalized_bytes != original_bytes:
            script_path.write_bytes(normalized_bytes)
            patched_files.append(str(script_path))
    return patched_files


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
    if patch_name == "dialogue_parser_apt_retry":
        if task_id != "dialogue-parser":
            raise ValueError(f"Patch {patch_name} is only valid for dialogue-parser, not {task_id}")
        dockerfile_path = task_root / "environment" / "Dockerfile"
        dockerfile_text = dockerfile_path.read_text(encoding="utf-8")
        updated_text = dockerfile_text.replace(
            "RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*\n",
            (
                "RUN apt-get update -o Acquire::Retries=5 \\\n"
                "    -o Acquire::http::Timeout=30 \\\n"
                "    -o Acquire::https::Timeout=30 \\\n"
                "    && apt-get install -y --fix-missing \\\n"
                "    -o Acquire::Retries=5 \\\n"
                "    -o Acquire::http::Timeout=30 \\\n"
                "    -o Acquire::https::Timeout=30 \\\n"
                "    graphviz \\\n"
                "    && rm -rf /var/lib/apt/lists/*\n"
            ),
        )
        if updated_text == dockerfile_text:
            raise ValueError(f"Patch {patch_name} could not find expected Dockerfile snippet for {task_id}")
        dockerfile_path.write_text(updated_text, encoding="utf-8")
        return [str(dockerfile_path)]
    if patch_name == "citation_check_apt_retry":
        if task_id != "citation-check":
            raise ValueError(f"Patch {patch_name} is only valid for citation-check, not {task_id}")
        dockerfile_path = task_root / "environment" / "Dockerfile"
        dockerfile_text = dockerfile_path.read_text(encoding="utf-8")
        updated_text = dockerfile_text.replace(
            "RUN apt-get update && apt-get install -y \\\n"
            "    python3 \\\n"
            "    python3-pip \\\n"
            "    python3-venv \\\n"
            "    wget \\\n"
            "    curl \\\n"
            "    ca-certificates \\\n"
            "    && rm -rf /var/lib/apt/lists/*\n",
            (
                "RUN apt-get update -o Acquire::Retries=5 \\\n"
                "    -o Acquire::http::Timeout=30 \\\n"
                "    -o Acquire::https::Timeout=30 \\\n"
                "    && apt-get install -y --fix-missing \\\n"
                "    -o Acquire::Retries=5 \\\n"
                "    -o Acquire::http::Timeout=30 \\\n"
                "    -o Acquire::https::Timeout=30 \\\n"
                "    python3 \\\n"
                "    python3-pip \\\n"
                "    python3-venv \\\n"
                "    wget \\\n"
                "    curl \\\n"
                "    ca-certificates \\\n"
                "    && rm -rf /var/lib/apt/lists/*\n"
            ),
        )
        if updated_text == dockerfile_text:
            raise ValueError(f"Patch {patch_name} could not find expected Dockerfile snippet for {task_id}")
        dockerfile_path.write_text(updated_text, encoding="utf-8")
        return [str(dockerfile_path)]
    if patch_name == "citation_check_python_runtime":
        if task_id != "citation-check":
            raise ValueError(f"Patch {patch_name} is only valid for citation-check, not {task_id}")
        dockerfile_path = task_root / "environment" / "Dockerfile"
        test_script_path = task_root / "tests" / "test.sh"
        dockerfile_path.write_text(
            (
                "FROM python:3.12.8-slim\n\n"
                "WORKDIR /root\n\n"
                "RUN pip install --no-cache-dir \\\n"
                "    requests==2.32.3 \\\n"
                "    bibtexparser==1.4.2\n\n"
                "COPY test.bib /root/test.bib\n\n"
                "COPY skills /root/.claude/skills\n"
                "COPY skills /root/.codex/skills\n"
                "COPY skills /root/.opencode/skill\n"
                "COPY skills /root/.goose/skills\n"
                "COPY skills /root/.factory/skills\n"
                "COPY skills /root/.agents/skills\n"
                "COPY skills /root/.gemini/skills\n"
            ),
            encoding="utf-8",
        )
        test_script_path.write_text(
            (
                "#!/bin/bash\n"
                "set -x\n\n"
                "# Ensure logs directory exists\n"
                "mkdir -p /logs/verifier\n\n"
                "# Install test dependencies directly with pip to avoid extra bootstrap drift.\n"
                "python3 -m pip install --no-cache-dir \\\n"
                "  pytest==8.4.1 \\\n"
                "  pytest-json-ctrf==0.3.5\n\n"
                "pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA -v 2>&1 | tee /logs/verifier/pytest_output.txt\n"
                "RESULT=${PIPESTATUS[0]}\n\n"
                "if [ -f /logs/verifier/ctrf.json ]; then\n"
                "  PASSED=$(python3 -c \"import json; d=json.load(open('/logs/verifier/ctrf.json')); print(d['results']['summary']['passed'])\" 2>/dev/null || echo 0)\n"
                "  TOTAL=$(python3 -c \"import json; d=json.load(open('/logs/verifier/ctrf.json')); print(d['results']['summary']['tests'])\" 2>/dev/null || echo 1)\n"
                "  if [ \"$TOTAL\" -gt 0 ]; then\n"
                "    SCORE=$(python3 -c \"print(round($PASSED / $TOTAL, 3))\")\n"
                "  else\n"
                "    SCORE=0.0\n"
                "  fi\n"
                "else\n"
                "  SCORE=0.0\n"
                "fi\n\n"
                "echo \"$SCORE\" > /logs/verifier/reward.txt\n"
                "exit $RESULT\n"
            ),
            encoding="utf-8",
        )
        return [str(dockerfile_path), str(test_script_path)]
    raise ValueError(f"Unsupported task patch: {patch_name}")


def _safe_rmtree(path: Path) -> None:
    def _onerror(func: Any, failed_path: str, exc_info: Any) -> None:
        os.chmod(failed_path, stat.S_IWRITE)
        func(failed_path)

    shutil.rmtree(path, onerror=_onerror)
