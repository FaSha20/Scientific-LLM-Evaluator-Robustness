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
from scientific_llm_evaluator_robustness.scientific_metrics import load_metrics_config
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
        default="prompts/review_gen/review_generation.md",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of paper records processed from the input file.",
    )
    parser.add_argument(
        "--variant-prefix",
        action="append",
        default=[],
        help="Only process variants whose label starts with this prefix; repeatable.",
    )
    parser.add_argument(
        "--variant-name",
        action="append",
        default=[],
        help="Only process an exactly named variant; repeatable.",
    )
    parser.add_argument(
        "--source-id",
        nargs="+",
        action="append",
        default=[],
        help="Only process these source IDs; accepts one or more IDs and is repeatable.",
    )
    parser.add_argument(
        "--merge-existing-reviews",
        action="store_true",
        help="Merge newly generated SciStyleBench records into an existing output scistylebench_reviews.json.",
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
    parser.add_argument(
        "--draft-reviews-path",
        default=None,
        help=(
            "Existing scistylebench_reviews.json to use as drafts. Requires "
            "--self-refine; matching drafts are reused and missing variants are generated."
        ),
    )
    parser.add_argument(
        "--metrics-config",
        default=None,
        help="SciStyleBench JSON variant mappings and SBI formula for SBI/SRR/AWR evaluation.",
    )
    parser.add_argument(
        "--robustness-report-dir",
        default=None,
        help=(
            "Directory for the SciStyleBench robustness figures. Defaults to "
            "<output-dir>/robustness_report."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--debate",
        action="store_true",
        help="Run a critic-and-revision pass after each initial SciStyleBench review.",
    )
    mode.add_argument(
        "--self-refine",
        action="store_true",
        help="Have the original reviewer regenerate its review from the idea and its own draft.",
    )
    mode.add_argument(
        "--moderated-panel",
        action="store_true",
        help="Run independent technical and rhetoric reviews, then synthesize them with a moderator.",
    )
    parser.add_argument(
        "--critic-prompt-path",
        default="prompts/review_gen/review_critic.txt",
        help="System prompt for the independent review critic.",
    )
    parser.add_argument(
        "--critic-model-name",
        default=None,
        help="Critic model; defaults to --model-name.",
    )
    parser.add_argument(
        "--critic-temperature",
        type=float,
        default=0.7,
        help="Sampling temperature for the critic's alternative interpretations.",
    )
    parser.add_argument(
        "--self-refine-temperature",
        type=float,
        default=0.4,
        help=(
            "Sampling temperature for the self-refinement pass; independent of "
            "--temperature used for the initial review."
        ),
    )
    parser.add_argument(
        "--self-refine-system-addendum-path",
        default=None,
        help="Optional system-prompt addendum used only during self-refinement calls.",
    )
    parser.add_argument(
        "--technical-prompt-path",
        default="prompts/review_gen/technical_scientific_reviewer.txt",
        help="Role prompt appended to the base review prompt for the technical reviewer.",
    )
    parser.add_argument(
        "--rhetoric-prompt-path",
        default="prompts/review_gen/rhetoric_auditor.txt",
        help="Role prompt appended to the base review prompt for the independent rhetoric auditor.",
    )
    parser.add_argument(
        "--moderator-prompt-path",
        default="prompts/review_gen/review_moderator.txt",
        help="Role prompt appended to the base review prompt for the final moderator.",
    )
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
    if scistylebench_prompt == "prompts/review_gen/review_generation.md":
        scistylebench_prompt = "prompts/review_gen/research_idea_evaluation.txt"

    scistylebench_output = args.output_dir
    if scistylebench_output == "outputs/variant_reviews":
        scistylebench_output = "outputs/scistylebench/qwen4b_summary_idea"

    result = generate_scistylebench_reviews(
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
        debate=args.debate,
        self_refine=args.self_refine,
        self_refine_temperature=args.self_refine_temperature,
        self_refine_system_addendum_path=(
            resolve_project_path(args.self_refine_system_addendum_path)
            if args.self_refine_system_addendum_path else None
        ),
        draft_reviews_path=(resolve_project_path(args.draft_reviews_path) if args.draft_reviews_path else None),
        metrics_config=load_metrics_config(resolve_project_path(args.metrics_config) if args.metrics_config else None),
        critic_prompt_path=resolve_project_path(args.critic_prompt_path) if args.debate else None,
        critic_model_name=args.critic_model_name,
        critic_temperature=args.critic_temperature,
        moderated_panel=args.moderated_panel,
        technical_prompt_path=(
            resolve_project_path(args.technical_prompt_path) if args.moderated_panel else None
        ),
        rhetoric_prompt_path=(
            resolve_project_path(args.rhetoric_prompt_path) if args.moderated_panel else None
        ),
        moderator_prompt_path=(
            resolve_project_path(args.moderator_prompt_path) if args.moderated_panel else None
        ),
        robustness_report_dir=(
            resolve_project_path(args.robustness_report_dir)
            if args.robustness_report_dir
            else None
        ),
        variant_prefixes=tuple(args.variant_prefix),
        variant_names=tuple(args.variant_name),
        source_ids=tuple(source_id for group in args.source_id for source_id in group),
        merge_existing_reviews=args.merge_existing_reviews,
    )
    print(f"Scientific metrics: {result['scientific_metrics']['report_path']}")
    if args.debate:
        print(f"Debate visualizations: {result['debate_heatmaps_path']}")
    else:
        print(f"Robustness figures: {result['robustness_report_figures_dir']}")


if __name__ == "__main__":
    main()
