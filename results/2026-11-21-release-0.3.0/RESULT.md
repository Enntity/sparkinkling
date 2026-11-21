<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling 0.3.0: Spark past vLLM everywhere, Strict level with it (2026-11-21)

The 0.3.0 image, `ghcr.io/enntity/atlas-sparkinkling:75c0c6f7962f` (Atlas
`Enntity/atlas` `inkling2/mini-20261121` at `db19431be`, the `inkling-2-mini`
kernel target), served through `./start.sh` with the default profile (8
sequences, 131,072 tokens, 0.80 of GPU memory, BF16 KV, 4,096-token prefill
chunks, programmatic dependent launch) and the default drafter (DSpark, seven
drafts, with one live request, only while drafts pay), measured with
[RigMark](https://github.com/alexellis/rigmark) `40fabcaf6e96`, protocol 1.1.0,
on one DGX Spark with nothing else serving. Weights:
`thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`; Spark adds
`Enntity/Inkling-2-Mini-Spark-NVFP4` @ `e9df93dc`.

The image build ran the engine's whole CPU workspace suite (8,747 tests passed,
the skips listed in `install/Dockerfile`) and Clippy. `./start.sh` passed its
smoke test in both modes (`raw/img-*.start.log`).

## What changed since 0.2.0

- **Decode.** The expert GEMVs read each weight row's block scales in one
  request instead of one per 16-byte code chunk; decode attention and the block
  residuals keep their per-head arrays in registers (the compiler had put them
  in local memory); the short convolution rolls its own state; the target's
  kernels launch with programmatic dependent launch, so each launch overlaps
  its predecessor's tail. All bit-identical. Strict decodes a token at 2K
  context in about 29.7 ms (34.0 ms in 0.2.0, development measurements).
- **Speculation only while it pays.** DSpark stops proposing for a sequence
  whose drafts average under two accepted a step over twelve steps and
  re-probes 256 tokens later. Prose accepts under one a step, where a
  seven-draft verify costs about 2.6 plain steps, so prose now decodes plainly.
- **Spark prefill on the checkpoint's own tensors.** Prefill rows read the
  checkpoint's BF16 projections and its experts at the declared numerics in
  both modes; the overlay serves decode and verify. Spark prefills exactly as
  Strict does.

## Results

Medians over the repetitions of each suite (two decode runs per workload, two
cold prefill requests per depth, two rounds per concurrency). Every repetition
is in `raw/`; `CARD.md` holds the two code-suite cards unedited.

| | Strict | Spark | Strict 0.2.0 | Spark 0.2.0 | vLLM, no speculation | vLLM, DSpark |
|---|---:|---:|---:|---:|---:|---:|
| Code decode, tok/s | 48.8 | 66.9 | 50.0 | 60.9 | 35.1 | 69.8 |
| Prose decode | 33.2 | 50.5 | 22.8 | 25.7 | 35.6 | 31.2 |
| Structured decode | 86.3 | 96.1 | 79.5 | 87.3 | 35.6 | 104.3 |
| 32K cold prefill | 3,326 | 3,339 | 3,271 | 3,128 | 2,722 | 2,723 |
| 8K cold prefill | 3,533 | 3,546 | 3,463 | 3,363 | | |
| Short code, aggregate C1 / C2 / C4 / C8 | 35.5 / 48.0 / 80.5 / 117.2 | 50.0 / 68.8 / 102.2 / 135.0 | 32.0 / 44.1 / 72.2 / 105.3 | 35.8 / 63.1 / 90.0 / 115.5 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| Short prose, aggregate C1 / C4 / C8 | 33.1 / 79.0 / 114.6 | 50.5 / 97.7 / 127.9 | 25.7 / 71.7 / 104.9 | 31.8 / 87.3 / 116.0 | 35.3 / 89.2 / 126.4 | 36.0 / 88.2 / 122.1 |
| Basic output gates | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 | 6/6 |

The vLLM columns are vLLM's own Inkling 2 Mini image
(`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`) on the same Spark with
the same protocol, measured 2026-11-20; receipts in
[`../2026-11-21-release-0.1.0/raw/vllm-*`](../2026-11-21-release-0.1.0/raw/).

## What it shows

- **Spark** is ahead of vLLM without speculation in every cell: 1.91x on code,
  1.42x on prose, 2.70x on structured output, 1.23x on 32K prefill, 1.42x at
  one short-code request and 1.10x at eight. Against vLLM with its DSpark
  drafter it leads on prose (1.62x), prefill and C1 to C4, and trails on code
  (0.96x), structured output (0.92x) and C8 (0.94x).
- **Strict** is ahead of vLLM without speculation on code (1.39x), structured
  output (2.42x), 32K prefill (1.22x) and one request (1.01x), and within 4-11%
  of it on prose (0.93x) and at two to eight requests (0.89x / 0.93x / 0.96x).
  It reads its BF16 attention weights and head as shipped, so a decode step
  reads about twice the bytes Spark's does.
- **Prose with the drafter** now decodes plainly (Strict 22.8 -> 33.2 tok/s);
  code gives up about 2% against 0.2.0 to the probes that confirm prose.
- **Gates**: both modes pass all six. Spark's 0.2.0 miss (a code answer that
  reasoned past the 4,096-token allowance) does not recur.

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
  metadata; `raw/run_image.sh`, `raw/rc030.sh` the commands.
- `raw/probe-*.json`, `raw/task_probe.py`, `raw/probe_image.sh`: the task probe.
- `SHA256SUMS` covers every file.
