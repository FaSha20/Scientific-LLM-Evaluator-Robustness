from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SCRIPTS_DIR))

from scientific_llm_evaluator_robustness.scistylebench import summarize_directional_alignment, render_direction_summary
from scientific_llm_evaluator_robustness.scistylebench import (
    build_source_rating_heatmap_rows,
    sample_source_heatmap_rows,
    write_source_rating_heatmap_svg,
)


def resolve_project_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze SciStyleBench rating shifts against expected quality direction."
    )
    parser.add_argument(
        "--input-dir",
        default="outputs/scistylebench/qwen4b_summary_idea",
    )
    parser.add_argument("--rating-threshold", type=float, default=0.25)
    parser.add_argument("--heatmap-sample-size", type=int, default=30)
    parser.add_argument("--heatmap-seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = resolve_project_path(args.input_dir)
    grouped_reviews = json.loads((input_dir / "scistylebench_reviews.json").read_text(encoding="utf-8"))
    summary = summarize_directional_alignment(grouped_reviews, rating_threshold=args.rating_threshold)
    heatmap_rows = build_source_rating_heatmap_rows(grouped_reviews)
    sampled_heatmap_rows = sample_source_heatmap_rows(
        heatmap_rows,
        sample_size=args.heatmap_sample_size,
        seed=args.heatmap_seed,
    )
    (input_dir / "rating_effect_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (input_dir / "rating_effect_summary.md").write_text(
        render_direction_summary(summary),
        encoding="utf-8",
    )
    (input_dir / "sampled_source_variant_ratings.json").write_text(
        json.dumps(sampled_heatmap_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_source_rating_heatmap_svg(input_dir / "sampled_source_variant_ratings_heatmap.svg", sampled_heatmap_rows)
    print(f"Updated rating summary in {input_dir}")


if __name__ == "__main__":
    main()
