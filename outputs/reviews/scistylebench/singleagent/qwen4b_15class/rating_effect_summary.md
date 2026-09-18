# SciStyleBench Rating Robustness Summary

- Sources: 37
- Variants: 548
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 548 | 6.6022 | 6.7007 | 0.0985 | 0.3796 | 60.6% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 111 | 0.0360 | 0.2342 | 78.4% |
| B_rhetoric_and_framing | 181 | 0.1271 | 0.2818 | 72.9% |
| C_substance_and_logic | 108 | 0.0000 | 0.4259 | 31.5% |
| H_hybrid_mixed_perturbations | 148 | 0.1824 | 0.5743 | 53.4% |

## By Variant

| Variant | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A1_Identity | 37 | 0.0000 | 0.1081 | 91.9% |
| A2_Paraphrase_Only | 37 | -0.0270 | 0.3514 | 67.6% |
| A3_Plain_Core | 37 | 0.1351 | 0.2432 | 75.7% |
| B1_Verbose_Elaborate | 37 | 0.1622 | 0.2703 | 75.7% |
| B2_Grand_Narrative | 36 | 0.0556 | 0.3889 | 63.9% |
| B3_Over_Confident | 36 | 0.1667 | 0.2222 | 77.8% |
| B4_Novelty | 36 | 0.1389 | 0.2500 | 75.0% |
| B5_Application_Impact | 36 | 0.1111 | 0.2778 | 72.2% |
| C1_Hollow_Shell | 36 | -0.4722 | 0.5833 | 47.2% |
| C2_Logic_Flawed | 36 | 0.0833 | 0.3056 | 11.1% |
| C3_Substance_Enriched | 36 | 0.3889 | 0.3889 | 36.1% |
| H1_Deceptive_Hollow | 37 | -0.4054 | 0.5676 | 45.9% |
| H2_Confident_Flaw | 37 | 0.0000 | 0.4865 | 24.3% |
| H3_Verbose_Enriched | 37 | 0.8919 | 0.8919 | 73.0% |
| H4_Ultimate_Hype | 37 | 0.2432 | 0.3514 | 70.3% |
