from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RELEASE_SCHEMA_ASSETS = (
    Path("results/dryrun/sample_runs.jsonl"),
    Path("results/dryrun/summary.jsonl"),
    Path("results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl"),
)
OPTIONAL_HISTORICAL_ARTIFACTS = (
    Path("results/protocol_runs/tau_bench_retail_historical_suite/combined_runs.jsonl"),
    Path("results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl"),
)


def _result_only_configs(protocol_dir: Path = ROOT / "protocol") -> list[Path]:
    configs: list[Path] = []
    for config_path in sorted(protocol_dir.glob("*.json")):
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if config.get("suite_kind") == "result-only":
            configs.append(config_path)
    return configs


def _run_result_only_suite_check(*, config_path: Path, output_root: Path, python_bin: str) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    suite_name = str(config["suite_name"])
    suite_output = output_root / suite_name
    command = [
        python_bin,
        "scripts/run_protocol.py",
        "run-medical-suite",
        "--config",
        str(config_path),
        "--out-root",
        str(suite_output),
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"result-only suite {suite_name} failed: {completed.stderr.strip() or completed.stdout.strip()}")
    cli_report = json.loads(completed.stdout)
    combined_path = suite_output / "combined_runs.jsonl"
    summary_path = suite_output / "summary.jsonl"
    suite_report_path = suite_output / "suite_report.json"
    validation_commands = [
        [python_bin, "scripts/validate_records.py", "--data", str(combined_path), "--schema", "runs"],
        [python_bin, "scripts/validate_records.py", "--data", str(summary_path), "--schema", "summary"],
    ]
    for validation_command in validation_commands:
        validation = subprocess.run(validation_command, cwd=ROOT, capture_output=True, text=True)
        if validation.returncode != 0:
            raise RuntimeError(f"result-only artifact validation failed: {validation.stderr.strip() or validation.stdout.strip()}")

    records = []
    with combined_path.open("r", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]
    suite_report = json.loads(suite_report_path.read_text(encoding="utf-8"))
    expected = config.get("expected_artifacts", {})
    expected_records = int(expected.get("records", len(records)))
    expected_runs = int(expected.get("runs_per_suite", len(suite_report.get("runs", []))))
    if len(records) != expected_records or len(suite_report.get("runs", [])) != expected_runs:
        raise RuntimeError(
            f"result-only suite {suite_name} expected {expected_runs} runs/{expected_records} records, "
            f"got {len(suite_report.get('runs', []))} runs/{len(records)} records"
        )

    failure_families = Counter(
        str((record.get("metadata") or {}).get("failure_reason") or "unknown")
        for record in records
        if not record.get("success")
    )
    cost_fields = ("token_total", "tool_calls_total", "wall_clock_seconds", "cost_usd", "human_interventions")
    costs = {field: sum(float(record.get(field, 0) or 0) for record in records) for field in cost_fields}
    artifact_paths = [combined_path, summary_path, suite_report_path]
    return {
        "suite_name": suite_name,
        "config": str(config_path.relative_to(ROOT)),
        "command": command,
        "run_count": len(suite_report.get("runs", [])),
        "record_count": len(records),
        "expected_runs": expected_runs,
        "expected_records": expected_records,
        "costs": costs,
        "failure_families": dict(sorted(failure_families.items())),
        "artifact_hashes": {path.name: _file_sha256(path) for path in artifact_paths},
        "out_root": str(suite_output),
        "cli_report": cli_report,
        "status": "passed",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run release-facing SIP-Bench validation checks."
    )
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python interpreter used to run the checked scripts.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip unit tests.",
    )
    parser.add_argument(
        "--skip-import-check",
        action="store_true",
        help="Skip the SkillsBench Harbor job import smoke check.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary generated artifacts for inspection.",
    )
    parser.add_argument(
        "--no-hash",
        action="store_true",
        help="Skip release artifact snapshot hashes.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Optional path to write the JSON run report.",
    )
    parser.add_argument(
        "--plan-matrix",
        action="store_true",
        help="Run protocol matrix consistency check.",
    )
    parser.add_argument(
        "--plan-matrix-protocol-dir",
        default="protocol",
        help="Protocol directory for optional plan-matrix check.",
    )
    parser.add_argument(
        "--plan-matrix-config",
        action="append",
        default=None,
        help="Optional explicit suite config path. Repeatable.",
    )
    parser.add_argument(
        "--plan-matrix-strict",
        action="store_true",
        help="Fail if any declared suite artifact is missing.",
    )
    return parser.parse_args()


def run_step(name: str, command: list[str]) -> dict[str, object]:
    print(f"[release-check] {name}", flush=True)
    print(f"[release-check] command: {shlex.join(command)}", flush=True)
    result = subprocess.run(command, cwd=ROOT)
    return {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "status": "passed" if result.returncode == 0 else "failed",
    }


def _compact_plan_matrix(report: dict[str, object]) -> dict[str, object]:
    """Keep CI output readable by storing only the top-level plan-matrix summary."""
    return {
        "checked": report.get("checked"),
        "failed": report.get("failed"),
        "warnings": report.get("warnings"),
        "strict": report.get("strict"),
        "status": report.get("status"),
    }


def _file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_hashes(paths: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in paths:
        path = path.resolve()
        rows.append(
            {
                "path": str(path.relative_to(ROOT)),
                "exists": path.exists(),
                "sha256": _file_sha256(path),
            }
        )
    return rows


def release_artifact_gate(root: Path = ROOT) -> dict[str, object]:
    """Classify release-required schema records separately from optional history."""
    missing_required = [str(path) for path in REQUIRED_RELEASE_SCHEMA_ASSETS if not (root / path).exists()]
    missing_optional = [str(path) for path in OPTIONAL_HISTORICAL_ARTIFACTS if not (root / path).exists()]
    return {
        "required_schema_assets_present": not missing_required,
        "missing_required": missing_required,
        "missing_optional_historical": missing_optional,
    }



def _load_check_plan_matrix_module() -> object:
    module_path = ROOT / "scripts" / "check_plan_matrix.py"
    spec = importlib.util.spec_from_file_location("sip_check_plan_matrix", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import check_plan_matrix module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    args = parse_args()
    python_bin = str(Path(args.python_bin))
    temp_dir = Path(tempfile.mkdtemp(prefix="sip-release-check-"))
    summary_path = temp_dir / "sip_summary.jsonl"
    import_path = temp_dir / "skillsbench_job_runs.jsonl"

    steps: list[dict[str, object]] = []
    result_only_reports: list[dict[str, object]] = []

    try:
        if not args.skip_tests:
            steps.append(
                run_step(
                    "unit-tests",
                    [
                        python_bin,
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-p",
                        "test_*.py",
                    ],
                )
            )

        result_only_root = (Path(args.report).resolve().parent / "result_only") if args.report else temp_dir / "result_only"
        for config_path in _result_only_configs():
            try:
                native_report = _run_result_only_suite_check(
                    config_path=config_path,
                    output_root=result_only_root,
                    python_bin=python_bin,
                )
                result_only_reports.append(native_report)
                steps.append(
                    {
                        "name": f"result-only:{native_report['suite_name']}",
                        "command": native_report["command"],
                        "returncode": 0,
                        "status": "passed",
                        "result_only": native_report,
                    }
                )
            except Exception as exc:
                steps.append(
                    {
                        "name": f"result-only:{config_path.stem}",
                        "command": [python_bin, "scripts/run_protocol.py", "run-medical-suite", "--config", str(config_path)],
                        "returncode": 1,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        steps.append(
            run_step(
                "aggregate-dryrun-sample",
                [
                    python_bin,
                    "scripts/aggregate_metrics.py",
                    "--runs",
                    "results/dryrun/sample_runs.jsonl",
                    "--out",
                    str(summary_path),
                ],
            )
        )

        if not args.skip_import_check:
            import_step = run_step(
                "import-skillsbench-harbor-job",
                [
                    python_bin,
                    "scripts/run_eval.py",
                    "import-skillsbench-job",
                    "--job-dir",
                    "tests/fixtures/skillsbench_harbor_job_sample",
                    "--out",
                    str(import_path),
                    "--benchmark-split",
                    "smoke",
                    "--phase",
                    "T0",
                    "--path-type",
                    "oracle",
                    "--seed",
                    "21",
                    "--registry",
                    "tests/fixtures/skillsbench_registry_sample.json",
                    "--agent-version",
                    "fixture-import",
                    "--benchmark-version",
                    "skillsbench-harbor-fixture",
                ],
            )
            steps.append(import_step)
            if import_step["status"] == "passed":
                steps.append(
                    run_step(
                        "validate-imported-skillsbench-runs",
                        [
                            python_bin,
                            "scripts/validate_records.py",
                            "--data",
                            str(import_path),
                            "--schema",
                            "runs",
                        ],
                    )
                )

        steps.extend(
            [
                run_step(
                    "validate-dryrun-runs",
                    [
                        python_bin,
                        "scripts/validate_records.py",
                        "--data",
                        "results/dryrun/sample_runs.jsonl",
                        "--schema",
                        "runs",
                    ],
                ),
                run_step(
                    "validate-dryrun-summary",
                    [
                        python_bin,
                        "scripts/validate_records.py",
                        "--data",
                        "results/dryrun/summary.jsonl",
                        "--schema",
                        "summary",
                    ],
                ),
                run_step(
                    "validate-real-suite-runs",
                    [
                        python_bin,
                        "scripts/validate_records.py",
                        "--data",
                        "results/protocol_runs/skillsbench_oracle_real_suite/combined_runs.jsonl",
                        "--schema",
                        "runs",
                    ],
                ),
                run_step(
                    "validate-real-suite-summary",
                    [
                        python_bin,
                        "scripts/validate_records.py",
                        "--data",
                        "results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl",
                        "--schema",
                        "summary",
                    ],
                ),
            ]
        )

        if args.plan_matrix:
            check_plan_matrix = _load_check_plan_matrix_module()
            matrix_step_command = [
                python_bin,
                "scripts/check_plan_matrix.py",
                "--protocol-dir",
                args.plan_matrix_protocol_dir,
            ]
            if args.plan_matrix_strict:
                matrix_step_command.append("--strict")
            for config in args.plan_matrix_config or []:
                matrix_step_command.extend(["--config", config])
            steps.append(
                run_step(
                    "plan-matrix",
                    matrix_step_command,
                )
            )

            if steps[-1]["status"] == "passed":
                matrix_report = check_plan_matrix.run_plan_matrix(
                    protocol_dir=Path(args.plan_matrix_protocol_dir),
                    configs=args.plan_matrix_config or [],
                    strict=args.plan_matrix_strict,
                )
                if args.plan_matrix_strict and matrix_report["status"] != "pass":
                    steps[-1]["status"] = "failed"
                    steps[-1]["returncode"] = 1
                steps[-1]["plan_matrix"] = _compact_plan_matrix(matrix_report)

        report = {
            "python_bin": python_bin,
            "temp_dir": str(temp_dir),
            "steps": steps,
            "result_only_suites": result_only_reports,
            "passed": sum(step["status"] == "passed" for step in steps),
            "failed": sum(step["status"] == "failed" for step in steps),
        }

        if not args.no_hash:
            report["artifact_hashes"] = _artifact_hashes(
                [
                    ROOT / "results/dryrun/sample_runs.jsonl",
                    ROOT / "results/dryrun/summary.jsonl",
                    ROOT / "results/protocol_runs/skillsbench_oracle_real_suite/combined_runs.jsonl",
                    ROOT / "results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl",
                    ROOT / "results/protocol_runs/tau_bench_retail_historical_suite/combined_runs.jsonl",
                    ROOT / "results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl",
                    ROOT / "docs/results_table_data/protocol_summary_snapshot.csv",
                    ROOT / "docs/results_table_data/protocol_summary_snapshot.json",
                ]
            )

            report["artifact_gate"] = release_artifact_gate()

        print(json.dumps(report, indent=2), flush=True)
        if args.report:
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0 if report["failed"] == 0 else 1
    finally:
        if not args.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
