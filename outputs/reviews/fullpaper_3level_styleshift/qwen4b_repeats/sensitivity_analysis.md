# Review Sensitivity Analysis

- Runs: 10
- Run labels: run_001, run_002, run_003, run_004, run_005, run_006, run_007, run_008, run_009, run_010

This report tests whether signed review shifts under rhetoric variants are larger than ordinary run-to-run randomness.

## plain_core

| Metric | Mean shift | Mean abs shift | Exact sign-flip p | Mean within-delta std | Signal/noise |
|---|---:|---:|---:|---:|---:|
| rating | 0.0214 | 0.2929 | 0.808594 | 0.4558 | 0.0470 |
| soundness | -0.0357 | 0.0357 | 0.500000 | 0.1129 | 0.3162 |
| presentation | 0.0500 | 0.1071 | 0.281250 | 0.2482 | 0.2014 |
| contribution | -0.0786 | 0.1786 | 0.390625 | 0.3524 | 0.2230 |

- Mean decision flip rate: 0.0%
- Mean main decision instability across runs: 0.0%
- Mean variant decision instability across runs: 0.0%

## rhetoric_heavy

| Metric | Mean shift | Mean abs shift | Exact sign-flip p | Mean within-delta std | Signal/noise |
|---|---:|---:|---:|---:|---:|
| rating | -0.0559 | 0.3185 | 0.542969 | 0.4440 | 0.1259 |
| soundness | -0.0286 | 0.0296 | 1.000000 | 0.0904 | 0.3162 |
| presentation | 0.0238 | 0.1407 | 0.656250 | 0.2762 | 0.0862 |
| contribution | -0.0742 | 0.1741 | 0.335938 | 0.3441 | 0.2156 |

- Mean decision flip rate: 0.0%
- Mean main decision instability across runs: 0.0%
- Mean variant decision instability across runs: 0.0%

## rhetoric_heavier

| Metric | Mean shift | Mean abs shift | Exact sign-flip p | Mean within-delta std | Signal/noise |
|---|---:|---:|---:|---:|---:|
| rating | 0.1272 | 0.3942 | 0.101562 | 0.5123 | 0.2482 |
| soundness | 0.1095 | 0.1971 | 0.375000 | 0.3935 | 0.2783 |
| presentation | 0.1774 | 0.3139 | 0.183594 | 0.5587 | 0.3175 |
| contribution | 0.2514 | 0.4599 | 0.125000 | 0.7176 | 0.3503 |

- Mean decision flip rate: 0.0%
- Mean main decision instability across runs: 0.0%
- Mean variant decision instability across runs: 0.0%

## Overall

- Mean variant rating shift: 0.0309
- Smallest rating p-value across variants: 0.101562
- Variants with rating p < 0.05: none