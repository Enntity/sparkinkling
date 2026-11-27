# inkling-2-mini · SparkModelBench

1x NVIDIA DGX Spark (GB10, 128 GB) · vLLM, its Inkling 2 Mini image

Serving measurements and quality tasks by **Alex Ellis, OpenFaaS Ltd**. [RigMark](https://github.com/alexellis/rigmark) · [RigMark Quality](https://github.com/alexellis/rigmark-quality). Enntity adds the staggered four-request field guide.

Comparison `sparkinkling-0.5.1` · suite `293a44f82dd9`

## RigMark Quality · task completion

| Task | Checks passed | Finished | Seconds | Output tokens |
|---|---|---|---:|---:|
| python-expiry | True | True | 25.60 | 1158 |
| go-transfer-ledger | True | True | 90.30 | 3889 |
| payment-recovery | True | True | 6.20 | 431 |
| evidence-revisions | True | True | 6.10 | 408 |

## RigMark · generation, median

| Workload | Tok/s | Last output (s) | Output tokens | Gates |
|---|---:|---:|---:|---:|
| code | 70.84 | 53.64 | 3477 | 5/5 |
| prose | 31.08 | 37.67 | 1148 | 5/5 |
| structured | 104.32 | 9.99 | 1017 | 5/5 |

## SparkGLM · staggered C4

| Round | Wall (s) | Stream TTFT (s) | Longest visible gap (s) | Full streams |
|---|---:|---|---:|---|
| warmup | 41.14 | —, —, —, — | — | False |
| 1 | 39.23 | —, —, —, — | — | False |
| 2 | 39.65 | —, —, —, — | — | False |
| 3 | 38.74 | —, —, —, — | — | False |

## RigMark · prefill

| Prompt tokens | First TTFT (s) | First tok/s | Replay TTFT (s) | Replay tok/s | First cache evidence |
|---:|---:|---:|---:|---:|---|
| 8192 | 2.86 | 2,862.34 | 0.18 | 44,790.48 | unverified |
| 32768 | 11.98 | 2,735.49 | 0.16 | 200,467.40 | unverified |
| 65536 | 26.43 | 2,479.95 | 0.21 | 312,150.51 | unverified |
| 131072 | 62.91 | 2,083.48 | 0.26 | 502,216.59 | unverified |
| 262144 | 165.31 | 1,585.80 | 0.41 | 647,293.11 | unverified |
