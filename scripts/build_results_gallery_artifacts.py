#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SVG_NS = "http://www.w3.org/2000/svg"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate gallery artifacts from suite summary rows.")
    parser.add_argument(
        "--summary",
        required=True,
        nargs="+",
        help="Path to summary.jsonl file(s). The first valid row is used.",
    )
    parser.add_argument(
        "--out-dir",
        default="docs/figures",
        help="Directory for SVG outputs.",
    )
    parser.add_argument("--overwrite", action="store_true", default=True, help="Overwrite existing SVG files.")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print generated artifact paths to stdout.",
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
) -> None:
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


def build_heldout_replay_chart(metrics_row: dict[str, Any], out_path: Path) -> None:
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
    )


def build_fg_br_ie_chart(metrics_row: dict[str, Any], out_path: Path) -> None:
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
    )


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[Path, dict[str, Any]]] = []
    for summary in args.summary:
        summary_path = Path(summary)
        row = load_summary_row(summary_path)
        if row:
            rows.append((summary_path, row))

    if not rows:
        print("no valid summary rows found")
        return 1

    # Use first summary by default; this keeps the script minimal and stable.
    source_path, metrics_row = rows[0]
    run_label = metrics_row.get("run_name") or source_path.parent.name

    heldout_svg = out_dir / "heldout_vs_replay_delta.svg"
    fg_svg = out_dir / "fg_br_ie.svg"

    build_heldout_replay_chart(metrics_row=metrics_row, out_path=heldout_svg)
    build_fg_br_ie_chart(metrics_row=metrics_row, out_path=fg_svg)

    if args.stdout:
        print(f"generated: {heldout_svg}")
        print(f"generated: {fg_svg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
