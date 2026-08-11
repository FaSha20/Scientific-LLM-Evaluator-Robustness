from __future__ import annotations

import re


NUMBER_PATTERN = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?:%|e-?\d+)?", re.IGNORECASE)


def extract_numbers(text: str) -> list[str]:
    return NUMBER_PATTERN.findall(text)


def find_missing_numbers(source_text: str, transformed_text: str) -> list[str]:
    source_numbers = set(extract_numbers(source_text))
    transformed_numbers = set(extract_numbers(transformed_text))
    return sorted(source_numbers - transformed_numbers)


def validate_transformation(source_text: str, transformed_text: str) -> dict[str, object]:
    missing_numbers = find_missing_numbers(source_text, transformed_text)
    return {
        "missing_numbers": missing_numbers,
        "has_text": bool(transformed_text.strip()),
        "source_length": len(source_text),
        "transformed_length": len(transformed_text),
    }

