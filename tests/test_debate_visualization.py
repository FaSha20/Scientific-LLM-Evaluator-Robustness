import io

from PIL import Image

from scientific_llm_evaluator_robustness.debate_visualization import (
    render_debate_heatmap,
    write_debate_visualizations,
    summarize_debate_shifts,
    render_mean_shift_chart,
)


def test_heatmap_preserves_multiple_recommendations_and_scales():
    debate = {
        "draft_review": {"overall_rating": {"score": 6}},
        "critic_feedback": {"score_questions": [
            {"dimension": "overall_rating", "recommended_score": 7},
            {"dimension": "overall_rating", "recommended_score": None},
        ]},
    }
    png = render_debate_heatmap("Source <one> & variant", debate, {"overall_rating": {"score": 8}})
    image = Image.open(io.BytesIO(png))
    assert image.format == "PNG"
    assert image.width == 2120
    labels = image.info["Description"].splitlines()
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
    assert len(list(path.parent.glob("*.png"))) == 1
    assert not list(path.parent.glob("*.svg"))
    image_path = next(path.parent.glob("*.png"))
    modified = image_path.stat().st_mtime_ns
    write_debate_visualizations(records + records, path.parent)
    assert len(list(path.parent.glob("*.png"))) == 1
    assert image_path.stat().st_mtime_ns == modified
    empty = write_debate_visualizations([], tmp_path / "empty")
    assert "No debate records found" in empty.read_text(encoding="utf-8")


def test_mean_shifts_use_matched_pairs_and_count_sources_once():
    def review(score):
        return {"overall_rating": {"score": score}}

    records = [{
        "source_key": "one", "source_review": review(7),
        "source_review_debate": {"draft_review": review(6)},
        "variants": [
            {"variant": "style", "review": review(9), "review_debate": {"draft_review": review(7)}},
            {"variant": "missing", "review": review(10)},
        ],
    }, {
        "source_key": "two", "source_review": review(5),
        "source_review_debate": {"draft_review": review(6)},
        "variants": [{"variant": "style", "review": review(5), "review_debate": {"draft_review": review(5)}}],
    }]
    summary = summarize_debate_shifts(records + records)
    row = next(row for row in summary["variants"] if row["variant"] == "style" and row["dimension"] == "overall_rating")
    assert row["n"] == 2
    assert row["mean_shift_before"] == 0
    assert row["mean_shift_after"] == 1
    assert row["mean_reviewer_revision"] == 1
    assert summary["source_revision"]["overall_rating"] == {"n": 2, "mean_after_minus_before": 0}
    missing = next(row for row in summary["variants"] if row["variant"] == "missing" and row["dimension"] == "overall_rating")
    assert missing["n"] == 0
    assert missing["mean_shift_before"] is None
    assert Image.open(io.BytesIO(render_mean_shift_chart(summary))).format == "PNG"
