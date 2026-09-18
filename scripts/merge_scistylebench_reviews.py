from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scientific_llm_evaluator_robustness.review_merge import merge_review_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely merge grouped SciStyleBench review JSON files.")
    parser.add_argument("--base-path", type=Path, required=True)
    parser.add_argument("--additions-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, help="Defaults to --base-path.")
    args = parser.parse_args()
    print(merge_review_files(
        base_path=args.base_path,
        additions_path=args.additions_path,
        output_path=args.output_path,
    ))


if __name__ == "__main__":
    main()
