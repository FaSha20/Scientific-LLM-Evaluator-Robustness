from __future__ import annotations

import csv
import html
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .io import append_jsonl, read_jsonl, write_json
from .llm import CallLLM


IDEA_SCORE_DIMS = (
    "problem_significance",
    "question_specificity",
    "hypothesis_quality",
    "testability",
    "novelty_contribution",
    "technical_plausibility",
    "scientific_insight",
)


def load_scistylebench_rows(csv_path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    input_path = Path(csv_path)
    sample_fields = _read_csv_fieldnames(input_path)

    if "variant_text" in sample_fields and "source_idea_id" in sample_fields:
        variant_rows = _read_csv_rows(input_path, limit=limit)
        source_path = input_path.with_name("source_ideas.csv")
        if source_path.exists():
            return _merge_variant_and_source_rows(
                variant_rows,
                _read_csv_rows(source_path),
            )
        return variant_rows

    if "source_text" in sample_fields and "variant_text" not in sample_fields:
        source_rows = _read_csv_rows(input_path)
        variant_path = input_path.with_name("variant_items_15class.csv")
        if not variant_path.exists():
            raise ValueError(f"Could not find sibling variant file for {input_path}")
        variant_rows = _read_csv_rows(variant_path, limit=limit)
        return _merge_variant_and_source_rows(variant_rows, source_rows)

    return _read_csv_rows(input_path, limit=limit)


def build_summary_idea_input(*, discipline: str | None, idea_text: str) -> str:
    discipline_text = discipline.strip() if isinstance(discipline, str) and discipline.strip() else "Unknown"
    return (
        "A summarized research idea is provided below. Evaluate it as a short idea summary, "
        "not as a full paper.\n\n"
        f"Discipline: {discipline_text}\n\n"
        "Idea Summary:\n"
        f"{idea_text.strip()}"
    )


def generate_scistylebench_reviews(
    *,
    csv_path: str | Path,
    output_dir: str | Path,
    review_prompt_path: str | Path,
    call_llm: CallLLM,
    url: str | None = None,
    api_key: str | None = None,
    model_name: str = "Qwen/Qwen3-4B",
    temperature: float = 0.0,
    max_tokens: int | None = None,
    seed: int | None = None,
    max_retries: int = 3,
    resume: bool = True,
    limit: int | None = None,
    run_label: str | None = None,
    heatmap_sample_size: int = 30,
    heatmap_seed: int = 42,
) -> dict[str, Any]:
    rows = load_scistylebench_rows(csv_path, limit=limit)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    prompt_text = Path(review_prompt_path).read_text(encoding="utf-8")
    source_checkpoint = output_root / "source_reviews_checkpoint.jsonl"
    pair_checkpoint = output_root / "pair_reviews_checkpoint.jsonl"
    completed_sources = _load_source_checkpoint(source_checkpoint) if resume else {}
    completed_pairs = _load_pair_checkpoint(pair_checkpoint) if resume else {}

    source_reviews: dict[str, dict[str, Any]] = dict(completed_sources)
    pair_reviews: dict[str, dict[str, Any]] = dict(completed_pairs)

    unique_sources = _unique_sources(rows)
    total_source_calls = len(unique_sources)
    for index, source in enumerate(unique_sources, start=1):
        source_key = source["source_key"]
        if source_key in source_reviews:
            print(f"[source {index}/{total_source_calls}] Skipping completed {source_key}")
            continue
        print(f"[source {index}/{total_source_calls}] Reviewing source {source_key}")
        review_input = build_summary_idea_input(
            discipline=source.get("discipline"),
            idea_text=str(source["source_text"]),
        )
        review = compact_review(
            call_llm(
                review_input,
                prompt_text,
                jsonify=True,
                temp=temperature,
                url=url,
                api_key=api_key,
                model_name=model_name,
                max_tokens=max_tokens,
                seed=seed,
                max_retries=max_retries,
            )
        )
        payload = {
            "source_key": source_key,
            "discipline": source.get("discipline"),
            "source_text": source.get("source_text"),
            "review": review,
        }
        append_jsonl(source_checkpoint, payload)
        source_reviews[source_key] = payload

    total_pair_calls = len(rows)
    for index, row in enumerate(rows, start=1):
        pair_key = _pair_key(row)
        if pair_key in pair_reviews:
            print(f"[variant {index}/{total_pair_calls}] Skipping completed {pair_key}")
            continue
        print(f"[variant {index}/{total_pair_calls}] Reviewing variant {pair_key}")
        review_input = build_summary_idea_input(
            discipline=row.get("discipline"),
            idea_text=str(row.get("variant_text") or ""),
        )
        review = compact_review(
            call_llm(
                review_input,
                prompt_text,
                jsonify=True,
                temp=temperature,
                url=url,
                api_key=api_key,
                model_name=model_name,
                max_tokens=max_tokens,
                seed=seed,
                max_retries=max_retries,
            )
        )
        payload = {
            "pair_key": pair_key,
            "source_key": _source_key(row),
            "variant": row.get("variant"),
            "variant_group": row.get("variant_group"),
            "expected_quality_direction": normalize_direction(row.get("expected_quality_direction")),
            "variant_text": row.get("variant_text"),
            "review": review,
        }
        append_jsonl(pair_checkpoint, payload)
        pair_reviews[pair_key] = payload

    grouped_reviews = build_grouped_reviews(
        rows=rows,
        source_reviews=source_reviews,
        pair_reviews=pair_reviews,
    )
    summary = summarize_directional_alignment(grouped_reviews)
    heatmap_rows = build_source_rating_heatmap_rows(grouped_reviews)
    sampled_heatmap_rows = sample_source_heatmap_rows(
        heatmap_rows,
        sample_size=heatmap_sample_size,
        seed=heatmap_seed,
    )

    write_json(output_root / "scistylebench_reviews.json", grouped_reviews)
    write_json(output_root / "rating_effect_summary.json", summary)
    write_json(output_root / "sampled_source_variant_ratings.json", sampled_heatmap_rows)
    (output_root / "rating_effect_summary.md").write_text(render_direction_summary(summary), encoding="utf-8")
    write_source_rating_heatmap_svg(output_root / "sampled_source_variant_ratings_heatmap.svg", sampled_heatmap_rows)

    return {
        "output_dir": str(output_root),
        "n_sources": len(grouped_reviews),
        "n_variants": sum(len(record["variants"]) for record in grouped_reviews),
        "reviews_path": str(output_root / "scistylebench_reviews.json"),
        "summary_path": str(output_root / "rating_effect_summary.json"),
        "heatmap_path": str(output_root / "sampled_source_variant_ratings_heatmap.svg"),
    }


def build_grouped_reviews(
    *,
    rows: list[dict[str, Any]],
    source_reviews: dict[str, dict[str, Any]],
    pair_reviews: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for source in _unique_sources(rows):
        source_key = source["source_key"]
        source_review = source_reviews.get(source_key, {}).get("review", {})
        grouped[source_key] = {
            "source_key": source_key,
            "discipline": source.get("discipline"),
            "source_text": source.get("source_text"),
            "source_review": compact_review(source_review),
            "variants": [],
        }

    for row in rows:
        source_key = _source_key(row)
        pair_key = _pair_key(row)
        pair = pair_reviews.get(pair_key)
        if not pair or source_key not in grouped:
            continue

        source_scores = extract_scores(grouped[source_key]["source_review"])
        variant_review = compact_review(pair.get("review", {}))
        variant_scores = extract_scores(variant_review)
        grouped[source_key]["variants"].append(
            {
                "variant": row.get("variant"),
                "variant_group": row.get("variant_group"),
                "expected_quality_direction": normalize_direction(row.get("expected_quality_direction")),
                "variant_text": row.get("variant_text"),
                "review": variant_review,
                "score_shift": {
                    "overall_rating": _subtract_scores(variant_scores["rating"], source_scores["rating"]),
                    "problem_significance": _subtract_scores(
                        variant_scores["problem_significance"],
                        source_scores["problem_significance"],
                    ),
                    "question_specificity": _subtract_scores(
                        variant_scores["question_specificity"],
                        source_scores["question_specificity"],
                    ),
                    "hypothesis_quality": _subtract_scores(
                        variant_scores["hypothesis_quality"],
                        source_scores["hypothesis_quality"],
                    ),
                    "testability": _subtract_scores(
                        variant_scores["testability"],
                        source_scores["testability"],
                    ),
                    "novelty_contribution": _subtract_scores(
                        variant_scores["novelty_contribution"],
                        source_scores["novelty_contribution"],
                    ),
                    "technical_plausibility": _subtract_scores(
                        variant_scores["technical_plausibility"],
                        source_scores["technical_plausibility"],
                    ),
                    "scientific_insight": _subtract_scores(
                        variant_scores["scientific_insight"],
                        source_scores["scientific_insight"],
                    ),
                },
            }
        )

    for record in grouped.values():
        record["variants"].sort(key=lambda item: (str(item.get("variant_group")), str(item.get("variant"))))

    return sorted(grouped.values(), key=lambda item: str(item["source_key"]))


def summarize_directional_alignment(
    grouped_reviews: list[dict[str, Any]],
    *,
    rating_threshold: float = 0.25,
) -> dict[str, Any]:
    rating_rows: list[dict[str, Any]] = []
    for source_record in grouped_reviews:
        source_review = source_record.get("source_review", {})
        source_scores = extract_scores(source_review)
        source_rating = source_scores.get("rating")
        if source_rating is None:
            continue

        for variant in source_record.get("variants", []):
            variant_scores = extract_scores(variant.get("review", {}))
            variant_rating = variant_scores.get("rating")
            if variant_rating is None:
                continue

            shift = variant_rating - source_rating
            expected = normalize_direction(variant.get("expected_quality_direction"))
            predicted = classify_direction(shift, rating_threshold)
            rating_rows.append(
                {
                    "source_key": source_record.get("source_key"),
                    "variant": variant.get("variant"),
                    "variant_group": variant.get("variant_group"),
                    "expected_quality_direction": expected,
                    "predicted_direction": predicted,
                    "source_rating": source_rating,
                    "variant_rating": variant_rating,
                    "rating_shift": shift,
                    "direction_match": predicted == expected,
                }
            )

    return {
        "dataset": {
            "n_sources": len(grouped_reviews),
            "n_variants": len(rating_rows),
        },
        "rating_threshold": rating_threshold,
        "overall": aggregate_rating_rows(rating_rows),
        "by_variant_group": aggregate_rating_rows(rating_rows, group_key="variant_group"),
        "by_variant": aggregate_rating_rows(rating_rows, group_key="variant"),
    }


def build_source_rating_heatmap_rows(grouped_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_record in grouped_reviews:
        source_key = str(source_record.get("source_key"))
        source_review = source_record.get("source_review", {})
        source_rating = _score_value(source_review.get("overall_rating"))
        variant_ratings = {
            str(variant.get("variant") or ""): _score_value(variant.get("review", {}).get("overall_rating"))
            for variant in source_record.get("variants", [])
        }
        variant_shifts = {
            variant_name: _subtract_scores(variant_rating, source_rating)
            for variant_name, variant_rating in variant_ratings.items()
        }
        rows.append(
            {
                "source_key": source_key,
                "discipline": str(source_record.get("discipline") or ""),
                "source_rating": source_rating,
                "variant_ratings": variant_ratings,
                "variant_shifts": variant_shifts,
            }
        )
    return rows


def sample_source_heatmap_rows(rows: list[dict[str, Any]], *, sample_size: int = 30, seed: int = 42) -> list[dict[str, Any]]:
    if sample_size <= 0 or len(rows) <= sample_size:
        return sorted(rows, key=lambda row: row["source_key"])
    rng = random.Random(seed)
    sampled = rng.sample(rows, sample_size)
    return sorted(sampled, key=lambda row: row["source_key"])


def write_source_rating_heatmap_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    variants = sorted({variant for row in rows for variant in row.get("variant_ratings", {}).keys()})
    columns = [("source_rating", "Source")] + [(variant, variant) for variant in variants]
    cell_w, cell_h = 118, 24
    left, top = 230, 70
    width = left + cell_w * len(columns) + 40
    height = top + cell_h * max(len(rows), 1) + 70
    max_abs_shift = max(
        (
            abs(float(shift))
            for row in rows
            for shift in row.get("variant_shifts", {}).values()
            if shift is not None
        ),
        default=1.0,
    )
    parts = [
        _svg_header(width, height),
        "<text x='30' y='35' class='title'>Sampled Source-Centered Rating Shift Heatmap</text>",
        "<text x='30' y='52' class='note'>Cell text = variant rating minus source rating. Color intensity tracks shift magnitude.</text>",
    ]

    for col, (_, label) in enumerate(columns):
        x = left + col * cell_w + cell_w / 2
        parts.append(f"<text x='{x}' y='{top - 15}' class='label' text-anchor='middle'>{html.escape(label)}</text>")

    for row_index, row in enumerate(rows):
        y = top + row_index * cell_h
        discipline = row.get("discipline") or "unknown"
        row_label = f"{row['source_key']} [{discipline}]"
        parts.append(f"<text x='20' y='{y + 16}' class='label'>{html.escape(row_label)}</text>")
        variant_shifts = row.get("variant_shifts", {})
        for col, (key, _) in enumerate(columns):
            x = left + col * cell_w
            if key == "source_rating":
                label = "0.0"
                color = "#eef1f5"
            else:
                shift = variant_shifts.get(key)
                label = "" if shift is None else f"{float(shift):+.1f}"
                color = _shift_color(shift, max_abs_shift)
            parts.append(f"<rect x='{x}' y='{y}' width='{cell_w - 2}' height='{cell_h - 2}' fill='{color}'/>")
            parts.append(f"<text x='{x + cell_w / 2}' y='{y + 16}' class='label' text-anchor='middle'>{html.escape(label)}</text>")

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def _diverging_color(value: float, max_abs: float) -> str:
    if max_abs == 0:
        return "#f4f4f4"
    intensity = min(abs(value) / max_abs, 1.0)
    base = 245
    channel = int(base - intensity * 120)
    if value >= 0:
        return f"rgb({channel},{base},{channel})"
    return f"rgb({base},{channel},{channel})"


def _shift_color(shift: float | None, max_abs_shift: float) -> str:
    if shift is None:
        return "#f4f4f4"
    if abs(float(shift)) < 1e-9:
        return "#eef1f5"
    return _diverging_color(float(shift), max_abs_shift)


def _svg_header(width: int, height: int) -> str:
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
        "<style>.title{font:700 22px Arial}.label{font:12px Arial}.note{font:12px Arial;fill:#555}</style>"
        "<rect width='100%' height='100%' fill='white'/>"
    )


def compact_review(review: Any) -> dict[str, Any]:
    data = review if isinstance(review, dict) else {}
    return {
        "summary": _string_value(data.get("summary")),
        "strengths": _string_list(data.get("strengths")),
        "weaknesses": _string_list(data.get("weaknesses")),
        "suggestions": _string_list(data.get("suggestions")),
        "questions": _string_list(data.get("questions")),
        "problem_significance": _compact_scored_item(data.get("problem_significance")),
        "question_specificity": _compact_scored_item(data.get("question_specificity")),
        "hypothesis_quality": _compact_scored_item(data.get("hypothesis_quality")),
        "testability": _compact_scored_item(data.get("testability")),
        "novelty_contribution": _compact_scored_item(data.get("novelty_contribution")),
        "technical_plausibility": _compact_scored_item(data.get("technical_plausibility")),
        "scientific_insight": _compact_scored_item(data.get("scientific_insight")),
        "overall_rating": _compact_scored_item(data.get("overall_rating")),
        "confidence": _score_value(data.get("confidence")),
    }


def extract_scores(review: dict[str, Any]) -> dict[str, float | None]:
    scores = {"rating": _score_value(review.get("overall_rating"))}
    for dim in IDEA_SCORE_DIMS:
        scores[dim] = _score_value(review.get(dim))
    return scores


def aggregate_rating_rows(
    rows: list[dict[str, Any]],
    *,
    group_key: str | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    if group_key is None:
        return _build_rating_summary(rows)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_key) or "unknown")].append(row)

    results: list[dict[str, Any]] = []
    for group_value, group_rows in sorted(grouped.items(), key=lambda item: item[0]):
        record = _build_rating_summary(group_rows)
        record[group_key] = group_value
        results.append(record)
    return results


def _build_rating_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "n": 0,
            "mean_source_rating": None,
            "mean_variant_rating": None,
            "mean_shift": None,
            "mean_abs_shift": None,
            "direction_accuracy": None,
            "expected_counts": {},
            "predicted_counts": {},
            "confusion": _empty_confusion(),
        }

    return {
        "n": len(rows),
        "mean_source_rating": mean(row["source_rating"] for row in rows),
        "mean_variant_rating": mean(row["variant_rating"] for row in rows),
        "mean_shift": mean(row["rating_shift"] for row in rows),
        "mean_abs_shift": mean(abs(row["rating_shift"]) for row in rows),
        "direction_accuracy": mean(1.0 if row["direction_match"] else 0.0 for row in rows),
        "expected_counts": dict(Counter(row["expected_quality_direction"] for row in rows)),
        "predicted_counts": dict(Counter(row["predicted_direction"] for row in rows)),
        "confusion": build_confusion(rows),
    }


def build_confusion(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    confusion = _empty_confusion()
    for row in rows:
        expected = normalize_direction(row["expected_quality_direction"])
        predicted = normalize_direction(row["predicted_direction"])
        confusion[expected][predicted] += 1
    return confusion


def render_direction_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# SciStyleBench Rating Robustness Summary",
        "",
        f"- Sources: {summary['dataset']['n_sources']}",
        f"- Variants: {summary['dataset']['n_variants']}",
        f"- Rating threshold for 'same': {summary['rating_threshold']}",
        "",
        "## Overall",
        "",
        "| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    overall = summary["overall"]
    lines.append(
        f"| {overall['n']} | {overall['mean_source_rating']:.4f} | {overall['mean_variant_rating']:.4f} | "
        f"{overall['mean_shift']:.4f} | {overall['mean_abs_shift']:.4f} | {overall['direction_accuracy']:.1%} |"
    )

    lines.extend(
        [
            "",
            "## By Variant Group",
            "",
            "| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in summary["by_variant_group"]:
        lines.append(
            f"| {row['variant_group']} | {row['n']} | {row['mean_shift']:.4f} | "
            f"{row['mean_abs_shift']:.4f} | {row['direction_accuracy']:.1%} |"
        )

    lines.extend(
        [
            "",
            "## By Variant",
            "",
            "| Variant | n | Mean shift | Mean abs shift | Direction accuracy |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in summary["by_variant"]:
        lines.append(
            f"| {row['variant']} | {row['n']} | {row['mean_shift']:.4f} | "
            f"{row['mean_abs_shift']:.4f} | {row['direction_accuracy']:.1%} |"
        )
    return "\n".join(lines) + "\n"


def _compact_scored_item(value: Any) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    return {
        "score": _score_value(data.get("score", value)),
        "justification": _string_value(data.get("justification")),
    }


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_string_value(item) for item in value if _string_value(item)]
    text = _string_value(value)
    return [text] if text else []


def _score_value(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("score")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _subtract_scores(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def classify_direction(shift: float, threshold: float) -> str:
    if shift > threshold:
        return "up"
    if shift < -threshold:
        return "down"
    return "same"


def normalize_direction(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text not in {"down", "same", "up"}:
        return "same"
    return text


def _source_key(row: dict[str, Any]) -> str:
    source_id = (
        row.get("annotation_source_id")
        or row.get("source_idea_id")
        or row.get("\ufeffsource_idea_id")
    )
    if not source_id:
        raise ValueError(f"Source row has no unique source ID: {row}")
    return str(source_id)


def _pair_key(row: dict[str, Any]) -> str:
    item_id = (
        row.get("annotation_item_id")
        or row.get("item_id")
        or row.get("\ufeffannotation_item_id")
        or row.get("\ufeffitem_id")
    )
    if not item_id:
        raise ValueError(f"Variant row has no unique item ID: {row}")
    return str(item_id)


def _unique_sources(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = _source_key(row)
        if key in seen:
            continue
        seen.add(key)
        unique.append(
            {
                "source_key": key,
                "discipline": row.get("discipline"),
                "source_text": row.get("source_text"),
            }
        )
    return unique


def _read_csv_fieldnames(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def _read_csv_rows(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(dict(row))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def _merge_variant_and_source_rows(
    variant_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_lookup = {
        str(row.get("source_idea_id") or ""): row
        for row in source_rows
        if row.get("source_idea_id")
    }

    merged_rows: list[dict[str, Any]] = []
    for variant_row in variant_rows:
        merged = dict(variant_row)
        source = source_lookup.get(str(variant_row.get("source_idea_id") or ""))
        if source:
            merged["source_text"] = source.get("source_text", merged.get("source_text"))
            merged["discipline"] = source.get("discipline", merged.get("discipline"))
            merged["base_idea_id"] = source.get("base_idea_id", merged.get("base_idea_id"))
            merged["round_id"] = source.get("round_id", merged.get("round_id"))
        merged_rows.append(merged)
    return merged_rows


def _load_source_checkpoint(path: Path) -> dict[str, dict[str, Any]]:
    completed: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(path):
        key = record.get("source_key")
        if isinstance(key, str):
            completed[key] = record
    return completed


def _load_pair_checkpoint(path: Path) -> dict[str, dict[str, Any]]:
    completed: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(path):
        key = record.get("pair_key")
        if isinstance(key, str):
            completed[key] = record
    return completed


def _empty_confusion() -> dict[str, dict[str, int]]:
    return {direction: {"down": 0, "same": 0, "up": 0} for direction in ("down", "same", "up")}
