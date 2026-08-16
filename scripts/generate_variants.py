from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SCRIPTS_DIR))

from scientific_llm_evaluator_robustness.pipeline import generate_rhetoric_variants
from utils import AVAL_AI_KEY, AVAL_AI_URL, DEEPSEEK_V3, call_llm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate rhetoric robustness variants.")
    parser.add_argument("--input-path", default="dataset/Hard/stuctured_papers.jsonl")
    parser.add_argument("--output-dir", default="outputs/rhetoric_variants")
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--text-field", default="full_text")
    parser.add_argument(
        "--source-mode",
        choices=["auto", "structured_text", "full_text"],
        default="auto",
        help=(
            "Choose the source text passed to the variant LLM. "
            "auto uses structured_text when extracted_content exists, otherwise full_text."
        ),
    )
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    generate_rhetoric_variants(
        input_path=args.input_path,
        output_dir=args.output_dir,
        call_llm=call_llm,
        sample_size=args.sample_size,
        seed=args.seed,
        text_field=args.text_field,
        url=AVAL_AI_URL,
        api_key=AVAL_AI_KEY,
        model_name=DEEPSEEK_V3,
        temperature=args.temperature,
        max_retries=args.max_retries,
        resume=not args.no_resume,
        source_mode=args.source_mode,
    )


if __name__ == "__main__":
    main()
