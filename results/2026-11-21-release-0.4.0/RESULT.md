<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling 0.4.0: prefix caching, on disk too, and three profiles (2026-11-21)

The 0.4.0 image, `ghcr.io/enntity/atlas-sparkinkling:646b6c9dafe6` (Atlas
`Enntity/atlas` `inkling2/mini-20261121` at `f0f0a2c78`, the `inkling-2-mini`
kernel target), served through `./start.sh` with the default profile (8
sequences, 131,072 tokens, 0.80 of GPU memory, BF16 KV, 4,096-token prefill
chunks, programmatic dependent launch, prefix caching with 128 conv-state
snapshots) and the default drafter (DSpark, seven drafts, with one live
request, only while drafts pay), measured with
[RigMark](https://github.com/alexellis/rigmark) `40fabcaf6e96`, protocol 1.1.0,
on one DGX Spark with nothing else serving. Weights:
`thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`; Spark adds
`Enntity/Inkling-2-Mini-Spark-NVFP4` @ `e9df93dc`.

The image build ran the engine's whole CPU workspace suite (8,750 tests
passed, the skips listed in `install/Dockerfile`) and Clippy. `./start.sh` passed its smoke test in
both modes (`raw/img-*.start.log`); the task probe's Strict start ran with
`PREFIX_CACHE_DIR` set, and its engine log shows the disk tier open at
`/prefix-cache/strict/kv` (`raw/probe-strict.server.log`).

## What changed since 0.3.0

- **Prefix caching.** Each layer visit's short-conv state rides the prefix
  cache's snapshots, so a request that repeats an earlier prompt's beginning
  resumes from the deepest snapshot it matches. A replayed 7.5K-token prompt
  answered identically at 0.11 s to first token against 2.12 s cold; a chat's
  second turn at about 7K tokens starts in 0.29 s; RigMark's immediate replay
  of its 32K prompt takes 0.16 s against 10.0 s cold.
- **Prefix cache on disk.** With `PREFIX_CACHE_DIR`, KV blocks the cache
  evicts go to disk and come back with the conversation: 5.82 s -> 0.90 s to
  first token for a returning ~20K-token conversation, same answer.
- **Profiles** `default`, `max` (32 x 262,144 tokens at 0.85) and `saver`
  (8 x 131,072 at 0.50), SparkQwen's serving flags (hour-long requests, 32,768
  tokens for a tool-calling request, more snapshots).
- **Decode.** The row RMSNorm holds its row in registers (bit-identical).

Development checks behind these: [`../2026-11-21-prefix-cache-and-profiles`](../2026-11-21-prefix-cache-and-profiles/RESULT.md).

## Results

Medians over the repetitions of each suite (two decode runs per workload, two
cold prefill requests per depth, two rounds per concurrency). Every repetition
is in `raw/`; `CARD.md` holds the two code-suite cards unedited.

| | Strict | Spark | Strict 0.3.0 | Spark 0.3.0 | vLLM, no speculation | vLLM, DSpark |
|---|---:|---:|---:|---:|---:|---:|
| Code decode, tok/s | 49.2 | 66.8 | 48.8 | 66.9 | 35.1 | 69.8 |
| Prose decode | 33.6 | 51.6 | 33.2 | 50.5 | 35.6 | 31.2 |
| Structured decode | 86.4 | 96.4 | 86.3 | 96.1 | 35.6 | 104.3 |
| 32K cold prefill | 3,277 | 3,275 | 3,326 | 3,339 | 2,722 | 2,723 |
| 8K cold prefill | 3,332 | 3,366 | 3,533 | 3,546 | | |
| Short code, aggregate C1 / C2 / C4 / C8 | 35.9 / 49.1 / 78.1 / 119.6 | 50.9 / 72.0 / 101.3 / 134.9 | 35.5 / 48.0 / 80.5 / 117.2 | 50.0 / 68.8 / 102.2 / 135.0 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| Short prose, aggregate C1 / C4 / C8 | 33.8 / 81.3 / 115.1 | 51.9 / 99.6 / 129.5 | 33.1 / 79.0 / 114.6 | 50.5 / 97.7 / 127.9 | 35.3 / 89.2 / 126.4 | 36.0 / 88.2 / 122.1 |
| 32K / 8K immediate replay, time to first token | 0.16 s / 0.14 s | 0.15 s / 0.14 s | 9.8 s / 2.3 s | 9.8 s / 2.3 s | | |
| Basic output gates | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

The vLLM columns are vLLM's own Inkling 2 Mini image
(`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`) on the same Spark with
the same protocol, measured 2026-11-20; receipts in
[`../2026-11-21-release-0.1.0/raw/vllm-*`](../2026-11-21-release-0.1.0/raw/).

## What it shows

- **Spark** is ahead of vLLM without speculation in every cell: 1.90x on code,
  1.45x on prose, 2.71x on structured output, 1.20x on 32K prefill, 1.45x at
  one short-code request and 1.10x at eight. Against vLLM with its DSpark
  drafter it leads on prose (1.65x), prefill and one to four requests, and
  trails on code (0.96x), structured output (0.92x) and eight requests (0.94x).
- **Strict** is ahead of vLLM without speculation on code (1.40x), structured
  output (2.43x), 32K prefill (1.20x) and one request (1.02x), and within
  2-10% of it on prose (0.94x) and at two to eight requests (0.91x / 0.90x /
  0.98x). It reads its BF16 attention weights and head as shipped.
- **Against 0.3.0** every decode and concurrency cell is level or ahead
  (single-round concurrency cells move 3-5% between runs). Cold prefill gives
  up about 2% at 32K and 5-6% at 8K: a prompt of 512 tokens or more runs its last
  17-32 rows as a second pass, so the next turn has a snapshot below its
  match, and that pass still reads nearly every expert (about 0.1 s). It is
  what makes a chat's second turn start in 0.3 s instead of recomputing its
  prompt. Below 512 tokens the pass is skipped (on every short prompt it cost
  2-4% at four and eight requests).
- **Replay**: an exact repeat of a prompt that ends on a KV block boundary
  (RigMark's 8,192- and 32,768-token prompts do) resumes from the tail
  checkpoint 32 tokens below its end (0.3.0 had no prefix cache and
  prefilled it again).
- **Gates**: both modes pass all six.

## Task probe

`raw/task_probe.py` against both modes on this image (reasoning low,
temperature 0): 30 arithmetic word problems with exact answers and 10
single-tool calls. Strict (with the disk tier on) 30/30 and 10/10; Spark
30/30 and 10/10 (`raw/probe-*.json`, `raw/probe_image.sh`). A smoke-level
check, not a benchmark.

## Files

- `CARD.md`: the RigMark cards of the two code suites, unedited.
- `raw/img-{strict,spark}-{code,prose}.json` and `.card.txt`: RigMark output;
  `raw/img-*.log` the runner output; `raw/img-*.server.log` the engine log;
  `raw/img-*.start.log` the launcher; `raw/metadata-image-*.json` the run
  metadata; `raw/run_image.sh`, `raw/rc040.sh` the commands.
- `raw/probe-*.json`, `raw/task_probe.py`, `raw/probe_image.sh`,
  `raw/probe-strict.server.log`: the task probe.
- `SHA256SUMS` covers every file.
