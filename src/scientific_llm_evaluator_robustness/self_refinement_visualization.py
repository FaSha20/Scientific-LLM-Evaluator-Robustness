from __future__ import annotations

import argparse
import hashlib
import html
import io
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
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def render_self_refinement_heatmap(title: str, refinement: dict, final_review: dict) -> bytes:
    """Render all draft/final score changes for one self-refined review."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle

    title_lines = textwrap.wrap(title, width=82) or ["Review"]
    top = 120 + 22 * len(title_lines)
    height = top + len(DIMENSIONS) * 46 + 105
    figure = Figure(figsize=(8.8, height / 100), dpi=200, facecolor="white")
    FigureCanvasAgg(figure)
    axes = figure.add_axes((0, 0, 1, 1))
    axes.set_xlim(0, 880)
    axes.set_ylim(height, 0)
    axes.axis("off")
    labels: list[str] = []

    def label(horizontal, vertical, value, size=14, fill="#172033"):
        labels.append(str(value))
        axes.text(horizontal, vertical, str(value), fontsize=size * 0.72,
                  color=fill, fontfamily="DejaVu Sans", va="baseline")

    label(24, 30, "Self-refinement score comparison", 22)
    for index, line in enumerate(title_lines):
        label(24, 55 + index * 22, line)
    label(24, top - 48, "The refinement model re-evaluates the idea, then compares against its previous review.")
    for horizontal, heading in ((24, "Dimension / scale"), (410, "Draft"), (575, "Refined"), (740, "Change")):
        label(horizontal, top - 15, heading)
    draft = refinement.get("draft_review", {})
    for row_index, dimension in enumerate(DIMENSIONS):
        vertical = top + row_index * 46
        maximum = 10 if dimension == "overall_rating" else 5
        label(24, vertical + 26, dimension.replace("_", " ").capitalize() + f" (1–{maximum})", 13)
        before, after = _score(draft.get(dimension)), _score(final_review.get(dimension))
        for column, value in enumerate((before, after)):
            valid = value is not None and 1 <= value <= maximum
            shade = round((value - 1) / (maximum - 1) * 4) if valid else None
            horizontal = 400 + column * 165
            axes.add_patch(Rectangle((horizontal, vertical), 155, 38,
                                     facecolor=PALETTE[shade] if valid else "#eeeeee",
                                     edgecolor="#cbd5e1", linewidth=0.6))
            label(horizontal + 60, vertical + 25, f"{value:g}" if valid else "N/A", 16,
                  "white" if shade == 4 else "#172033")
        change = f"{after - before:+g}" if before is not None and after is not None else "N/A"
        label(750, vertical + 25, change, 16)
    footer = top + len(DIMENSIONS) * 46
    label(24, footer + 25, "Color: relative position within each score scale. Change = refined − draft.")
    for index, color in enumerate(PALETTE):
        axes.add_patch(Rectangle((24 + index * 45, footer + 40), 45, 16, facecolor=color, edgecolor="none"))
    label(265, footer + 54, "Low → high. Scores are not forced to change.", 13)
    output = io.BytesIO()
    figure.savefig(output, format="png", dpi=200, metadata={"Description": "\n".join(labels)})
    return output.getvalue()


def write_self_refinement_visualizations(records: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = ["# Self-refinement score heatmaps", "",
              "All saved source and variant self-refinements; no sampling. Each chart compares the original draft with the final refined review.", ""]
    count = 0
    changed_reviews = 0
    for record in records:
        reviews = [("Source", record.get("source_review_self_refinement"), record.get("source_review", {}))]
        reviews.extend((f"Variant {index}: {variant.get('variant', '')}", variant.get("review_self_refinement"), variant.get("review", {}))
                       for index, variant in enumerate(record.get("variants", []), start=1))
        for kind, refinement, final_review in reviews:
            if not refinement:
                continue
            count += 1
            title = f"{record.get('source_key', 'Unknown source')} — {kind}"
            identity = json.dumps([record.get("source_key"), kind, refinement, final_review], sort_keys=True, ensure_ascii=False)
            digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            filename = f"self_refinement_{digest}.png"
            image_path = output_dir / filename
            if not image_path.exists():
                image_path.write_bytes(render_self_refinement_heatmap(title, refinement, final_review))
            draft = refinement.get("draft_review", {})
            changed = [dimension for dimension in DIMENSIONS if _score(draft.get(dimension)) != _score(final_review.get(dimension))]
            changed_reviews += bool(changed)
            report.extend([f"## {html.escape(title)}", "", f"![Score comparison]({filename})", "",
                           f"Changed score dimensions: {', '.join(changed) if changed else 'none'}.", "",
                           "### Score justifications (draft / refined)", ""])
            for dimension in DIMENSIONS:
                report.extend([f"**{dimension.replace('_', ' ').capitalize()}**", "",
                               "```json", json.dumps({"draft": draft.get(dimension, {}), "refined": final_review.get(dimension, {})}, ensure_ascii=False, indent=2).replace("`", "\\u0060"), "```", ""])
    report[3:3] = [f"Refined reviews: {count}; reviews with at least one changed score: {changed_reviews}.", ""]
    if not count:
        report.append("No self-refinement records found. Run review generation with --self-refine first.")
    path = output_dir / "README.md"
    path.write_text("\n".join(report), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render saved self-refinement scores without additional LLM calls.")
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    records = json.loads(args.input_path.read_text(encoding="utf-8"))
    print(write_self_refinement_visualizations(records, args.output_dir or args.input_path.parent / "self_refinement_heatmaps"))


if __name__ == "__main__":
    main()
