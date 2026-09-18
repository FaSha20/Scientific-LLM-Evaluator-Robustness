import io

from PIL import Image

from scientific_llm_evaluator_robustness.self_refinement_visualization import (
    render_self_refinement_heatmap,
    write_self_refinement_visualizations,
)


def test_self_refinement_heatmap_and_report(tmp_path):
    review = {"overall_rating": {"score": 6}, "problem_significance": {"score": 3}}
    final = {"overall_rating": {"score": 7}, "problem_significance": {"score": 3}}
    image = Image.open(io.BytesIO(render_self_refinement_heatmap(
        "Source <one>", {"draft_review": review}, final,
    )))
    assert image.format == "PNG"
    assert "Self-refinement score comparison" in image.info["Description"]
    records = [{
        "source_key": "one",
        "source_review": final,
        "source_review_self_refinement": {"draft_review": review},
        "variants": [],
    }]
    path = write_self_refinement_visualizations(records, tmp_path / "report")
    contents = path.read_text(encoding="utf-8")
    assert "reviews with at least one changed score: 1" in contents
    assert "Changed score dimensions: overall_rating" in contents
    assert len(list(path.parent.glob("*.png"))) == 1
