from __future__ import annotations

from collections.abc import Callable
from typing import Any


CallLLM = Callable[..., Any]


def transform_with_call_llm(
    call_llm: CallLLM,
    full_text: str,
    system_prompt: str,
    *,
    url: str | None = None,
    api_key: str | None = None,
    model_name: str = "deepseek-v3.2",
    temperature: float = 0.2,
    max_retries: int = 3,
) -> dict[str, Any]:
    user_message = (
        "Rewrite the following paper according to the system instructions.\n\n"
        "<paper_text>\n"
        f"{full_text}\n"
        "</paper_text>"
    )
    return call_llm(
        user_message,
        system_prompt,
        jsonify=True,
        temp=temperature,
        url=url,
        api_key=api_key,
        model_name=model_name,
        max_retries=max_retries,
    )

