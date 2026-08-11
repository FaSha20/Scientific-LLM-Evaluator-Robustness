from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import append_jsonl, read_json, write_json
from .llm import CallLLM, transform_with_call_llm
from .prompts import load_prompt
from .sampling import sample_records
from .validation import validate_transformation


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
) -> list[dict[str, Any]]:
    records = read_json(input_path)
    selected_records = sample_records(records, sample_size=sample_size, seed=seed)

    output_path = Path(output_dir)
    write_json(output_path / "selected_original_records.json", selected_records)

    rhetoric_prompt = load_prompt("rhetoric_heavy")
    plain_prompt = load_prompt("plain_core")
    checkpoint_path = output_path / "generation_checkpoint.jsonl"

    generated_records: list[dict[str, Any]] = []
    for position, record in enumerate(selected_records, start=1):
        source_text = record[text_field]
        rhetoric_result = transform_with_call_llm(
            call_llm,
            source_text,
            rhetoric_prompt,
            url=url,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_retries=max_retries,
        )
        plain_result = transform_with_call_llm(
            call_llm,
            source_text,
            plain_prompt,
            url=url,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_retries=max_retries,
        )

        generated = {
            **record,
            "variant_generation": {
                "sample_seed": seed,
                "sample_position": position,
                "model_name": model_name,
            },
            "rhetoric_heavy": rhetoric_result,
            "plain_core": plain_result,
            "validation": {
                "rhetoric_heavy": validate_transformation(
                    source_text,
                    rhetoric_result.get("transformed_full_text", ""),
                ),
                "plain_core": validate_transformation(
                    source_text,
                    plain_result.get("transformed_full_text", ""),
                ),
            },
        }
        append_jsonl(checkpoint_path, generated)
        generated_records.append(generated)

    write_json(output_path / "hardest_papers_40_with_variants.json", generated_records)
    return generated_records

