# SciStyleBench Rating Robustness Summary

- Sources: 47
- Variants: 595
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 595 | 6.3076 | 5.8151 | -0.4924 | 1.1815 | 58.7% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 111 | -0.0180 | 0.5045 | 59.5% |
| B_rhetoric_and_framing | 185 | -0.0757 | 0.6270 | 48.6% |
| C_substance_and_logic | 111 | -0.3784 | 1.3874 | 54.1% |
| H_hybrid_mixed_perturbations | 188 | -1.2500 | 2.0053 | 70.7% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 37 | -0.0541 | 0.2162 | 83.8% |
| A2_Paraphrase_Only | 37 | 0.1081 | 0.6486 | 48.6% |
| A3_Plain_Core | 37 | -0.1081 | 0.6486 | 45.9% |
| B1_Verbose_Elaborate | 37 | 0.0270 | 0.5135 | 59.5% |
| B2_Grand_Narrative | 37 | -0.1081 | 0.6486 | 45.9% |
| B3_Over_Confident | 37 | -0.1892 | 0.6757 | 45.9% |
| B4_Novelty | 37 | 0.2973 | 0.6216 | 45.9% |
| B5_Application_Impact | 37 | -0.4054 | 0.6757 | 45.9% |
| C1_Hollow_Shell | 37 | -2.4324 | 2.4324 | 91.9% |
| C2_Logic_Flawed | 37 | 0.4054 | 0.7297 | 16.2% |
| C3_Substance_Enriched | 37 | 0.8919 | 1.0000 | 54.1% |
| H1_Deceptive_Hollow | 47 | -3.4468 | 3.4468 | 97.9% |
| H2_Confident_Flaw | 47 | -1.9362 | 1.9787 | 89.4% |
| H3_Verbose_Enriched | 47 | 1.3617 | 1.4043 | 72.3% |
| H4_Ultimate_Hype | 47 | -0.9787 | 1.1915 | 23.4% |
