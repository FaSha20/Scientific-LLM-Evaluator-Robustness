from __future__ import annotations

from collections.abc import Callable
import json
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


def transform_text_with_call_llm(
    call_llm: CallLLM,
    *,
    source_text: str,
    system_prompt: str,
    url: str | None = None,
    api_key: str | None = None,
    model_name: str = "deepseek-v3.2",
    temperature: float = 0.2,
    max_retries: int = 3,
) -> str:
    user_message = (
        "Rewrite the following scientific text according to the system instructions. "
        "Return only the rewritten text, with no JSON, no markdown fence, and no extra "
        "commentary.\n\n"
        "<source_text>\n"
        f"{source_text}\n"
        "</source_text>"
    )
    return call_llm(
        user_message,
        system_prompt,
        jsonify=False,
        temp=temperature,
        url=url,
        api_key=api_key,
        model_name=model_name,
        max_retries=max_retries,
    )


def transform_sections_with_call_llm(
    call_llm: CallLLM,
    *,
    abstract: str,
    introduction: str,
    system_prompt: str,
    url: str | None = None,
    api_key: str | None = None,
    model_name: str = "deepseek-v3.2",
    temperature: float = 0.2,
    max_retries: int = 3,
) -> dict[str, Any]:
    user_message = (
        "Rewrite only the abstract and introduction sections according to the "
        "system instructions. Return valid JSON only.\n\n"
        + json.dumps(
            {
                "abstract": abstract,
                "introduction": introduction,
            },
            ensure_ascii=False,
        )
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


def transform_structured_idea_with_call_llm(
    call_llm: CallLLM,
    *,
    idea_text: str,
    system_prompt: str,
    url: str | None = None,
    api_key: str | None = None,
    model_name: str = "deepseek-v3.2",
    temperature: float = 0.2,
    max_retries: int = 3,
) -> str:
    user_message = (
        "Rewrite the following textual research idea according to the system "
        "instructions. Return only the rewritten textual idea, with no JSON, "
        "no markdown fence, and no extra commentary.\n\n"
        "<research_idea>\n"
        f"{idea_text}\n"
        "</research_idea>"
    )
    return call_llm(
        user_message,
        system_prompt,
        jsonify=False,
        temp=temperature,
        url=url,
        api_key=api_key,
        model_name=model_name,
        max_retries=max_retries,
    )
