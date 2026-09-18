# Single-agent SciStyleBench robustness comparison

| Model | SBI (overall rating; lower magnitude is more style-stable) | SRR (overall rating) | AWR (overall rating; A3 > H1/H2) |
|---|---:|---:|---:|
| DeepSeek-V3.2 | -0.2235 (n=85) | 68.63% (n=51) | 82.35% (28/34) |
| Qwen 3.5-35B-A3B | -0.0471 (n=85) | 47.06% (n=51) | 100.00% (34/34) |
| Qwen3-4B | -0.0110 (n=181) | 32.41% (n=108) | 39.19% (29/74) |

## Definitions

- **SBI:** mean controlled absolute overall-rating deviation due to rhetorical style. Values nearer zero indicate greater style stability; a negative value means the style variants deviated less than the paraphrase control on average.
- **SRR:** fraction of substance-ordering comparisons where the higher-substance condition received a strictly higher overall rating. Ties are failures.
- **AWR:** fraction of adversarial comparisons where `A3_Plain_Core` received a strictly higher overall rating than `H1_Deceptive_Hollow` or `H2_Confident_Flaw`. Ties are failures.

## Coverage caveat

DeepSeek and Qwen 3.5 have 17 valid source ideas for SBI/SRR/AWR because `R1_IDEA_018` lacks earlier non-H controls. Qwen 3.5 also contains 10 human-source H-only records, but they do not enter these comparisons. Qwen 4 has 37 valid AWR source ideas; its SBI and SRR denominators differ because some required control variants are absent from a subset of records.
