from __future__ import annotations

import argparse
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
                steps[-1]["plan_matrix"] = matrix_report

        report = {
            "python_bin": python_bin,
            "temp_dir": str(temp_dir),
            "steps": steps,
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

            report["artifact_gate"] = {
                "required_schema_assets_present": all(
                    Path(path).exists()
                    for path in [
                        ROOT / "results/dryrun/sample_runs.jsonl",
                        ROOT / "results/dryrun/summary.jsonl",
                        ROOT / "results/protocol_runs/skillsbench_oracle_real_suite/summary.jsonl",
                        ROOT / "results/protocol_runs/tau_bench_retail_historical_suite/summary.jsonl",
                    ]
                )
            }

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
