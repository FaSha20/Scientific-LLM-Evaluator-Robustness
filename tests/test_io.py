from scientific_llm_evaluator_robustness.io import append_jsonl, read_jsonl


def test_read_jsonl_returns_empty_list_for_missing_file(tmp_path):
    assert read_jsonl(tmp_path / "missing.jsonl") == []


def test_append_and_read_jsonl(tmp_path):
    path = tmp_path / "records.jsonl"

    append_jsonl(path, {"id": 1})
    append_jsonl(path, {"id": 2})

    assert read_jsonl(path) == [{"id": 1}, {"id": 2}]
