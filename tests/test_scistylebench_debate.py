import json

from scientific_llm_evaluator_robustness.scistylebench import (
    build_review_critique_input,
    build_review_revision_input,
    generate_scistylebench_reviews,
)


def _review(score: int, summary: str) -> dict:
    return {
        "summary": summary,
        "strengths": ["A concrete hypothesis."],
        "weaknesses": [],
        "suggestions": [],
        "questions": [],
        "problem_significance": {"score": 3, "justification": "Moderate importance."},
        "question_specificity": {"score": 3, "justification": "A specific question."},
        "hypothesis_quality": {"score": 3, "justification": "Testable claim."},
        "testability": {"score": 3, "justification": "Can be evaluated."},
        "novelty_contribution": {"score": 3, "justification": "Potential contribution."},
        "technical_plausibility": {"score": 3, "justification": "Plausible."},
        "scientific_insight": {"score": 3, "justification": "Could teach something."},
        "overall_rating": {"score": score, "justification": "Overall calibration."},
        "confidence": 4,
    }


def test_debate_inputs_preserve_draft_and_feedback():
    draft = _review(6, "Draft")
    critique = {"overall_assessment": "Check the score.", "score_questions": []}

    critic_input = build_review_critique_input(review_input="Idea text", draft_review=draft)
    revision_input = build_review_revision_input(
        review_input="Idea text",
        draft_review=draft,
        critic_feedback=critique,
    )

    assert "<draft_review>" in critic_input
    assert '"summary": "Draft"' in critic_input
    assert "<critic_feedback>" in revision_input
    assert "Check the score." in revision_input


def test_scistylebench_debate_persists_draft_critique_and_revision(tmp_path):
    (tmp_path / "source_ideas.csv").write_text(
        "source_idea_id,discipline,source_text\nsource-1,ML,Original idea\n",
        encoding="utf-8",
    )
    input_path = tmp_path / "variant_items_15class.csv"
    input_path.write_text(
        "item_id,source_idea_id,variant,variant_group,expected_quality_direction,variant_text\n"
        "variant-1,source-1,wording,style,same,Variant idea\n",
        encoding="utf-8",
    )
    reviewer_prompt = tmp_path / "reviewer.txt"
    critic_prompt = tmp_path / "critic.txt"
    reviewer_prompt.write_text("reviewer system", encoding="utf-8")
    critic_prompt.write_text("critic system", encoding="utf-8")
    calls = []

    def fake_call_llm(user_message, system_message, **kwargs):
        calls.append((user_message, system_message, kwargs))
        if system_message == "critic system":
            assert "<draft_review>" in user_message
            return {
                "overall_assessment": "The overall score is too low.",
                "score_questions": [
                    {
                        "dimension": "overall_rating",
                        "question_mark": "Why is this only a 6?",
                        "concern": "The draft understates the hypothesis.",
                        "speculative_alternative": "Speculatively, the mechanism may generalize.",
                        "recommended_score": 7,
                        "rationale": "The idea states a testable mechanism.",
                    }
                ],
                "unsupported_claims": [],
                "revision_priorities": ["Reassess the overall score."],
                "confidence": 4,
            }
        if "<critic_feedback>" in user_message:
            assert "Defend supported judgments" in system_message
            review = _review(7, "Revised")
            review["feedback_responses"] = [{
                "feedback_type": "score_questions",
                "feedback_index": 0,
                "decision": "accept",
                "defense": "The initial 6 reflected uncertainty about generalization.",
                "justification": "The stated testable mechanism supports increasing 6 to 7.",
            }]
            return review
        return _review(6, "Draft")

    result = generate_scistylebench_reviews(
        csv_path=input_path,
        output_dir=tmp_path / "out",
        review_prompt_path=reviewer_prompt,
        critic_prompt_path=critic_prompt,
        call_llm=fake_call_llm,
        debate=True,
        resume=False,
    )

    assert len(calls) == 6  # source + variant: draft, critic, then reviewer revision
    assert result["debate_enabled"] is True
    assert result["debate_heatmaps_path"].endswith("README.md")
    assert len(list((tmp_path / "out" / "debate_heatmaps").glob("*.svg"))) == 2
    assert "testable mechanism" in (tmp_path / "out" / "debate_heatmaps" / "README.md").read_text(encoding="utf-8")
    records = json.loads((tmp_path / "out" / "scistylebench_reviews.json").read_text(encoding="utf-8"))
    assert records[0]["source_review"]["summary"] == "Revised"
    assert records[0]["source_review_debate"]["draft_review"]["summary"] == "Draft"
    assert records[0]["source_review_debate"]["critic_feedback"]["score_questions"][0]["dimension"] == "overall_rating"
    assert records[0]["variants"][0]["review"]["overall_rating"]["score"] == 7.0
    assert "review_debate" in records[0]["variants"][0]
    for debate in (records[0]["source_review_debate"], records[0]["variants"][0]["review_debate"]):
        assert debate["feedback_responses"][0]["decision"] == "accept"
        comparison = debate["score_comparison"][-1]
        assert comparison["reviewer_score_before"] == 6
        assert comparison["critic_recommendations"] == [{"feedback_index": 0, "recommended_score": 7}]
        assert comparison["reviewer_score_after"] == 7
        assert debate["score_comparison"][0]["critic_recommendations"] == []
        assert debate["score_comparison"][0]["reviewer_score_before"] == 3
        assert debate["score_comparison"][0]["reviewer_score_after"] == 3
    assert (tmp_path / "out" / "source_review_debates_checkpoint.jsonl").exists()
    assert (tmp_path / "out" / "robustness_report" / "figures" / "mean_rating_shift.svg").exists()
    assert (tmp_path / "out" / "robustness_report" / "figures" / "paper_rating_shift_heatmap.svg").exists()
