# Robustness of LLM Reviews to Style Variants

## Executive Summary

- **Scope:** 56 generated reviews across 14 papers and 4 review conditions: `main` plus 3 style variants, using `outputs\reviews\full_paper_variant_reviews_more\variant_reviews.json`.
- **Overall robustness index:** 0.930 on a 0-1 scale, where higher means smaller rating, score, and decision drift from the main version.
- **Average absolute rating shift:** 0.397 rating points versus the main full-paper review.
- **Average decision flip rate:** 9.5% across variants.
- **Least robust condition:** `plain_core` had the lowest robustness index.

## Metric Definitions

- **Rating shift:** variant overall rating minus main overall rating for the same paper.
- **Mean absolute rating shift:** average absolute rating movement on the 1-10 review scale.
- **Decision flip rate:** share of papers where the inferred accept/reject decision changes relative to main.
- **Score-dimension drift:** average absolute movement in soundness, presentation, and contribution scores.
- **Robustness index:** average of rating stability, score stability, and decision stability. Rating stability normalizes by the 1-10 range; score stability normalizes by the 1-5 range.

## Variant-Level Results

| Variant | n | Mean rating shift | Mean abs rating shift | Decision flip rate | Score drift | Robustness index |
|---|---:|---:|---:|---:|---:|---:|
| plain_core | 14 | -0.286 | 0.429 | 14.3% | 0.190 | 0.921 |
| rhetoric_heavy | 14 | -0.143 | 0.429 | 7.1% | 0.286 | 0.937 |
| rhetoric_heavier | 14 | 0.000 | 0.333 | 7.1% | 0.361 | 0.934 |

## Visual Outputs

- `figures/mean_absolute_rating_shift.svg`: rating drift magnitude by variant.
- `figures/decision_flip_rate.svg`: accept/reject instability by variant.
- `figures/robustness_index.svg`: combined robustness score by variant.
- `figures/paper_rating_shift_heatmap.svg`: per-paper rating shifts.

## Caveats

- The decision is inferred from `overall_rating >= 6` when the review output does not include an explicit decision.
- The report measures robustness of the reviewer model to style variants, not scientific correctness of the variants themselves.
- Small sample sizes should be interpreted as diagnostic evidence rather than final statistical proof.

## Output Inventory

- Data JSON: `outputs\reports\robustness_full_paper_reviews_more\data`
- Tables CSV: `outputs\reports\robustness_full_paper_reviews_more\tables`
- Figures SVG: `outputs\reports\robustness_full_paper_reviews_more\figures`
- Text report: `outputs\reports\robustness_full_paper_reviews_more\text\robustness_report.md`

_Generated at 2026-08-18 23:30._