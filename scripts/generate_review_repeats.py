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
from utils import AVAL_AI_KEY, SERVER_URL, QWEN4B, call_llm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate repeated review runs for randomness and sensitivity analysis."
    )
    parser.add_argument(
        "--input-path",
        default="outputs/rhetoric_variants/hardest_papers_40_with_variants.json",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/reviews/repeated_reviews",
        help="Root directory containing per-run subdirectories such as run_001.",
    )
    parser.add_argument(
        "--review-prompt-path",
        default="prompts/review_generation.md",
    )
    parser.add_argument("--num-runs", type=int, default=5)
    parser.add_argument("--start-run-index", type=int, default=1)
    parser.add_argument("--run-prefix", default="run")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--seed-base", type=int, default=None)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--url", default=SERVER_URL)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--model-name", default=QWEN4B)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def resolve_api_key(url: str, api_key: str | None) -> str | None:
    if api_key is not None:
        return api_key
    if "avalai" in url:
        return os.getenv("AVAL_AI_KEY", AVAL_AI_KEY)
    return "dummy"


def main() -> None:
    args = parse_args()
    api_key = resolve_api_key(args.url, args.api_key)
    output_root = Path(args.output_root)

    for offset in range(args.num_runs):
        run_index = args.start_run_index + offset
        run_label = f"{args.run_prefix}_{run_index:03d}"
        run_output_dir = output_root / run_label
        run_seed = None if args.seed_base is None else args.seed_base + offset
        print(
            f"=== Starting {run_label} | model={args.model_name} "
            f"| temperature={args.temperature} | seed={run_seed} ==="
        )
        generate_variant_reviews(
            input_path=args.input_path,
            output_dir=run_output_dir,
            review_prompt_path=args.review_prompt_path,
            call_llm=call_llm,
            url=args.url,
            api_key=api_key,
            model_name=args.model_name,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            seed=run_seed,
            max_retries=args.max_retries,
            resume=not args.no_resume,
            run_label=run_label,
        )
        print(f"=== Finished {run_label}: {run_output_dir / 'variant_reviews.json'} ===")


if __name__ == "__main__":
    main()
