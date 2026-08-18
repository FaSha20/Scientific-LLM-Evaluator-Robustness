from __future__ import annotations

from collections import defaultdict
import csv
from datetime import datetime
import html
import json
from pathlib import Path
from statistics import mean
from typing import Any

from .io import read_json, write_json


VARIANT_ORDER = ("plain_core", "rhetoric_heavy", "rhetoric_heavier")
SCORE_DIMS = ("soundness", "presentation", "contribution")


def build_robustness_report(
    *,
    input_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    records = read_json(input_path)
    if not isinstance(records, list):
        raise ValueError("Review input must be a JSON array")

    output_root = Path(output_dir)
    dirs = {
        "data": output_root / "data",
        "tables": output_root / "tables",
        "figures": output_root / "figures",
        "text": output_root / "text",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    review_rows = [_flatten_review_record(record) for record in records]
    comparison_rows = _build_comparison_rows(review_rows)
    variant_summary = _summarize_variants(comparison_rows)
    overall_summary = _summarize_overall(variant_summary)

    write_json(dirs["data"] / "review_rows.json", review_rows)
    write_json(dirs["data"] / "comparison_rows.json", comparison_rows)
    write_json(dirs["data"] / "variant_summary.json", variant_summary)
    write_json(dirs["data"] / "overall_summary.json", overall_summary)
    _write_csv(dirs["tables"] / "review_rows.csv", review_rows)
    _write_csv(dirs["tables"] / "comparison_rows.csv", comparison_rows)
    _write_csv(dirs["tables"] / "variant_summary.csv", variant_summary)

    _write_bar_svg(
        dirs["figures"] / "mean_absolute_rating_shift.svg",
        title="Mean Absolute Rating Shift vs Main",
        values={row["variant_name"]: row["mean_abs_rating_shift"] for row in variant_summary},
        y_label="Rating points",
    )
    _write_bar_svg(
        dirs["figures"] / "decision_flip_rate.svg",
        title="Decision Flip Rate vs Main",
        values={row["variant_name"]: row["decision_flip_rate"] for row in variant_summary},
        y_label="Flip rate",
        percent=True,
    )
    _write_bar_svg(
        dirs["figures"] / "robustness_index.svg",
        title="Robustness Index by Variant",
        values={row["variant_name"]: row["robustness_index"] for row in variant_summary},
        y_label="0-1 index",
        max_value=1.0,
    )
    _write_heatmap_svg(
        dirs["figures"] / "paper_rating_shift_heatmap.svg",
        comparison_rows,
        value_key="rating_shift",
    )

    report_text = _build_markdown_report(
        input_path=Path(input_path),
        output_root=output_root,
        review_rows=review_rows,
        comparison_rows=comparison_rows,
        variant_summary=variant_summary,
        overall_summary=overall_summary,
    )
    (dirs["text"] / "robustness_report.md").write_text(report_text, encoding="utf-8")

    return {
        "output_dir": str(output_root),
        "data_dir": str(dirs["data"]),
        "tables_dir": str(dirs["tables"]),
        "figures_dir": str(dirs["figures"]),
        "text_dir": str(dirs["text"]),
        "overall_summary": overall_summary,
    }


def _flatten_review_record(record: dict[str, Any]) -> dict[str, Any]:
    review = record.get("review", {})
    if not isinstance(review, dict):
        review = {}

    rating = _score_value(review.get("overall_rating"))
    decision = _extract_decision(review, rating)
    return {
        "paper_key": record.get("paper_key"),
        "paper_position": record.get("paper_position"),
        "title": record.get("title"),
        "variant_name": record.get("variant_name"),
        "rating": rating,
        "decision": decision,
        "soundness": _score_value(review.get("soundness")),
        "presentation": _score_value(review.get("presentation")),
        "contribution": _score_value(review.get("contribution")),
        "confidence": _score_value(review.get("confidence")),
        "Rating_gt": record.get("paper_metadata", {}).get("Rating_gt"),
        "Rating_pred": record.get("paper_metadata", {}).get("Rating_pred"),
        "Decision_gt": record.get("paper_metadata", {}).get("Decision_gt"),
        "Decision_pred": record.get("paper_metadata", {}).get("Decision_pred"),
        "hardness": record.get("paper_metadata", {}).get("hardness"),
    }


def _score_value(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("score")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _extract_decision(review: dict[str, Any], rating: float | None) -> str | None:
    decision = review.get("decision")
    if isinstance(decision, str) and decision.strip():
        return decision.strip()
    meta = review.get("meta_review")
    if isinstance(meta, dict) and isinstance(meta.get("decision"), str):
        return meta["decision"].strip()
    if rating is None:
        return None
    return "Accept" if rating >= 6 else "Reject"


def _build_comparison_rows(review_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_paper: dict[Any, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in review_rows:
        by_paper[row["paper_key"]][row["variant_name"]] = row

    comparison_rows: list[dict[str, Any]] = []
    for paper_key, variants in by_paper.items():
        main = variants.get("main")
        if not main:
            continue
        for variant_name in VARIANT_ORDER:
            variant = variants.get(variant_name)
            if not variant:
                continue
            row = {
                "paper_key": paper_key,
                "paper_position": main.get("paper_position"),
                "title": main.get("title"),
                "variant_name": variant_name,
                "main_rating": main.get("rating"),
                "variant_rating": variant.get("rating"),
                "rating_shift": _diff(variant.get("rating"), main.get("rating")),
                "abs_rating_shift": _abs_diff(variant.get("rating"), main.get("rating")),
                "main_decision": main.get("decision"),
                "variant_decision": variant.get("decision"),
                "decision_flip": _decision_flip(main.get("decision"), variant.get("decision")),
                "hardness": main.get("hardness"),
                "Rating_gt": main.get("Rating_gt"),
                "Rating_pred": main.get("Rating_pred"),
            }
            dim_abs_shifts = []
            for dim in SCORE_DIMS:
                shift = _diff(variant.get(dim), main.get(dim))
                row[f"{dim}_shift"] = shift
                row[f"abs_{dim}_shift"] = abs(shift) if shift is not None else None
                if shift is not None:
                    dim_abs_shifts.append(abs(shift))
            row["mean_abs_score_dim_shift"] = mean(dim_abs_shifts) if dim_abs_shifts else None
            comparison_rows.append(row)
    return comparison_rows


def _summarize_variants(comparison_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in comparison_rows:
        grouped[row["variant_name"]].append(row)

    summary = []
    for variant_name in VARIANT_ORDER:
        rows = grouped.get(variant_name, [])
        if not rows:
            continue
        mean_abs_rating_shift = _mean_present(row.get("abs_rating_shift") for row in rows)
        mean_abs_score_shift = _mean_present(row.get("mean_abs_score_dim_shift") for row in rows)
        decision_flip_rate = _mean_present(1.0 if row.get("decision_flip") else 0.0 for row in rows)
        rating_stability = 1 - min((mean_abs_rating_shift or 0) / 9, 1)
        score_stability = 1 - min((mean_abs_score_shift or 0) / 4, 1)
        decision_stability = 1 - (decision_flip_rate or 0)
        robustness_index = mean([rating_stability, score_stability, decision_stability])
        summary.append(
            {
                "variant_name": variant_name,
                "n_papers": len(rows),
                "mean_rating_shift": _mean_present(row.get("rating_shift") for row in rows),
                "mean_abs_rating_shift": mean_abs_rating_shift,
                "max_abs_rating_shift": max(_present(row.get("abs_rating_shift") for row in rows), default=None),
                "mean_abs_score_dim_shift": mean_abs_score_shift,
                "decision_flip_rate": decision_flip_rate,
                "rating_stability": rating_stability,
                "score_stability": score_stability,
                "decision_stability": decision_stability,
                "robustness_index": robustness_index,
            }
        )
    return summary


def _summarize_overall(variant_summary: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n_variants": len(variant_summary),
        "n_review_conditions": len(variant_summary) + 1,
        "mean_abs_rating_shift": _mean_present(row.get("mean_abs_rating_shift") for row in variant_summary),
        "mean_decision_flip_rate": _mean_present(row.get("decision_flip_rate") for row in variant_summary),
        "mean_robustness_index": _mean_present(row.get("robustness_index") for row in variant_summary),
        "least_robust_variant": min(
            variant_summary,
            key=lambda row: row.get("robustness_index", 1),
            default={},
        ).get("variant_name"),
    }


def _diff(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def _abs_diff(left: Any, right: Any) -> float | None:
    value = _diff(left, right)
    return abs(value) if value is not None else None


def _decision_flip(left: Any, right: Any) -> bool | None:
    if left is None or right is None:
        return None
    return str(left).strip().lower() != str(right).strip().lower()


def _present(values: Any) -> list[float]:
    return [float(value) for value in values if value is not None]


def _mean_present(values: Any) -> float | None:
    present = _present(values)
    return mean(present) if present else None


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_bar_svg(
    path: Path,
    *,
    title: str,
    values: dict[str, float | None],
    y_label: str,
    percent: bool = False,
    max_value: float | None = None,
) -> None:
    clean_values = {key: float(value or 0) for key, value in values.items()}
    max_observed = max(clean_values.values(), default=0)
    scale_max = max_value or (max_observed * 1.2 if max_observed else 1)
    width, height = 760, 420
    left, top, chart_w, chart_h = 90, 70, 610, 250
    bar_gap = 28
    bar_w = (chart_w - bar_gap * (len(clean_values) - 1)) / max(len(clean_values), 1)
    colors = ["#5277c3", "#c95f45", "#6c9f58", "#8d63b8"]
    parts = [_svg_header(width, height), f"<text x='30' y='35' class='title'>{html.escape(title)}</text>"]
    parts.append(f"<text x='30' y='390' class='note'>{html.escape(y_label)}</text>")
    parts.append(f"<line x1='{left}' y1='{top + chart_h}' x2='{left + chart_w}' y2='{top + chart_h}' class='axis'/>")
    for index, (name, value) in enumerate(clean_values.items()):
        x = left + index * (bar_w + bar_gap)
        bar_h = 0 if scale_max == 0 else (value / scale_max) * chart_h
        y = top + chart_h - bar_h
        label = f"{value:.0%}" if percent else f"{value:.2f}"
        parts.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bar_w:.1f}' height='{bar_h:.1f}' fill='{colors[index % len(colors)]}'/>")
        parts.append(f"<text x='{x + bar_w / 2:.1f}' y='{y - 8:.1f}' class='label' text-anchor='middle'>{label}</text>")
        parts.append(f"<text x='{x + bar_w / 2:.1f}' y='{top + chart_h + 24:.1f}' class='label' text-anchor='middle'>{html.escape(name)}</text>")
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_heatmap_svg(path: Path, rows: list[dict[str, Any]], *, value_key: str) -> None:
    papers = sorted({row["paper_key"] for row in rows})
    variants = [variant for variant in VARIANT_ORDER if any(row["variant_name"] == variant for row in rows)]
    cell_w, cell_h = 150, 34
    left, top = 180, 70
    width = left + cell_w * len(variants) + 40
    height = top + cell_h * len(papers) + 80
    max_abs = max((abs(float(row[value_key])) for row in rows if row.get(value_key) is not None), default=1)
    lookup = {(row["paper_key"], row["variant_name"]): row for row in rows}
    parts = [_svg_header(width, height), "<text x='30' y='35' class='title'>Rating Shift by Paper and Variant</text>"]
    for col, variant in enumerate(variants):
        x = left + col * cell_w + cell_w / 2
        parts.append(f"<text x='{x}' y='{top - 15}' class='label' text-anchor='middle'>{html.escape(variant)}</text>")
    for row_index, paper in enumerate(papers):
        y = top + row_index * cell_h
        parts.append(f"<text x='20' y='{y + 22}' class='label'>{html.escape(str(paper))}</text>")
        for col, variant in enumerate(variants):
            x = left + col * cell_w
            row = lookup.get((paper, variant), {})
            value = row.get(value_key)
            color = _diverging_color(float(value or 0), max_abs)
            label = "" if value is None else f"{float(value):+.1f}"
            parts.append(f"<rect x='{x}' y='{y}' width='{cell_w - 2}' height='{cell_h - 2}' fill='{color}'/>")
            parts.append(f"<text x='{x + cell_w / 2}' y='{y + 22}' class='label' text-anchor='middle'>{label}</text>")
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def _diverging_color(value: float, max_abs: float) -> str:
    if max_abs == 0:
        return "#f4f4f4"
    intensity = min(abs(value) / max_abs, 1)
    base = 245
    channel = int(base - intensity * 120)
    if value >= 0:
        return f"rgb({channel},{base},{channel})"
    return f"rgb({base},{channel},{channel})"


def _svg_header(width: int, height: int) -> str:
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
        "<style>.title{font:700 22px Arial}.label{font:13px Arial}.note{font:12px Arial;fill:#555}.axis{stroke:#333;stroke-width:1}</style>"
        "<rect width='100%' height='100%' fill='white'/>"
    )


def _build_markdown_report(
    *,
    input_path: Path,
    output_root: Path,
    review_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    variant_summary: list[dict[str, Any]],
    overall_summary: dict[str, Any],
) -> str:
    n_papers = len({row["paper_key"] for row in review_rows})
    n_reviews = len(review_rows)
    n_conditions = overall_summary.get("n_review_conditions", len(variant_summary) + 1)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    least = overall_summary.get("least_robust_variant") or "n/a"
    robustness = _fmt(overall_summary.get("mean_robustness_index"))
    mean_shift = _fmt(overall_summary.get("mean_abs_rating_shift"))
    flip_rate = _fmt_pct(overall_summary.get("mean_decision_flip_rate"))

    lines = [
        "# Robustness of LLM Reviews to Style Variants",
        "",
        "## Executive Summary",
        "",
        f"- **Scope:** {n_reviews} generated reviews across {n_papers} papers and {n_conditions} review conditions: `main` plus {len(variant_summary)} style variants, using `{input_path}`.",
        f"- **Overall robustness index:** {robustness} on a 0-1 scale, where higher means smaller rating, score, and decision drift from the main version.",
        f"- **Average absolute rating shift:** {mean_shift} rating points versus the main full-paper review.",
        f"- **Average decision flip rate:** {flip_rate} across variants.",
        f"- **Least robust condition:** `{least}` had the lowest robustness index.",
        "",
        "## Metric Definitions",
        "",
        "- **Rating shift:** variant overall rating minus main overall rating for the same paper.",
        "- **Mean absolute rating shift:** average absolute rating movement on the 1-10 review scale.",
        "- **Decision flip rate:** share of papers where the inferred accept/reject decision changes relative to main.",
        "- **Score-dimension drift:** average absolute movement in soundness, presentation, and contribution scores.",
        "- **Robustness index:** average of rating stability, score stability, and decision stability. Rating stability normalizes by the 1-10 range; score stability normalizes by the 1-5 range.",
        "",
        "## Variant-Level Results",
        "",
        "| Variant | n | Mean rating shift | Mean abs rating shift | Decision flip rate | Score drift | Robustness index |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in variant_summary:
        lines.append(
            "| {variant_name} | {n_papers} | {mean_rating_shift} | {mean_abs_rating_shift} | {decision_flip_rate} | {mean_abs_score_dim_shift} | {robustness_index} |".format(
                variant_name=row["variant_name"],
                n_papers=row["n_papers"],
                mean_rating_shift=_fmt(row.get("mean_rating_shift")),
                mean_abs_rating_shift=_fmt(row.get("mean_abs_rating_shift")),
                decision_flip_rate=_fmt_pct(row.get("decision_flip_rate")),
                mean_abs_score_dim_shift=_fmt(row.get("mean_abs_score_dim_shift")),
                robustness_index=_fmt(row.get("robustness_index")),
            )
        )
    lines.extend(
        [
            "",
            "## Visual Outputs",
            "",
            "- `figures/mean_absolute_rating_shift.svg`: rating drift magnitude by variant.",
            "- `figures/decision_flip_rate.svg`: accept/reject instability by variant.",
            "- `figures/robustness_index.svg`: combined robustness score by variant.",
            "- `figures/paper_rating_shift_heatmap.svg`: per-paper rating shifts.",
            "",
            "## Caveats",
            "",
            "- The decision is inferred from `overall_rating >= 6` when the review output does not include an explicit decision.",
            "- The report measures robustness of the reviewer model to style variants, not scientific correctness of the variants themselves.",
            "- Small sample sizes should be interpreted as diagnostic evidence rather than final statistical proof.",
            "",
            "## Output Inventory",
            "",
            f"- Data JSON: `{output_root / 'data'}`",
            f"- Tables CSV: `{output_root / 'tables'}`",
            f"- Figures SVG: `{output_root / 'figures'}`",
            f"- Text report: `{output_root / 'text' / 'robustness_report.md'}`",
            "",
            f"_Generated at {generated_at}._",
        ]
    )
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.3f}"


def _fmt_pct(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.1%}"
