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
