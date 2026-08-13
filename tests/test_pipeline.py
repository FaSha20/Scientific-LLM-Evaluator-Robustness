from scientific_llm_evaluator_robustness.pipeline import record_key
from scientific_llm_evaluator_robustness.pipeline import generate_rhetoric_variants


def test_record_key_prefers_paper_id():
    assert record_key({"paperId": "abc", "index": 3}) == "paperId:abc"


def test_record_key_uses_index():
    assert record_key({"index": 3}) == "index:3"


def test_generate_variants_from_structured_text(tmp_path):
    input_path = tmp_path / "records.jsonl"
    input_path.write_text(
        '{"paper_name": "Paper", "extracted_content": {"basic_idea": ["Idea"], "rag_queries": ["query"]}}\n',
        encoding="utf-8",
    )

    def fake_call_llm(user_message, system_message=None, **kwargs):
        assert kwargs["jsonify"] is False
        assert "<research_idea>" in user_message
        return "Rewritten idea"

    records = generate_rhetoric_variants(
        input_path=input_path,
        output_dir=tmp_path / "out",
        call_llm=fake_call_llm,
        sample_size=1,
        source_mode="structured_text",
        resume=False,
    )

    assert records[0]["variant_generation"]["source_format"] == "structured_text"
    assert "rag_queries" not in records[0]["original_content"]
    assert records[0]["variants"]["plain_core"]["transformed_text"] == "Rewritten idea"


def test_generate_variants_from_full_text(tmp_path):
    input_path = tmp_path / "records.json"
    input_path.write_text(
        '[{"index": 1, "title": "Paper", "full_text": "Full paper text."}]',
        encoding="utf-8",
    )

    def fake_call_llm(user_message, system_message=None, **kwargs):
        assert kwargs["jsonify"] is False
        assert "<source_text>" in user_message
        return "Rewritten full text"

    records = generate_rhetoric_variants(
        input_path=input_path,
        output_dir=tmp_path / "out",
        call_llm=fake_call_llm,
        sample_size=1,
        source_mode="full_text",
        resume=False,
    )

    assert records[0]["variant_generation"]["source_format"] == "full_text"
    assert records[0]["original_text"] == "Full paper text."
    assert records[0]["variants"]["rhetoric_heavy"]["transformed_text"] == "Rewritten full text"
