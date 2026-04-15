from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.validation import validate_data_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate SIP-Bench data files against JSON Schema."
    )
    parser.add_argument("--data", required=True, help="Path to .json or .jsonl file.")
    parser.add_argument(
        "--schema",
        required=True,
        help="Path to schema file or built-in name: runs | summary",
    )
    parser.add_argument("--input-format", choices=["json", "jsonl"])
    parser.add_argument("--max-errors", type=int, default=20)
    return parser.parse_args()


def resolve_schema(schema_arg: str) -> Path:
    if schema_arg == "runs":
        return ROOT / "schemas" / "runs.schema.json"
    if schema_arg == "summary":
        return ROOT / "schemas" / "summary.schema.json"
    return Path(schema_arg)


def main() -> int:
    args = parse_args()
    report = validate_data_file(
        data_path=args.data,
        schema_path=resolve_schema(args.schema),
        input_format=args.input_format,
        max_errors=args.max_errors,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
