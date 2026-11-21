<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling 0.1.0: Strict and Spark on one Spark (2026-11-21)

The release image, `ghcr.io/enntity/atlas-sparkinkling:9ea2ff174e03` (Atlas
`Enntity/atlas` `inkling2/mini-20261121` at `035de2214`, the `inkling-2-mini`
kernel target), served through `./start.sh` with the default profile (8
sequences, 131,072 tokens, 0.80 of GPU memory, BF16 KV) and the default
drafter (DSpark, seven drafts, speculating with one live request), measured
with [RigMark](https://github.com/alexellis/rigmark) `40fabcaf6e96`, protocol
1.1.0, on one DGX Spark with nothing else serving. Weights:
`thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`; Spark adds
`Enntity/Inkling-2-Mini-Spark-NVFP4` @ `e9df93dc`.

The image build ran the engine's whole CPU workspace suite (8,747 tests
passed, the skips listed in `install/Dockerfile`) and Clippy. `./start.sh`
downloaded both pins into an empty model root, checked every pinned sha256,
assembled the drafter and Spark directories, and passed its smoke test in both
modes (`raw/img-*.start.log`).

## Results

Medians over the repetitions of each suite (two decode runs per workload, two
cold prefill requests per depth, two rounds per concurrency). Every repetition
is in `raw/`; `CARD.md` holds the two code-suite cards unedited.

| | Strict | Spark | vLLM, no speculation | vLLM, DSpark |
|---|---:|---:|---:|---:|
| Code decode, tok/s | 52.0 | 57.7 | 35.1 | 69.8 |
| Prose decode | 22.2 | 25.9 | 35.6 | 31.2 |
| Structured decode | 79.2 | 86.2 | 35.6 | 104.3 |
| 8K cold prefill, tok/s | 1,639 | 1,591 | | |
| 32K cold prefill | 1,455 | 1,418 | 2,722 | 2,723 |
| Short code, aggregate C1 / C2 / C4 / C8 | 31.7 / 44.4 / 71.4 / 108.7 | 42.4 / 60.3 / 86.3 / 117.9 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| Short prose, aggregate C1 / C4 / C8 | 27.6 / 70.1 / 102.2 | 32.1 / 86.5 / 114.7 | 35.3 / 89.2 / 126.4 | 36.0 / 88.2 / 122.1 |
| Basic output gates | 6/6 | 6/6 | 6/6 | 6/6 |

The vLLM columns are vLLM's own Inkling 2 Mini image
(`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`, the checkpoint as
shipped, 0.75 of memory, 262,144 tokens) on the same Spark with the same
RigMark protocol, measured the day before (2026-11-20): `raw/vllm-*`.

## What it shows

- **Where SparkInkling leads.** Code and structured-output decode in both
  modes beat vLLM without speculation (Strict 1.5x and 2.2x). Spark's
  short-code C2 (60.3) is level with vLLM DSpark's (60.9), and its C4 (86.3)
  with vLLM's without speculation (86.6).
- **Where it trails.** vLLM's DSpark is faster on every decode workload
  (Strict code 52.0 against 69.8). Prose decode with DSpark is slower than
  without it here: few prose drafts are accepted (0.84 a step against 3.4-3.6
  on code, `raw/img-strict.server.log`), and a seven-draft verify step costs
  about 2.6 single-token steps. Without the drafter, an earlier build of this
  branch (`fb1bc1f18`) decoded prose at 30.1-30.2 tok/s in Strict
  (`raw/dev-fb1bc1f18-nodrafter-*`, 5/6 gates: that build's stream loop guard
  cut one code answer, since turned off). Prefill reaches about half of vLLM's at 32K, where the prefill
  attention of the full-attention visits takes a third of the time. Prefix
  caching is refused (the conv states are not snapshotted), so immediate
  replays are cold too.
- **Spark against Strict.** Spark is faster on every decode cell (up to 1.34x
  at C1 short code) and slightly slower at prefill (its NVFP4 projection tile
  trails cuBLASLt's BF16 GEMM there). The 2x-vLLM target is not met.

## Task probe

`raw/task_probe.py` against both modes on the same engine (reasoning low,
temperature 0): 30 arithmetic word problems with exact answers and 10
single-tool calls (right function, right argument), both through the OpenAI
API with `tools`. Strict 30/30 and 10/10; Spark 30/30 and 10/10
(`raw/probe-*.json`). A smoke-level check that both modes answer and call
tools correctly, not a benchmark. The Spark overlay's quality evidence is its
KL to the checkpoint as shipped, 0.0081 [0.0075, 0.0088] over 224 held-out
documents, in the overlay repository.

## Files

- `CARD.md`: the RigMark cards of the two code suites, unedited.
- `raw/img-{strict,spark}-{code,prose}.json` and `.card.txt`: RigMark output;
  `raw/img-*.log` the runner output; `raw/img-*.server.log` the engine log;
  `raw/img-*.start.log` the launcher; `raw/metadata-image-*.json` the run
  metadata; `raw/run_image.sh` the commands.
- `raw/vllm-*`: the vLLM baseline receipts and metadata.
- `raw/dev-fb1bc1f18-nodrafter-*`: Strict without the drafter on an earlier
  development build, for the prose comparison only.
- `raw/probe-*.json`, `raw/task_probe.py`: the task probe.
- `SHA256SUMS` covers every file.
