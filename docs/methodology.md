# Methodology

This project measures whether LLM-based scientific evaluators are robust to rhetoric-only transformations of paper text.

## Variant Families

- Original: source paper text.
- Rhetoric-heavy: same scientific substance with stronger rhetorical framing.
- Plain core: same scientific substance with rhetorical packaging removed.

## Preservation Principle

The transformations must not change scientific substance: methods, datasets, numbers, baselines, claims, limitations, citations, equations, and conclusions should remain intact.

## Initial Experiment

1. Randomly sample 40 records from `dataset/Hard/hardest_papers.json`.
2. Generate the two variants using DeepSeek V3.
3. Run the same evaluator on all versions.
4. Compare changes in soundness, presentation, contribution, rating, and decision.

