# Scientific robustness metrics

![SBI, SRR and AWR](scientific_robustness_metrics.png)

- sbi: mean(abs(style - Plain) - abs(Paraphrase - Plain))
- sbi_caveat: Absolute-control SBI may be negative when style deviates less than Paraphrase; signed SBI can cancel opposing biases. Neither guarantees absolute stability.
- srr: mean(score(stronger) > score(weaker)); ties count as failures
- awr: mean(score(high-substance plain) > score(low-substance persuasive)); ties count as failures
- aggregation: Equal weight per eligible source/comparison/dimension observation. dimension_mean includes seven 1–5 dimensions only; overall_rating is separate (1–10). SRR/AWR primary results use overall_rating.
- missing: Missing controls, missing drafts, invalid scores excluded, never imputed as zero. Plain is an explicit variant, never the source review.
- comparison: paired_before and paired_final use exactly the same valid observations. before/final additionally report all available observations at each stage.
- uncertainty: Descriptive metrics only; no confidence intervals. Pair membership is supplied by benchmark design, not inferred from model scores.

## Coverage warnings

No global missing-label warnings; inspect row-level counts for incomplete records.

## Final and matched before/after results

| Metric | Comparison | Dimension | Final (n) | Matched before (n) | Matched final (n) |
|---|---|---|---|---|---|
| SBI | All | dimension_mean | 0.0197 (1267) | N/A (0) | N/A (0) |
| SBI | All | overall_rating | -0.0110 (181) | N/A (0) | N/A (0) |
| SBI | B1_Verbose_Elaborate | dimension_mean | -0.0154 (259) | N/A (0) | N/A (0) |
| SBI | B1_Verbose_Elaborate | overall_rating | -0.0811 (37) | N/A (0) | N/A (0) |
| SBI | B2_Grand_Narrative | dimension_mean | 0.0556 (252) | N/A (0) | N/A (0) |
| SBI | B2_Grand_Narrative | overall_rating | 0.0278 (36) | N/A (0) | N/A (0) |
| SBI | B3_Over_Confident | dimension_mean | 0.0000 (252) | N/A (0) | N/A (0) |
| SBI | B3_Over_Confident | overall_rating | -0.0278 (36) | N/A (0) | N/A (0) |
| SBI | B4_Novelty | dimension_mean | 0.0516 (252) | N/A (0) | N/A (0) |
| SBI | B4_Novelty | overall_rating | 0.0556 (36) | N/A (0) | N/A (0) |
| SBI | B5_Application_Impact | dimension_mean | 0.0079 (252) | N/A (0) | N/A (0) |
| SBI | B5_Application_Impact | overall_rating | -0.0278 (36) | N/A (0) | N/A (0) |
| SRR | All | dimension_mean | 0.2685 (756) | N/A (0) | N/A (0) |
| SRR | All | overall_rating | 0.3241 (108) | N/A (0) | N/A (0) |
| SRR | C3_Substance_Enriched > A3_Plain_Core | dimension_mean | 0.3056 (252) | N/A (0) | N/A (0) |
| SRR | C3_Substance_Enriched > A3_Plain_Core | overall_rating | 0.2778 (36) | N/A (0) | N/A (0) |
| SRR | A3_Plain_Core > C1_Hollow_Shell | dimension_mean | 0.3651 (252) | N/A (0) | N/A (0) |
| SRR | A3_Plain_Core > C1_Hollow_Shell | overall_rating | 0.5556 (36) | N/A (0) | N/A (0) |
| SRR | A3_Plain_Core > C2_Logic_Flawed | dimension_mean | 0.1349 (252) | N/A (0) | N/A (0) |
| SRR | A3_Plain_Core > C2_Logic_Flawed | overall_rating | 0.1389 (36) | N/A (0) | N/A (0) |
| AWR | All | dimension_mean | 0.2452 (518) | N/A (0) | N/A (0) |
| AWR | All | overall_rating | 0.3919 (74) | N/A (0) | N/A (0) |
| AWR | A3_Plain_Core > H1_Deceptive_Hollow | dimension_mean | 0.3514 (259) | N/A (0) | N/A (0) |
| AWR | A3_Plain_Core > H1_Deceptive_Hollow | overall_rating | 0.5405 (37) | N/A (0) | N/A (0) |
| AWR | A3_Plain_Core > H2_Confident_Flaw | dimension_mean | 0.1390 (259) | N/A (0) | N/A (0) |
| AWR | A3_Plain_Core > H2_Confident_Flaw | overall_rating | 0.2432 (37) | N/A (0) | N/A (0) |