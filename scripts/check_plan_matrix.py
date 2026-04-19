from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TypedDict

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.protocol_runner import load_protocol_suite_config


class CheckRecord(TypedDict, total=False):
    suite_name: str
    label: str
    path: str
    status: str
    message: str


def _format_path(path: Path) -> str:
    """Return a repo-relative path when possible."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _normalize_suite_name(value: object) -> str:
    return str(value) if value is not None else "unknown"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for plan-matrix consistency checks."""
    parser = argparse.ArgumentParser(
        description="Quick consistency check for protocol suite configs and reproducible paths."
    )
    parser.add_argument(
        "--protocol-dir",
        default="protocol",
        help="Directory containing protocol suite JSON files.",
    )
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        help="Explicit suite config path. Repeatable. Defaults to all protocol/*.json.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when declared suite outputs are missing.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional path for JSON report output.",
    )
    return parser.parse_args()


def _collect_protocol_configs(protocol_dir: Path, explicit: list[str]) -> list[Path]:
    """Collect suite config files from explicit paths or the protocol directory."""
    if explicit:
        files: list[Path] = []
        for entry in explicit:
            candidate = Path(entry)
            if not candidate.is_absolute():
                candidate = ROOT / candidate
            if candidate.is_dir():
                files.extend(sorted(candidate.glob("*.json")))
            elif candidate.exists():
                files.append(candidate)
        return sorted({path.resolve() for path in files})

    return sorted((ROOT / protocol_dir).glob("*.json"))


def _check_required_path(
    *,
    label: str,
    suite_name: str,
    path: Path,
    strict: bool,
    checks: list[CheckRecord],
) -> None:
    """Append a file-existence requirement check record."""
    status = "pass" if path.exists() else ("fail" if strict else "warn")
    checks.append(
        {
            "suite_name": suite_name,
            "label": label,
            "path": _format_path(path),
            "status": status,
        }
    )


def _run_suite_check(
    config_path: Path,
    strict: bool,
    checks: list[CheckRecord],
) -> dict[str, Any]:
    """Validate one suite and return a compact suite-level check summary."""
    config = load_protocol_suite_config(config_path)
    suite_name = _normalize_suite_name(config.get("suite_name"))
    out_root = Path(config.get("out_root", ""))
    if not out_root.is_absolute():
        out_root = (config_path.parent / out_root).resolve()

    suite_check: dict[str, Any] = {
        "config": _format_path(config_path),
        "suite_name": suite_name,
        "out_root": _format_path(out_root),
        "run_rows": [],
        "status": "pass",
        "errors": 0,
        "warnings": 0,
    }

    for run in config.get("runs", []):
        run_name = str(run.get("run_name"))
        if not run_name:
            checks.append(
                {
                    "suite_name": suite_name,
                    "label": "run_spec_name",
                    "path": _format_path(config_path),
                    "status": "fail",
                    "message": "run_name is required",
                }
            )
            suite_check["status"] = "fail"
            suite_check["errors"] += 1
            continue

        run_has_source_job = "source_job_dir" in run
        has_import_inputs = run_has_source_job or "source_result_file" in run
        planned_artifacts: list[tuple[str, Path]] = []
        planned_artifacts.append(("plan", out_root / "plans" / f"{run_name}.json"))

        if not run.get("source_result_file"):
            planned_artifacts.append(("hydration", out_root / "hydration" / f"{run_name}.json"))
            planned_artifacts.append(("execution", out_root / "execution" / f"{run_name}.json"))

        planned_artifacts.append(("runs", out_root / "runs" / f"{run_name}.jsonl"))

        if has_import_inputs:
            if "source_job_dir" in run:
                _check_required_path(
                    label=f"run:{run_name}:source_job_dir",
                    suite_name=suite_name,
                    path=(config_path.parent / str(run["source_job_dir"])).resolve(),
                    strict=strict,
                    checks=checks,
                )
                planned_artifacts.append(("source_plan", out_root / "plans" / f"{run_name}.source.json"))
            if "source_result_file" in run:
                _check_required_path(
                    label=f"run:{run_name}:source_result_file",
                    suite_name=suite_name,
                    path=(config_path.parent / str(run["source_result_file"])).resolve(),
                    strict=strict,
                    checks=checks,
                )
        else:
            _check_required_path(
                label=f"run:{run_name}:source_plan",
                suite_name=suite_name,
                path=out_root / "plans" / f"{run_name}.source.json",
                strict=strict,
                checks=checks,
            )

        run_row = {"run_name": run_name, "artifacts": []}
        for label, path in planned_artifacts:
            status = "pass" if path.exists() else ("fail" if strict else "warn")
            if status == "fail":
                suite_check["status"] = "fail"
                suite_check["errors"] += 1
            elif status == "warn":
                suite_check["warnings"] += 1

            checks.append(
                {
                    "suite_name": suite_name,
                    "label": f"run:{run_name}:{label}",
                    "path": _format_path(path),
                    "status": status,
                }
            )
            run_row["artifacts"].append(
                {
                    "label": label,
                    "path": _format_path(path),
                    "status": status,
                }
            )

        suite_check["run_rows"].append(run_row)

    _check_required_path(
        label="suite:combined_runs",
        suite_name=suite_name,
        path=out_root / "combined_runs.jsonl",
        strict=strict,
        checks=checks,
    )
    _check_required_path(
        label="suite:summary",
        suite_name=suite_name,
        path=out_root / "summary.jsonl",
        strict=strict,
        checks=checks,
    )
    _check_required_path(
        label="suite:suite_report",
        suite_name=suite_name,
        path=out_root / "suite_report.json",
        strict=strict,
        checks=checks,
    )

    return suite_check


def main() -> int:
    args = parse_args()
    protocol_dir = Path(args.protocol_dir)
    checks: list[CheckRecord] = []
    suite_checks: list[dict[str, Any]] = []

    for config_path in _collect_protocol_configs(protocol_dir, args.config):
        try:
            suite_checks.append(
                _run_suite_check(
                    config_path=config_path,
                    strict=args.strict,
                    checks=checks,
                )
            )
        except Exception as exc:
            checks.append(
                {
                    "suite_name": _format_path(config_path),
                    "label": "load",
                    "path": _format_path(config_path),
                    "status": "fail",
                    "message": str(exc),
                }
            )

    failed = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warn"]
    report = {
        "checked": len(suite_checks),
        "failed": len(failed),
        "warnings": len(warnings),
        "strict": args.strict,
        "checks": checks,
        "suites": suite_checks,
        "status": "fail" if failed else ("warn" if warnings else "pass"),
    }
    print(json.dumps(report, indent=2), flush=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
def run_plan_matrix(
    protocol_dir: str = "protocol",
    configs: list[str] | None = None,
    strict: bool = False,
) -> dict[str, object]:
    """Build a structured plan-matrix report without printing or exiting."""
    protocol_dir_path = Path(protocol_dir)
    checks: list[CheckRecord] = []
    suite_checks: list[dict[str, Any]] = []
    config_files = _collect_protocol_configs(protocol_dir_path, configs or [])
    for config_path in config_files:
        try:
            suite_checks.append(
                _run_suite_check(
                    config_path=config_path,
                    strict=strict,
                    checks=checks,
                )
            )
        except Exception as exc:
            checks.append(
                {
                    "suite_name": _format_path(config_path),
                    "label": "load",
                    "path": _format_path(config_path),
                    "status": "fail",
                    "message": str(exc),
                }
            )

    failed = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warn"]
    return {
        "checked": len(suite_checks),
        "failed": len(failed),
        "warnings": len(warnings),
        "strict": strict,
        "checks": checks,
        "suites": suite_checks,
        "status": "fail" if failed else ("warn" if warnings else "pass"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
