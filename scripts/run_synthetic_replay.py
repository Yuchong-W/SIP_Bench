"""Export or verify deterministic synthetic diagnosis fixtures without providers."""
from __future__ import annotations

import argparse
import json

from sip_bench.synthetic_replay import build_artifacts, verify_replay, write_replay


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verify", action="store_true", help="Recompute and compare existing artifacts; write nothing")
    parser.add_argument("--seed", type=int, default=7)
    for split in ("adapt", "replay", "heldout", "drift"):
        parser.add_argument(f"--{split}-patients", type=int, default=1)
    args = parser.parse_args()
    if not args.verify:
        artifacts = build_artifacts(args.source, args.source_manifest,
                                    patient_counts={split: getattr(args, f"{split}_patients") for split in ("adapt", "replay", "heldout", "drift")},
                                    seed=args.seed)
        write_replay(artifacts, args.out)
    print(json.dumps(verify_replay(args.out, args.source, args.source_manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
