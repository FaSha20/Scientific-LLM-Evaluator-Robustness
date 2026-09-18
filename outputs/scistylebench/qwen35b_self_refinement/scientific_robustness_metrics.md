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
| SBI | All | dimension_mean | 0.0303 (595) | 0.0437 (595) | 0.0303 (595) |
| SBI | All | overall_rating | 0.0941 (85) | -0.0471 (85) | 0.0941 (85) |
| SBI | B1_Verbose_Elaborate | dimension_mean | 0.0000 (119) | 0.0504 (119) | 0.0000 (119) |
| SBI | B1_Verbose_Elaborate | overall_rating | -0.0588 (17) | -0.1176 (17) | -0.0588 (17) |
| SBI | B2_Grand_Narrative | dimension_mean | 0.1597 (119) | 0.0756 (119) | 0.1597 (119) |
| SBI | B2_Grand_Narrative | overall_rating | 0.4118 (17) | 0.1765 (17) | 0.4118 (17) |
| SBI | B3_Over_Confident | dimension_mean | -0.0336 (119) | 0.0336 (119) | -0.0336 (119) |
| SBI | B3_Over_Confident | overall_rating | -0.0588 (17) | -0.0588 (17) | -0.0588 (17) |
| SBI | B4_Novelty | dimension_mean | -0.0084 (119) | 0.0168 (119) | -0.0084 (119) |
| SBI | B4_Novelty | overall_rating | 0.0588 (17) | 0.0000 (17) | 0.0588 (17) |
| SBI | B5_Application_Impact | dimension_mean | 0.0336 (119) | 0.0420 (119) | 0.0336 (119) |
| SBI | B5_Application_Impact | overall_rating | 0.1176 (17) | -0.2353 (17) | 0.1176 (17) |
| SRR | All | dimension_mean | 0.3810 (357) | 0.3417 (357) | 0.3810 (357) |
| SRR | All | overall_rating | 0.5686 (51) | 0.4706 (51) | 0.5686 (51) |
| SRR | C3_Substance_Enriched > A3_Plain_Core | dimension_mean | 0.3697 (119) | 0.3697 (119) | 0.3697 (119) |
| SRR | C3_Substance_Enriched > A3_Plain_Core | overall_rating | 0.4706 (17) | 0.5294 (17) | 0.4706 (17) |
| SRR | A3_Plain_Core > C1_Hollow_Shell | dimension_mean | 0.6134 (119) | 0.6050 (119) | 0.6134 (119) |
| SRR | A3_Plain_Core > C1_Hollow_Shell | overall_rating | 0.8824 (17) | 0.8824 (17) | 0.8824 (17) |
| SRR | A3_Plain_Core > C2_Logic_Flawed | dimension_mean | 0.1597 (119) | 0.0504 (119) | 0.1597 (119) |
| SRR | A3_Plain_Core > C2_Logic_Flawed | overall_rating | 0.3529 (17) | 0.0000 (17) | 0.3529 (17) |
| AWR | All | dimension_mean | 0.7563 (238) | 0.7185 (238) | 0.7563 (238) |
| AWR | All | overall_rating | 1.0000 (34) | 1.0000 (34) | 1.0000 (34) |
| AWR | A3_Plain_Core > H1_Deceptive_Hollow | dimension_mean | 0.8655 (119) | 0.8739 (119) | 0.8655 (119) |
| AWR | A3_Plain_Core > H1_Deceptive_Hollow | overall_rating | 1.0000 (17) | 1.0000 (17) | 1.0000 (17) |
| AWR | A3_Plain_Core > H2_Confident_Flaw | dimension_mean | 0.6471 (119) | 0.5630 (119) | 0.6471 (119) |
| AWR | A3_Plain_Core > H2_Confident_Flaw | overall_rating | 1.0000 (17) | 1.0000 (17) | 1.0000 (17) |