from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "0.1.0"
REQUIRED_SPLITS = ("replay", "adapt", "heldout", "drift")
GROUP_FIELDS = (
    "benchmark_name",
    "benchmark_version",
    "path_type",
    "model_name",
    "agent_name",
    "agent_version",
)


@dataclass
class RepeatSummary:
    seed: int
    t0_replay: float
    t1_replay: float
    t2_replay: float | None
    t0_heldout: float
    t1_heldout: float
    t2_heldout: float | None
    fg: float
    br: float
    br_ratio: float
    ie: float | None
    pds: float | None
    nis: float
    token_total: float
    tool_calls_total: float
    wall_clock_seconds: float
    cost_usd: float
    human_interventions: float


def compute_protocol_metrics(
    *,
    t0_replay: float,
    t1_replay: float,
    t0_heldout: float,
    t1_heldout: float,
    t2_target: float | None,
    cost: float,
    lambda_penalty: float = 1.0,
    eps: float = 1e-6,
) -> dict[str, float | None]:
    fg = t1_heldout - t0_heldout
    br = t1_replay - t0_replay
    br_ratio = t1_replay / max(t0_replay, eps)
    ie = None if cost <= 0 else fg / cost
    pds = None if t2_target is None else t2_target - t1_heldout
    nis = fg - (lambda_penalty * max(0.0, -br))

    return {
        "fg": fg,
        "br": br,
        "br_ratio": br_ratio,
        "ie": ie,
        "pds": pds,
        "nis": nis,
    }


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {path}") from exc
    return records


def write_jsonl(path: str | Path, records: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def aggregate_runs(
    records: list[dict[str, Any]],
    *,
    cost_field: str = "token_total",
    lambda_penalty: float = 1.0,
    eps: float = 1e-6,
) -> list[dict[str, Any]]:
    if not records:
        return []

    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = tuple(record.get(field) for field in GROUP_FIELDS)
        grouped[key].append(record)

    return [
        _aggregate_group(
            group_records,
            cost_field=cost_field,
            lambda_penalty=lambda_penalty,
            eps=eps,
        )
        for group_records in grouped.values()
    ]


def _aggregate_group(
    records: list[dict[str, Any]],
    *,
    cost_field: str,
    lambda_penalty: float,
    eps: float,
) -> dict[str, Any]:
    first = records[0]
    per_seed: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        per_seed[int(record["seed"])].append(record)

    repeats = [
        _summarize_seed(
            seed_records,
            cost_field=cost_field,
            lambda_penalty=lambda_penalty,
            eps=eps,
        )
        for _, seed_records in sorted(per_seed.items())
    ]

    sample_sizes = {
        split: len({record["task_id"] for record in records if record["benchmark_split"] == split})
        for split in REQUIRED_SPLITS
    }

    summary = {
        "schema_version": PROTOCOL_VERSION,
        "summary_id": _make_summary_id(first),
        "benchmark_name": first["benchmark_name"],
        "path_type": first["path_type"],
        "model_name": first["model_name"],
        "agent_name": first["agent_name"],
        "agent_version": first["agent_version"],
        "sample_sizes": sample_sizes,
        "metrics": {
            "t0_replay_mean": _mean(repeat.t0_replay for repeat in repeats),
            "t1_replay_mean": _mean(repeat.t1_replay for repeat in repeats),
            "t2_replay_mean": _mean_optional(repeat.t2_replay for repeat in repeats),
            "t0_heldout_mean": _mean(repeat.t0_heldout for repeat in repeats),
            "t1_heldout_mean": _mean(repeat.t1_heldout for repeat in repeats),
            "t2_heldout_mean": _mean_optional(repeat.t2_heldout for repeat in repeats),
            "fg_mean": _mean(repeat.fg for repeat in repeats),
            "fg_std": _std(repeat.fg for repeat in repeats),
            "br_mean": _mean(repeat.br for repeat in repeats),
            "br_std": _std(repeat.br for repeat in repeats),
            "br_ratio_mean": _mean(repeat.br_ratio for repeat in repeats),
            "ie_mean": _mean_optional(repeat.ie for repeat in repeats),
            "ie_std": _std_optional(repeat.ie for repeat in repeats),
            "pds_mean": _mean_optional(repeat.pds for repeat in repeats),
            "pds_std": _std_optional(repeat.pds for repeat in repeats),
            "nis_mean": _mean(repeat.nis for repeat in repeats),
            "nis_std": _std(repeat.nis for repeat in repeats),
        },
        "costs": {
            "token_total_mean": _mean(repeat.token_total for repeat in repeats),
            "tool_calls_mean": _mean(repeat.tool_calls_total for repeat in repeats),
            "wall_clock_seconds_mean": _mean(repeat.wall_clock_seconds for repeat in repeats),
            "cost_usd_mean": _mean(repeat.cost_usd for repeat in repeats),
            "human_interventions_mean": _mean(repeat.human_interventions for repeat in repeats),
        },
        "repeats": len(repeats),
        "generated_at": _now_utc(),
        "provenance": {
            "protocol_version": PROTOCOL_VERSION,
        },
    }

    if first.get("benchmark_version"):
        summary["benchmark_version"] = first["benchmark_version"]

    return summary


def _summarize_seed(
    seed_records: list[dict[str, Any]],
    *,
    cost_field: str,
    lambda_penalty: float,
    eps: float,
) -> RepeatSummary:
    t0_replay = _require_score(seed_records, phase="T0", split="replay")
    t1_replay = _require_score(seed_records, phase="T1", split="replay")
    t0_heldout = _require_score(seed_records, phase="T0", split="heldout")
    t1_heldout = _require_score(seed_records, phase="T1", split="heldout")
    t2_replay = _optional_score(seed_records, phase="T2", split="replay")
    t2_heldout = _optional_score(seed_records, phase="T2", split="heldout")
    t2_drift = _optional_score(seed_records, phase="T2", split="drift")
    t2_target = t2_drift if t2_drift is not None else t2_heldout

    protocol_metrics = compute_protocol_metrics(
        t0_replay=t0_replay,
        t1_replay=t1_replay,
        t0_heldout=t0_heldout,
        t1_heldout=t1_heldout,
        t2_target=t2_target,
        cost=_adaptation_cost(seed_records, cost_field),
        lambda_penalty=lambda_penalty,
        eps=eps,
    )

    return RepeatSummary(
        seed=int(seed_records[0]["seed"]),
        t0_replay=t0_replay,
        t1_replay=t1_replay,
        t2_replay=t2_replay,
        t0_heldout=t0_heldout,
        t1_heldout=t1_heldout,
        t2_heldout=t2_heldout,
        fg=float(protocol_metrics["fg"]),
        br=float(protocol_metrics["br"]),
        br_ratio=float(protocol_metrics["br_ratio"]),
        ie=_optional_float(protocol_metrics["ie"]),
        pds=_optional_float(protocol_metrics["pds"]),
        nis=float(protocol_metrics["nis"]),
        token_total=_adaptation_total(seed_records, "token_total"),
        tool_calls_total=_adaptation_total(seed_records, "tool_calls_total"),
        wall_clock_seconds=_adaptation_total(seed_records, "wall_clock_seconds"),
        cost_usd=_adaptation_total(seed_records, "cost_usd"),
        human_interventions=_adaptation_total(seed_records, "human_interventions"),
    )


def _records_for_cost(seed_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    adapt_records = [
        record
        for record in seed_records
        if record["phase"] == "T1" and record["benchmark_split"] == "adapt"
    ]
    if adapt_records:
        return adapt_records

    return [record for record in seed_records if record["phase"] == "T1"]


def _adaptation_cost(seed_records: list[dict[str, Any]], field: str) -> float:
    return _adaptation_total(seed_records, field)


def _adaptation_total(seed_records: list[dict[str, Any]], field: str) -> float:
    total = 0.0
    for record in _records_for_cost(seed_records):
        value = record.get(field, 0) or 0
        total += float(value)
    return total


def _require_score(seed_records: list[dict[str, Any]], *, phase: str, split: str) -> float:
    score = _optional_score(seed_records, phase=phase, split=split)
    if score is None:
        seed = seed_records[0]["seed"]
        raise ValueError(f"Missing score for seed={seed}, phase={phase}, split={split}")
    return score


def _optional_score(seed_records: list[dict[str, Any]], *, phase: str, split: str) -> float | None:
    scores = [
        float(record["score"])
        for record in seed_records
        if record["phase"] == phase and record["benchmark_split"] == split
    ]
    if not scores:
        return None
    return statistics.fmean(scores)


def _mean(values: Any) -> float:
    values_list = [float(value) for value in values]
    return statistics.fmean(values_list)


def _std(values: Any) -> float:
    values_list = [float(value) for value in values]
    if len(values_list) <= 1:
        return 0.0
    return statistics.stdev(values_list)


def _mean_optional(values: Any) -> float | None:
    values_list = [float(value) for value in values if value is not None]
    if not values_list:
        return None
    return statistics.fmean(values_list)


def _std_optional(values: Any) -> float | None:
    values_list = [float(value) for value in values if value is not None]
    if not values_list:
        return None
    if len(values_list) == 1:
        return 0.0
    return statistics.stdev(values_list)


def _optional_float(value: float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _make_summary_id(record: dict[str, Any]) -> str:
    parts = [
        record["benchmark_name"],
        record["path_type"],
        record["model_name"],
        record["agent_name"],
        record["agent_version"],
    ]
    if record.get("benchmark_version"):
        parts.insert(1, record["benchmark_version"])
    return "::".join(parts)


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
