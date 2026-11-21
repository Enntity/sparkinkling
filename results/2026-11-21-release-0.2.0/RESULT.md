<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling 0.2.0: prefill past vLLM (2026-11-21)

The 0.2.0 image, `ghcr.io/enntity/atlas-sparkinkling:fca1a84f41cf` (Atlas
`Enntity/atlas` `inkling2/mini-20261121` at `f5acf5a71`, the `inkling-2-mini`
kernel target), served through `./start.sh` with the default profile (8
sequences, 131,072 tokens, 0.80 of GPU memory, BF16 KV, prefill chunks of 4,096
tokens) and the default drafter (DSpark, seven drafts, speculating with one live
request), measured with [RigMark](https://github.com/alexellis/rigmark)
`40fabcaf6e96`, protocol 1.1.0, on one DGX Spark with nothing else serving.
Weights: `thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`; Spark adds
`Enntity/Inkling-2-Mini-Spark-NVFP4` @ `e9df93dc`.

The image build ran the engine's whole CPU workspace suite (8,747 tests passed,
the skips listed in `install/Dockerfile`) and Clippy. `./start.sh` passed its
smoke test in both modes (`raw/img-*.start.log`).

## What changed since 0.1.0

Prefill only; decode is the 0.1.0 engine's.

- **The experts at the checkpoint's declared numerics.** The checkpoint's
  `hf_quant_config.json` requires its experts' inputs quantized: NVFP4 rows for
  the NVFP4 experts of layers 0-19 (a per-row scale and, per 16 values, the E4M3
  block scale that takes the block's maximum to 6 or to 4, whichever
  reconstructs it better) and MXFP8 rows for the MXFP8 experts of layers 20-23.
  vLLM's Inkling 2 image runs them that way; 0.1.0 gave them BF16 rows. Prefill
  now quantizes them as declared and runs the experts on the block-scaled
  tensor cores (W4A4 and W8A8).
- **Attention** for prefill chunks shares each K/V tile across a KV head's three
  query heads and computes the relative-position bias where it adds it (bit for
  bit the 0.1.0 bias).
- **Loop message gates and block residuals** run fused, a row tile at a time.
- **Prefill chunks of 4,096 tokens** in the default profile (2,048 in 0.1.0).

## Results

Medians over the repetitions of each suite (two decode runs per workload, two
cold prefill requests per depth, two rounds per concurrency). Every repetition
is in `raw/`; `CARD.md` holds the two code-suite cards unedited.

| | Strict | Spark | Strict 0.1.0 | vLLM, no speculation | vLLM, DSpark |
|---|---:|---:|---:|---:|---:|
| 32K cold prefill, tok/s | **3,271** | **3,128** | 1,455 | 2,722 | 2,723 |
| 8K cold prefill | 3,463 | 3,363 | 1,639 | | |
| Code decode, tok/s | 50.0 | 60.9 | 52.0 | 35.1 | 69.8 |
| Prose decode | 22.8 | 25.7 | 22.2 | 35.6 | 31.2 |
| Structured decode | 79.5 | 87.3 | 79.2 | 35.6 | 104.3 |
| Short code, aggregate C1 / C2 / C4 / C8 | 32.0 / 44.1 / 72.2 / 105.3 | 35.8 / 63.1 / 90.0 / 115.5 | 31.7 / 44.4 / 71.4 / 108.7 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| Short prose, aggregate C1 / C4 / C8 | 25.7 / 71.7 / 104.9 | 31.8 / 87.3 / 116.0 | 27.6 / 70.1 / 102.2 | 35.3 / 89.2 / 126.4 | 36.0 / 88.2 / 122.1 |
| Basic output gates | 6/6 | 5/6 | 6/6 | 6/6 | 6/6 |

The vLLM columns are vLLM's own Inkling 2 Mini image
(`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`) on the same Spark with
the same protocol, measured 2026-11-20; receipts in
[`../2026-11-21-release-0.1.0/raw/vllm-*`](../2026-11-21-release-0.1.0/raw/).

## What it shows

- **Prefill.** A 32K-token prompt is ready in 10.0 s in Strict (22.5 s in
  0.1.0): 1.20x vLLM's 32K prefill, and 1.15x in Spark.
- **Chunk size.** The same image with 0.1.0's 2,048-token chunks reads 2,895
  tok/s at 32K and 3,120 at 8K (`raw/img-strict-chunk2048.*`, Strict, prefill
  cells only); 4,096-token chunks add 13%. The cost: while one request
  prefills, the others' decode steps wait for a chunk that takes about twice
  as long.
- **Spark's one gate.** The second code run in Spark reasoned past RigMark's
  4,096-token cap and was cut (`finish_reason: length`, `raw/img-spark-code.json`),
  so its card reads 5/6 and RigMark marks it not to be headlined. The answer
  was coherent Go, cut mid-test. Every engine spends most of the cap on this
  task (0.1.0 Strict and Spark 3,461-3,534 tokens, vLLM 2,915-3,269), and the run
  repeated the same way on a second measurement. The Strict card is 6/6.
- **Spark prefill** trails Strict's by 4%: its overlay's attention projections
  and layer 20-23 experts still run on a BF16 tensor-core tile.
- **Decode** is unchanged from 0.1.0. The short-code C1 cell of Spark reads 35.8
  against 0.1.0's 42.4: both first rounds were alike (35.4 and 34.7), and
  0.1.0's second round accepted more drafts (50.1), so the 0.1.0 median of two
  was the higher. Where vLLM's DSpark leads (decode) and where plain decode
  beats SparkInkling's DSpark (prose) is as in 0.1.0.

## Task probe

`raw/task_probe.py` against both modes on this image (reasoning low,
temperature 0): 30 arithmetic word problems with exact answers and 10
single-tool calls. Strict 30/30 and 10/10; Spark 30/30 and 10/10
(`raw/probe-*.json`, `raw/probe_image.sh`). A smoke-level check, not a
benchmark.

## Files

- `CARD.md`: the RigMark cards of the two code suites, unedited.
- `raw/img-{strict,spark}-{code,prose}.json` and `.card.txt`: RigMark output;
  `raw/img-*.log` the runner output; `raw/img-*.server.log` the engine log;
  `raw/img-*.start.log` the launcher; `raw/metadata-image-*.json` the run
  metadata; `raw/run_image.sh` the commands.
- `raw/img-strict-chunk2048.*`, `raw/profile-chunk2048.json`,
  `raw/metadata-image-strict-chunk2048.json`, `raw/chunk2048.sh`: the prefill
  cells with 2,048-token chunks.
- `raw/probe-*.json`, `raw/task_probe.py`, `raw/probe_image.sh`: the task probe.
- `SHA256SUMS` covers every file.
