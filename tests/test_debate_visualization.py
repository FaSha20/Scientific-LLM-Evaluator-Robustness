import xml.etree.ElementTree as ET

from scientific_llm_evaluator_robustness.debate_visualization import (
    render_debate_heatmap,
    write_debate_visualizations,
)


def test_heatmap_preserves_multiple_recommendations_and_scales():
    debate = {
        "draft_review": {"overall_rating": {"score": 6}},
        "critic_feedback": {"score_questions": [
            {"dimension": "overall_rating", "recommended_score": 7},
            {"dimension": "overall_rating", "recommended_score": None},
        ]},
    }
    svg = render_debate_heatmap("Source <one> & variant", debate, {"overall_rating": {"score": 8}})
    root = ET.fromstring(svg)
    labels = [element.text for element in root.iter("{http://www.w3.org/2000/svg}text")]
    assert "Source <one> & variant" in labels
    assert "Overall rating (1–10) · critic #0" in labels
    assert "Overall rating (1–10) · critic #1" in labels
    assert labels.count("+2") == 2
    assert "7" in labels
    assert "N/A" in labels
    assert "Problem significance (1–5)" in labels


def test_report_supports_old_checkpoints_and_empty_input(tmp_path):
    records = [{"source_key": "one", "source_review": {}, "source_review_debate": {
        "draft_review": {}, "critic_feedback": {},
    }, "variants": []}]
    path = write_debate_visualizations(records, tmp_path / "old")
    assert "No reviewer rebuttals were saved" in path.read_text(encoding="utf-8")
    assert (path.parent / "debate_00001.svg").exists()
    empty = write_debate_visualizations([], tmp_path / "empty")
    assert "No debate records found" in empty.read_text(encoding="utf-8")
