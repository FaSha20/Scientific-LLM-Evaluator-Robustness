from __future__ import annotations

import random
from typing import Any


def sample_records(
    records: list[dict[str, Any]],
    sample_size: int,
    seed: int,
) -> list[dict[str, Any]]:
    if sample_size < 1:
        raise ValueError("sample_size must be positive")
    if sample_size > len(records):
        raise ValueError("sample_size cannot exceed number of records")

    rng = random.Random(seed)
    selected_indices = rng.sample(range(len(records)), sample_size)
    return [records[index] for index in selected_indices]

