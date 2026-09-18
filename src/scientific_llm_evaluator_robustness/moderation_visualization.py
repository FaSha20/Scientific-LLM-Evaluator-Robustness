from __future__ import annotations

import html
import json
import math
import textwrap
from pathlib import Path


DIMENSIONS = (
    "problem_significance", "question_specificity", "hypothesis_quality",
    "testability", "novelty_contribution", "technical_plausibility",
    "scientific_insight", "overall_rating",
)
PALETTE = ("#eff6ff", "#dbeafe", "#93c5fd", "#60a5fa", "#2563eb")


def _score(value):
    if isinstance(value, dict):
        value = value.get("score")
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def render_moderation_heatmap(title: str, moderation: dict, final_review: dict) -> str:
    technical = moderation.get("technical_review", {})
    rhetoric = moderation.get("rhetoric_review", {})
    title_lines = textwrap.wrap(title, width=90) or ["Review"]
    top = 125 + 22 * len(title_lines)
    height = top + len(DIMENSIONS) * 46 + 100
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="{height}" viewBox="0 0 1060 {height}" role="img">',
        f'<title>{html.escape(title)} — moderated review score comparison</title>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial, sans-serif" fill="#172033">',
    ]

    def label(horizontal, vertical, value, size=14, fill="#172033"):
        parts.append(f'<text x="{horizontal}" y="{vertical}" font-size="{size}" fill="{fill}">{html.escape(str(value))}</text>')

    label(24, 30, "Independent reviewers / moderator score comparison", 22)
    for index, line in enumerate(title_lines):
        label(24, 55 + index * 22, line)
    label(24, top - 48, "Two independent reviews; the moderator synthesizes the final review.")
    for horizontal, heading in ((24, "Dimension / scale"), (370, "Technical reviewer"),
                                (545, "Rhetoric auditor"), (720, "Moderator final")):
        label(horizontal, top - 15, heading)

    for row_index, dimension in enumerate(DIMENSIONS):
        vertical = top + row_index * 46
        maximum = 10 if dimension == "overall_rating" else 5
        label(24, vertical + 26, dimension.replace("_", " ").capitalize() + f" (1–{maximum})", 13)
        values = (_score(technical.get(dimension)), _score(rhetoric.get(dimension)), _score(final_review.get(dimension)))
        for column, value in enumerate(values):
            valid = value is not None and 1 <= value <= maximum
            shade = round((value - 1) / (maximum - 1) * 4) if valid else None
            color = PALETTE[shade] if valid else "#eeeeee"
            horizontal = 360 + column * 175
            parts.append(f'<rect x="{horizontal}" y="{vertical}" width="165" height="38" fill="{color}" stroke="#cbd5e1"/>')
            label(horizontal + 65, vertical + 25, f"{value:g}" if valid else "N/A", 16,
                  "white" if shade == 4 else "#172033")

    footer = top + len(DIMENSIONS) * 46
    label(24, footer + 25, "Color: relative position within each row's score scale (not a shared raw-score scale).")
    for index, color in enumerate(PALETTE):
        parts.append(f'<rect x="{24 + index * 45}" y="{footer + 40}" width="45" height="16" fill="{color}"/>')
    label(265, footer + 54, "Low → high. Gray N/A = absent, null, or invalid score.", 13)
    label(24, footer + 80, "Source: scistylebench_reviews.json. Scores are never mechanically averaged.", 12)
    parts.append("</g></svg>")
    return "\n".join(parts)


def write_moderation_visualizations(records: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = ["# Moderated review score heatmaps", "", "Technical and rhetoric reviews are independent; the moderator produces the final review.", ""]
    count = 0
    for record in records:
        reviews = [("Source", record.get("source_review_moderation"), record.get("source_review", {}))]
        reviews.extend(
            (f"Variant {index}: {variant.get('variant', '')}", variant.get("review_moderation"), variant.get("review", {}))
            for index, variant in enumerate(record.get("variants", []), start=1)
        )
        for kind, moderation, final_review in reviews:
            if not moderation:
                continue
            count += 1
            title = f"{record.get('source_key', 'Unknown source')} — {kind}"
            filename = f"moderation_{count:05d}.svg"
            (output_dir / filename).write_text(render_moderation_heatmap(title, moderation, final_review), encoding="utf-8")
            report.extend([
                f"## {html.escape(title)}", "", f"![Score comparison]({filename})", "",
                "### Independent reviews", "", "```json",
                json.dumps(moderation, ensure_ascii=False, indent=2).replace("`", "\\u0060"), "```", "",
            ])
    if not count:
        report.append("No moderation records found. Run review generation with --moderated-panel first.")
    path = output_dir / "README.md"
    path.write_text("\n".join(report), encoding="utf-8")
    return path
