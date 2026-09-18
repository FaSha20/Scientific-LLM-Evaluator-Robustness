# SciStyleBench Rating Robustness Summary

- Sources: 37
- Variants: 555
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 555 | 4.4595 | 4.4054 | -0.0541 | 0.8577 | 58.7% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 111 | -0.0450 | 0.5315 | 51.4% |
| B_rhetoric_and_framing | 185 | -0.0378 | 0.5243 | 54.6% |
| C_substance_and_logic | 111 | 0.1351 | 1.1261 | 57.7% |
| H_hybrid_mixed_perturbations | 148 | -0.2230 | 1.3176 | 70.3% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 37 | 0.0811 | 0.2432 | 78.4% |
| A2_Paraphrase_Only | 37 | -0.2432 | 0.6757 | 40.5% |
| A3_Plain_Core | 37 | 0.0270 | 0.6757 | 35.1% |
| B1_Verbose_Elaborate | 37 | -0.0541 | 0.5405 | 54.1% |
| B2_Grand_Narrative | 37 | -0.1081 | 0.4324 | 62.2% |
| B3_Over_Confident | 37 | -0.0270 | 0.6216 | 45.9% |
| B4_Novelty | 37 | 0.0811 | 0.4595 | 59.5% |
| B5_Application_Impact | 37 | -0.0811 | 0.5676 | 51.4% |
| C1_Hollow_Shell | 37 | -1.2703 | 1.3243 | 81.1% |
| C2_Logic_Flawed | 37 | 0.1892 | 0.5135 | 13.5% |
| C3_Substance_Enriched | 37 | 1.4865 | 1.5405 | 78.4% |
| H1_Deceptive_Hollow | 37 | -1.8108 | 1.8108 | 94.6% |
| H2_Confident_Flaw | 37 | -0.7027 | 0.7568 | 54.1% |
| H3_Verbose_Enriched | 37 | 2.0270 | 2.0270 | 86.5% |
| H4_Ultimate_Hype | 37 | -0.4054 | 0.6757 | 45.9% |
