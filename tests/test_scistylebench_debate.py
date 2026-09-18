import json

from scientific_llm_evaluator_robustness.scistylebench import (
    build_review_critique_input,
    build_review_revision_input,
    build_self_refinement_input,
    enforce_critic_grounding,
    generate_scistylebench_reviews,
    _load_pair_checkpoint,
    _load_source_checkpoint,
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


def test_self_refinement_uses_only_the_idea_and_previous_review():
    draft = _review(6, "Draft")
    refinement_input = build_self_refinement_input(review_input="Idea text", draft_review=draft)
    assert "<research_idea>" in refinement_input
    assert "<previous_review>" in refinement_input
    assert '"summary": "Draft"' in refinement_input
    assert "critic" not in refinement_input.lower()
    assert "provisional evidence" in refinement_input
    assert "independently" in refinement_input


def test_scistylebench_self_refinement_reuses_reviewer_model_and_prompt(tmp_path):
    (tmp_path / "source_ideas.csv").write_text(
        "source_idea_id,discipline,source_text\nsource-1,ML,Original idea\n", encoding="utf-8"
    )
    input_path = tmp_path / "variant_items_15class.csv"
    input_path.write_text(
        "item_id,source_idea_id,variant,variant_group,expected_quality_direction,variant_text\n"
        "variant-1,source-1,wording,style,same,Variant idea\n", encoding="utf-8"
    )
    reviewer_prompt = tmp_path / "reviewer.txt"
    reviewer_prompt.write_text("reviewer system", encoding="utf-8")
    calls = []

    def fake_call_llm(user_message, system_message, **kwargs):
        calls.append((user_message, system_message, kwargs))
        return _review(
            7 if "<previous_review>" in user_message else 6,
            "Refined" if "<previous_review>" in user_message else "Draft",
        )

    result = generate_scistylebench_reviews(
        csv_path=input_path,
        output_dir=tmp_path / "out",
        review_prompt_path=reviewer_prompt,
        call_llm=fake_call_llm,
        self_refine=True,
        self_refine_temperature=0.4,
        resume=False,
    )

    assert len(calls) == 4  # source + variant: draft, then self-refinement
    assert {system_message for _, system_message, _ in calls} == {"reviewer system"}
    assert [kwargs["temp"] for _, _, kwargs in calls] == [0.0, 0.0, 0.4, 0.4]
    assert result["self_refinement_enabled"] is True
    records = json.loads((tmp_path / "out" / "scistylebench_reviews.json").read_text(encoding="utf-8"))
    refinement = records[0]["variants"][0]["review_self_refinement"]
    assert refinement["draft_review"]["summary"] == "Draft"
    assert records[0]["variants"][0]["review"]["summary"] == "Refined"
    assert not (tmp_path / "out" / "debate_heatmaps").exists()


def test_self_refinement_can_use_saved_reviews_without_initial_calls(tmp_path):
    (tmp_path / "source_ideas.csv").write_text(
        "source_idea_id,discipline,source_text\nsource-1,ML,Original idea\n", encoding="utf-8"
    )
    input_path = tmp_path / "variant_items_15class.csv"
    input_path.write_text(
        "item_id,source_idea_id,variant,variant_group,expected_quality_direction,variant_text\n"
        "variant-1,source-1,wording,style,same,Variant idea\n", encoding="utf-8"
    )
    saved_reviews = tmp_path / "drafts.json"
    saved_reviews.write_text(json.dumps([{
        "source_key": "source-1",
        "source_review": _review(6, "Saved source draft"),
        "variants": [{"variant": "wording", "review": _review(6, "Saved variant draft")}],
    }]), encoding="utf-8")
    reviewer_prompt = tmp_path / "reviewer.txt"
    reviewer_prompt.write_text("reviewer system", encoding="utf-8")
    calls = []

    def fake_call_llm(user_message, system_message, **kwargs):
        calls.append((user_message, system_message, kwargs))
        return _review(7, "Refined")

    generate_scistylebench_reviews(
        csv_path=input_path,
        output_dir=tmp_path / "out",
        review_prompt_path=reviewer_prompt,
        call_llm=fake_call_llm,
        self_refine=True,
        draft_reviews_path=saved_reviews,
        resume=False,
    )

    assert len(calls) == 2  # source + variant self-refinement only
    assert all("<previous_review>" in user_message for user_message, _, _ in calls)


def test_variant_prefix_limits_scistylebench_reviews(tmp_path):
    input_path = tmp_path / "variants.csv"
    input_path.write_text(
        "item_id,source_idea_id,discipline,source_text,variant,variant_text\n"
        "one,source-1,ML,Source,H1_Test,H idea\n"
        "two,source-1,ML,Source,A1_Test,A idea\n",
        encoding="utf-8",
    )
    prompt = tmp_path / "reviewer.txt"
    prompt.write_text("reviewer", encoding="utf-8")
    calls = []

    def fake_call_llm(*args, **kwargs):
        calls.append(args)
        return _review(6, "Review")

    result = generate_scistylebench_reviews(
        csv_path=input_path,
        output_dir=tmp_path / "out",
        review_prompt_path=prompt,
        call_llm=fake_call_llm,
        variant_prefixes=("H",),
        resume=False,
    )
    assert result["n_sources"] == 1
    assert result["n_variants"] == 1
    assert len(calls) == 2


def test_variant_name_limits_scistylebench_reviews(tmp_path):
    input_path = tmp_path / "variants.csv"
    input_path.write_text(
        "item_id,source_idea_id,discipline,source_text,variant,variant_text\n"
        "one,source-1,ML,Source,A3_Plain_Core,Plain idea\n"
        "two,source-1,ML,Source,C2_Logic_Flawed,Flawed idea\n",
        encoding="utf-8",
    )
    prompt = tmp_path / "reviewer.txt"
    prompt.write_text("reviewer", encoding="utf-8")
    calls = []

    def fake_call_llm(*args, **kwargs):
        calls.append(args)
        return _review(6, "Review")

    result = generate_scistylebench_reviews(
        csv_path=input_path, output_dir=tmp_path / "out", review_prompt_path=prompt,
        call_llm=fake_call_llm, variant_names=("C2_Logic_Flawed",), resume=False,
    )
    assert result["n_sources"] == 1
    assert result["n_variants"] == 1
    assert len(calls) == 2


def test_saved_drafts_generate_only_missing_variants_before_self_refinement(tmp_path):
    input_path = tmp_path / "variant_items_15class.csv"
    input_path.write_text(
        "item_id,source_idea_id,variant,variant_group,expected_quality_direction,variant_text\n"
        "one,source-1,A3_Plain_Core,baseline,same,Plain idea\n"
        "two,source-1,H1_Deceptive_Hollow,hybrid,down,H idea\n", encoding="utf-8"
    )
    saved_reviews = tmp_path / "drafts.json"
    saved_reviews.write_text(json.dumps([{
        "source_key": "source-1", "source_review": _review(6, "Saved source draft"),
        "variants": [{"variant": "A3_Plain_Core", "review": _review(6, "Saved plain draft")}],
    }]), encoding="utf-8")
    reviewer_prompt = tmp_path / "reviewer.txt"
    reviewer_prompt.write_text("reviewer system", encoding="utf-8")
    calls = []

    def fake_call_llm(user_message, system_message, **kwargs):
        calls.append(user_message)
        return _review(7, "Generated or refined")

    result = generate_scistylebench_reviews(
        csv_path=input_path, output_dir=tmp_path / "out", review_prompt_path=reviewer_prompt,
        call_llm=fake_call_llm, self_refine=True, draft_reviews_path=saved_reviews, resume=False,
    )

    assert len(calls) == 4  # H draft, source refinement, A3 refinement, H refinement.
    assert sum("<previous_review>" in call for call in calls) == 3
    assert result["n_variants"] == 2


def test_variant_prefix_can_merge_generated_reviews_into_existing_output(tmp_path):
    input_path = tmp_path / "variants.csv"
    input_path.write_text(
        "item_id,source_idea_id,discipline,source_text,variant,variant_text\n"
        "one,new-source,ML,New source,H1_Test,H idea\n", encoding="utf-8"
    )
    prompt = tmp_path / "reviewer.txt"
    prompt.write_text("reviewer", encoding="utf-8")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / "scistylebench_reviews.json").write_text(json.dumps([{
        "source_key": "existing-source", "source_review": _review(6, "Existing"), "variants": [],
    }]), encoding="utf-8")

    generate_scistylebench_reviews(
        csv_path=input_path,
        output_dir=output_dir,
        review_prompt_path=prompt,
        call_llm=lambda *args, **kwargs: _review(6, "New"),
        variant_prefixes=("H",),
        merge_existing_reviews=True,
        resume=False,
    )
    merged = json.loads((output_dir / "scistylebench_reviews.json").read_text(encoding="utf-8"))
    assert [record["source_key"] for record in merged] == ["existing-source", "new-source"]


def test_source_id_limits_scistylebench_reviews(tmp_path):
    input_path = tmp_path / "variants.csv"
    input_path.write_text(
        "item_id,source_idea_id,discipline,source_text,variant,variant_text\n"
        "one,source-1,ML,Source,A1_Test,First idea\n"
        "two,source-2,ML,Source,A1_Test,Second idea\n",
        encoding="utf-8",
    )
    prompt = tmp_path / "reviewer.txt"
    prompt.write_text("reviewer", encoding="utf-8")
    result = generate_scistylebench_reviews(
        csv_path=input_path,
        output_dir=tmp_path / "out",
        review_prompt_path=prompt,
        call_llm=lambda *args, **kwargs: _review(6, "Review"),
        source_ids=("source-2",),
        resume=False,
    )
    assert result["n_sources"] == 1
    assert result["n_variants"] == 1


def test_legacy_checkpoint_keys_are_normalized(tmp_path):
    source_path = tmp_path / "source.jsonl"
    source_path.write_text(json.dumps({"source_key": "None::source-1", "review": _review(6, "Draft")}) + "\n")
    pair_path = tmp_path / "pair.jsonl"
    pair_path.write_text(json.dumps({"pair_key": "None", "source_key": "None::source-1", "variant": "H1_Test", "review": _review(6, "Draft")}) + "\n")
    assert set(_load_source_checkpoint(source_path)) == {"source-1"}
    assert set(_load_pair_checkpoint(pair_path)) == {"source-1::H1_Test"}


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
                        "evidence_from_idea": "Variant idea" if "Variant idea" in user_message else "Original idea",
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
    assert (tmp_path / "out" / "scientific_robustness_metrics.png").exists()
    metrics = json.loads((tmp_path / "out" / "scientific_robustness_metrics.json").read_text(encoding="utf-8"))
    assert {row["metric"] for row in metrics["summaries"]} == {"SBI", "SRR", "AWR"}
    assert result["debate_heatmaps_path"].endswith("README.md")
    assert len(list((tmp_path / "out" / "debate_heatmaps").glob("*.png"))) == 3
    assert not list((tmp_path / "out").rglob("*.svg"))
    assert "testable mechanism" in (tmp_path / "out" / "debate_heatmaps" / "README.md").read_text(encoding="utf-8")
    records = json.loads((tmp_path / "out" / "scistylebench_reviews.json").read_text(encoding="utf-8"))
    assert records[0]["source_review"]["summary"] == "Revised"
    assert records[0]["source_review_debate"]["draft_review"]["summary"] == "Draft"
    assert records[0]["source_review_debate"]["critic_feedback"]["score_questions"][0]["dimension"] == "overall_rating"
    assert records[0]["variants"][0]["review"]["overall_rating"]["score"] == 7.0
    assert "review_debate" in records[0]["variants"][0]
    for expected_evidence, debate in (
        ("Original idea", records[0]["source_review_debate"]),
        ("Variant idea", records[0]["variants"][0]["review_debate"]),
    ):
        assert debate["feedback_responses"][0]["decision"] == "accept"
        comparison = debate["score_comparison"][-1]
        assert comparison["reviewer_score_before"] == 6
        assert comparison["critic_recommendations"] == [{
            "feedback_index": 0,
            "recommended_score": 7,
            "evidence_from_idea": expected_evidence,
            "grounding_status": "grounded",
        }]
        assert comparison["reviewer_score_after"] == 7
        assert debate["score_comparison"][0]["critic_recommendations"] == []
        assert debate["score_comparison"][0]["reviewer_score_before"] == 3
        assert debate["score_comparison"][0]["reviewer_score_after"] == 3
    assert (tmp_path / "out" / "source_review_debates_checkpoint.jsonl").exists()
    assert not (tmp_path / "out" / "robustness_report").exists()


def test_ungrounded_upward_critic_recommendation_is_blocked():
    feedback = {"score_questions": [{
        "dimension": "overall_rating",
        "recommended_score": 7,
        "evidence_from_idea": "A future experiment that was never stated.",
    }]}

    result = enforce_critic_grounding(
        feedback,
        draft_review=_review(6, "Draft"),
        review_input="A summarized research idea is provided below.\n\nIdea Summary:\nOriginal idea",
    )

    question = result["score_questions"][0]
    assert question["recommended_score"] is None
    assert question["grounding_status"] == "blocked_missing_or_unverifiable_evidence"


def test_same_score_critic_recommendation_becomes_refinement_only():
    feedback = {"score_questions": [{"dimension": "overall_rating", "recommended_score": 6}]}

    result = enforce_critic_grounding(
        feedback,
        draft_review=_review(6, "Draft"),
        review_input="Idea Summary:\nOriginal idea",
    )

    question = result["score_questions"][0]
    assert question["recommended_score"] is None
    assert question["grounding_status"] == "same_as_draft_not_actionable"


def test_scistylebench_moderated_panel_persists_independent_reviews(tmp_path):
    (tmp_path / "source_ideas.csv").write_text(
        "source_idea_id,discipline,source_text\nsource-1,ML,Original idea\n", encoding="utf-8"
    )
    input_path = tmp_path / "variant_items_15class.csv"
    input_path.write_text(
        "item_id,source_idea_id,variant,variant_group,expected_quality_direction,variant_text\n"
        "variant-1,source-1,wording,style,same,Variant idea\n", encoding="utf-8"
    )
    base_prompt, technical_prompt, rhetoric_prompt, moderator_prompt = (
        tmp_path / "base.txt", tmp_path / "technical.txt", tmp_path / "rhetoric.txt", tmp_path / "moderator.txt"
    )
    base_prompt.write_text("base system", encoding="utf-8")
    technical_prompt.write_text("technical role", encoding="utf-8")
    rhetoric_prompt.write_text("rhetoric role", encoding="utf-8")
    moderator_prompt.write_text("moderator role", encoding="utf-8")
    calls = []

    def fake_call_llm(user_message, system_message, **kwargs):
        calls.append((user_message, system_message))
        if "moderator role" in system_message:
            assert "<technical_scientific_review>" in user_message
            assert "<rhetoric_audit_review>" in user_message
            return _review(8, "Moderated")
        if "rhetoric role" in system_message:
            assert "<technical_scientific_review>" not in user_message
            return _review(5, "Rhetoric")
        assert "technical role" in system_message
        return _review(6, "Technical")

    result = generate_scistylebench_reviews(
        csv_path=input_path, output_dir=tmp_path / "out", review_prompt_path=base_prompt,
        technical_prompt_path=technical_prompt, rhetoric_prompt_path=rhetoric_prompt,
        moderator_prompt_path=moderator_prompt, call_llm=fake_call_llm,
        moderated_panel=True, resume=False,
    )

    assert len(calls) == 6
    assert result["moderated_panel_enabled"] is True
    assert result["moderation_heatmaps_path"].endswith("README.md")
    records = json.loads((tmp_path / "out" / "scistylebench_reviews.json").read_text(encoding="utf-8"))
    assert records[0]["source_review"]["summary"] == "Moderated"
    source_panel = records[0]["source_review_moderation"]
    assert source_panel["technical_review"]["summary"] == "Technical"
    assert source_panel["rhetoric_review"]["summary"] == "Rhetoric"
    assert records[0]["variants"][0]["review"]["summary"] == "Moderated"
    assert "review_moderation" in records[0]["variants"][0]
    assert (tmp_path / "out" / "source_moderated_reviews_checkpoint.jsonl").exists()
    assert (tmp_path / "out" / "pair_moderated_reviews_checkpoint.jsonl").exists()
    assert len(list((tmp_path / "out" / "moderation_heatmaps").glob("*.svg"))) == 2
