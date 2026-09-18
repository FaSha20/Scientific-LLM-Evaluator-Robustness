# SciStyleBench Rating Robustness Summary

- Sources: 17
- Variants: 255
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 255 | 6.5294 | 5.8706 | -0.6588 | 1.2549 | 52.2% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 51 | -0.0196 | 0.6078 | 47.1% |
| B_rhetoric_and_framing | 85 | -0.0824 | 0.7647 | 36.5% |
| C_substance_and_logic | 51 | -0.7843 | 1.4510 | 56.9% |
| H_hybrid_mixed_perturbations | 68 | -1.7647 | 2.2059 | 72.1% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 17 | -0.1176 | 0.5882 | 52.9% |
| A2_Paraphrase_Only | 17 | 0.0588 | 0.6471 | 41.2% |
| A3_Plain_Core | 17 | 0.0000 | 0.5882 | 47.1% |
| B1_Verbose_Elaborate | 17 | 0.2353 | 0.7059 | 41.2% |
| B2_Grand_Narrative | 17 | -0.4706 | 0.8235 | 35.3% |
| B3_Over_Confident | 17 | -0.2353 | 0.8235 | 29.4% |
| B4_Novelty | 17 | 0.3529 | 0.7059 | 41.2% |
| B5_Application_Impact | 17 | -0.2941 | 0.7647 | 35.3% |
| C1_Hollow_Shell | 17 | -2.8235 | 2.8235 | 94.1% |
| C2_Logic_Flawed | 17 | -0.1176 | 0.7059 | 23.5% |
| C3_Substance_Enriched | 17 | 0.5882 | 0.8235 | 52.9% |
| H1_Deceptive_Hollow | 17 | -4.0000 | 4.0000 | 100.0% |
| H2_Confident_Flaw | 17 | -2.5882 | 2.5882 | 100.0% |
| H3_Verbose_Enriched | 17 | 0.7647 | 0.8824 | 64.7% |
| H4_Ultimate_Hype | 17 | -1.2353 | 1.3529 | 23.5% |
