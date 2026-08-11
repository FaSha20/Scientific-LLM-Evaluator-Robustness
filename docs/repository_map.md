# Repository Map

This workspace now contains two kinds of material:

1. The clean robustness-evaluation repository structure.
2. Previous research artifacts that remain useful as inputs or references, but should not be committed by default.

## Current Repo Identity

- Project name: `scientific-llm-evaluator-robustness`
- Python package: `scientific_llm_evaluator_robustness`
- Local folder name: `Evaluator_Model`
- Git remote: none configured yet

## Robustness-Evaluation Structure

These are the folders/files intended for the new repo:

```text
configs/
data/
docs/
notebooks/
prompts/
scripts/
src/
tests/
.env.example
.gitignore
pyproject.toml
README.md
```

Their roles:

- `configs/`: experiment settings, such as sample size, seed, model name, and input/output paths.
- `prompts/`: controlled prompts for rhetoric-heavy and plain-core transformations.
- `src/`: reusable Python code for sampling, IO, LLM calls, validation, and pipelines.
- `scripts/`: runnable command-line scripts.
- `tests/`: focused checks for reusable code.
- `docs/`: methodology and project notes.
- `data/`: tiny tracked examples only.
- `notebooks/`: exploratory notebooks after logic has been moved into `src/`.

## Previous Workspace Artifacts

These existed before the repo skeleton and are ignored by git by default:

```text
dataset/
Model_outputs/
group_accuracy_bias_checking/
clustering/
Qwen/
*.csv
alaki2.json
گزارش_کار_پروژه.md
```

Recommended use:

- `dataset/`: keep as the source data location for now, especially `dataset/Hard/hardest_papers.json`.
- `Model_outputs/`: previous model outputs; useful for comparison, but too large/noisy for normal commits.
- `group_accuracy_bias_checking/`: previous analysis outputs and plots.
- `clustering/`: previous clustering/category artifacts.
- `Qwen/`: previous notebook and prompt experiments. The reusable pieces should gradually move into `src/` and `prompts/`.
- CSV/JSON/report files at the root: previous summary artifacts; keep as references unless they are intentionally cleaned or migrated.

## What Is Needed For The Robustness Evaluation

Minimum needed:

```text
configs/rhetoric_variants.yaml
prompts/rhetoric_heavy.md
prompts/plain_core.md
src/scientific_llm_evaluator_robustness/
scripts/generate_rhetoric_variants.py
dataset/Hard/hardest_papers.json
```

Optional but useful:

```text
docs/methodology.md
tests/
.env.example
```

The dataset is intentionally not tracked in git yet. The code points to the existing local dataset path through config/script defaults.
