# SciStyleBench Rating Robustness Summary

- Sources: 37
- Variants: 400
- Rating threshold for 'same': 0.25

## Overall

| n | Mean source rating | Mean variant rating | Mean shift | Mean abs shift | Direction accuracy |
|---:|---:|---:|---:|---:|---:|
| 400 | 6.6050 | 6.6725 | 0.0675 | 0.3075 | 63.2% |

## By Variant Group

| Variant group | n | Mean shift | Mean abs shift | Direction accuracy |
|---|---:|---:|---:|---:|
| A_baseline_expression_control | 111 | 0.0360 | 0.2342 | 78.4% |
| B_rhetoric_and_framing | 181 | 0.1271 | 0.2818 | 72.9% |
| C_substance_and_logic | 108 | 0.0000 | 0.4259 | 31.5% |

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
