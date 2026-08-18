from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SCRIPTS_DIR))

from scientific_llm_evaluator_robustness.full_paper_variants import add_rhetoric_heavier_variant
from utils import AVAL_AI_KEY, AVAL_AI_URL, DEEPSEEK_V3, call_llm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add a 5-of-5 rhetoric-heavier full-paper variant.")
    parser.add_argument(
        "--input-path",
        default="outputs/rhetoric_variants_full_paper/hardest_papers_40_with_variants.json",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="Defaults to overwriting --input-path in place.",
    )
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    add_rhetoric_heavier_variant(
        input_path=args.input_path,
        output_path=args.output_path,
        call_llm=call_llm,
        url=AVAL_AI_URL,
        api_key=AVAL_AI_KEY,
        model_name=DEEPSEEK_V3,
        temperature=args.temperature,
        max_retries=args.max_retries,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
