# SciStyleBench Rating Robustness Summary

- Sources: 37
- Variants: 555
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 555 | 3.7568 | 4.0162 | 0.2595 | 1.0703 | 49.9% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 111 | 0.2342 | 0.7568 | 41.4% |
| B_rhetoric_and_framing | 185 | 0.2324 | 0.8595 | 37.8% |
| C_substance_and_logic | 111 | 0.3784 | 1.2793 | 55.9% |
| H_hybrid_mixed_perturbations | 148 | 0.2230 | 1.4122 | 66.9% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 37 | 0.2162 | 0.5405 | 59.5% |
| A2_Paraphrase_Only | 37 | 0.1081 | 0.8649 | 35.1% |
| A3_Plain_Core | 37 | 0.3784 | 0.8649 | 29.7% |
| B1_Verbose_Elaborate | 37 | 0.2432 | 0.9459 | 32.4% |
| B2_Grand_Narrative | 37 | 0.1351 | 0.7297 | 48.6% |
| B3_Over_Confident | 37 | 0.0541 | 0.8108 | 37.8% |
| B4_Novelty | 37 | 0.4054 | 0.8919 | 35.1% |
| B5_Application_Impact | 37 | 0.3243 | 0.9189 | 35.1% |
| C1_Hollow_Shell | 37 | -0.8919 | 1.1081 | 59.5% |
| C2_Logic_Flawed | 37 | 0.2432 | 0.8919 | 29.7% |
| C3_Substance_Enriched | 37 | 1.7838 | 1.8378 | 78.4% |
| H1_Deceptive_Hollow | 37 | -1.2162 | 1.2162 | 75.7% |
| H2_Confident_Flaw | 37 | -0.5676 | 1.0000 | 56.8% |
| H3_Verbose_Enriched | 37 | 2.6486 | 2.6486 | 94.6% |
| H4_Ultimate_Hype | 37 | 0.0270 | 0.7838 | 40.5% |
