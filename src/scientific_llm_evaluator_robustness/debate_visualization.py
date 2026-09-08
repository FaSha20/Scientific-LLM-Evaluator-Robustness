from __future__ import annotations

import argparse
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


def render_debate_heatmap(title: str, debate: dict, final_review: dict) -> str:
    questions = debate.get("critic_feedback", {}).get("score_questions", [])
    rows = []
    for dimension in DIMENSIONS:
        matches = [(index, question) for index, question in enumerate(questions)
                   if question.get("dimension") == dimension]
        for index, question in matches or [(None, {})]:
            rows.append((dimension, index, question))
    title_lines = textwrap.wrap(title, width=90) or ["Review"]
    top = 125 + 22 * len(title_lines)
    height = top + len(rows) * 46 + 100
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="{height}" viewBox="0 0 1060 {height}" role="img">',
             f'<title>{html.escape(title)} — debate score comparison</title>',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="Arial, sans-serif" fill="#172033">']

    def label(horizontal, vertical, value, size=14, fill="#172033"):
        parts.append(f'<text x="{horizontal}" y="{vertical}" font-size="{size}" fill="{fill}">{html.escape(str(value))}</text>')

    label(24, 30, "Reviewer / critic score comparison", 22)
    for index, line in enumerate(title_lines):
        label(24, 55 + index * 22, line)
    label(24, top - 48, "One review; all dimensions. Critic # refers to zero-based score_questions index.")
    for horizontal, heading in ((24, "Dimension / scale"), (370, "Reviewer before"),
                                (545, "Critic recommended"), (720, "Reviewer after"), (895, "Change")):
        label(horizontal, top - 15, heading)
    draft = debate.get("draft_review", {})
    for row_index, (dimension, feedback_index, question) in enumerate(rows):
        vertical = top + row_index * 46
        maximum = 10 if dimension == "overall_rating" else 5
        suffix = f" · critic #{feedback_index}" if feedback_index is not None else ""
        label(24, vertical + 26, dimension.replace("_", " ").capitalize() + f" (1–{maximum})" + suffix, 13)
        before = _score(draft.get(dimension))
        after = _score(final_review.get(dimension))
        values = (before, _score(question.get("recommended_score")), after)
        for column, value in enumerate(values):
            valid = value is not None and 1 <= value <= maximum
            shade = round((value - 1) / (maximum - 1) * 4) if valid else None
            color = PALETTE[shade] if valid else "#eeeeee"
            horizontal = 360 + column * 175
            parts.append(f'<rect x="{horizontal}" y="{vertical}" width="165" height="38" fill="{color}" stroke="#cbd5e1"/>')
            label(horizontal + 65, vertical + 25, f"{value:g}" if valid else "N/A", 16,
                  "white" if shade == 4 else "#172033")
        change = f"{after - before:+g}" if all(value is not None and 1 <= value <= maximum for value in (before, after)) else "N/A"
        label(920, vertical + 25, change, 16)
    footer = top + len(rows) * 46
    label(24, footer + 25, "Color: relative position within each row's score scale (not a shared raw-score scale).")
    for index, color in enumerate(PALETTE):
        parts.append(f'<rect x="{24 + index * 45}" y="{footer + 40}" width="45" height="16" fill="{color}"/>')
    label(265, footer + 54, "Low → high. Gray N/A = absent, null, or invalid score. Change = after − before.", 13)
    label(24, footer + 80, "Source: scistylebench_reviews.json. Multiple critic recommendations are separate rows; never averaged.", 12)
    parts.append("</g></svg>")
    return "\n".join(parts)


def write_debate_visualizations(records: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = ["# Debate score heatmaps", "",
              "All saved source and variant debates; no sampling. Scores are read from draft, critic, and final review records.", ""]
    count = 0
    for record in records:
        reviews = [("Source", record.get("source_review_debate"), record.get("source_review", {}))]
        reviews.extend((f"Variant {index}: {variant.get('variant', '')}", variant.get("review_debate"), variant.get("review", {}))
                       for index, variant in enumerate(record.get("variants", []), start=1))
        for kind, debate, final_review in reviews:
            if not debate:
                continue
            count += 1
            title = f"{record.get('source_key', 'Unknown source')} — {kind}"
            filename = f"debate_{count:05d}.svg"
            (output_dir / filename).write_text(render_debate_heatmap(title, debate, final_review), encoding="utf-8")
            report.extend([f"## {html.escape(title)}", "", f"![Score comparison]({filename})", "",
                           "### Critic feedback and reviewer rebuttals", ""])
            responses = debate.get("feedback_responses", [])
            if not responses:
                report.extend(["No reviewer rebuttals were saved (for example, an older checkpoint).", ""])
            report.extend(["```json", json.dumps({"critic_feedback": debate.get("critic_feedback", {}),
                                                  "feedback_responses": responses}, ensure_ascii=False, indent=2).replace("`", "\\u0060"), "```", "",
                           "### Score justifications (before / after)", ""])
            for dimension in DIMENSIONS:
                before = debate.get("draft_review", {}).get(dimension, {})
                after = final_review.get(dimension, {})
                report.extend([f"**{dimension.replace('_', ' ').capitalize()}**", "",
                               "```json", json.dumps({"before": before, "after": after}, ensure_ascii=False, indent=2).replace("`", "\\u0060"), "```", ""])
    if not count:
        report.append("No debate records found. Run review generation with --debate first.")
    path = output_dir / "README.md"
    path.write_text("\n".join(report), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render saved debate scores without additional LLM calls.")
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    records = json.loads(args.input_path.read_text(encoding="utf-8"))
    print(write_debate_visualizations(records, args.output_dir or args.input_path.parent / "debate_heatmaps"))


if __name__ == "__main__":
    main()
