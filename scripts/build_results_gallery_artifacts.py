#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

SVG_NS = "http://www.w3.org/2000/svg"
TABLE_COLUMNS: list[tuple[str, str | tuple[str, ...]]] = [
    ("source", "source"),
    ("suite_name", "summary_id"),
    ("benchmark_name", "benchmark_name"),
    ("path_type", "path_type"),
    ("agent_version", "agent_version"),
    ("model_name", "model_name"),
    ("generated_at", "generated_at"),
    ("repeats", "repeats"),
    ("sample_sizes", "sample_sizes"),
    ("t0_replay_mean", ("metrics", "t0_replay_mean")),
    ("t1_replay_mean", ("metrics", "t1_replay_mean")),
    ("t2_replay_mean", ("metrics", "t2_replay_mean")),
    ("t0_heldout_mean", ("metrics", "t0_heldout_mean")),
    ("t1_heldout_mean", ("metrics", "t1_heldout_mean")),
    ("t2_heldout_mean", ("metrics", "t2_heldout_mean")),
    ("fg_mean", ("metrics", "fg_mean")),
    ("br_mean", ("metrics", "br_mean")),
    ("ie_mean", ("metrics", "ie_mean")),
    ("pds_mean", ("metrics", "pds_mean")),
    ("nis_mean", ("metrics", "nis_mean")),
    ("br_ratio_mean", ("metrics", "br_ratio_mean")),
    ("token_total_mean", ("costs", "token_total_mean")),
    ("tool_calls_mean", ("costs", "tool_calls_mean")),
    ("wall_clock_seconds_mean", ("costs", "wall_clock_seconds_mean")),
    ("cost_usd_mean", ("costs", "cost_usd_mean")),
    ("human_interventions_mean", ("costs", "human_interventions_mean")),
]
TABLE_FILENAME = "protocol_summary_snapshot"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate gallery artifacts from suite summary rows.")
    parser.add_argument(
        "--summary",
        required=True,
        nargs="+",
        action="append",
        help="Path to summary.jsonl file(s). Can be repeated.",
    )
    parser.add_argument(
        "--out-dir",
        default="docs/figures",
        help="Directory for SVG outputs.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=True,
        help="Overwrite existing generated SVGs.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print generated artifact paths to stdout.",
    )
    parser.add_argument(
        "--table-dir",
        default="docs/results_table_data",
        help="Directory for JSON/CSV table outputs.",
    )
    parser.add_argument(
        "--table-filename",
        default=TABLE_FILENAME,
        help="Base filename for generated table outputs.",
    )
    return parser.parse_args()


def load_summary_row(summary_path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with summary_path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            text = raw.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    if not rows:
        return {}
    # newest rows are usually final and already sorted; use the last entry if present.
    return rows[-1]


def read_summary_rows(summary_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with summary_path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            text = raw.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


def _extract_nested(row: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = row
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _coerce_scalar(value: Any) -> Any:
    if value is None:
        return "n/a"
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def build_summary_table_rows(summary_paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary_path in summary_paths:
        source_rows = read_summary_rows(summary_path)
        if not source_rows:
            continue

        source_row = source_rows[-1]
        entry: dict[str, Any] = {}
        for column, source in TABLE_COLUMNS:
            if source == "source":
                value: Any = str(summary_path)
            elif isinstance(source, tuple):
                value = _extract_nested(source_row, source)
            else:
                value = source_row.get(source)
            if isinstance(value, float):
                value = round(value, 6)
            elif isinstance(value, dict):
                value = json.dumps(value, sort_keys=True)
            entry[column] = _coerce_scalar(value)
        rows.append(entry)
    return rows


def write_table_artifacts(rows: list[dict[str, Any]], *, out_dir: Path, base: str) -> None:
    if not rows:
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{base}.json"
    csv_path = out_dir / f"{base}.csv"

    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[column for column, _ in TABLE_COLUMNS])
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "n/a") for column in writer.fieldnames})


def svg_canvas(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"#ffffff\"/>",
    ]


def svg_text(x: float, y: float, text: str, size: int = 13, weight: str = "normal", color: str = "#111827") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" fill="{color}" font-weight="{weight}">{text}</text>'
    )


def svg_bar_chart(
    metrics: dict[str, float],
    out_path: Path,
    title: str,
    y_label: str,
    palette: list[str],
    overwrite: bool,
) -> None:
    if out_path.exists() and not overwrite:
        return
    width, height = 900, 420
    left, right, top, bottom = 80, 40, 30, 80
    plot_h = height - top - bottom
    plot_w = width - left - right
    max_value = max(metrics.values(), default=1.0)
    max_value = max(max_value, 1.0) if max_value > 0 else 1.0
    y_top = top + 10
    y_bottom = height - bottom
    x_step = plot_w / max(2, len(metrics))

    lines: list[str] = svg_canvas(width, height)
    lines.append(f'<text x="{left}" y="{top - 8}" font-family="Arial" font-size="16" font-weight="700">{title}</text>')
    lines.append(f'<line x1="{left}" y1="{y_top}" x2="{left}" y2="{y_bottom}" stroke="#6b7280" stroke-width="1"/>')
    lines.append(f'<line x1="{left}" y1="{y_bottom}" x2="{width-right}" y2="{y_bottom}" stroke="#6b7280" stroke-width="1"/>')

    for idx, (label, value) in enumerate(metrics.items()):
        bar_h = (value / max_value) * (plot_h - 10)
        x = left + idx * x_step + x_step * 0.2
        w = x_step * 0.6
        y = y_bottom - bar_h
        color = palette[idx % len(palette)] if palette else "#2563eb"
        lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{bar_h:.2f}" fill="{color}" opacity="0.85"/>')
        lines.append(f'<text x="{x + w / 2:.2f}" y="{y - 6:.2f}" text-anchor="middle" font-size="11" fill="#111827">{value:.3f}</text>')
        lines.append(f'<text x="{x + w / 2:.2f}" y="{y_bottom + 18:.2f}" text-anchor="middle" font-size="12" fill="#374151">{label}</text>')

    lines.append(svg_text(14, height - 28, "0.0", 11, color="#6b7280"))
    lines.append(svg_text(width - right + 10, y_bottom + 2, f"{max_value:.2f}", 11, color="#6b7280"))
    lines.append(
        f'<text x="{width / 2}" y="{height - 16}" text-anchor="middle" font-size="12" fill="#374151">{y_label}</text>'
    )
    lines.append("</svg>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def extract_metric(row: dict[str, Any], key: str) -> float | None:
    value = row.get("metrics", {}).get(key)
    if value is None:
        return None
    try:
        value_float = float(value)
    except (TypeError, ValueError):
        return None
    return value_float


def build_heldout_replay_chart(metrics_row: dict[str, Any], out_path: Path, overwrite: bool) -> None:
    keys = [
        ("T0 Replay", extract_metric(metrics_row, "t0_replay_mean")),
        ("T1 Replay", extract_metric(metrics_row, "t1_replay_mean")),
        ("T0 Heldout", extract_metric(metrics_row, "t0_heldout_mean")),
        ("T1 Heldout", extract_metric(metrics_row, "t1_heldout_mean")),
    ]
    values = {label: value for label, value in keys if value is not None}
    if not values:
        return
    svg_bar_chart(
        values,
        out_path=out_path,
        title="Heldout and Replay Mean Score Snapshot",
        y_label="Score",
        palette=["#2563eb", "#16a34a", "#9333ea", "#f97316"],
        overwrite=overwrite,
    )


def build_fg_br_ie_chart(metrics_row: dict[str, Any], out_path: Path, overwrite: bool) -> None:
    raw = {
        "FG": extract_metric(metrics_row, "fg_mean"),
        "|BR|": abs(extract_metric(metrics_row, "br_mean") or 0.0),
        "|IE|": abs(extract_metric(metrics_row, "ie_mean") or 0.0),
    }
    values = {label: value for label, value in raw.items() if value is not None}
    if not values:
        return
    svg_bar_chart(
        values,
        out_path=out_path,
        title="FG / BR / IE Profile",
        y_label="Metric Magnitude",
        palette=["#0369a1", "#0369a1", "#db2777"],
        overwrite=overwrite,
    )


def build_cost_vs_gain_chart(metrics_row: dict[str, Any], out_path: Path, overwrite: bool) -> None:
    costs = metrics_row.get("costs", {})
    raw = {
        "FG": extract_metric(metrics_row, "fg_mean"),
        "IE": extract_metric(metrics_row, "ie_mean"),
        "BR": extract_metric(metrics_row, "br_mean"),
        "Tokens": _coerce_scalar(costs.get("token_total_mean")),
        "Tool calls": _coerce_scalar(costs.get("tool_calls_mean")),
        "Wall clock (s)": _coerce_scalar(costs.get("wall_clock_seconds_mean")),
    }

    values = {}
    for label, value in raw.items():
        if value is None or value == "n/a":
            continue
        if isinstance(value, bool):
            value = int(value)
        try:
            value_float = float(value)
        except (TypeError, ValueError):
            continue
        values[label] = value_float

    if len(values) < 2:
        return
    svg_bar_chart(
        values,
        out_path=out_path,
        title="Cost and Metric Delta Summary",
        y_label="Metric / Cost Magnitude",
        palette=["#2563eb", "#db2777", "#f97316", "#16a34a", "#9333ea", "#111827"],
        overwrite=overwrite,
    )


def build_t0_t1_t2_stability_chart(metrics_row: dict[str, Any], out_path: Path, overwrite: bool) -> None:
    raw = {
        "T0 Replay": extract_metric(metrics_row, "t0_replay_mean"),
        "T1 Replay": extract_metric(metrics_row, "t1_replay_mean"),
        "T2 Replay": extract_metric(metrics_row, "t2_replay_mean"),
        "T0 Heldout": extract_metric(metrics_row, "t0_heldout_mean"),
        "T1 Heldout": extract_metric(metrics_row, "t1_heldout_mean"),
        "T2 Heldout": extract_metric(metrics_row, "t2_heldout_mean"),
        "PDS": extract_metric(metrics_row, "pds_mean"),
    }
    values = {label: value for label, value in raw.items() if value is not None}
    if len(values) < 2:
        return
    svg_bar_chart(
        values,
        out_path=out_path,
        title="T0/T1/T2 Stability Snapshot",
        y_label="Score / PDS",
        palette=["#2563eb", "#16a34a", "#9333ea", "#ea580c", "#7c3aed", "#0ea5e9", "#334155"],
        overwrite=overwrite,
    )


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[Path, dict[str, Any]]] = []
    summary_paths: list[Path] = []
    for summary in args.summary:
        if isinstance(summary, list):
            summary_paths.extend(summary)
        else:
            summary_paths.append(summary)

    rows: list[tuple[Path, dict[str, Any]]] = []
    for summary in summary_paths:
        summary_path = Path(summary)
        row = load_summary_row(summary_path)
        if row:
            rows.append((summary_path, row))

    if not rows:
        print("no valid summary rows found")
        return 1

    # Use first summary by default; this keeps the script minimal and stable.
    _, metrics_row = rows[0]

    heldout_svg = out_dir / "heldout_vs_replay_delta.svg"
    fg_svg = out_dir / "fg_br_ie.svg"
    cost_svg = out_dir / "cost_vs_gain.svg"
    stability_svg = out_dir / "t0_t1_t2_stability.svg"

    build_heldout_replay_chart(
        metrics_row=metrics_row, out_path=heldout_svg, overwrite=args.overwrite
    )
    build_fg_br_ie_chart(metrics_row=metrics_row, out_path=fg_svg, overwrite=args.overwrite)
    build_cost_vs_gain_chart(metrics_row=metrics_row, out_path=cost_svg, overwrite=args.overwrite)
    build_t0_t1_t2_stability_chart(
        metrics_row=metrics_row, out_path=stability_svg, overwrite=args.overwrite
    )

    table_rows = build_summary_table_rows([path for path, _ in rows])
    table_dir = Path(args.table_dir)
    write_table_artifacts(table_rows, out_dir=table_dir, base=args.table_filename)

    if args.stdout:
        print(f"generated: {heldout_svg}")
        print(f"generated: {fg_svg}")
        print(f"generated: {cost_svg}")
        print(f"generated: {stability_svg}")
        print(f"generated: {table_dir / f'{args.table_filename}.json'}")
        print(f"generated: {table_dir / f'{args.table_filename}.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
