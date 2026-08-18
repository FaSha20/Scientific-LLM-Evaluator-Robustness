from scientific_llm_evaluator_robustness.review_pipeline import (
    build_full_paper_review_input,
    extract_full_paper_review_variants,
    extract_paper_metadata,
    group_reviews_by_paper,
)


def test_build_full_paper_review_input_hides_variant_name():
    text = build_full_paper_review_input(
        title="Paper",
        full_text="Full paper body.",
    )

    assert "full research paper" in text
    assert "Variant:" not in text
    assert "Full paper body." in text


def test_extract_full_paper_review_variants():
    record = {
        "title": "Paper",
        "full_text": "Original full paper.",
        "variants": {
            "plain_core": {"transformed_full_text": "Plain full paper."},
            "rhetoric_heavy": {"transformed_full_text": "Rhetorical full paper."},
            "rhetoric_heavier": {"transformed_full_text": "Heavier rhetorical full paper."},
        },
    }

    variants = extract_full_paper_review_variants(record)

    assert variants["main"]["full_text"] == "Original full paper."
    assert variants["plain_core"]["full_text"] == "Plain full paper."
    assert variants["rhetoric_heavy"]["full_text"] == "Rhetorical full paper."
    assert variants["rhetoric_heavier"]["full_text"] == "Heavier rhetorical full paper."


def test_extract_paper_metadata_includes_gt_and_pred_rating():
    metadata = extract_paper_metadata(
        {
            "Rating_gt": 7.5,
            "Rating_pred": 4.75,
            "Decision_gt": "Accept",
            "Decision_pred": "Reject",
            "full_text": "not copied",
        }
    )

    assert metadata == {
        "Rating_gt": 7.5,
        "Rating_pred": 4.75,
        "Decision_gt": "Accept",
        "Decision_pred": "Reject",
    }


def test_group_reviews_by_paper_keeps_metadata():
    grouped = group_reviews_by_paper(
        [
            {
                "paper_key": "index:1",
                "paper_position": 1,
                "title": "Paper",
                "variant_name": "main",
                "paper_metadata": {"Rating_gt": 7.5},
                "review": {"rating": 5},
            },
            {
                "paper_key": "index:1",
                "paper_position": 1,
                "title": "Paper",
                "variant_name": "plain_core",
                "paper_metadata": {"Rating_gt": 7.5},
                "review": {"rating": 4},
            },
            {
                "paper_key": "index:1",
                "paper_position": 1,
                "title": "Paper",
                "variant_name": "rhetoric_heavier",
                "paper_metadata": {"Rating_gt": 7.5},
                "review": {"rating": 3},
            },
        ]
    )

    assert grouped[0]["paper_metadata"] == {"Rating_gt": 7.5}
    assert grouped[0]["reviews"]["main"] == {"rating": 5}
    assert grouped[0]["reviews"]["plain_core"] == {"rating": 4}
    assert grouped[0]["reviews"]["rhetoric_heavier"] == {"rating": 3}
