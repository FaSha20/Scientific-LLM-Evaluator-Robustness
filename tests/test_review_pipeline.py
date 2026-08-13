from scientific_llm_evaluator_robustness.review_pipeline import (
    build_review_input,
    build_full_paper_review_input,
    build_structured_review_input,
    extract_full_paper_review_variants,
    extract_review_variants,
    extract_structured_review_variants,
    group_reviews_by_paper,
)


def test_build_review_input_uses_only_abstract_and_intro():
    text = build_review_input(
        title="Paper",
        variant_name="main",
        abstract="Abstract text.",
        introduction="Intro text.",
    )

    assert "Only the abstract and introduction are provided" in text
    assert "Abstract text." in text
    assert "Intro text." in text


def test_extract_review_variants_from_generated_record():
    record = {
        "title": "Paper",
        "original_sections": {"abstract": "A0", "introduction": "I0"},
        "variants": {
            "plain_core": {"transformed_abstract": "A1", "transformed_introduction": "I1"},
            "rhetoric_heavy": {"transformed_abstract": "A2", "transformed_introduction": "I2"},
        },
    }

    variants = extract_review_variants(record)

    assert variants["main"]["abstract"] == "A0"
    assert variants["plain_core"]["introduction"] == "I1"
    assert variants["rhetoric_heavy"]["abstract"] == "A2"


def test_extract_full_paper_review_variants():
    record = {
        "title": "Paper",
        "full_text": "Original full paper.",
        "variants": {
            "plain_core": {"transformed_full_text": "Plain full paper."},
            "rhetoric_heavy": {"transformed_full_text": "Rhetorical full paper."},
        },
    }

    variants = extract_full_paper_review_variants(record)

    assert variants["main"]["full_text"] == "Original full paper."
    assert variants["plain_core"]["full_text"] == "Plain full paper."
    assert variants["rhetoric_heavy"]["full_text"] == "Rhetorical full paper."


def test_build_full_paper_review_input():
    text = build_full_paper_review_input(
        title="Paper",
        variant_name="main",
        full_text="Full paper body.",
    )

    assert "full research paper" in text
    assert "Full paper body." in text


def test_structured_review_input_excludes_full_paper_assumption():
    text = build_structured_review_input(
        title="Paper",
        variant_name="main",
        idea_text="Basic Idea\n- Idea",
    )

    assert "textual research idea specification" in text
    assert "search query" not in text
    assert "Idea" in text


def test_extract_structured_review_variants():
    record = {
        "paper_name": "Paper",
        "original_text": "A0",
        "variants": {
            "plain_core": {"transformed_text": "A1"},
            "rhetoric_heavy": {"transformed_text": "A2"},
        },
    }

    variants = extract_structured_review_variants(record)

    assert variants["main"]["idea_text"] == "A0"
    assert variants["plain_core"]["idea_text"] == "A1"


def test_group_reviews_by_paper():
    grouped = group_reviews_by_paper(
        [
            {
                "paper_key": "index:1",
                "paper_position": 1,
                "title": "Paper",
                "variant_name": "main",
                "review": {"rating": 5},
            },
            {
                "paper_key": "index:1",
                "paper_position": 1,
                "title": "Paper",
                "variant_name": "plain_core",
                "review": {"rating": 4},
            },
        ]
    )

    assert grouped[0]["reviews"]["main"] == {"rating": 5}
    assert grouped[0]["reviews"]["plain_core"] == {"rating": 4}
