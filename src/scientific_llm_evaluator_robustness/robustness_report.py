from __future__ import annotations

from collections import defaultdict
import html
from pathlib import Path
from statistics import mean
from typing import Any

from .io import read_json


VARIANT_ORDER = ("plain_core", "rhetoric_heavy", "rhetoric_heavier")
SCORE_DIMS = ("soundness", "presentation", "contribution")
SCISTYLEBENCH_SCORE_DIMS = (
    "problem_significance",
    "question_specificity",
    "hypothesis_quality",
    "testability",
    "novelty_contribution",
    "technical_plausibility",
    "scientific_insight",
)


def build_robustness_report(
    *,
    input_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    records = read_json(input_path)
    if not isinstance(records, list):
        raise ValueError("Review input must be a JSON array")

    output_root = Path(output_dir)
    figures_dir = output_root / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    review_rows, variant_order, score_dims, score_scale, dataset_kind = _prepare_review_rows(records)
    comparison_rows = _build_comparison_rows(
        review_rows,
        variant_order=variant_order,
        score_dims=score_dims,
    )
    variant_summary = _summarize_variants(
        comparison_rows,
        variant_order=variant_order,
        score_dims=score_dims,
        score_scale=score_scale,
    )
    overall_summary = _summarize_overall(variant_summary)

    _write_bar_svg(
        figures_dir / "mean_rating_shift.svg",
        title="Mean Rating Shift vs Main",
        values={row["variant_name"]: row["mean_rating_shift"] for row in variant_summary},
        y_label="Rating points",
        signed=True,
    )
    _write_bar_svg(
        figures_dir / "decision_flip_rate.svg",
        title="Decision Flip Rate vs Main",
        values={row["variant_name"]: row["decision_flip_rate"] for row in variant_summary},
        y_label="Flip rate",
        percent=True,
    )
    _write_bar_svg(
        figures_dir / "robustness_index.svg",
        title="Robustness Index by Variant",
        values={row["variant_name"]: row["robustness_index"] for row in variant_summary},
        y_label="0-1 index",
        max_value=1.0,
    )
    _write_heatmap_svg(
        figures_dir / "paper_rating_shift_heatmap.svg",
        comparison_rows,
        value_key="rating_shift",
        variant_order=variant_order,
    )

    return {
        "output_dir": str(output_root),
        "figures_dir": str(figures_dir),
        "dataset_kind": dataset_kind,
        "overall_summary": overall_summary,
        "variant_summary": variant_summary,
    }


def _prepare_review_rows(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], tuple[str, ...], tuple[str, ...], float, str]:
    if records and isinstance(records[0], dict) and "source_review" in records[0] and "variants" in records[0]:
        rows, variant_order = _flatten_scistylebench_records(records)
        return rows, variant_order, SCISTYLEBENCH_SCORE_DIMS, 5.0, "scistylebench"

    return (
        [_flatten_review_record(record) for record in records],
        VARIANT_ORDER,
        SCORE_DIMS,
        4.0,
        "full_paper",
    )


def _flatten_scistylebench_records(
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    rows: list[dict[str, Any]] = []
    variant_names: set[str] = set()
    for record in records:
        source_key = record.get("source_key")
        source_row = _flatten_review_payload(
            review=record.get("source_review", {}),
            paper_key=source_key,
            paper_position=None,
            title=source_key,
            variant_name="main",
            metadata={"discipline": record.get("discipline")},
        )
        rows.append(source_row)
        for variant in record.get("variants", []):
            if not isinstance(variant, dict):
                continue
            variant_name = str(variant.get("variant") or variant.get("variant_group") or "unknown")
            variant_names.add(variant_name)
            rows.append(
                _flatten_review_payload(
                    review=variant.get("review", {}),
                    paper_key=source_key,
                    paper_position=None,
                    title=source_key,
                    variant_name=variant_name,
                    metadata={
                        "discipline": record.get("discipline"),
                        "variant_group": variant.get("variant_group"),
                        "expected_quality_direction": variant.get("expected_quality_direction"),
                    },
                )
            )
    return rows, tuple(sorted(variant_names))


def _flatten_review_record(record: dict[str, Any]) -> dict[str, Any]:
    return _flatten_review_payload(
        review=record.get("review", {}),
        paper_key=record.get("paper_key"),
        paper_position=record.get("paper_position"),
        title=record.get("title"),
        variant_name=record.get("variant_name"),
        metadata=record.get("paper_metadata", {}),
    )


def _flatten_review_payload(
    *,
    review: Any,
    paper_key: Any,
    paper_position: Any,
    title: Any,
    variant_name: Any,
    metadata: Any,
) -> dict[str, Any]:
    if not isinstance(review, dict):
        review = {}
    if not isinstance(metadata, dict):
        metadata = {}

    rating = _score_value(review.get("overall_rating"))
    decision = _extract_decision(review, rating)
    row = {
        "paper_key": paper_key,
        "paper_position": paper_position,
        "title": title,
        "variant_name": variant_name,
        "rating": rating,
        "decision": decision,
        "soundness": _score_value(review.get("soundness")),
        "presentation": _score_value(review.get("presentation")),
        "contribution": _score_value(review.get("contribution")),
        "confidence": _score_value(review.get("confidence")),
        "Rating_gt": metadata.get("Rating_gt"),
        "Rating_pred": metadata.get("Rating_pred"),
        "Decision_gt": metadata.get("Decision_gt"),
        "Decision_pred": metadata.get("Decision_pred"),
        "hardness": metadata.get("hardness"),
    }
    for dim in SCISTYLEBENCH_SCORE_DIMS:
        row[dim] = _score_value(review.get(dim))
    return row


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


def _build_comparison_rows(
    review_rows: list[dict[str, Any]],
    *,
    variant_order: tuple[str, ...],
    score_dims: tuple[str, ...],
) -> list[dict[str, Any]]:
    by_paper: dict[Any, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in review_rows:
        by_paper[row["paper_key"]][row["variant_name"]] = row

    comparison_rows: list[dict[str, Any]] = []
    for paper_key, variants in by_paper.items():
        main = variants.get("main")
        if not main:
            continue
        for variant_name in variant_order:
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
            for dim in score_dims:
                shift = _diff(variant.get(dim), main.get(dim))
                row[f"{dim}_shift"] = shift
                row[f"abs_{dim}_shift"] = abs(shift) if shift is not None else None
                if shift is not None:
                    dim_abs_shifts.append(abs(shift))
            row["mean_abs_score_dim_shift"] = mean(dim_abs_shifts) if dim_abs_shifts else None
            comparison_rows.append(row)
    return comparison_rows


def _summarize_variants(
    comparison_rows: list[dict[str, Any]],
    *,
    variant_order: tuple[str, ...],
    score_dims: tuple[str, ...],
    score_scale: float,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in comparison_rows:
        grouped[row["variant_name"]].append(row)

    summary = []
    for variant_name in variant_order:
        rows = grouped.get(variant_name, [])
        if not rows:
            continue
        mean_abs_rating_shift = _mean_present(row.get("abs_rating_shift") for row in rows)
        mean_abs_score_shift = _mean_present(row.get("mean_abs_score_dim_shift") for row in rows)
        decision_flip_rate = _mean_present(1.0 if row.get("decision_flip") else 0.0 for row in rows)
        rating_stability = 1 - min((mean_abs_rating_shift or 0) / 9, 1)
        score_stability = 1 - min((mean_abs_score_shift or 0) / score_scale, 1)
        decision_stability = 1 - (decision_flip_rate or 0)
        robustness_index = mean([rating_stability, score_stability, decision_stability])
        summary_row = {
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
            "mean_score_shifts": {
                dim: _mean_present(row.get(f"{dim}_shift") for row in rows)
                for dim in score_dims
            },
        }
        for dim in SCORE_DIMS:
            summary_row[f"mean_{dim}_shift"] = _mean_present(row.get(f"{dim}_shift") for row in rows)
        summary.append(summary_row)
    return summary


def _summarize_overall(variant_summary: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n_variants": len(variant_summary),
        "n_review_conditions": len(variant_summary) + 1,
        "mean_rating_shift": _mean_present(row.get("mean_rating_shift") for row in variant_summary),
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


def _write_bar_svg(
    path: Path,
    *,
    title: str,
    values: dict[str, float | None],
    y_label: str,
    percent: bool = False,
    max_value: float | None = None,
    signed: bool = False,
) -> None:
    clean_values = {key: float(value or 0) for key, value in values.items()}
    if signed:
        max_abs = max((abs(value) for value in clean_values.values()), default=0)
        scale_max = max_value or (max_abs * 1.2 if max_abs else 1)
    else:
        max_observed = max(clean_values.values(), default=0)
        scale_max = max_value or (max_observed * 1.2 if max_observed else 1)

    width = max(760, 130 * len(clean_values) + 150)
    height = 420
    left, top, chart_w, chart_h = 90, 70, width - 150, 250
    bar_gap = 28
    bar_w = (chart_w - bar_gap * (len(clean_values) - 1)) / max(len(clean_values), 1)
    colors = ["#5277c3", "#c95f45", "#6c9f58", "#8d63b8"]
    baseline_y = top + chart_h / 2 if signed else top + chart_h

    parts = [_svg_header(width, height), f"<text x='30' y='35' class='title'>{html.escape(title)}</text>"]
    parts.append(f"<text x='30' y='390' class='note'>{html.escape(y_label)}</text>")
    parts.append(f"<line x1='{left}' y1='{baseline_y}' x2='{left + chart_w}' y2='{baseline_y}' class='axis'/>")

    for index, (name, value) in enumerate(clean_values.items()):
        x = left + index * (bar_w + bar_gap)
        if signed:
            bar_h = 0 if scale_max == 0 else (abs(value) / scale_max) * (chart_h / 2)
            y = baseline_y - bar_h if value >= 0 else baseline_y
            fill = "#6c9f58" if value >= 0 else "#c95f45"
        else:
            bar_h = 0 if scale_max == 0 else (value / scale_max) * chart_h
            y = top + chart_h - bar_h
            fill = colors[index % len(colors)]
        label = f"{value:.0%}" if percent else f"{value:.2f}"
        label_y = y - 8 if value >= 0 or not signed else y + bar_h + 18
        parts.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bar_w:.1f}' height='{bar_h:.1f}' fill='{fill}'/>")
        parts.append(f"<text x='{x + bar_w / 2:.1f}' y='{label_y:.1f}' class='label' text-anchor='middle'>{label}</text>")
        parts.append(f"<text x='{x + bar_w / 2:.1f}' y='{top + chart_h + 24:.1f}' class='label' text-anchor='middle'>{html.escape(name)}</text>")
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def _write_heatmap_svg(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    value_key: str,
    variant_order: tuple[str, ...],
) -> None:
    papers = sorted({row["paper_key"] for row in rows})
    variants = [variant for variant in variant_order if any(row["variant_name"] == variant for row in rows)]
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
