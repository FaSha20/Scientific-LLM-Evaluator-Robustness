from scientific_llm_evaluator_robustness.sampling import sample_records


def test_sample_records_is_reproducible():
    records = [{"id": index} for index in range(10)]

    first = sample_records(records, sample_size=4, seed=42)
    second = sample_records(records, sample_size=4, seed=42)

    assert first == second
    assert len(first) == 4

