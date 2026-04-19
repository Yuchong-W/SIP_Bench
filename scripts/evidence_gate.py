from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sip_bench.protocol_runner import EVIDENCE_DEFAULTS


DEFAULT_ARGS = {
    "attempts": int(EVIDENCE_DEFAULTS["min_repeat_count"]),
    "ceiling_gap": float(EVIDENCE_DEFAULTS["ceiling_gap"]),
    "protocol_shift": float(EVIDENCE_DEFAULTS["min_protocol_effect"]),
    "ie_shift": float(EVIDENCE_DEFAULTS["min_ie_effect"]),
}


def _parse_default_int() -> int:
    return max(1, int(DEFAULT_ARGS["attempts"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate whether a suite summary is candidate evidence.")
    parser.add_argument("--summary", required=True, help="Path to a suite summary.jsonl file.")
    parser.add_argument(
        "--attempts",
        type=int,
        default=_parse_default_int(),
        help="Required minimum attempt/repeat count for evidence status.",
    )
    parser.add_argument(
        "--ceiling-gap",
        type=float,
        default=float(DEFAULT_ARGS["ceiling_gap"]),
        help="Ceiling-gate threshold for score fields.",
    )
    parser.add_argument(
        "--protocol-shift",
        type=float,
        default=float(DEFAULT_ARGS["protocol_shift"]),
        help="Required FG/BR absolute shift to qualify as non-ceiling.",
    )
    parser.add_argument(
        "--ie-shift",
        type=float,
        default=float(DEFAULT_ARGS["ie_shift"]),
        help="Required |IE| absolute shift to qualify as non-ceiling.",
    )
    return parser.parse_args()


def _load_summary_rows(summary_path: Path) -> list[dict]:
    rows = []
    with summary_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def _evaluate_gate(*, rows: list[dict], attempts: int, ceiling_gap: float, protocol_shift: float, ie_shift: float) -> dict:
    if not rows:
        return {
            "evidence_status": "blocked",
            "non_ceiling": False,
            "reason": "summary_is_empty",
            "required_repeats": attempts,
            "max_repeats_observed": 0,
            "score_fields_present": False,
            "required_repeats_ok": False,
        }

    non_ceiling = False
    score_fields_present = False

    for row in rows:
        metrics = row.get("metrics", {})
        score_fields = [
            metrics.get("t0_replay_mean"),
            metrics.get("t1_replay_mean"),
            metrics.get("t0_heldout_mean"),
            metrics.get("t1_heldout_mean"),
            metrics.get("t2_heldout_mean"),
            metrics.get("t2_replay_mean"),
        ]
        score_fields_present = score_fields_present or any(value is not None for value in score_fields)
        if any(value is not None and value < 1.0 - ceiling_gap for value in score_fields):
            non_ceiling = True

        protocol_delta = max(
            abs(float(metrics.get("fg_mean", 0.0) or 0.0)),
            abs(float(metrics.get("br_mean", 0.0) or 0.0)),
        )
        ie_mean = metrics.get("ie_mean")
        if protocol_delta >= protocol_shift:
            non_ceiling = True
        if ie_mean is not None and abs(float(ie_mean)) >= ie_shift:
            non_ceiling = True

    repeats_list = [int(row.get("repeats", 0) or 0) for row in rows if row.get("repeats") is not None]
    if not repeats_list:
        repeats_list = [
            int(row.get("attempts", 0) or 0) for row in rows if int(row.get("attempts", 0) or 0) > 0
        ]

    repeats_observed = max(repeats_list) if repeats_list else 0
    repeats_ok = repeats_observed >= attempts

    if repeats_ok and non_ceiling:
        status = "evidence"
    else:
        status = "screening"

    return {
        "evidence_status": status,
        "non_ceiling": bool(non_ceiling),
        "required_repeats": attempts,
        "max_repeats_observed": repeats_observed,
        "score_fields_present": score_fields_present,
        "required_repeats_ok": repeats_ok,
    }


def main() -> int:
    args = parse_args()
    summary_path = Path(args.summary)
    rows = _load_summary_rows(summary_path)

    gate = _evaluate_gate(
        rows=rows,
        attempts=args.attempts,
        ceiling_gap=args.ceiling_gap,
        protocol_shift=args.protocol_shift,
        ie_shift=args.ie_shift,
    )

    print(json.dumps(gate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
