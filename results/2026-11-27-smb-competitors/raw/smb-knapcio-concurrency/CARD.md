# inkling-2-mini · SparkModelBench

1x NVIDIA DGX Spark (GB10, 128 GB) · SGLang + knapcio/Inkling-2-Mini-1x-DGX-Spark v2.9.7 overlays (09febfe)

Serving measurements and quality tasks by **Alex Ellis, OpenFaaS Ltd**. [RigMark](https://github.com/alexellis/rigmark) · [RigMark Quality](https://github.com/alexellis/rigmark-quality). Enntity adds the staggered four-request field guide.

Comparison `sparkinkling-0.5.1` · suite `293a44f82dd9`

## RigMark · concurrency

Code prompts started together, 256 output tokens each, median of 3 rounds. Aggregate throughput includes prefill and scheduling.

| Requests | Aggregate tok/s | Per-stream tok/s | Per-stream TTFT (s) |
|---:|---:|---:|---:|
| 1 | 68.88 | 72.92 | 0.21 |
| 2 | 99.22 | 53.29 | 0.25 |
| 4 | 151.95 | 43.36 | 0.39 |
| 8 | 243.42 | 33.83 | 0.59 |
