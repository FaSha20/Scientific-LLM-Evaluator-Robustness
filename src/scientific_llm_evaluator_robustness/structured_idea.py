from __future__ import annotations

import copy
import random
from typing import Any


SURFACE_CHANGES = {
    "B1_verbose": "Verbose: expand descriptions with modest additional detail.",
    "B2_grand_narrative": "Grand Narrative: add broader framing without unsupported claims.",
    "B3_overconfident": "Overconfident: make existing claims sound more certain, without changing evidence.",
    "B4_novelty_emphasis": "Novelty Emphasis: strengthen novelty-related wording.",
    "B5_application_framing": "Application Framing: emphasize practical value and potential impact.",
}


def strip_rag_queries(extracted_content: dict[str, Any]) -> dict[str, Any]:
    content = copy.deepcopy(extracted_content)
    content.pop("rag_queries", None)
    return content


def get_structured_content(record: dict[str, Any]) -> dict[str, Any]:
    extracted_content = record.get("extracted_content")
    if not isinstance(extracted_content, dict):
        raise ValueError("Structured record must contain an extracted_content object")
    return strip_rag_queries(extracted_content)


def serialize_structured_idea(title: str, content: dict[str, Any]) -> str:
    lines = [f"Title: {title}".strip(), ""]
    for field_name, value in content.items():
        lines.append(_format_heading(field_name))
        lines.append(_format_value(value))
        lines.append("")
    return "\n".join(lines).strip()


def _format_heading(field_name: str) -> str:
    return field_name.replace("_", " ").title()


def _format_value(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, list):
        return "\n".join(f"{prefix}- {_format_value(item, indent + 2).strip()}" for item in value)
    if isinstance(value, dict):
        blocks = []
        for key, item in value.items():
            blocks.append(f"{prefix}{_format_heading(str(key))}:\n{_format_value(item, indent + 2)}")
        return "\n".join(blocks)
    return f"{prefix}{value}"


def select_surface_changes(key: str, seed: int, count: int = 2) -> list[str]:
    if count < 1:
        raise ValueError("count must be positive")
    if count > len(SURFACE_CHANGES):
        raise ValueError("count cannot exceed number of available surface changes")

    rng = random.Random(f"{seed}:{key}")
    return rng.sample(list(SURFACE_CHANGES), count)


def describe_surface_changes(change_ids: list[str]) -> str:
    return "\n".join(f"- {change_id}: {SURFACE_CHANGES[change_id]}" for change_id in change_ids)
