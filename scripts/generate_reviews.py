from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SCRIPTS_DIR))

from scientific_llm_evaluator_robustness.review_pipeline import generate_variant_reviews
from utils import AVAL_AI_KEY, AVAL_AI_URL, DEEPSEEK_V3, call_llm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OpenReview-style reviews for variants.")
    parser.add_argument(
        "--input-path",
        default="outputs/rhetoric_variants/hardest_papers_40_with_variants.json",
    )
    parser.add_argument("--output-dir", default="outputs/variant_reviews")
    parser.add_argument(
        "--review-prompt-path",
        default="prompts/review_generation.md",
    )
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_variant_reviews(
        input_path=args.input_path,
        output_dir=args.output_dir,
        review_prompt_path=args.review_prompt_path,
        call_llm=call_llm,
        url=AVAL_AI_URL,
        api_key=AVAL_AI_KEY,
        model_name=DEEPSEEK_V3,
        temperature=args.temperature,
        max_retries=args.max_retries,
        resume=not args.no_resume,
    )


if __name__ == "__main__":
    main()
