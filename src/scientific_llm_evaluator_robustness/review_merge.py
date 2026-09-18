from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def merge_grouped_reviews(
    base_records: list[dict[str, Any]], additions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Append grouped SciStyleBench records while rejecting conflicting duplicates."""
    merged = deepcopy(base_records)
    index = {str(record.get("source_key")): record for record in merged if record.get("source_key") is not None}
    for addition in additions:
        source_key = str(addition.get("source_key"))
        if source_key not in index:
            merged.append(deepcopy(addition))
            index[source_key] = merged[-1]
            continue
        target = index[source_key]
        for field in ("discipline", "source_text", "source_review"):
            original, incoming = target.get(field), addition.get(field)
            if original not in (None, "", {}) and incoming not in (None, "", {}) and original != incoming:
                raise ValueError(f"Conflicting {field} for source_key={source_key}")
            if original in (None, "", {}):
                target[field] = deepcopy(incoming)
        variants = target.setdefault("variants", [])
        variant_index = {str(variant.get("variant")): variant for variant in variants}
        for variant in addition.get("variants", []):
            key = str(variant.get("variant"))
            if key in variant_index:
                if variant_index[key] != variant:
                    raise ValueError(f"Conflicting variant={key} for source_key={source_key}")
                continue
            variants.append(deepcopy(variant))
    for record in merged:
        record["variants"] = sorted(record.get("variants", []), key=lambda item: str(item.get("variant")))
    return sorted(merged, key=lambda item: str(item.get("source_key")))


def merge_review_files(
    *, base_path: str | Path, additions_path: str | Path, output_path: str | Path | None = None,
) -> Path:
    base = Path(base_path)
    additions = Path(additions_path)
    output = Path(output_path) if output_path else base
    base_records = json.loads(base.read_text(encoding="utf-8"))
    addition_records = json.loads(additions.read_text(encoding="utf-8"))
    if not isinstance(base_records, list) or not isinstance(addition_records, list):
        raise ValueError("Both review files must be JSON arrays")
    merged = merge_grouped_reviews(base_records, addition_records)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
