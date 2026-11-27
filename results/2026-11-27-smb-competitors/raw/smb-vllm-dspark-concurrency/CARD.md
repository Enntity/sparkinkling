# inkling-2-mini · SparkModelBench

1x NVIDIA DGX Spark (GB10, 128 GB) · vLLM, its Inkling 2 Mini image

Serving measurements and quality tasks by **Alex Ellis, OpenFaaS Ltd**. [RigMark](https://github.com/alexellis/rigmark) · [RigMark Quality](https://github.com/alexellis/rigmark-quality). Enntity adds the staggered four-request field guide.

Comparison `sparkinkling-0.5.1` · suite `293a44f82dd9`

## RigMark · concurrency

Code prompts started together, 256 output tokens each, median of 3 rounds. Aggregate throughput includes prefill and scheduling.

| Requests | Aggregate tok/s | Per-stream tok/s | Per-stream TTFT (s) |
|---:|---:|---:|---:|
| 1 | 43.63 | 45.57 | 0.27 |
| 2 | 69.21 | 36.99 | 0.34 |
| 4 | 106.64 | 28.63 | 0.48 |
| 8 | 156.40 | 24.63 | 2.75 |
