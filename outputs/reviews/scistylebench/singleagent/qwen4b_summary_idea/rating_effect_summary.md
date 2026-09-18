# SciStyleBench Rating Robustness Summary

- Sources: 10
- Variants: 150
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 150 | 5.0000 | 5.4600 | 0.4600 | 0.5267 | 47.3% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 30 | 0.2333 | 0.3000 | 76.7% |
| B_rhetoric_and_framing | 50 | 0.3000 | 0.4600 | 60.0% |
| C_substance_and_logic | 30 | 0.4000 | 0.4000 | 20.0% |
| H_hybrid_mixed_perturbations | 40 | 0.8750 | 0.8750 | 30.0% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 10 | 0.0000 | 0.0000 | 100.0% |
| A2_Paraphrase_Only | 10 | 0.3000 | 0.3000 | 70.0% |
| A3_Plain_Core | 10 | 0.4000 | 0.6000 | 60.0% |
| B1_Verbose_Elaborate | 10 | 0.2000 | 0.6000 | 50.0% |
| B2_Grand_Narrative | 10 | 0.5000 | 0.5000 | 60.0% |
| B3_Over_Confident | 10 | 0.1000 | 0.3000 | 70.0% |
| B4_Novelty | 10 | 0.4000 | 0.6000 | 50.0% |
| B5_Application_Impact | 10 | 0.3000 | 0.3000 | 70.0% |
| C1_Hollow_Shell | 10 | 0.0000 | 0.0000 | 0.0% |
| C2_Logic_Flawed | 10 | 0.4000 | 0.4000 | 0.0% |
| C3_Substance_Enriched | 10 | 0.8000 | 0.8000 | 60.0% |
| H1_Deceptive_Hollow | 10 | 0.8000 | 0.8000 | 0.0% |
| H2_Confident_Flaw | 10 | 0.6000 | 0.6000 | 0.0% |
| H3_Verbose_Enriched | 10 | 1.3000 | 1.3000 | 100.0% |
| H4_Ultimate_Hype | 10 | 0.8000 | 0.8000 | 20.0% |
