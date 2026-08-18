from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import append_jsonl, read_json, write_json
from .llm import CallLLM, transform_text_with_call_llm
from .prompts import load_prompt
from .structured_idea import SURFACE_CHANGES, describe_surface_changes
from .validation import validate_transformation


RHETORIC_HEAVIER_VARIANT = "rhetoric_heavier"


def add_rhetoric_heavier_variant(
    *,
    input_path: str | Path,
    call_llm: CallLLM,
    output_path: str | Path | None = None,
    checkpoint_path: str | Path | None = None,
    url: str | None = None,
    api_key: str | None = None,
    model_name: str = "deepseek-v3.2",
    temperature: float = 0.2,
    max_retries: int = 3,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    source_path = Path(input_path)
    target_path = Path(output_path) if output_path else source_path
    checkpoint = Path(checkpoint_path) if checkpoint_path else target_path.with_suffix(".rhetoric_heavier_checkpoint.jsonl")

    records = read_json(source_path)
    if not isinstance(records, list):
        raise ValueError("Input variant dataset must be a JSON array")

    all_changes = list(SURFACE_CHANGES)
    system_prompt = (
        load_prompt("rhetoric_heavy")
        + "\n\nSelected surface-level changes for this record:\n"
        + describe_surface_changes(all_changes)
        + "\n\nApply all five selected surface-level changes across the full paper text."
    )

    total = len(records)
    for position, record in enumerate(records, start=1):
        variants = record.setdefault("variants", {})
        if not isinstance(variants, dict):
            raise ValueError(f"Record {position} has invalid variants field")

        if RHETORIC_HEAVIER_VARIANT in variants and not overwrite:
            print(f"[{position}/{total}] Skipping existing {RHETORIC_HEAVIER_VARIANT}")
            continue

        full_text = record.get("full_text")
        if not isinstance(full_text, str) or not full_text.strip():
            raise ValueError(f"Record {position} is missing full_text")

        print(f"[{position}/{total}] Generating {RHETORIC_HEAVIER_VARIANT}")
        transformed_text = transform_text_with_call_llm(
            call_llm,
            source_text=full_text,
            system_prompt=system_prompt,
            url=url,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_retries=max_retries,
        )

        variants[RHETORIC_HEAVIER_VARIANT] = {
            "transformed_text": transformed_text,
            "transformed_full_text": transformed_text,
            "applied_surface_changes": all_changes,
            "change_strength": "5_of_5",
        }

        generation = record.setdefault("variant_generation", {})
        if isinstance(generation, dict):
            generation["rhetoric_heavier_surface_changes"] = all_changes

        validation = record.setdefault("validation", {})
        if isinstance(validation, dict):
            validation[RHETORIC_HEAVIER_VARIANT] = validate_transformation(full_text, transformed_text)

        append_jsonl(
            checkpoint,
            {
                "position": position,
                "record_key": generation.get("record_key") if isinstance(generation, dict) else None,
                "variant_name": RHETORIC_HEAVIER_VARIANT,
                "applied_surface_changes": all_changes,
            },
        )
        write_json(target_path, records)
        print(f"[{position}/{total}] Wrote {RHETORIC_HEAVIER_VARIANT}")

    write_json(target_path, records)
    return records
