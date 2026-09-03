from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SCRIPTS_DIR))

from scientific_llm_evaluator_robustness.review_pipeline import generate_variant_reviews
from scientific_llm_evaluator_robustness.scistylebench import generate_scistylebench_reviews
from utils import *


def resolve_project_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OpenReview-style reviews for variants.")
    parser.add_argument(
        "--dataset",
        choices=("variants", "scistylebench"),
        default="variants",
        help="Choose the input dataset/pipeline to run.",
    )
    parser.add_argument(
        "--input-path",
        default="outputs/rhetoric_variants/hardest_papers_40_with_variants.json",
    )
    parser.add_argument("--output-dir", default="outputs/variant_reviews")
    parser.add_argument(
        "--review-prompt-path",
        default="prompts/review_generation.md",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of paper records processed from the input file.",
    )
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--heatmap-sample-size", type=int, default=30)
    parser.add_argument("--heatmap-seed", type=int, default=42)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--url", default=SERVER_URL)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--model-name", default=QWEN4B)
    parser.add_argument("--run-label", default=None)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = args.api_key
    if api_key is None:
        if "avalai" in args.url:
            api_key = os.getenv("AVAL_AI_KEY", AVAL_AI_KEY_ROHBAN)
        else:
            api_key = "dummy"

    if args.dataset == "variants":
        generate_variant_reviews(
            input_path=resolve_project_path(args.input_path),
            output_dir=resolve_project_path(args.output_dir),
            review_prompt_path=resolve_project_path(args.review_prompt_path),
            call_llm=call_llm,
            limit=args.limit,
            url=args.url,
            model_name=args.model_name,
            api_key=api_key,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            seed=args.seed,
            max_retries=args.max_retries,
            resume=not args.no_resume,
            run_label=args.run_label,
        )
        return

    scistylebench_prompt = args.review_prompt_path
    if scistylebench_prompt == "prompts/review_generation.md":
        scistylebench_prompt = "prompts/research_idea_evaluation.txt"

    scistylebench_output = args.output_dir
    if scistylebench_output == "outputs/variant_reviews":
        scistylebench_output = "outputs/scistylebench/qwen4b_summary_idea"

    generate_scistylebench_reviews(
        csv_path=resolve_project_path(args.input_path),
        output_dir=resolve_project_path(scistylebench_output),
        review_prompt_path=resolve_project_path(scistylebench_prompt),
        call_llm=call_llm,
        limit=args.limit,
        url=args.url,
        model_name=args.model_name,
        api_key=api_key,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        seed=args.seed,
        max_retries=args.max_retries,
        resume=not args.no_resume,
        run_label=args.run_label,
        heatmap_sample_size=args.heatmap_sample_size,
        heatmap_seed=args.heatmap_seed,
    )


if __name__ == "__main__":
    main()
