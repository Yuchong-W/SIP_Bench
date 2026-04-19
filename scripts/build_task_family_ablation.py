#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from sip_bench.protocol_runner import _infer_failure_family  # type: ignore
except Exception:  # pragma: no cover - fallback for CLI robustness
    def _infer_failure_family(*, exception_type: str | None = None, exception_message: str | None = None) -> str | None:
        text = " ".join(
            value for value in [str(exception_type or ""), str(exception_message or "")] if value
        ).lower()
        if not text:
            return None
        for value in ["environment", "docker", "vsock", "credential", "curl", "timeout", "connection"]:
            if value in text:
                return "docker" if value in {"environment", "docker", "vsock"} else "credentials"
        return "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a protocol task-family ablation table from combined run files."
        )
    )
    parser.add_argument(
        "--combined-runs",
        action="append",
        required=True,
        help="Path to a combined_runs.jsonl file.",
    )
    parser.add_argument(
        "--out-dir",
        default="docs/results_task_family_ablation",
        help="Directory for generated artifact files.",
    )
    parser.add_argument(
        "--out-name",
        default="task_family_ablation",
        help="Base filename for JSON/CSV outputs.",
    )
    parser.add_argument(
        "--suite-filter",
        action="append",
        help="Optional suite name substring filter; can be repeated.",
    )
    parser.add_argument(
        "--print-md",
        action="store_true",
        help="Print a markdown summary to stdout.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            text = raw.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


def _safe_num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_family(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        metadata = row.get("metadata") or {}
        suite = row.get("run_id", "unknown").split("::")[0]
        task_id = row.get("task_id") or metadata.get("task_id") or "unknown"
        difficulty = metadata.get("difficulty") or "unknown"
        category = metadata.get("category") or "unknown"
        key = (suite, difficulty, category, task_id)
        grouped[key].append(row)

    output: list[dict[str, Any]] = []
    for (suite, difficulty, category, task_id), family_rows in grouped.items():
        by_split_phase: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        family_failures: dict[str, int] = defaultdict(int)
        success_count = 0

        for row in family_rows:
            split = row.get("benchmark_split", "unknown")
            phase = row.get("phase", "unknown")
            score = _safe_num(row.get("score"))
            if score is not None:
                by_split_phase[split][phase].append(score)
            if row.get("success"):
                success_count += 1
            else:
                metadata = row.get("metadata") or {}
                failure_family = _infer_failure_family(
                    exception_type=metadata.get("exception_type"),
                    exception_message=metadata.get("exception_message"),
                ) or "unknown"
                family_failures[failure_family] += 1

        def mean(values: list[float]) -> float | None:
            if not values:
                return None
            return round(statistics.fmean(values), 6)

        replay_t0 = mean(by_split_phase["replay"]["T0"])
        replay_t1 = mean(by_split_phase["replay"]["T1"])
        replay_t2 = mean(by_split_phase["replay"]["T2"])
        heldout_t0 = mean(by_split_phase["heldout"]["T0"])
        heldout_t1 = mean(by_split_phase["heldout"]["T1"])
        heldout_t2 = mean(by_split_phase["heldout"]["T2"])
        fg = None if heldout_t0 is None or heldout_t1 is None else round(heldout_t1 - heldout_t0, 6)
        br = None if replay_t0 is None or replay_t1 is None else round(replay_t1 - replay_t0, 6)

        total_runs = len(family_rows)
        failure_count = sum(family_failures.values())
        failure_signature = ",".join(f"{k}:{v}" for k, v in sorted(family_failures.items()))
        output.append(
            {
                "suite": suite,
                "task_id": task_id,
                "difficulty": difficulty,
                "category": category,
                "records": total_runs,
                "success_rate": round(success_count / total_runs, 6) if total_runs else 0.0,
                "replay_t0_mean": replay_t0,
                "replay_t1_mean": replay_t1,
                "replay_t2_mean": replay_t2,
                "heldout_t0_mean": heldout_t0,
                "heldout_t1_mean": heldout_t1,
                "heldout_t2_mean": heldout_t2,
                "fg": fg,
                "br": br,
                "failure_count": failure_count,
                "failure_signature": failure_signature or "none",
                "failure_signature_counts": family_failures,
            }
        )

    # Keep the output deterministic for docs/review.
    output.sort(key=lambda item: (item["suite"], item["difficulty"], item["category"], item["task_id"]))
    return output


def write_outputs(results: list[dict[str, Any]], *, out_dir: Path, base: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{base}.json"
    csv_path = out_dir / f"{base}.csv"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    if not results:
        return json_path, csv_path

    columns = [
        "suite",
        "task_id",
        "difficulty",
        "category",
        "records",
        "success_rate",
        "heldout_t0_mean",
        "heldout_t1_mean",
        "heldout_t2_mean",
        "replay_t0_mean",
        "replay_t1_mean",
        "replay_t2_mean",
        "fg",
        "br",
        "failure_count",
        "failure_signature",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in results:
            writer.writerow({column: row.get(column, "n/a") for column in columns})
    return json_path, csv_path


def print_markdown(results: list[dict[str, Any]]) -> None:
    print("| suite | difficulty | category | task_id | records | success | replay_t0 | replay_t1 | heldout_t0 | heldout_t1 | FG | BR | failures |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in results:
        print(
            f"| {row['suite']} | {row['difficulty']} | {row['category']} | {row['task_id']} | {row['records']} | "
            f"{row['success_rate']} | {row['replay_t0_mean']} | {row['replay_t1_mean']} | {row['heldout_t0_mean']} | "
            f"{row['heldout_t1_mean']} | {row['fg']} | {row['br']} | {row['failure_signature']} |"
        )


def main() -> None:
    args = parse_args()
    combined_files = [Path(path) for path in args.combined_runs]
    suite_filters = args.suite_filter or []

    rows: list[dict[str, Any]] = []
    for path in combined_files:
        if not path.exists():
            raise FileNotFoundError(f"combined_runs file not found: {path}")
        if not suite_filters or any(f in str(path) for f in suite_filters):
            rows.extend(load_rows(path))

    results = summarize_family(rows)
    out_dir = Path(args.out_dir)
    json_path, csv_path = write_outputs(results, out_dir=out_dir, base=args.out_name)

    if args.print_md:
        print_markdown(results)
    else:
        print(f"JSON: {json_path}")
        print(f"CSV: {csv_path}")


if __name__ == "__main__":
    main()
