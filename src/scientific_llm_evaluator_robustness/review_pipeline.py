from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import append_jsonl, read_json, read_jsonl, write_json
from .llm import CallLLM
from .pipeline import record_key, record_title


VARIANT_ORDER = ("main", "plain_core", "rhetoric_heavy", "rhetoric_heavier")


def build_full_paper_review_input(
    *,
    title: str,
    full_text: str,
) -> str:
    return (
        "A full research paper is provided for this review. Ground the review in "
        "the complete paper text.\n\n"
        f"Title: {title}\n"
        "\n"
        f"{full_text.strip()}"
    )


def extract_full_paper_review_variants(record: dict[str, Any]) -> dict[str, dict[str, str]]:
    title = str(record.get("title") or record.get("title_gt") or record.get("title_pred") or record_title(record))
    full_text = record.get("full_text")
    if not isinstance(full_text, str):
        raise ValueError("Full-paper review generation requires record.full_text")

    variants_payload = record.get("variants", {})
    if not isinstance(variants_payload, dict):
        raise ValueError("Record does not contain a variants object")

    variants: dict[str, dict[str, str]] = {
        "main": {
            "title": title,
            "full_text": full_text,
        }
    }
    for variant_name in ("plain_core", "rhetoric_heavy", "rhetoric_heavier"):
        payload = variants_payload.get(variant_name)
        if not isinstance(payload, dict):
            raise ValueError(f"Record is missing variant '{variant_name}'")

        transformed_full_text = payload.get("transformed_full_text")
        if not isinstance(transformed_full_text, str):
            raise ValueError(f"Variant '{variant_name}' is missing transformed_full_text")

        variants[variant_name] = {
            "title": title,
            "full_text": transformed_full_text,
        }
    return variants


def extract_paper_metadata(record: dict[str, Any]) -> dict[str, Any]:
    metadata_keys = (
        "Rating_gt",
        "Decision_gt",
        "Rating_pred",
        "Decision_pred",
        "hardness"
    )
    return {key: record[key] for key in metadata_keys if key in record}


def generate_variant_reviews(
    *,
    input_path: str | Path,
    output_dir: str | Path,
    review_prompt_path: str | Path,
    call_llm: CallLLM,
    url: str | None = None,
    api_key: str | None = None,
    model_name: str = "deepseek-v3.2",
    temperature: float = 0.2,
    max_retries: int = 3,
    resume: bool = True,
) -> list[dict[str, Any]]:
    records = read_json(input_path)
    if not isinstance(records, list):
        raise ValueError("Input variant dataset must be a JSON array")

    output_path = Path(output_dir)
    checkpoint_path = output_path / "review_generation_checkpoint.jsonl"
    completed_by_key = _load_completed_reviews(checkpoint_path) if resume else {}
    review_prompt = Path(review_prompt_path).read_text(encoding="utf-8")

    generated_reviews: list[dict[str, Any]] = []
    total_calls = len(records) * len(VARIANT_ORDER)
    call_index = 0

    for paper_position, record in enumerate(records, start=1):
        paper_key = record.get("variant_generation", {}).get("record_key")
        if not isinstance(paper_key, str):
            paper_key = record_key(record, fallback_position=paper_position)

        variants = extract_full_paper_review_variants(record)
        metadata = extract_paper_metadata(record)

        for variant_name in VARIANT_ORDER:
            call_index += 1
            review_key = _review_key(paper_key, variant_name)
            if review_key in completed_by_key:
                print(f"[{call_index}/{total_calls}] Skipping completed review {review_key}")
                generated_reviews.append(completed_by_key[review_key])
                continue

            variant = variants[variant_name]
            print(f"[{call_index}/{total_calls}] Generating review for {review_key}")
            review_input = build_full_paper_review_input(
                title=variant["title"],
                full_text=variant["full_text"],
            )
            review = call_llm(
                review_input,
                review_prompt,
                jsonify=True,
                temp=temperature,
                url=url,
                api_key=api_key,
                model_name=model_name,
                max_retries=max_retries,
            )

            generated = {
                "paper_key": paper_key,
                "paper_position": paper_position,
                "title": variant["title"],
                "variant_name": variant_name,
                "paper_metadata": metadata,
                "review": review,
                "review_generation": {
                    "review_key": review_key,
                    "model_name": model_name,
                    "input_kind": "full_paper",
                },
            }
            append_jsonl(checkpoint_path, generated)
            generated_reviews.append(generated)
            print(f"[{call_index}/{total_calls}] Wrote checkpoint for {review_key}")

    write_json(output_path / "variant_reviews.json", generated_reviews)
    write_json(output_path / "variant_reviews_by_paper.json", group_reviews_by_paper(generated_reviews))
    print(f"Wrote final reviews to {output_path / 'variant_reviews.json'}")
    return generated_reviews


def group_reviews_by_paper(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for review_record in reviews:
        paper_key = str(review_record["paper_key"])
        paper = grouped.setdefault(
            paper_key,
            {
                "paper_key": paper_key,
                "paper_position": review_record["paper_position"],
                "title": review_record["title"],
                "paper_metadata": review_record.get("paper_metadata", {}),
                "reviews": {},
            },
        )
        paper["reviews"][review_record["variant_name"]] = review_record["review"]
    return sorted(grouped.values(), key=lambda item: item["paper_position"])


def _review_key(paper_key: str, variant_name: str) -> str:
    return f"{paper_key}::{variant_name}"


def _load_completed_reviews(checkpoint_path: Path) -> dict[str, dict[str, Any]]:
    completed: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(checkpoint_path):
        key = record.get("review_generation", {}).get("review_key")
        if isinstance(key, str):
            completed[key] = record
    return completed
