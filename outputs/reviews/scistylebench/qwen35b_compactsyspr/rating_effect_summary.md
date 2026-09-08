# SciStyleBench Rating Robustness Summary

- Sources: 18
- Variants: 198
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 198 | 6.1111 | 5.9949 | -0.1162 | 0.8434 | 55.6% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 54 | 0.0556 | 0.5370 | 64.8% |
| B_rhetoric_and_framing | 90 | 0.0333 | 0.7444 | 51.1% |
| C_substance_and_logic | 54 | -0.5370 | 1.3148 | 53.7% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 18 | 0.1667 | 0.2778 | 72.2% |
| A2_Paraphrase_Only | 18 | 0.1667 | 0.7222 | 55.6% |
| A3_Plain_Core | 18 | -0.1667 | 0.6111 | 66.7% |
| B1_Verbose_Elaborate | 18 | 0.2222 | 0.5556 | 66.7% |
| B2_Grand_Narrative | 18 | -0.0556 | 0.7222 | 38.9% |
| B3_Over_Confident | 18 | -0.2778 | 0.9444 | 44.4% |
| B4_Novelty | 18 | 0.2222 | 0.7778 | 50.0% |
| B5_Application_Impact | 18 | 0.0556 | 0.7222 | 55.6% |
| C1_Hollow_Shell | 18 | -2.4444 | 2.5556 | 94.4% |
| C2_Logic_Flawed | 18 | 0.1111 | 0.5556 | 16.7% |
| C3_Substance_Enriched | 18 | 0.7222 | 0.8333 | 50.0% |
