from __future__ import annotations

import argparse
import json
import math
import textwrap
from pathlib import Path
from statistics import mean


DIMENSIONS = (
    "problem_significance", "question_specificity", "hypothesis_quality",
    "testability", "novelty_contribution", "technical_plausibility", "scientific_insight",
)
DEFAULT_CONFIG = {
    "plain": "Plain",
    "paraphrase": "Paraphrase",
    "enriched": "Enriched",
    "hollow": "Hollow",
    "flawed": "Flawed",
    "style_variants": [],
    "adversarial_pairs": [],
    "sbi_formula": "absolute_controlled",
}


def load_metrics_config(path: str | Path | None = None) -> dict:
    supplied = json.loads(Path(path).read_text(encoding="utf-8")) if path else {}
    if not isinstance(supplied, dict):
        raise ValueError("Metrics config must be a JSON object")
    return validate_metrics_config(supplied)


def validate_metrics_config(supplied: dict | None = None) -> dict:
    supplied = supplied or {}
    unknown = set(supplied) - set(DEFAULT_CONFIG)
    if unknown:
        raise ValueError(f"Unknown metrics config fields: {sorted(unknown)}")
    config = {**DEFAULT_CONFIG, **supplied}
    for field in ("plain", "paraphrase", "enriched", "hollow", "flawed"):
        if not isinstance(config[field], str) or not config[field].strip():
            raise ValueError(f"{field} must be a nonempty variant label")
    if len({_name(config[field]) for field in ("plain", "paraphrase", "enriched", "hollow", "flawed")}) != 5:
        raise ValueError("Plain, Paraphrase, Enriched, Hollow, and Flawed labels must be distinct")
    if config["sbi_formula"] not in ("absolute_controlled", "signed"):
        raise ValueError("sbi_formula must be absolute_controlled or signed")
    if not isinstance(config["style_variants"], list) or any(
        not isinstance(label, str) or not label.strip() for label in config["style_variants"]
    ):
        raise ValueError("style_variants must be a list of nonempty variant labels")
    if len({_name(label) for label in config["style_variants"]}) != len(config["style_variants"]):
        raise ValueError("Duplicate style variant labels")
    controls = {_name(config[field]) for field in ("plain", "paraphrase", "enriched", "hollow", "flawed")}
    if controls.intersection(_name(label) for label in config["style_variants"]):
        raise ValueError("style_variants must not include control or substance-changing variants")
    pairs = config["adversarial_pairs"]
    if not isinstance(pairs, list) or any(
        not isinstance(pair, list) or len(pair) != 2 or any(
            not isinstance(label, str) or not label.strip() for label in pair
        ) or _name(pair[0]) == _name(pair[1]) for pair in pairs
    ):
        raise ValueError("adversarial_pairs must contain [high-substance plain label, low-substance persuasive label] pairs")
    if len({tuple(_name(label) for label in pair) for pair in pairs}) != len(pairs):
        raise ValueError("Duplicate adversarial pairs")
    return config


def _name(value: str) -> str:
    return value.strip().casefold()


def _score(review: dict, dimension: str) -> float | None:
    value = review.get(dimension)
    if isinstance(value, dict):
        value = value.get("score")
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    maximum = 10 if dimension == "overall_rating" else 5
    return number if math.isfinite(number) and 1 <= number <= maximum else None


def _index_records(records: list[dict]) -> dict:
    sources = {}
    for record in records:
        source_key = record.get("source_key")
        if not isinstance(source_key, str) or not source_key:
            raise ValueError("Scientific metrics require a nonempty source_key for every record")
        variants = sources.setdefault(source_key, {})
        for variant in record.get("variants", []):
            label = variant.get("variant")
            if not isinstance(label, str) or not label.strip():
                continue
            key = _name(label)
            if key in variants and variants[key] != variant:
                raise ValueError(f"Conflicting duplicate variant {label!r} for source {source_key!r}")
            variants[key] = variant
    return sources


def _aggregate(observations: list[dict], field: str, *, paired: bool, rate: bool) -> dict:
    eligible = [row for row in observations if row[field] is not None and (
        not paired or (row["before"] is not None and row["final"] is not None)
    )]
    result = {
        "value": mean(row[field] for row in eligible) if eligible else None,
        "n": len(eligible), "n_sources": len({row["source_key"] for row in eligible}),
        "n_candidates": len(observations), "n_excluded": len(observations) - len(eligible),
    }
    if rate:
        result["wins"] = sum(row[field] for row in eligible)
        result["ties"] = sum(row[f"{field}_tie"] for row in eligible)
    return result


def evaluate_scientific_metrics(records: list[dict], config: dict | None = None) -> dict:
    config = validate_metrics_config(config)
    sources = _index_records(records)
    styles = list(config["style_variants"])
    if not styles:
        controls = {_name(config[field]) for field in ("plain", "paraphrase", "enriched", "hollow", "flawed")}
        discovered = {}
        for variants in sources.values():
            for key, variant in variants.items():
                if key not in controls and _name(str(variant.get("variant_group", ""))) == "style" and _name(str(variant.get("expected_quality_direction", ""))) == "same":
                    discovered[key] = variant["variant"]
        styles = [discovered[key] for key in sorted(discovered)]
    definitions = [("SBI", style, [style, config["plain"], config["paraphrase"]]) for style in styles]
    definitions.extend(("SRR", f"{high} > {low}", [high, low]) for high, low in (
        (config["enriched"], config["plain"]), (config["plain"], config["hollow"]),
        (config["plain"], config["flawed"]),
    ))
    definitions.extend(("AWR", f"{high} > {low}", [high, low]) for high, low in config["adversarial_pairs"])
    observations = []
    for source_key, variants in sorted(sources.items()):
        for metric, comparison, labels in definitions:
            selected = [variants.get(_name(label)) for label in labels]
            for dimension in (*DIMENSIONS, "overall_rating"):
                row = {"source_key": source_key, "metric": metric, "comparison": comparison,
                       "dimension": dimension, "variants": labels}
                for stage in ("before", "final"):
                    reviews = [
                        ((variant.get("review_debate") or variant.get("review_self_refinement") or {}).get("draft_review", {}) if stage == "before" else variant.get("review", {}))
                        if variant else {} for variant in selected
                    ]
                    values = [_score(review, dimension) for review in reviews]
                    row[f"{stage}_scores"] = values
                    row[f"{stage}_tie"] = False
                    if any(value is None for value in values):
                        row[stage] = None
                    elif metric == "SBI":
                        style_score, plain_score, para_score = values
                        row[stage] = (
                            abs(style_score - plain_score) - abs(para_score - plain_score)
                            if config["sbi_formula"] == "absolute_controlled"
                            else (style_score - plain_score) - (para_score - plain_score)
                        )
                    else:
                        row[stage] = int(values[0] > values[1])
                        row[f"{stage}_tie"] = values[0] == values[1]
                observations.append(row)
    summaries = []
    for metric in ("SBI", "SRR", "AWR"):
        comparisons = [comparison for candidate, comparison, _ in definitions if candidate == metric]
        for comparison in [None, *comparisons]:
            for dimension in ("dimension_mean", *DIMENSIONS, "overall_rating"):
                selected = [row for row in observations if row["metric"] == metric
                            and (comparison is None or row["comparison"] == comparison)
                            and (row["dimension"] in DIMENSIONS if dimension == "dimension_mean" else row["dimension"] == dimension)]
                summaries.append({
                    "metric": metric, "comparison": comparison, "dimension": dimension,
                    "before": _aggregate(selected, "before", paired=False, rate=metric != "SBI"),
                    "final": _aggregate(selected, "final", paired=False, rate=metric != "SBI"),
                    "paired_before": _aggregate(selected, "before", paired=True, rate=metric != "SBI"),
                    "paired_final": _aggregate(selected, "final", paired=True, rate=metric != "SBI"),
                })
    warnings = []
    if not styles:
        warnings.append("SBI unavailable: configure style_variants or supply variant_group=style and expected_quality_direction=same.")
    if not config["adversarial_pairs"]:
        warnings.append("AWR unavailable: configure scientifically verified high-substance/plain versus low-substance/persuasive pairs; none are inferred.")
    observed_labels = sorted({variant["variant"] for variants in sources.values() for variant in variants.values()})
    required_labels = {label for _, _, labels in definitions for label in labels}
    absent = sorted(label for label in required_labels if _name(label) not in {_name(value) for value in observed_labels})
    if absent:
        warnings.append(f"Required variant labels absent from all records: {', '.join(absent)}")
    return {
        "config": config, "resolved_style_variants": styles, "observed_variant_labels": observed_labels,
        "n_sources": len(sources), "warnings": warnings,
        "methodology": {
            "sbi": "mean(abs(style - Plain) - abs(Paraphrase - Plain))" if config["sbi_formula"] == "absolute_controlled" else "mean((style - Plain) - (Paraphrase - Plain))",
            "sbi_caveat": "Absolute-control SBI may be negative when style deviates less than Paraphrase; signed SBI can cancel opposing biases. Neither guarantees absolute stability.",
            "srr": "mean(score(stronger) > score(weaker)); ties count as failures",
            "awr": "mean(score(high-substance plain) > score(low-substance persuasive)); ties count as failures",
            "aggregation": "Equal weight per eligible source/comparison/dimension observation. dimension_mean includes seven 1–5 dimensions only; overall_rating is separate (1–10). SRR/AWR primary results use overall_rating.",
            "missing": "Missing controls, missing drafts, invalid scores excluded, never imputed as zero. Plain is an explicit variant, never the source review.",
            "comparison": "paired_before and paired_final use exactly the same valid observations. before/final additionally report all available observations at each stage.",
            "uncertainty": "Descriptive metrics only; no confidence intervals. Pair membership is supplied by benchmark design, not inferred from model scores.",
        },
        "summaries": summaries, "observations": observations,
    }


def render_scientific_metrics(summary: dict, *, paired: bool) -> bytes:
    import io

    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(15, 7), dpi=160, facecolor="white")
    FigureCanvasAgg(figure)
    axes_list = figure.subplots(1, 3)
    figure.subplots_adjust(left=0.09, right=0.98, bottom=0.32, top=0.77, wspace=0.75)
    figure.suptitle("Scientific robustness: SBI, SRR, and AWR", fontsize=18, y=0.97)
    subtitle = "Matched before/after observations only" if paired else "Final reviews: all eligible observations"
    figure.text(0.09, 0.90, subtitle + "; gray N/A means insufficient or unconfigured data, not zero.", fontsize=10)
    for axes, metric in zip(axes_list, ("SBI", "SRR", "AWR")):
        # Use the same 1–10 overall-rating scale for all three headline chart metrics.
        # Dimension-level SBI remains available in the JSON/Markdown breakdown.
        dimension = "overall_rating"
        row = next(row for row in summary["summaries"] if row["metric"] == metric and row["comparison"] is None and row["dimension"] == dimension)
        fields = ("paired_before", "paired_final") if paired else ("final",)
        for index, field in enumerate(fields):
            result = row[field]
            value = result["value"]
            if value is None:
                axes.text(index, 0, "N/A", ha="center", va="bottom", color="#64748b")
            else:
                axes.bar(index, value, width=0.55, color="#dbeafe" if index == 0 and paired else "#2563eb", edgecolor="#2563eb")
                axes.annotate(f"{value:+.3f}" if metric == "SBI" else f"{value:.1%}", (index, value),
                              xytext=(0, 6 if value >= 0 else -6), textcoords="offset points",
                              ha="center", va="bottom" if value >= 0 else "top", fontsize=11)
        axes.set_xticks(range(len(fields)), [("Before" if field == "paired_before" else "Final") + f"\nn={row[field]['n']}" for field in fields])
        axes.set_xlim(-0.6, len(fields) - 0.4)
        axes.axhline(0, color="#334155", linewidth=0.8)
        axes.spines[["top", "right"]].set_visible(False)
        axes.set_title(metric + (" · lower excess deviation" if metric == "SBI" else " · higher is better"), fontsize=11)
        if metric == "SBI":
            values = [row[field]["value"] for field in fields if row[field]["value"] is not None]
            bound = max([abs(value) for value in values] + [0.2]) * 1.4
            axes.set_ylim(-bound, bound)
            axes.set_ylabel("Controlled deviation (1–10 overall-rating points)")
            if summary["config"]["sbi_formula"] == "signed":
                axes.set_title("SBI · signed difference, not magnitude", fontsize=11)
                axes.set_ylabel("Signed difference (1–10 overall-rating points)")
        else:
            axes.set_ylim(0, 1.2)
            axes.set_yticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
            axes.set_ylabel("Strict correct-order rate (overall rating)")
    notes = ["SBI: " + summary["methodology"]["sbi"] + "; calculated from overall rating (1–10).",
             "SRR/AWR: ties are failures. n = eligible observations (SBI: source × style × dimension; rates: source × pair).",
             "Missing variants/scores are excluded. Matched coverage can be smaller than final-only coverage. No uncertainty intervals.",
             "Source: scistylebench_reviews.json; full mappings, per-style/pair/dimension results and counts are in scientific_robustness_metrics.json."]
    notes.extend(textwrap.shorten(warning, width=140, placeholder="… (see report)") for warning in summary["warnings"][:2])
    figure.text(0.09, 0.03, "\n".join(textwrap.fill(note, 145) for note in notes), fontsize=8, va="bottom")
    output = io.BytesIO()
    figure.savefig(output, format="png", dpi=160)
    return output.getvalue()


def write_scientific_metrics(records: list[dict], output_dir: Path, config: dict | None = None) -> dict:
    summary = evaluate_scientific_metrics(records, config)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "scientific_robustness_metrics.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    paired = any(
        variant.get("review_debate") or variant.get("review_self_refinement")
        for record in records for variant in record.get("variants", [])
    )
    png_path = output_dir / "scientific_robustness_metrics.png"
    png_path.write_bytes(render_scientific_metrics(summary, paired=paired))
    lines = ["# Scientific robustness metrics", "", "![SBI, SRR and AWR](scientific_robustness_metrics.png)", ""]
    lines.extend(f"- {key}: {value}" for key, value in summary["methodology"].items())
    lines.extend(["", "## Coverage warnings", "", *(summary["warnings"] or ["No global missing-label warnings; inspect row-level counts for incomplete records."]), "",
                  "## Final and matched before/after results", "",
                  "| Metric | Comparison | Dimension | Final (n) | Matched before (n) | Matched final (n) |",
                  "|---|---|---|---|---|---|"])
    for row in summary["summaries"]:
        if row["dimension"] not in ("dimension_mean", "overall_rating"):
            continue
        cells = []
        for field in ("final", "paired_before", "paired_final"):
            result = row[field]
            cells.append((f"{result['value']:.4f}" if result["value"] is not None else "N/A") + f" ({result['n']})")
        comparison = str(row["comparison"] or "All").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {row['metric']} | {comparison} | {row['dimension']} | " + " | ".join(cells) + " |")
    markdown_path = output_dir / "scientific_robustness_metrics.md"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json_path": str(json_path), "figure_path": str(png_path), "report_path": str(markdown_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate SBI/SRR/AWR from saved reviews without LLM calls.")
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--metrics-config", type=Path)
    args = parser.parse_args()
    records = json.loads(args.input_path.read_text(encoding="utf-8"))
    result = write_scientific_metrics(records, args.output_dir or args.input_path.parent,
                                      load_metrics_config(args.metrics_config))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
