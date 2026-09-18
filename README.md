# Scientific LLM Evaluator Robustness

Utilities for studying how scientific-paper evaluators respond to rhetorical perturbations while preserving the underlying scientific substance.

## Repository Name

- Project name: `scientific-llm-evaluator-robustness`
- Local folder: `Evaluator_Model`
- Remote repository: not configured yet

## Project Goals

- Sample hard scientific papers from existing evaluation datasets.
- Generate controlled variants of each paper:
  - rhetoric-heavy framing: verbose, grand narrative, overconfident, novelty-emphasizing, and application-oriented
  - plain core framing: direct scientific substance with rhetorical packaging removed
- Run LLM evaluators on original and transformed versions.
- Measure robustness, score shifts, and bias sensitivity across evaluation dimensions.

## Repository Layout

```text
configs/          Experiment configuration files.
data/             Small tracked examples only; large datasets stay outside git.
docs/             Notes, methodology, and experiment writeups.
notebooks/        Exploratory notebooks.
outputs/          Generated experiment outputs, ignored by git.
prompts/          Prompt templates for transformations and evaluation.
scripts/          Command-line entry points.
src/              Reusable Python package code.
tests/            Focused tests for sampling, IO, and validation logic.
```

The previous research artifacts are still available in this workspace but are ignored by git by default. See `docs/repository_map.md` for the separation between legacy folders and the new robustness-evaluation code.

## First Pipeline Target

Generate two controlled variants for 40 randomly sampled records from:

```text
dataset/Hard/hardest_papers.json
```

The pipeline will preserve the original record metadata and add generated text fields for the rhetoric-heavy and plain-core versions.

## Development

```powershell
python -m pip install -e .
python -m pytest
```

## SciStyleBench review debate

The SciStyleBench runner can optionally add a three-step reviewer–critic–reviewer
loop. It first creates the ordinary review, asks an independent critic to question
only score sections whose grounding or calibration is doubtful (including clearly
labeled speculative alternatives), then asks the original reviewer to regenerate
the complete review while treating that feedback as advisory.

```bash
python3 scripts/generate_reviews.py \
  --dataset scistylebench \
  --input-path data/SciStyleBench/variant_items_15class.csv \
  --output-dir outputs/scistylebench/qwen4b_debate \
  --review-prompt-path prompts/review_gen/research_idea_evaluation.txt \
  --debate \
  --critic-prompt-path prompts/review_gen/review_critic.txt
```

Use `--critic-model-name` to use a different critic model and
`--critic-temperature` (default `0.7`) to vary its alternative interpretations.
Debate runs save resumable draft/critic/revision checkpoints and include that
provenance beside the final reviews in `scistylebench_reviews.json`. The final
review remains the one used for the robustness summaries and heatmap.

The final reviewer is instructed to defend its initial assessment against each
feedback item, concede grounded criticism, and justify changed or retained scores.

## Self-refinement baseline

For a same-model, no-critic comparison, use `--self-refine`. It makes one initial
review and then asks that same reviewer model, with the unchanged reviewer system
prompt, to independently recalibrate each score from the idea before comparing its
own prior review. The refinement pass defaults to temperature `0.4`, independently
of the initial-review `--temperature`; override it with `--self-refine-temperature`.
Draft and final scores are saved in `*_self_refinements_checkpoint.jsonl` and the
final JSON under `source_review_self_refinement` / `review_self_refinement`.

To refine already-generated reviews without repeating initial-review calls, add
`--draft-reviews-path` and write to a new output directory:

```bash
python3 scripts/generate_reviews.py --dataset scistylebench \
  --input-path data/SciStyleBench/variant_items_15class.csv \
  --output-dir outputs/scistylebench/qwen35b_self_refine_strict \
  --draft-reviews-path outputs/scistylebench/qwen35b_self_refine/scistylebench_reviews.json \
  --review-prompt-path prompts/review_gen/research_idea_evaluation.txt \
  --self-refine --self-refine-temperature 0.4
```

```bash
python3 scripts/generate_reviews.py --dataset scistylebench \
  --input-path data/SciStyleBench/variant_items_15class.csv \
  --output-dir outputs/scistylebench/self_refinement_test \
  --review-prompt-path prompts/review_gen/research_idea_evaluation.txt \
  --self-refine
```
Debate metadata includes `feedback_responses` (decisions, defenses, justifications)
and `score_comparison` (reviewer scores before/after, critic `recommended_score`
values indexed by feedback item, and original/final justifications for each dimension).
An empty recommendations list means the critic did not question that dimension.
These fields are saved in checkpoints and beside each source/variant review.
Use a fresh output directory for the new behavior: resume skips completed debates
and does not retrofit these fields into old checkpoints.

Debate runs create `debate_heatmaps/README.md` with one PNG heatmap per
source/variant review and the saved critic feedback, reviewer rebuttals, and
before/after justifications. Open the Markdown preview to see the heatmaps and
notes together, or open individual PNG files. Columns show reviewer
before, critic recommendation, reviewer after, and signed score change. Colors
are normalized within each dimension's scale (1–5; overall 1–10); gray N/A cells
are missing/null/invalid scores, not zero. Multiple recommendations remain separate
rows and are never averaged. All saved debates are included without sampling.
Debate mode skips the unrelated robustness figures and source/variant SVG heatmap.
Identical repeated debate records share one image; unchanged images are reused on
reruns through content-based filenames. Distinct reviews remain separate even if
their scores match. Existing images from older runs are not deleted automatically;
use a fresh output directory to avoid mixing old SVGs with the new PNG output.

`mean_score_shift_before_after.png` adds one two-panel summary: mean overall
variant-minus-source rating before/after criticism, and mean reviewer revision
(after minus before). The first uses identical complete source/variant pairs at
both stages; the second counts source reviews once and reports variant revisions
on those same complete pairs. Invalid/missing scores are excluded, not replaced by
zero. Sample sizes are shown. The accompanying JSON includes all dimensions.
These descriptive means do not establish critic bias or causation, and a positive
variant-minus-source shift is not necessarily an upward reviewer revision.

The critic prompt now explicitly audits both inflated and unduly harsh scores,
requires grounded recommendations, and avoids speculative upgrades or forced
directional balance. Testing the revised prompt requires a fresh generation run;
rerendering saved results updates charts only, not reviews or critic feedback.

To visualize an existing run without making any LLM calls (after `pip install -e .`):

```powershell
python -m scientific_llm_evaluator_robustness.debate_visualization --input-path outputs/scistylebench/debate_defense_v1/scistylebench_reviews.json
```

Older checkpoints can still show scores, but cannot show reviewer rebuttals that
were never saved. Missing rebuttals are explicitly labeled.

## SBI, SRR, and AWR

Every SciStyleBench generation run now writes these files in its output directory:

- `scientific_robustness_metrics.json`: formulas, effective mappings, eligible and
  excluded counts, per-source score observations, and results by style/pair/dimension.
- `scientific_robustness_metrics.md`: final and matched before/after evaluation tables.
- `scientific_robustness_metrics.png`: one three-panel metric comparison, PNG only.

The chart compares matched draft/final observations when debate metadata is present;
otherwise it shows final-only results. The JSON and Markdown additionally retain
final-only coverage, even if some drafts are unavailable. These metrics evaluate
one saved model/run at a time; do not pool different model runs into the same input.

### Definitions and interpretation

- **SBI per style p:** the provisional default is
  `mean(abs(score_p - score_plain) - abs(score_paraphrase - score_plain))`.
  It averages eligible source/dimension observations over the seven 1–5 dimensions;
  the aggregate chart pools eligible styles too. Per-style SBI is saved separately.
  Overall-rating SBI (1–10 points) is reported separately, never mixed into that mean.
  Lower values mean less deviation relative to the rewriting control. Negative SBI
  means less deviation than Paraphrase, not proof of perfect absolute stability.
- The pasted SBI equation was ambiguous about absolute-value bars. Set
  `"sbi_formula": "signed"` to reproduce the literal signed expression
  `mean((score_p - score_plain) - (score_paraphrase - score_plain))`, which simplifies
  to `mean(score_p - score_paraphrase)` and can cancel opposing biases. The selected
  formula is saved and displayed; no clipping to zero is applied.
- **SRR:** fraction of correctly ordered pairs, using `Enriched > Plain`,
  `Plain > Hollow`, and `Plain > Flawed` within the same source idea.
- **AWR:** fraction of configured pairs where the high-substance/plain item scores
  strictly above the low-substance/persuasive item. Higher is better, as in the
  requested definition (this is not an attack-success rate).
- Primary SRR/AWR values and the chart use overall rating. Per-dimension rates and
  pooled seven-dimension diagnostics are also saved. Ties count as failures, not
  half-wins. Missing, non-finite, boolean, and out-of-range scores are excluded,
  never counted as zeros or failed comparisons. Empty denominators produce N/A.
- Comparisons never cross source ideas. Plain must be an explicit variant; the
  original source review is not substituted. Identical duplicates are deduplicated;
  conflicting duplicates raise an error rather than arbitrarily choosing a review.
- Sample counts are observation counts, not independent sample sizes. These are
  descriptive metrics without confidence intervals or causal claims.

### Configure the actual benchmark labels

Pass `--metrics-config configs/scientific_metrics.example.json` to
`scripts/generate_reviews.py` after editing the example to match your dataset.
Label matching ignores case and surrounding spaces but does not guess aliases.
The supplied example uses Plain, Paraphrase, Enriched, Hollow, and Flawed; it leaves
`style_variants` and `adversarial_pairs` empty because dataset-specific mappings
must not be invented.

`style_variants` lists substance-preserving presentation variants. If empty, only
records explicitly marked `variant_group=style` and
`expected_quality_direction=same` are discovered automatically, excluding controls.
`adversarial_pairs` must explicitly list `[high_substance_plain_label,
low_substance_persuasive_label]` pairs verified from benchmark design. For example,
`[["Plain", "Hollow persuasive"]]` is valid **only if those labels exist and really
have those semantics**. No adversarial pairs are inferred from scores or names.
Unconfigured/missing metrics appear as N/A with coverage warnings and observed labels.

Use all required variants per source. A small `--limit` can omit controls and make
metrics unavailable. To evaluate existing saved reviews without further LLM calls:

```powershell
python -m scientific_llm_evaluator_robustness.scientific_metrics --input-path outputs/scistylebench/qwen35_balanced_debate_v2/scistylebench_reviews.json --metrics-config configs/scientific_metrics.example.json
```

This writes the three scientific-metric files only; it does not regenerate reviews
or duplicate the individual debate heatmaps.
