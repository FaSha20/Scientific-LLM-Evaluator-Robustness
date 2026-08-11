from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scientific_llm_evaluator_robustness.pipeline import generate_rhetoric_variants


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate rhetoric robustness variants.")
    parser.add_argument("--input-path", default="dataset/Hard/hardest_papers.json")
    parser.add_argument("--output-dir", default="outputs/rhetoric_variants")
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--text-field", default="full_text")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        from Qwen.test import call_llm  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Could not import call_llm. Move the helper into an importable Python "
            "module or update this script's import."
        ) from exc

    generate_rhetoric_variants(
        input_path=args.input_path,
        output_dir=args.output_dir,
        call_llm=call_llm,
        sample_size=args.sample_size,
        seed=args.seed,
        text_field=args.text_field,
        url=os.getenv("AVAL_AI_URL"),
        api_key=os.getenv("AVAL_AI_KEY"),
        model_name=os.getenv("DEEPSEEK_V3", "deepseek-v3.2"),
    )


if __name__ == "__main__":
    main()

