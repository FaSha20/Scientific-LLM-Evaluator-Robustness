from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from statistics import mean, stdev
from typing import Any


METRICS = ("rating", "soundness", "presentation", "contribution")
VARIANT_ORDER = ("plain_core", "rhetoric_heavy", "rhetoric_heavier")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate whether rhetoric variants change reviews beyond ordinary run-to-run randomness."
        )
    )
    parser.add_argument(
        "--runs-root",
        required=True,
        help="Directory containing per-run subdirectories such as run_001, run_002, ...",
    )
    parser.add_argument("--run-glob", default="run_*")
    parser.add_argument("--reviews-file-name", default="variant_reviews.json")
    parser.add_argument(
        "--output-path",
        default=None,
        help="JSON output path. Defaults to <runs-root>/sensitivity_analysis.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs_root = Path(args.runs_root)
    output_path = (
        Path(args.output_path)
        if args.output_path is not None
        else runs_root / "sensitivity_analysis.json"
    )

    run_records = load_runs(runs_root, args.run_glob, args.reviews_file_name)
    analysis = build_analysis(run_records)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path = output_path.with_suffix(".md")
    markdown_path.write_text(render_markdown(analysis), encoding="utf-8")

    print(f"Wrote sensitivity analysis JSON to {output_path}")
    print(f"Wrote sensitivity analysis markdown to {markdown_path}")


def load_runs(runs_root: Path, run_glob: str, reviews_file_name: str) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for run_dir in sorted(runs_root.glob(run_glob)):
        if not run_dir.is_dir():
            continue
        reviews_path = run_dir / reviews_file_name
        if not reviews_path.exists():
            continue
        records = json.loads(reviews_path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError(f"{reviews_path} must contain a JSON array")
        runs.append(
            {
                "run_label": run_dir.name,
                "reviews_path": str(reviews_path),
                "records": records,
            }
        )
    if not runs:
        raise ValueError(f"No run directories with {reviews_file_name} found under {runs_root}")
    return runs


def build_analysis(run_records: list[dict[str, Any]]) -> dict[str, Any]:
    flat_rows = flatten_runs(run_records)
    variant_stats = analyze_variants(flat_rows)
    overall = build_overall_summary(variant_stats)
    return {
        "n_runs": len(run_records),
        "run_labels": [run["run_label"] for run in run_records],
        "variant_stats": variant_stats,
        "overall_summary": overall,
    }


def flatten_runs(run_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in run_records:
        run_label = run["run_label"]
        for record in run["records"]:
            review = record.get("review", {})
            if not isinstance(review, dict):
                continue
            row = {
                "run_label": run_label,
                "paper_key": record.get("paper_key"),
                "paper_position": record.get("paper_position"),
                "title": record.get("title"),
                "variant_name": record.get("variant_name"),
                "rating": score_value(review.get("overall_rating")),
                "soundness": score_value(review.get("soundness")),
                "presentation": score_value(review.get("presentation")),
                "contribution": score_value(review.get("contribution")),
                "confidence": score_value(review.get("confidence")),
                "decision": extract_decision(review),
            }
            rows.append(row)
    return rows


def score_value(value: Any) -> float | None:
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


def extract_decision(review: dict[str, Any]) -> str | None:
    decision = review.get("decision")
    if isinstance(decision, str) and decision.strip():
        return decision.strip()
    rating = score_value(review.get("overall_rating"))
    if rating is None:
        return None
    return "Accept" if rating >= 6 else "Reject"


def analyze_variants(flat_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_run_paper: dict[tuple[str, Any], dict[str, dict[str, Any]]] = {}
    for row in flat_rows:
        key = (row["run_label"], row["paper_key"])
        by_run_paper.setdefault(key, {})[row["variant_name"]] = row

    by_paper_variant: dict[tuple[Any, str], list[dict[str, Any]]] = {}
    for row in flat_rows:
        if row["variant_name"] != "main":
            by_paper_variant.setdefault((row["paper_key"], row["variant_name"]), []).append(row)

    main_by_paper: dict[Any, list[dict[str, Any]]] = {}
    for row in flat_rows:
        if row["variant_name"] == "main":
            main_by_paper.setdefault(row["paper_key"], []).append(row)

    results: list[dict[str, Any]] = []
    for variant_name in VARIANT_ORDER:
        variant_result: dict[str, Any] = {
            "variant_name": variant_name,
            "metrics": {},
            "decision": {},
        }
        for metric in METRICS:
            paper_mean_deltas: list[float] = []
            all_run_deltas: list[float] = []
            within_main_stds: list[float] = []
            within_variant_stds: list[float] = []
            within_delta_stds: list[float] = []
            n_papers = 0
            n_run_pairs = 0

            paper_keys = sorted({paper_key for _, paper_key in by_run_paper.keys()})
            for paper_key in paper_keys:
                main_vals: list[float] = []
                variant_vals: list[float] = []
                delta_vals: list[float] = []

                run_labels = sorted({run_label for run_label, candidate_paper in by_run_paper.keys() if candidate_paper == paper_key})
                for run_label in run_labels:
                    variants = by_run_paper.get((run_label, paper_key), {})
                    main = variants.get("main")
                    variant = variants.get(variant_name)
                    if not main or not variant:
                        continue
                    main_value = main.get(metric)
                    variant_value = variant.get(metric)
                    if main_value is None or variant_value is None:
                        continue
                    main_vals.append(float(main_value))
                    variant_vals.append(float(variant_value))
                    delta_vals.append(float(variant_value) - float(main_value))

                if not delta_vals:
                    continue

                n_papers += 1
                n_run_pairs += len(delta_vals)
                paper_mean_deltas.append(mean(delta_vals))
                all_run_deltas.extend(delta_vals)
                if len(main_vals) > 1:
                    within_main_stds.append(stdev(main_vals))
                if len(variant_vals) > 1:
                    within_variant_stds.append(stdev(variant_vals))
                if len(delta_vals) > 1:
                    within_delta_stds.append(stdev(delta_vals))

            permutation = exact_sign_flip_test(paper_mean_deltas)
            variant_result["metrics"][metric] = {
                "n_papers": n_papers,
                "n_run_pairs": n_run_pairs,
                "mean_shift": safe_mean(all_run_deltas),
                "mean_abs_shift": safe_mean(abs(value) for value in all_run_deltas),
                "paper_level_mean_shift": safe_mean(paper_mean_deltas),
                "paper_level_std_shift": safe_stdev(paper_mean_deltas),
                "exact_sign_flip_pvalue": permutation["pvalue"],
                "exact_sign_flip_n": permutation["n"],
                "signal_to_noise": divide_abs(
                    safe_mean(paper_mean_deltas),
                    safe_mean(within_delta_stds),
                ),
                "mean_within_main_std": safe_mean(within_main_stds),
                "mean_within_variant_std": safe_mean(within_variant_stds),
                "mean_within_delta_std": safe_mean(within_delta_stds),
                "standardized_effect": standardized_effect(paper_mean_deltas),
            }

        flip_rates: list[float] = []
        main_instability: list[float] = []
        variant_instability: list[float] = []
        paper_keys = sorted({paper_key for _, paper_key in by_run_paper.keys()})
        for paper_key in paper_keys:
            main_decisions: list[str] = []
            variant_decisions: list[str] = []
            per_run_flips: list[float] = []
            run_labels = sorted({run_label for run_label, candidate_paper in by_run_paper.keys() if candidate_paper == paper_key})
            for run_label in run_labels:
                variants = by_run_paper.get((run_label, paper_key), {})
                main = variants.get("main")
                variant = variants.get(variant_name)
                if not main or not variant:
                    continue
                main_decision = main.get("decision")
                variant_decision = variant.get("decision")
                if main_decision is None or variant_decision is None:
                    continue
                main_decisions.append(str(main_decision))
                variant_decisions.append(str(variant_decision))
                per_run_flips.append(1.0 if normalize_decision(main_decision) != normalize_decision(variant_decision) else 0.0)
            if per_run_flips:
                flip_rates.append(mean(per_run_flips))
            if len(main_decisions) > 1:
                main_instability.append(binary_instability(main_decisions))
            if len(variant_decisions) > 1:
                variant_instability.append(binary_instability(variant_decisions))

        variant_result["decision"] = {
            "mean_flip_rate": safe_mean(flip_rates),
            "mean_main_instability": safe_mean(main_instability),
            "mean_variant_instability": safe_mean(variant_instability),
        }
        results.append(variant_result)
    return results


def exact_sign_flip_test(values: list[float]) -> dict[str, Any]:
    clean = [float(value) for value in values if value is not None and float(value) != 0.0]
    n = len(clean)
    if n == 0:
        return {"n": 0, "observed_mean": None, "pvalue": None}

    observed = abs(mean(clean))
    total = 0
    extreme = 0
    for signs in itertools.product((-1.0, 1.0), repeat=n):
        sample_mean = abs(sum(sign * value for sign, value in zip(signs, clean)) / n)
        total += 1
        if sample_mean >= observed - 1e-12:
            extreme += 1
    return {"n": n, "observed_mean": mean(clean), "pvalue": extreme / total}


def standardized_effect(values: list[float]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    if len(clean) < 2:
        return None
    sd = stdev(clean)
    if sd == 0:
        return None
    return mean(clean) / sd


def binary_instability(values: list[str]) -> float | None:
    normalized = [normalize_decision(value) for value in values if value is not None]
    if len(normalized) < 2:
        return None
    majority = max((normalized.count(label), label) for label in set(normalized))[1]
    mismatches = sum(1 for value in normalized if value != majority)
    return mismatches / len(normalized)


def normalize_decision(value: Any) -> str:
    return str(value).strip().lower()


def safe_mean(values: Any) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return mean(clean) if clean else None


def safe_stdev(values: list[float]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return stdev(clean) if len(clean) > 1 else None


def divide_abs(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return abs(float(numerator)) / float(denominator)


def build_overall_summary(variant_stats: list[dict[str, Any]]) -> dict[str, Any]:
    rating_shifts = [
        variant["metrics"]["rating"]["paper_level_mean_shift"]
        for variant in variant_stats
        if variant.get("metrics", {}).get("rating")
    ]
    pvalues = [
        variant["metrics"]["rating"]["exact_sign_flip_pvalue"]
        for variant in variant_stats
        if variant.get("metrics", {}).get("rating", {}).get("exact_sign_flip_pvalue") is not None
    ]
    return {
        "mean_variant_rating_shift": safe_mean(rating_shifts),
        "min_rating_pvalue": min(pvalues) if pvalues else None,
        "variants_with_p_lt_0_05_on_rating": [
            variant["variant_name"]
            for variant in variant_stats
            if (variant.get("metrics", {}).get("rating", {}).get("exact_sign_flip_pvalue") or 1.0) < 0.05
        ],
    }


def render_markdown(analysis: dict[str, Any]) -> str:
    lines = [
        "# Review Sensitivity Analysis",
        "",
        f"- Runs: {analysis['n_runs']}",
        f"- Run labels: {', '.join(analysis['run_labels'])}",
        "",
        "This report tests whether signed review shifts under rhetoric variants are larger than ordinary run-to-run randomness.",
        "",
    ]
    for variant in analysis["variant_stats"]:
        lines.append(f"## {variant['variant_name']}")
        lines.append("")
        lines.append("| Metric | Mean shift | Mean abs shift | Exact sign-flip p | Mean within-delta std | Signal/noise |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for metric in METRICS:
            stats = variant["metrics"][metric]
            lines.append(
                "| {metric} | {mean_shift} | {mean_abs_shift} | {pvalue} | {delta_std} | {signal_to_noise} |".format(
                    metric=metric,
                    mean_shift=fmt(stats["paper_level_mean_shift"]),
                    mean_abs_shift=fmt(stats["mean_abs_shift"]),
                    pvalue=fmt_p(stats["exact_sign_flip_pvalue"]),
                    delta_std=fmt(stats["mean_within_delta_std"]),
                    signal_to_noise=fmt(stats["signal_to_noise"]),
                )
            )
        decision = variant["decision"]
        lines.extend(
            [
                "",
                f"- Mean decision flip rate: {fmt_pct(decision['mean_flip_rate'])}",
                f"- Mean main decision instability across runs: {fmt_pct(decision['mean_main_instability'])}",
                f"- Mean variant decision instability across runs: {fmt_pct(decision['mean_variant_instability'])}",
                "",
            ]
        )
    overall = analysis["overall_summary"]
    lines.extend(
        [
            "## Overall",
            "",
            f"- Mean variant rating shift: {fmt(overall['mean_variant_rating_shift'])}",
            f"- Smallest rating p-value across variants: {fmt_p(overall['min_rating_pvalue'])}",
            f"- Variants with rating p < 0.05: {', '.join(overall['variants_with_p_lt_0_05_on_rating']) or 'none'}",
        ]
    )
    return "\n".join(lines)


def fmt(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.4f}"


def fmt_p(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.6f}"


def fmt_pct(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.1%}"


if __name__ == "__main__":
    main()
