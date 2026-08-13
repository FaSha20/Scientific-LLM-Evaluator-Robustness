from scientific_llm_evaluator_robustness.structured_idea import (
    serialize_structured_idea,
    select_surface_changes,
    strip_rag_queries,
)


def test_strip_rag_queries_keeps_other_fields():
    content = {"basic_idea": ["x"], "rag_queries": ["search"]}

    stripped = strip_rag_queries(content)

    assert stripped == {"basic_idea": ["x"]}
    assert "rag_queries" in content


def test_select_surface_changes_is_reproducible_and_limited():
    first = select_surface_changes("paper:1", seed=42)
    second = select_surface_changes("paper:1", seed=42)

    assert first == second
    assert len(first) == 2


def test_serialize_structured_idea_returns_text_not_json():
    text = serialize_structured_idea("Paper", {"basic_idea": ["Idea"], "method": {"step_1": ["Do x"]}})

    assert text.startswith("Title: Paper")
    assert "Basic Idea" in text
    assert "- Idea" in text
    assert "{" not in text
