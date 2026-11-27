# inkling-2-mini · SparkModelBench

1x NVIDIA DGX Spark (GB10, 128 GB) · SGLang + knapcio/Inkling-2-Mini-1x-DGX-Spark v2.9.7 overlays (09febfe)

Serving measurements and quality tasks by **Alex Ellis, OpenFaaS Ltd**. [RigMark](https://github.com/alexellis/rigmark) · [RigMark Quality](https://github.com/alexellis/rigmark-quality). Enntity adds the staggered four-request field guide.

Comparison `sparkinkling-0.5.1` · suite `293a44f82dd9`

## RigMark Quality · task completion

| Task | Checks passed | Finished | Seconds | Output tokens |
|---|---|---|---:|---:|
| python-expiry | True | True | 11.10 | 1031 |
| go-transfer-ledger | False | True | 66.90 | 4192 |
| payment-recovery | True | True | 4.40 | 392 |
| evidence-revisions | True | True | 4.90 | 421 |

## RigMark · generation, median

| Workload | Tok/s | Last output (s) | Output tokens | Gates |
|---|---:|---:|---:|---:|
| code | 97.78 | 34.12 | 3275 | 5/5 |
| prose | 59.67 | 20.49 | 1203 | 5/5 |
| structured | 147.73 | 7.05 | 1021 | 5/5 |

## SparkGLM · staggered C4

| Round | Wall (s) | Stream TTFT (s) | Longest visible gap (s) | Full streams |
|---|---:|---|---:|---|
| warmup | 22.52 | 10.84, 9.84, 8.84, 7.84 | — | False |
| 1 | 22.33 | 10.77, 9.77, 8.77, 7.77 | — | False |
| 2 | 22.36 | 10.77, 9.77, 8.77, 7.77 | — | False |
| 3 | 22.40 | 10.77, 9.77, 8.77, 7.77 | — | False |

## RigMark · prefill

| Prompt tokens | First TTFT (s) | First tok/s | Replay TTFT (s) | Replay tok/s | First cache evidence |
|---:|---:|---:|---:|---:|---|
| 8192 | 1.41 | 5,818.23 | 1.46 | 5,628.61 | unverified |
| 32768 | 6.07 | 5,398.98 | 1.69 | 19,437.77 | unverified |
| 65536 | 13.62 | 4,811.92 | 2.08 | 31,555.37 | unverified |
| 131072 | 32.99 | 3,973.10 | 2.83 | 46,288.89 | unverified |
| 262144 | 93.14 | 2,814.55 | 4.62 | 56,782.13 | unverified |
