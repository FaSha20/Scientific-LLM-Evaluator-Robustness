from __future__ import annotations

import argparse
import html
import hashlib
import io
import json
import math
import textwrap
from pathlib import Path
from statistics import mean


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


def summarize_debate_shifts(records: list[dict]) -> dict:
    groups = {}
    sources = {dimension: [] for dimension in DIMENSIONS}
    seen_sources = set()
    seen_pairs = set()
    for record in records:
        source_key = record.get("source_key")
        source_before = record.get("source_review_debate", {}).get("draft_review", {})
        source_after = record.get("source_review", {})
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            for dimension in DIMENSIONS:
                values = [_score(review.get(dimension)) for review in (source_before, source_after)]
                maximum = 10 if dimension == "overall_rating" else 5
                if all(value is not None and 1 <= value <= maximum for value in values):
                    sources[dimension].append(values[1] - values[0])
        for variant in record.get("variants", []):
            identity = json.dumps([source_key, variant], sort_keys=True, ensure_ascii=False)
            if identity in seen_pairs:
                continue
            seen_pairs.add(identity)
            name = str(variant.get("variant") or "Unknown variant")
            group = groups.setdefault(name, {dimension: [] for dimension in DIMENSIONS})
            variant_before = variant.get("review_debate", {}).get("draft_review", {})
            variant_after = variant.get("review", {})
            for dimension in DIMENSIONS:
                values = [_score(review.get(dimension)) for review in
                          (source_before, variant_before, source_after, variant_after)]
                maximum = 10 if dimension == "overall_rating" else 5
                if all(value is not None and 1 <= value <= maximum for value in values):
                    group[dimension].append((values[1] - values[0], values[3] - values[2],
                                             values[3] - values[1]))
    return {
        "source_revision": {
            dimension: {"n": len(values), "mean_after_minus_before": mean(values) if values else None}
            for dimension, values in sources.items()
        },
        "variants": [{
            "variant": name, "dimension": dimension, "n": len(values),
            "mean_shift_before": mean(value[0] for value in values) if values else None,
            "mean_shift_after": mean(value[1] for value in values) if values else None,
            "mean_reviewer_revision": mean(value[2] for value in values) if values else None,
        } for name, dimensions in sorted(groups.items()) for dimension, values in dimensions.items()],
    }


def render_mean_shift_chart(summary: dict) -> bytes:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    rows = [row for row in summary["variants"] if row["dimension"] == "overall_rating" and row["n"]]
    source = summary["source_revision"]["overall_rating"]
    figure = Figure(figsize=(15, max(6, 3.8 + len(rows) * 0.55)), dpi=160, facecolor="white")
    FigureCanvasAgg(figure)
    left, right = figure.subplots(1, 2)
    figure.subplots_adjust(left=0.23, right=0.96, top=0.74, bottom=0.25, wspace=0.8)
    figure.suptitle("Mean overall-rating shifts before and after critic feedback", fontsize=16, y=0.97)
    figure.text(0.23, 0.90, "Overall rating: 1–10 points. Descriptive paired means; not a causal estimate of critic bias.", fontsize=10)
    for axes in (left, right):
        axes.axvline(0, color="#334155", linewidth=0.8)
        axes.spines[["top", "right"]].set_visible(False)
        axes.tick_params(labelsize=9)
        axes.set_xlabel("Mean score difference (points)")
    labels = [textwrap.fill(f"{row['variant']} (n={row['n']})", 28) for row in rows]
    positions = list(range(len(rows)))
    left.barh([position - 0.18 for position in positions], [row["mean_shift_before"] for row in rows],
              height=0.32, color="#dbeafe", edgecolor="#2563eb", label="Before critic")
    left.barh([position + 0.18 for position in positions], [row["mean_shift_after"] for row in rows],
              height=0.32, color="#2563eb", label="After critic")
    left.set_yticks(positions, labels)
    left.invert_yaxis()
    left.set_title("Robustness: variant − source", fontsize=12)
    figure.legend(*left.get_legend_handles_labels(), loc="upper left",
                  bbox_to_anchor=(0.23, 0.86), ncol=2, fontsize=9, frameon=False)
    revisions = ([source["mean_after_minus_before"]] if source["n"] else []) + [row["mean_reviewer_revision"] for row in rows]
    revision_labels = ([f"Sources (n={source['n']})"] if source["n"] else []) + labels
    right.barh(range(len(revisions)), revisions, color="#2563eb")
    right.set_yticks(range(len(revisions)), revision_labels)
    right.invert_yaxis()
    right.set_title("Reviewer change: after − before", fontsize=12)
    all_values = [row[key] for row in rows for key in ("mean_shift_before", "mean_shift_after")] + revisions
    bound = max([abs(value) for value in all_values] + [0.25]) * 1.4
    for axes in (left, right):
        axes.set_xlim(-bound, bound)
        for container in axes.containers:
            axes.bar_label(container, fmt="%+.2f", padding=3, fontsize=8)
    if not rows:
        left.text(0.5, 0.5, "No complete source/variant pairs", transform=left.transAxes, ha="center")
    if not revisions:
        right.text(0.5, 0.5, "No paired reviewer scores", transform=right.transAxes, ha="center")
    figure.text(0.23, 0.04,
                "Source: scistylebench_reviews.json. Left: same complete pairs at both stages, equal weight per pair.\n"
                "Right: source reviews counted once; variant changes use those complete pairs. Missing/invalid scores excluded.\n"
                "Positive robustness shifts do not necessarily imply upward reviewer revisions. No uncertainty intervals shown.", fontsize=9)
    output = io.BytesIO()
    figure.savefig(output, format="png", dpi=160)
    return output.getvalue()


def render_debate_heatmap(title: str, debate: dict, final_review: dict) -> bytes:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle

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
    figure = Figure(figsize=(10.6, height / 100), dpi=200, facecolor="white")
    FigureCanvasAgg(figure)
    axes = figure.add_axes((0, 0, 1, 1))
    axes.set_xlim(0, 1060)
    axes.set_ylim(height, 0)
    axes.axis("off")
    labels = []

    def label(horizontal, vertical, value, size=14, fill="#172033"):
        labels.append(str(value))
        axes.text(horizontal, vertical, str(value), fontsize=size * 0.72,
                  color=fill, fontfamily="DejaVu Sans", va="baseline")

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
            axes.add_patch(Rectangle((horizontal, vertical), 165, 38,
                                     facecolor=color, edgecolor="#cbd5e1", linewidth=0.6))
            if column == 1 and feedback_index is None:
                cell_label, size = "No question", 12
            elif column == 1 and value is None:
                status = question.get("grounding_status")
                cell_label = "Blocked" if status == "blocked_missing_or_unverifiable_evidence" else "Refine only"
                size = 12
            else:
                cell_label, size = (f"{value:g}" if valid else "N/A"), 16
            label(horizontal + 65, vertical + 25, cell_label, size,
                  "white" if shade == 4 else "#172033")
        change = f"{after - before:+g}" if all(value is not None and 1 <= value <= maximum for value in (before, after)) else "N/A"
        label(920, vertical + 25, change, 16)
    footer = top + len(rows) * 46
    label(24, footer + 25, "Color: relative position within each row's score scale (not a shared raw-score scale).")
    for index, color in enumerate(PALETTE):
        axes.add_patch(Rectangle((24 + index * 45, footer + 40), 45, 16,
                                 facecolor=color, edgecolor="none"))
    label(265, footer + 54, "Low → high. Refine only = critic question with null score; No question = no critic challenge. Change = after − before.", 13)
    label(24, footer + 80, "Source: scistylebench_reviews.json. Multiple critic recommendations are separate rows; never averaged.", 12)
    output = io.BytesIO()
    figure.savefig(output, format="png", dpi=200, metadata={"Description": "\n".join(labels)})
    return output.getvalue()


def write_debate_visualizations(records: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = ["# Debate score heatmaps", "",
              "All saved source and variant debates; no sampling. Scores are read from draft, critic, and final review records.", ""]
    summary = summarize_debate_shifts(records)
    if any(row["n"] for row in summary["variants"]) or any(row["n"] for row in summary["source_revision"].values()):
        (output_dir / "mean_score_shift_before_after.png").write_bytes(render_mean_shift_chart(summary))
        (output_dir / "mean_score_shift_before_after.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        report.extend(["## Mean score shifts", "", "![Mean score shifts](mean_score_shift_before_after.png)", "",
                       "Left: mean variant-minus-source overall rating before versus after criticism. "
                       "Right: mean reviewer after-minus-before rating (sources counted once). "
                       "A positive value on the left is not itself evidence of reviewer score inflation. "
                       "The accompanying JSON includes every scoring dimension and sample counts.", ""])
    count = 0
    seen = set()
    for record in records:
        reviews = [("Source", record.get("source_review_debate"), record.get("source_review", {}))]
        reviews.extend((f"Variant {index}: {variant.get('variant', '')}", variant.get("review_debate"), variant.get("review", {}))
                       for index, variant in enumerate(record.get("variants", []), start=1))
        for kind, debate, final_review in reviews:
            if not debate:
                continue
            identity = json.dumps([record.get("source_key"), kind, debate, final_review], sort_keys=True, ensure_ascii=False)
            digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            count += 1
            title = f"{record.get('source_key', 'Unknown source')} — {kind}"
            filename = f"debate_{digest}.png"
            image_path = output_dir / filename
            if not image_path.exists():
                image_path.write_bytes(render_debate_heatmap(title, debate, final_review))
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
