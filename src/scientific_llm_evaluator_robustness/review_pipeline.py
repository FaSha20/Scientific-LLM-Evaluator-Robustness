from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import append_jsonl, read_json, read_jsonl, write_json
from .llm import CallLLM
from .pipeline import record_key, record_title
from .sections import extract_target_sections


VARIANT_ORDER = ("main", "plain_core", "rhetoric_heavy")
REVIEW_SOURCE_MODES = {"auto", "abstract_intro", "textual_idea", "full_paper"}


def build_review_input(
    *,
    title: str,
    variant_name: str,
    abstract: str,
    introduction: str,
) -> str:
    return (
        "Only the abstract and introduction are provided for this review. "
        "Ground the review only in these sections and explicitly state uncertainty "
        "when full-paper evidence would be needed.\n\n"
        f"Title: {title}\n"
        f"Variant: {variant_name}\n\n"
        "Abstract:\n"
        f"{abstract.strip()}\n\n"
        "Introduction:\n"
        f"{introduction.strip()}"
    )


def build_structured_review_input(
    *,
    title: str,
    variant_name: str,
    idea_text: str,
) -> str:
    return (
        "A textual research idea specification is provided for this review. "
        "It excludes retrieval query fields. Ground the review only in the provided "
        "idea text and explicitly state uncertainty when full-paper evidence would "
        "be needed.\n\n"
        f"Title: {title}\n"
        f"Variant: {variant_name}\n\n"
        f"{idea_text.strip()}"
    )


def build_full_paper_review_input(
    *,
    title: str,
    variant_name: str,
    full_text: str,
) -> str:
    return (
        "A full research paper is provided for this review. Ground the review in "
        "the complete paper text.\n\n"
        f"Title: {title}\n"
        f"Variant: {variant_name}\n\n"
        f"{full_text.strip()}"
    )


def extract_full_paper_review_variants(record: dict[str, Any]) -> dict[str, dict[str, str]]:
    title = str(record.get("title") or record.get("title_gt") or record.get("title_pred") or record_title(record))
    full_text = record.get("full_text")
    if not isinstance(full_text, str):
        raise ValueError("Full-paper review mode requires record.full_text")

    variant_payloads = record.get("variants", {})
    if not isinstance(variant_payloads, dict):
        raise ValueError("Record does not contain a variants object")

    variants: dict[str, dict[str, str]] = {
        "main": {
            "title": title,
            "full_text": full_text,
        }
    }
    for variant_name in ("plain_core", "rhetoric_heavy"):
        payload = variant_payloads.get(variant_name)
        if not isinstance(payload, dict):
            raise ValueError(f"Record is missing variant '{variant_name}'")
        transformed_full_text = payload.get("transformed_full_text")
        if not isinstance(transformed_full_text, str):
            transformed_text = payload.get("transformed_text")
            if not isinstance(transformed_text, str):
                raise ValueError(
                    f"Variant '{variant_name}' is missing transformed_full_text or transformed_text"
                )
            transformed_full_text = transformed_text
        variants[variant_name] = {
            "title": title,
            "full_text": transformed_full_text,
        }
    return variants


def extract_review_variants(record: dict[str, Any]) -> dict[str, dict[str, str]]:
    title = str(record.get("title") or record.get("title_gt") or record.get("title_pred") or "")
    original_sections = record.get("original_sections")
    if isinstance(original_sections, dict):
        main_abstract = str(original_sections.get("abstract", ""))
        main_introduction = str(original_sections.get("introduction", ""))
    else:
        sections = extract_target_sections(str(record["full_text"]))
        main_abstract = sections.abstract.text
        main_introduction = sections.introduction.text

    variants: dict[str, dict[str, str]] = {
        "main": {
            "title": title,
            "abstract": main_abstract,
            "introduction": main_introduction,
        }
    }

    variant_payloads = record.get("variants", {})
    if not isinstance(variant_payloads, dict):
        raise ValueError("Record does not contain a variants object")

    for variant_name in ("plain_core", "rhetoric_heavy"):
        payload = variant_payloads.get(variant_name)
        if not isinstance(payload, dict):
            raise ValueError(f"Record is missing variant '{variant_name}'")
        abstract = payload.get("transformed_abstract")
        introduction = payload.get("transformed_introduction")
        if not isinstance(abstract, str) or not isinstance(introduction, str):
            full_text = payload.get("transformed_full_text")
            if not isinstance(full_text, str):
                raise ValueError(f"Variant '{variant_name}' is missing transformed section text")
            sections = extract_target_sections(full_text)
            abstract = sections.abstract.text
            introduction = sections.introduction.text
        variants[variant_name] = {
            "title": title,
            "abstract": abstract,
            "introduction": introduction,
        }
    return variants


def extract_structured_review_variants(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    title = record_title(record)
    original_text = record.get("original_text")
    if not isinstance(original_text, str):
        raise ValueError("Structured variant record must contain original_text")

    variant_payloads = record.get("variants", {})
    if not isinstance(variant_payloads, dict):
        raise ValueError("Record does not contain a variants object")

    variants: dict[str, dict[str, Any]] = {
        "main": {
            "title": title,
            "idea_text": original_text,
        }
    }
    for variant_name in ("plain_core", "rhetoric_heavy"):
        payload = variant_payloads.get(variant_name)
        if not isinstance(payload, dict):
            raise ValueError(f"Record is missing variant '{variant_name}'")
        idea_text = payload.get("transformed_text")
        if not isinstance(idea_text, str):
            raise ValueError(f"Variant '{variant_name}' is missing transformed_text")
        variants[variant_name] = {
            "title": title,
            "idea_text": idea_text,
        }
    return variants


def _review_key(paper_key: str, variant_name: str) -> str:
    return f"{paper_key}::{variant_name}"


def _load_completed_reviews(checkpoint_path: Path) -> dict[str, dict[str, Any]]:
    completed: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(checkpoint_path):
        key = record.get("review_generation", {}).get("review_key")
        if isinstance(key, str):
            completed[key] = record
    return completed


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
    review_source: str = "auto",
) -> list[dict[str, Any]]:
    if review_source not in REVIEW_SOURCE_MODES:
        raise ValueError(f"review_source must be one of {sorted(REVIEW_SOURCE_MODES)}")

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

        source_format = record.get("variant_generation", {}).get("source_format")
        resolved_review_source = _resolve_review_source(record, review_source, source_format)
        if resolved_review_source == "full_paper":
            variants = extract_full_paper_review_variants(record)
        elif resolved_review_source == "textual_idea":
            variants = extract_structured_review_variants(record)
        else:
            variants = extract_review_variants(record)

        for variant_name in VARIANT_ORDER:
            call_index += 1
            review_key = _review_key(f"{paper_key}::{resolved_review_source}", variant_name)
            if review_key in completed_by_key:
                print(f"[{call_index}/{total_calls}] Skipping completed review {review_key}")
                generated_reviews.append(completed_by_key[review_key])
                continue

            variant = variants[variant_name]
            print(f"[{call_index}/{total_calls}] Generating review for {review_key}")
            if resolved_review_source == "full_paper":
                review_input = build_full_paper_review_input(
                    title=variant["title"],
                    variant_name=variant_name,
                    full_text=variant["full_text"],
                )
                input_kind = "full_paper"
            elif resolved_review_source == "textual_idea":
                review_input = build_structured_review_input(
                    title=variant["title"],
                    variant_name=variant_name,
                    idea_text=variant["idea_text"],
                )
                input_kind = str(source_format or "textual_idea")
            else:
                review_input = build_review_input(
                    title=variant["title"],
                    variant_name=variant_name,
                    abstract=variant["abstract"],
                    introduction=variant["introduction"],
                )
                input_kind = "abstract_introduction"
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
                "review": review,
                "review_generation": {
                    "review_key": review_key,
                    "model_name": model_name,
                    "input_kind": input_kind,
                    "review_source": resolved_review_source,
                },
            }
            append_jsonl(checkpoint_path, generated)
            generated_reviews.append(generated)
            print(f"[{call_index}/{total_calls}] Wrote checkpoint for {review_key}")

    write_json(output_path / "variant_reviews.json", generated_reviews)
    write_json(output_path / "variant_reviews_by_paper.json", group_reviews_by_paper(generated_reviews))
    print(f"Wrote final reviews to {output_path / 'variant_reviews.json'}")
    return generated_reviews


def _resolve_review_source(
    record: dict[str, Any],
    review_source: str,
    source_format: Any,
) -> str:
    if review_source != "auto":
        return review_source
    if isinstance(record.get("full_text"), str) and _variants_have_full_text(record):
        return "full_paper"
    if source_format in {"structured_text", "structured_idea", "full_text"}:
        return "textual_idea"
    return "abstract_intro"


def _variants_have_full_text(record: dict[str, Any]) -> bool:
    variants = record.get("variants", {})
    if not isinstance(variants, dict):
        return False
    return all(
        isinstance(variants.get(name), dict)
        and isinstance(variants[name].get("transformed_full_text"), str)
        for name in ("plain_core", "rhetoric_heavy")
    )


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
                "reviews": {},
            },
        )
        paper["reviews"][review_record["variant_name"]] = review_record["review"]
    return sorted(grouped.values(), key=lambda item: item["paper_position"])
