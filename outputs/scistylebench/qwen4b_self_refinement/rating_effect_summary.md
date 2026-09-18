# SciStyleBench Rating Robustness Summary

- Sources: 37
- Variants: 555
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 555 | 6.5946 | 6.7099 | 0.1153 | 0.3928 | 60.5% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 111 | 0.0541 | 0.2342 | 78.4% |
| B_rhetoric_and_framing | 185 | 0.1405 | 0.2919 | 71.9% |
| C_substance_and_logic | 111 | 0.0270 | 0.4595 | 32.4% |
| H_hybrid_mixed_perturbations | 148 | 0.1959 | 0.5878 | 54.1% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 37 | 0.0270 | 0.1351 | 89.2% |
| A2_Paraphrase_Only | 37 | -0.0270 | 0.3514 | 67.6% |
| A3_Plain_Core | 37 | 0.1622 | 0.2162 | 78.4% |
| B1_Verbose_Elaborate | 37 | 0.1622 | 0.2703 | 75.7% |
| B2_Grand_Narrative | 37 | 0.0541 | 0.3784 | 64.9% |
| B3_Over_Confident | 37 | 0.1892 | 0.2432 | 75.7% |
| B4_Novelty | 37 | 0.1622 | 0.2703 | 73.0% |
| B5_Application_Impact | 37 | 0.1351 | 0.2973 | 70.3% |
| C1_Hollow_Shell | 37 | -0.4865 | 0.5946 | 48.6% |
| C2_Logic_Flawed | 37 | 0.1081 | 0.3243 | 10.8% |
| C3_Substance_Enriched | 37 | 0.4595 | 0.4595 | 37.8% |
| H1_Deceptive_Hollow | 37 | -0.4054 | 0.5676 | 45.9% |
| H2_Confident_Flaw | 37 | 0.0000 | 0.4865 | 24.3% |
| H3_Verbose_Enriched | 37 | 0.9459 | 0.9459 | 75.7% |
| H4_Ultimate_Hype | 37 | 0.2432 | 0.3514 | 70.3% |
