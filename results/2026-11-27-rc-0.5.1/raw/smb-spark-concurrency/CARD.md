# inkling-2-mini-atlas · SparkModelBench

1x NVIDIA DGX Spark (GB10, 128 GB) · SparkInkling 0.5.1 candidate (Atlas, Enntity/atlas inkling2/rc-0.5.1-20261126 @ a4dbba378)

Serving measurements and quality tasks by **Alex Ellis, OpenFaaS Ltd**. [RigMark](https://github.com/alexellis/rigmark) · [RigMark Quality](https://github.com/alexellis/rigmark-quality). Enntity adds the staggered four-request field guide.

Comparison `sparkinkling-0.5.1` · suite `293a44f82dd9`

## RigMark · concurrency

Code prompts started together, 256 output tokens each, median of 3 rounds. Aggregate throughput includes prefill and scheduling.

| Requests | Aggregate tok/s | Per-stream tok/s | Per-stream TTFT (s) |
|---:|---:|---:|---:|
| 1 | 63.16 | 67.09 | 0.23 |
| 2 | 81.93 | 44.42 | 0.41 |
| 4 | 104.67 | 27.93 | 0.83 |
| 8 | 144.13 | 20.18 | 1.56 |
