from scientific_llm_evaluator_robustness.review_merge import merge_grouped_reviews


def test_merge_appends_hybrid_variants_and_sources():
    base = [{"source_key": "one", "source_review": {"overall_rating": {"score": 6}}, "variants": [
        {"variant": "A1", "review": {"overall_rating": {"score": 6}}},
    ]}]
    additions = [
        {"source_key": "one", "source_review": {"overall_rating": {"score": 6}}, "variants": [
            {"variant": "H1", "review": {"overall_rating": {"score": 5}}},
        ]},
        {"source_key": "two", "source_review": {"overall_rating": {"score": 7}}, "variants": []},
    ]
    merged = merge_grouped_reviews(base, additions)
    assert [record["source_key"] for record in merged] == ["one", "two"]
    assert [item["variant"] for item in merged[0]["variants"]] == ["A1", "H1"]


def test_merge_rejects_conflicting_variant():
    base = [{"source_key": "one", "variants": [{"variant": "H1", "review": {"overall_rating": {"score": 5}}}]}]
    additions = [{"source_key": "one", "variants": [{"variant": "H1", "review": {"overall_rating": {"score": 6}}}]}]
    try:
        merge_grouped_reviews(base, additions)
    except ValueError as exc:
        assert "Conflicting variant=H1" in str(exc)
    else:
        raise AssertionError("Expected conflict")
