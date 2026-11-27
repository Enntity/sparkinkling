# inkling-2-mini-atlas · SparkModelBench

1x NVIDIA DGX Spark (GB10, 128 GB) · SparkInkling 0.5.1 candidate (Atlas, Enntity/atlas inkling2/rc-0.5.1-20261126 @ a4dbba378)

Serving measurements and quality tasks by **Alex Ellis, OpenFaaS Ltd**. [RigMark](https://github.com/alexellis/rigmark) · [RigMark Quality](https://github.com/alexellis/rigmark-quality). Enntity adds the staggered four-request field guide.

Comparison `sparkinkling-0.5.1` · suite `293a44f82dd9`

## RigMark Quality · task completion

| Task | Checks passed | Finished | Seconds | Output tokens |
|---|---|---|---:|---:|
| python-expiry | True | True | 17.60 | 1046 |
| go-transfer-ledger | False | True | 74.00 | 3946 |
| payment-recovery | True | True | 5.30 | 406 |
| evidence-revisions | True | True | 5.20 | 394 |

## RigMark · generation, median

| Workload | Tok/s | Last output (s) | Output tokens | Gates |
|---|---:|---:|---:|---:|
| code | 88.21 | 37.37 | 3276 | 5/5 |
| prose | 57.04 | 21.81 | 1248 | 5/5 |
| structured | 129.90 | 8.16 | 1031 | 5/5 |

## SparkGLM · staggered C4

| Round | Wall (s) | Stream TTFT (s) | Longest visible gap (s) | Full streams |
|---|---:|---|---:|---|
| warmup | 31.96 | —, —, —, — | — | False |
| 1 | 31.64 | —, —, —, 20.89 | 0.10 | False |
| 2 | 31.67 | —, —, —, — | — | False |
| 3 | 31.89 | —, —, —, 24.43 | 0.10 | False |

## RigMark · prefill

| Prompt tokens | First TTFT (s) | First tok/s | Replay TTFT (s) | Replay tok/s | First cache evidence |
|---:|---:|---:|---:|---:|---|
| 8192 | 1.58 | 5,174.45 | 0.13 | 61,628.74 | zero cached tokens reported |
| 32768 | 6.52 | 5,023.98 | 0.15 | 216,269.02 | zero cached tokens reported |
| 65536 | 14.44 | 4,539.86 | 0.18 | 362,305.54 | zero cached tokens reported |
| 131072 | 34.67 | 3,780.67 | 0.23 | 558,230.66 | zero cached tokens reported |
| 262144 | 92.81 | 2,824.47 | 0.36 | 718,622.10 | zero cached tokens reported |
