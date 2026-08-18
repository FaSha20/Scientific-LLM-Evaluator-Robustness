from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scientific_llm_evaluator_robustness.robustness_report import build_robustness_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build textual and visual robustness report.")
    parser.add_argument(
        "--input-path",
        default="outputs/reviews/full_paper_variant_reviews/variant_reviews.json",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/reports/robustness_full_paper_reviews",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_robustness_report(
        input_path=args.input_path,
        output_dir=args.output_dir,
    )
    print("Robustness report generated:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
