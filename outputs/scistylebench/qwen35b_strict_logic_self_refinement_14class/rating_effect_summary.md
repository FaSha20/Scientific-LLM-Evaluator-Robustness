# SciStyleBench Rating Robustness Summary

- Sources: 16
- Variants: 240
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 240 | 6.6875 | 5.8875 | -0.8000 | 1.1083 | 59.2% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 48 | -0.2917 | 0.4583 | 62.5% |
| B_rhetoric_and_framing | 80 | -0.2000 | 0.5500 | 53.8% |
| C_substance_and_logic | 48 | -0.7917 | 1.2083 | 47.9% |
| H_hybrid_mixed_perturbations | 64 | -1.9375 | 2.2188 | 71.9% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 16 | -0.0625 | 0.1875 | 81.2% |
| A2_Paraphrase_Only | 16 | -0.1875 | 0.3125 | 68.8% |
| A3_Plain_Core | 16 | -0.6250 | 0.8750 | 37.5% |
| B1_Verbose_Elaborate | 16 | 0.1875 | 0.4375 | 56.2% |
| B2_Grand_Narrative | 16 | -0.4375 | 0.8125 | 25.0% |
| B3_Over_Confident | 16 | -0.4375 | 0.5625 | 62.5% |
| B4_Novelty | 16 | 0.0000 | 0.2500 | 75.0% |
| B5_Application_Impact | 16 | -0.3125 | 0.6875 | 50.0% |
| C1_Hollow_Shell | 16 | -2.7500 | 2.7500 | 93.8% |
| C2_Logic_Flawed | 16 | 0.0000 | 0.3750 | 12.5% |
| C3_Substance_Enriched | 16 | 0.3750 | 0.5000 | 37.5% |
| H1_Deceptive_Hollow | 16 | -4.1250 | 4.1250 | 100.0% |
| H2_Confident_Flaw | 16 | -3.1875 | 3.1875 | 100.0% |
| H3_Verbose_Enriched | 16 | 0.4375 | 0.6875 | 50.0% |
| H4_Ultimate_Hype | 16 | -0.8750 | 0.8750 | 37.5% |
