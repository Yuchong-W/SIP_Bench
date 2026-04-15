from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.metrics import aggregate_runs, load_jsonl, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate SIP-Bench run records into summary records."
    )
    parser.add_argument("--runs", required=True, help="Path to input runs.jsonl")
    parser.add_argument("--out", required=True, help="Path to output summary.jsonl")
    parser.add_argument(
        "--cost-field",
        default="token_total",
        choices=[
            "token_total",
            "wall_clock_seconds",
            "tool_calls_total",
            "cost_usd",
            "human_interventions",
        ],
        help="Field used to compute IE.",
    )
    parser.add_argument(
        "--lambda-penalty",
        type=float,
        default=1.0,
        help="Penalty weight used in NIS.",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=1e-6,
        help="Replay denominator guard used in BR_ratio.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runs_path = Path(args.runs)
    output_path = Path(args.out)

    run_records = load_jsonl(runs_path)
    summary_records = aggregate_runs(
        run_records,
        cost_field=args.cost_field,
        lambda_penalty=args.lambda_penalty,
        eps=args.eps,
    )

    for record in summary_records:
        record.setdefault("provenance", {})
        record["provenance"]["runs_file"] = str(runs_path)

    write_jsonl(output_path, summary_records)

    print(
        json.dumps(
            {
                "runs": len(run_records),
                "summaries": len(summary_records),
                "out": str(output_path),
                "cost_field": args.cost_field,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
