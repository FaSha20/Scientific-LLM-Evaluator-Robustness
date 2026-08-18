from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import append_jsonl, read_jsonl, read_records, write_json
from .llm import (
    CallLLM,
    transform_sections_with_call_llm,
    transform_structured_idea_with_call_llm,
    transform_text_with_call_llm,
)
from .prompts import load_prompt
from .sampling import sample_records
from .sections import TargetSections, extract_target_sections, replace_target_sections
from .structured_idea import (
    SURFACE_CHANGES,
    describe_surface_changes,
    get_structured_content,
    select_surface_changes,
    serialize_structured_idea,
)
from .validation import validate_transformation


SOURCE_MODES = {"auto", "structured_text", "full_text"}


def record_key(record: dict[str, Any], fallback_position: int | None = None) -> str:
    if "paperId" in record and record["paperId"]:
        return f"paperId:{record['paperId']}"
    if "paper_name" in record and record["paper_name"]:
        return f"paper_name:{record['paper_name']}"
    if "index" in record:
        return f"index:{record['index']}"
    if "title" in record and record["title"]:
        return f"title:{record['title']}"
    if fallback_position is not None:
        return f"position:{fallback_position}"
    raise ValueError("Cannot build a stable record key")


def record_title(record: dict[str, Any]) -> str:
    return str(record.get("paper_name") or record.get("title") or record.get("title_gt") or "")


def _require_text(record: dict[str, Any], text_field: str, key: str) -> str:
    text = record.get(text_field)
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Record {key} is missing non-empty text field '{text_field}'")
    return text


def _build_variant_record(
    *,
    record: dict[str, Any],
    source_text: str,
    key: str,
    position: int,
    seed: int,
    model_name: str,
    sections: TargetSections,
    rhetoric_result: dict[str, Any],
    plain_result: dict[str, Any],
) -> dict[str, Any]:
    rhetoric_abstract = rhetoric_result.get("transformed_abstract", "")
    rhetoric_introduction = rhetoric_result.get("transformed_introduction", "")
    plain_abstract = plain_result.get("transformed_abstract", "")
    plain_introduction = plain_result.get("transformed_introduction", "")

    rhetoric_text = replace_target_sections(
        source_text,
        sections,
        abstract=rhetoric_abstract,
        introduction=rhetoric_introduction,
    )
    plain_text = replace_target_sections(
        source_text,
        sections,
        abstract=plain_abstract,
        introduction=plain_introduction,
    )
    source_target_text = sections.abstract.text + "\n\n" + sections.introduction.text
    rhetoric_target_text = rhetoric_abstract + "\n\n" + rhetoric_introduction
    plain_target_text = plain_abstract + "\n\n" + plain_introduction

    return {
        **record,
        "variant_generation": {
            "record_key": key,
            "generation_key": _generation_key(key, "full_text_sections"),
            "sample_seed": seed,
            "sample_position": position,
            "model_name": model_name,
            "source_format": "full_text_sections",
            "transformed_sections": ["abstract", "introduction"],
        },
        "variants": {
            "rhetoric_heavy": {
                **rhetoric_result,
                "transformed_full_text": rhetoric_text,
            },
            "plain_core": {
                **plain_result,
                "transformed_full_text": plain_text,
            },
        },
        "original_sections": {
            "abstract": sections.abstract.text,
            "introduction": sections.introduction.text,
        },
        "validation": {
            "rhetoric_heavy": validate_transformation(source_target_text, rhetoric_target_text),
            "plain_core": validate_transformation(source_target_text, plain_target_text),
        },
    }


def _build_structured_variant_record(
    *,
    record: dict[str, Any],
    source_content: dict[str, Any],
    source_text: str,
    key: str,
    position: int,
    seed: int,
    model_name: str,
    selected_changes: list[str],
    rhetoric_text: str,
    rhetoric_heavier_text: str,
    plain_text: str,
) -> dict[str, Any]:
    return {
        **record,
        "variant_generation": {
            "record_key": key,
            "generation_key": _generation_key(key, "structured_text"),
            "sample_seed": seed,
            "sample_position": position,
            "model_name": model_name,
            "source_format": "structured_text",
            "excluded_fields": ["rag_queries"],
            "rhetoric_surface_changes": selected_changes,
        },
        "original_content": source_content,
        "original_text": source_text,
        "variants": {
            "rhetoric_heavy": {
                "transformed_text": rhetoric_text,
                "applied_surface_changes": selected_changes,
            },
            "rhetoric_heavier": {
                "transformed_text": rhetoric_heavier_text,
                "applied_surface_changes": list(SURFACE_CHANGES),
                "change_strength": "5_of_5",
            },
            "plain_core": {
                "transformed_text": plain_text,
            },
        },
        "validation": {
            "rhetoric_heavy": validate_transformation(source_text, rhetoric_text),
            "rhetoric_heavier": validate_transformation(source_text, rhetoric_heavier_text),
            "plain_core": validate_transformation(source_text, plain_text),
        },
    }


def _build_text_variant_record(
    *,
    record: dict[str, Any],
    source_text: str,
    source_format: str,
    key: str,
    position: int,
    seed: int,
    model_name: str,
    selected_changes: list[str],
    rhetoric_text: str,
    rhetoric_heavier_text: str,
    plain_text: str,
) -> dict[str, Any]:
    rhetoric_payload = {
        "transformed_text": rhetoric_text,
        "applied_surface_changes": selected_changes,
    }
    plain_payload = {
        "transformed_text": plain_text,
    }
    rhetoric_heavier_payload = {
        "transformed_text": rhetoric_heavier_text,
        "applied_surface_changes": list(SURFACE_CHANGES),
        "change_strength": "5_of_5",
    }
    if source_format == "full_text":
        rhetoric_payload["transformed_full_text"] = rhetoric_text
        plain_payload["transformed_full_text"] = plain_text
        rhetoric_heavier_payload["transformed_full_text"] = rhetoric_heavier_text

    return {
        **record,
        "variant_generation": {
            "record_key": key,
            "generation_key": _generation_key(key, source_format),
            "sample_seed": seed,
            "sample_position": position,
            "model_name": model_name,
            "source_format": source_format,
            "rhetoric_surface_changes": selected_changes,
            "rhetoric_heavier_surface_changes": list(SURFACE_CHANGES),
        },
        "original_text": source_text,
        "variants": {
            "rhetoric_heavy": rhetoric_payload,
            "rhetoric_heavier": rhetoric_heavier_payload,
            "plain_core": plain_payload,
        },
        "validation": {
            "rhetoric_heavy": validate_transformation(source_text, rhetoric_text),
            "rhetoric_heavier": validate_transformation(source_text, rhetoric_heavier_text),
            "plain_core": validate_transformation(source_text, plain_text),
        },
    }


def _generation_key(record_key_value: str, source_format: str) -> str:
    return f"{record_key_value}::{source_format}"


def _load_completed_records(checkpoint_path: Path) -> dict[str, dict[str, Any]]:
    completed: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(checkpoint_path):
        generation = record.get("variant_generation", {})
        key = generation.get("generation_key") or generation.get("record_key")
        if isinstance(key, str):
            completed[key] = record
    return completed


def _resolve_source_mode(record: dict[str, Any], source_mode: str) -> str:
    if source_mode not in SOURCE_MODES:
        raise ValueError(f"source_mode must be one of {sorted(SOURCE_MODES)}")
    if source_mode != "auto":
        return source_mode
    if isinstance(record.get("extracted_content"), dict):
        return "structured_text"
    return "full_text"


def generate_rhetoric_variants(
    *,
    input_path: str | Path,
    output_dir: str | Path,
    call_llm: CallLLM,
    sample_size: int = 40,
    seed: int = 42,
    text_field: str = "full_text",
    url: str | None = None,
    api_key: str | None = None,
    model_name: str = "deepseek-v3.2",
    temperature: float = 0.2,
    max_retries: int = 3,
    resume: bool = True,
    source_mode: str = "auto",
) -> list[dict[str, Any]]:
    records = read_records(input_path)
    selected_records = sample_records(records, sample_size=sample_size, seed=seed)

    output_path = Path(output_dir)
    write_json(output_path / "selected_original_records.json", selected_records)

    rhetoric_prompt = load_prompt("rhetoric_heavy")
    plain_prompt = load_prompt("plain_core")
    checkpoint_path = output_path / "generation_checkpoint.jsonl"
    completed_by_key = _load_completed_records(checkpoint_path) if resume else {}
    all_rhetoric_changes = list(SURFACE_CHANGES)

    generated_records: list[dict[str, Any]] = []
    for position, record in enumerate(selected_records, start=1):
        key = record_key(record, fallback_position=position)
        resolved_source_mode = _resolve_source_mode(record, source_mode)
        generation_key = _generation_key(key, resolved_source_mode)
        if generation_key in completed_by_key:
            print(f"[{position}/{sample_size}] Skipping completed record {generation_key}")
            generated_records.append(completed_by_key[generation_key])
            continue
        if key in completed_by_key and source_mode == "auto":
            print(f"[{position}/{sample_size}] Skipping completed record {key}")
            generated_records.append(completed_by_key[key])
            continue

        print(f"[{position}/{sample_size}] Generating variants for {generation_key}")
        if resolved_source_mode == "structured_text":
            title = record_title(record)
            source_content = get_structured_content(record)
            source_text = serialize_structured_idea(title, source_content)
            selected_changes = select_surface_changes(key, seed, count=2)
            rhetoric_prompt_with_changes = (
                rhetoric_prompt
                + "\n\nSelected surface-level changes for this record:\n"
                + describe_surface_changes(selected_changes)
            )
            rhetoric_heavier_prompt = (
                rhetoric_prompt
                + "\n\nSelected surface-level changes for this record:\n"
                + describe_surface_changes(all_rhetoric_changes)
                + "\n\nApply all five selected surface-level changes."
            )

            rhetoric_result = transform_structured_idea_with_call_llm(
                call_llm,
                idea_text=source_text,
                system_prompt=rhetoric_prompt_with_changes,
                url=url,
                api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_retries=max_retries,
            )

            rhetoric_heavier_result = transform_structured_idea_with_call_llm(
                call_llm,
                idea_text=source_text,
                system_prompt=rhetoric_heavier_prompt,
                url=url,
                api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_retries=max_retries,
            )

            plain_result = transform_structured_idea_with_call_llm(
                call_llm,
                idea_text=source_text,
                system_prompt=plain_prompt,
                url=url,
                api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_retries=max_retries,
            )

            generated = _build_structured_variant_record(
                record=record,
                source_content=source_content,
                source_text=source_text,
                key=key,
                position=position,
                seed=seed,
                model_name=model_name,
                selected_changes=selected_changes,
                rhetoric_text=rhetoric_result,
                rhetoric_heavier_text=rhetoric_heavier_result,
                plain_text=plain_result,
            )
            append_jsonl(checkpoint_path, generated)
            generated_records.append(generated)
            print(f"[{position}/{sample_size}] Wrote checkpoint for {key}")
            continue

        if resolved_source_mode == "full_text":
            source_text = _require_text(record, text_field, key)
            selected_changes = select_surface_changes(key, seed, count=2)
            rhetoric_prompt_with_changes = (
                rhetoric_prompt
                + "\n\nSelected surface-level changes for this record:\n"
                + describe_surface_changes(selected_changes)
            )
            rhetoric_heavier_prompt = (
                rhetoric_prompt
                + "\n\nSelected surface-level changes for this record:\n"
                + describe_surface_changes(all_rhetoric_changes)
                + "\n\nApply all five selected surface-level changes across the full paper text."
            )
            rhetoric_result = transform_text_with_call_llm(
                call_llm,
                source_text=source_text,
                system_prompt=rhetoric_prompt_with_changes,
                url=url,
                api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_retries=max_retries,
            )
            rhetoric_heavier_result = transform_text_with_call_llm(
                call_llm,
                source_text=source_text,
                system_prompt=rhetoric_heavier_prompt,
                url=url,
                api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_retries=max_retries,
            )
            plain_result = transform_text_with_call_llm(
                call_llm,
                source_text=source_text,
                system_prompt=plain_prompt,
                url=url,
                api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_retries=max_retries,
            )
            generated = _build_text_variant_record(
                record=record,
                source_text=source_text,
                source_format="full_text",
                key=key,
                position=position,
                seed=seed,
                model_name=model_name,
                selected_changes=selected_changes,
                rhetoric_text=rhetoric_result,
                rhetoric_heavier_text=rhetoric_heavier_result,
                plain_text=plain_result,
            )
            append_jsonl(checkpoint_path, generated)
            generated_records.append(generated)
            print(f"[{position}/{sample_size}] Wrote checkpoint for {key}")
            continue

        source_text = _require_text(record, text_field, key)
        sections = extract_target_sections(source_text)
        rhetoric_result = transform_sections_with_call_llm(
            call_llm,
            abstract=sections.abstract.text,
            introduction=sections.introduction.text,
            system_prompt=rhetoric_prompt,
            url=url,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_retries=max_retries,
        )
        plain_result = transform_sections_with_call_llm(
            call_llm,
            abstract=sections.abstract.text,
            introduction=sections.introduction.text,
            system_prompt=plain_prompt,
            url=url,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_retries=max_retries,
        )

        generated = _build_variant_record(
            record=record,
            source_text=source_text,
            key=key,
            position=position,
            seed=seed,
            model_name=model_name,
            sections=sections,
            rhetoric_result=rhetoric_result,
            plain_result=plain_result,
        )
        append_jsonl(checkpoint_path, generated)
        generated_records.append(generated)
        print(f"[{position}/{sample_size}] Wrote checkpoint for {key}")

    write_json(output_path / "hardest_papers_40_with_variants.json", generated_records)
    print(f"Wrote final dataset to {output_path / 'hardest_papers_40_with_variants.json'}")
    return generated_records
