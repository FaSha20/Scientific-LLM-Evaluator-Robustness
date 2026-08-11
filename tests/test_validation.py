from scientific_llm_evaluator_robustness.validation import find_missing_numbers


def test_find_missing_numbers_reports_removed_values():
    missing = find_missing_numbers("Accuracy was 92.5% on 10 datasets.", "Accuracy was 92.5%.")

    assert missing == ["10"]

