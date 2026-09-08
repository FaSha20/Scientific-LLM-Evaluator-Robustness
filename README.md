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
