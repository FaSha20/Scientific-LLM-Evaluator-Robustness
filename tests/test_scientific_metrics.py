import copy
import io
import json

import pytest
from PIL import Image

from scientific_llm_evaluator_robustness.scientific_metrics import (
    DIMENSIONS,
    evaluate_scientific_metrics,
    load_metrics_config,
    render_scientific_metrics,
    validate_metrics_config,
    write_scientific_metrics,
)


def _review(score, overall=None):
    return {**{dimension: {"score": score} for dimension in DIMENSIONS},
            "overall_rating": {"score": overall if overall is not None else score * 2}}


def _records():
    scores = {
        "Plain": (3, 3), "Paraphrase": (3, 4), "Enriched": (4, 4),
        "Hollow": (3, 2), "Flawed": (2, 3), "Verbose": (5, 4),
        "Hollow persuasive": (4, 2),
    }
    return [{"source_key": "idea-1", "source_review": _review(5), "variants": [
        {"variant": label, "review": _review(after), "review_debate": {"draft_review": _review(before)}}
        for label, (before, after) in scores.items()
    ]}]


def _config():
    return {"style_variants": ["Verbose"], "adversarial_pairs": [["Plain", "Hollow persuasive"]]}


def _summary(result, metric, dimension="overall_rating", comparison=None):
    return next(row for row in result["summaries"] if row["metric"] == metric
                and row["dimension"] == dimension and row["comparison"] == comparison)


def test_exact_formulas_controls_and_strict_ties():
    result = evaluate_scientific_metrics(_records(), _config())
    sbi = _summary(result, "SBI", "dimension_mean")
    assert sbi["paired_before"]["value"] == 2
    assert sbi["paired_final"]["value"] == 0
    assert sbi["final"]["n"] == 7
    srr = _summary(result, "SRR")
    assert srr["paired_before"]["value"] == pytest.approx(2 / 3)
    assert srr["paired_final"]["value"] == pytest.approx(2 / 3)
    assert srr["final"]["ties"] == 1
    assert srr["final"]["wins"] == 2
    awr = _summary(result, "AWR")
    assert awr["paired_before"]["value"] == 0
    assert awr["paired_final"]["value"] == 1
    assert awr["final"]["n"] == 1


def test_signed_sbi_is_not_absolute_deviation():
    records = _records()
    records[0]["variants"][-2]["review"] = _review(2)
    absolute = evaluate_scientific_metrics(records, _config())
    signed = evaluate_scientific_metrics(records, {**_config(), "sbi_formula": "signed"})
    assert _summary(absolute, "SBI", "dimension_mean")["final"]["value"] == 0
    assert _summary(signed, "SBI", "dimension_mean")["final"]["value"] == -2


def test_missing_controls_no_source_fallback_and_matched_cohorts():
    records = _records()
    second = copy.deepcopy(records[0])
    second["source_key"] = "idea-2"
    for variant in second["variants"]:
        variant.pop("review_debate")
    records.append(second)
    result = evaluate_scientific_metrics(records, _config())
    assert _summary(result, "SBI", "dimension_mean")["final"]["n"] == 14
    assert _summary(result, "SBI", "dimension_mean")["paired_final"]["n"] == 7
    for record in records:
        record["variants"] = [variant for variant in record["variants"] if variant["variant"] != "Plain"]
    missing = evaluate_scientific_metrics(records, _config())
    assert _summary(missing, "SBI")["final"]["value"] is None
    assert _summary(missing, "SRR")["final"]["value"] is None
    assert _summary(missing, "AWR")["final"]["value"] is None
    assert any("Plain" in warning for warning in missing["warnings"])


@pytest.mark.parametrize("invalid", [None, True, "nan", float("inf"), 0, 11])
def test_invalid_scores_are_excluded_not_failures(invalid):
    records = _records()
    records[0]["variants"][0]["review"]["overall_rating"]["score"] = invalid
    result = evaluate_scientific_metrics(records, _config())
    assert _summary(result, "AWR")["final"]["n"] == 0
    assert _summary(result, "AWR")["final"]["value"] is None


def test_duplicates_are_not_double_counted_and_conflicts_fail():
    records = _records()
    result = evaluate_scientific_metrics(records + records, _config())
    assert _summary(result, "AWR")["final"]["n"] == 1
    conflicting = copy.deepcopy(records[0])
    conflicting["variants"][0]["review"] = _review(4)
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        evaluate_scientific_metrics(records + [conflicting], _config())


def test_case_insensitive_labels_and_explicit_style_discovery():
    records = _records()
    for variant in records[0]["variants"]:
        variant["variant"] = variant["variant"].lower()
        if variant["variant"] == "verbose":
            variant.update(variant_group="style", expected_quality_direction="same")
    result = evaluate_scientific_metrics(records)
    assert result["resolved_style_variants"] == ["verbose"]
    assert _summary(result, "SRR")["final"]["n"] == 3
    assert _summary(result, "AWR")["final"]["value"] is None
    assert any("AWR unavailable" in warning for warning in result["warnings"])


def test_config_validation(tmp_path):
    with pytest.raises(ValueError, match="Unknown"):
        validate_metrics_config({"awr_pairs": []})
    with pytest.raises(ValueError, match="Duplicate adversarial"):
        validate_metrics_config({"adversarial_pairs": [["Plain", "Hollow persuasive"], ["plain", "hollow persuasive"]]})
    with pytest.raises(ValueError, match="must not include"):
        validate_metrics_config({"style_variants": ["Flawed"]})
    path = tmp_path / "config.json"
    path.write_text(json.dumps(_config()), encoding="utf-8")
    assert load_metrics_config(path)["style_variants"] == ["Verbose"]


def test_outputs_and_empty_metrics(tmp_path):
    result = write_scientific_metrics(_records(), tmp_path, _config())
    with Image.open(result["figure_path"]) as image:
        assert image.format == "PNG"
    assert "SBI" in (tmp_path / "scientific_robustness_metrics.md").read_text(encoding="utf-8")
    empty = evaluate_scientific_metrics([])
    assert _summary(empty, "SRR")["final"]["value"] is None
    assert Image.open(io.BytesIO(render_scientific_metrics(empty, paired=False))).format == "PNG"
