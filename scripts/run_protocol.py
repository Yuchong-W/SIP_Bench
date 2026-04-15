from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.protocol_runner import run_skillsbench_suite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a config-driven SIP protocol suite.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    skillsbench = subparsers.add_parser("run-skillsbench-suite")
    skillsbench.add_argument("--config", required=True, help="Path to the protocol suite config JSON.")
    skillsbench.add_argument(
        "--out-root",
        help="Optional override for the suite output root directory.",
    )
    skillsbench.add_argument(
        "--mode",
        default="subprocess",
        choices=("subprocess", "mock"),
        help="Execution mode for generated plans.",
    )
    skillsbench.add_argument(
        "--no-aggregate",
        action="store_true",
        help="Skip summary aggregation after combined runs are written.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "run-skillsbench-suite":
        report = run_skillsbench_suite(
            config_path=args.config,
            out_root=args.out_root,
            execute_mode=args.mode,
            aggregate=not args.no_aggregate,
        )
        print(
            json.dumps(
                {
                    "command": args.command,
                    "suite_name": report["suite_name"],
                    "out_root": report["out_root"],
                    "run_count": report["run_count"],
                    "runs_valid": report["runs_validation"]["valid"],
                    "summary": report["summary"],
                },
                indent=2,
            )
        )
        return 0
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
