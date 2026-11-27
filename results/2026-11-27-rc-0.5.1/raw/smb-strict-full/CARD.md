# inkling-2-mini-atlas · SparkModelBench

1x NVIDIA DGX Spark (GB10, 128 GB) · SparkInkling 0.5.1 candidate (Atlas, Enntity/atlas inkling2/rc-0.5.1-20261126 @ a4dbba378)

Serving measurements and quality tasks by **Alex Ellis, OpenFaaS Ltd**. [RigMark](https://github.com/alexellis/rigmark) · [RigMark Quality](https://github.com/alexellis/rigmark-quality). Enntity adds the staggered four-request field guide.

Comparison `sparkinkling-0.5.1` · suite `293a44f82dd9`

## RigMark Quality · task completion

| Task | Checks passed | Finished | Seconds | Output tokens |
|---|---|---|---:|---:|
| python-expiry | True | True | 20.60 | 1152 |
| go-transfer-ledger | False | True | 80.50 | 3793 |
| payment-recovery | True | True | 6.30 | 385 |
| evidence-revisions | True | True | 6.20 | 394 |

## RigMark · generation, median

| Workload | Tok/s | Last output (s) | Output tokens | Gates |
|---|---:|---:|---:|---:|
| code | 68.68 | 51.25 | 3503 | 5/5 |
| prose | 40.16 | 27.78 | 1117 | 5/5 |
| structured | 102.29 | 10.15 | 1013 | 5/5 |

## SparkGLM · staggered C4

| Round | Wall (s) | Stream TTFT (s) | Longest visible gap (s) | Full streams |
|---|---:|---|---:|---|
| warmup | 36.28 | —, —, —, 23.24 | 0.13 | False |
| 1 | 36.24 | —, —, —, 28.66 | 0.12 | False |
| 2 | 36.35 | —, —, —, — | — | False |
| 3 | 36.26 | —, —, —, — | — | False |

## RigMark · prefill

| Prompt tokens | First TTFT (s) | First tok/s | Replay TTFT (s) | Replay tok/s | First cache evidence |
|---:|---:|---:|---:|---:|---|
| 8192 | 1.59 | 5,136.64 | 0.14 | 60,156.12 | zero cached tokens reported |
| 32768 | 6.66 | 4,917.95 | 0.16 | 209,346.75 | zero cached tokens reported |
| 65536 | 14.63 | 4,480.73 | 0.18 | 353,770.58 | zero cached tokens reported |
| 131072 | 34.69 | 3,778.76 | 0.24 | 543,524.42 | zero cached tokens reported |
| 262144 | 92.71 | 2,827.49 | 0.37 | 707,697.79 | zero cached tokens reported |
