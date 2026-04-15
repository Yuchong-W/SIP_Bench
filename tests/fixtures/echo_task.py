from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--message", default="ok")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"{args.task_id}:{args.message}\n", encoding="utf-8")
    print(f"ran {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
