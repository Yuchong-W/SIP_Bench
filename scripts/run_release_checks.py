from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
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

        report = {
            "python_bin": python_bin,
            "temp_dir": str(temp_dir),
            "steps": steps,
            "passed": sum(step["status"] == "passed" for step in steps),
            "failed": sum(step["status"] == "failed" for step in steps),
        }
        print(json.dumps(report, indent=2), flush=True)
        return 0 if report["failed"] == 0 else 1
    finally:
        if not args.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
