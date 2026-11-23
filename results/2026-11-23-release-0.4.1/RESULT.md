<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling 0.4.1: images, no more reasoning loops, streamed tool calls (2026-11-23)

The 0.4.1 image, `ghcr.io/enntity/atlas-sparkinkling:3f625e2d302e` (Atlas
`Enntity/atlas` `inkling2/mini-20261121` at `6cf40a5a0`, the `inkling-2-mini`
kernel target), served through `./start.sh` with the default profile (8
sequences, 131,072 tokens, 0.80 of GPU memory, BF16 KV, 4,096-token prefill
chunks, prefix caching with 128 conv-state snapshots and branch checkpoints)
and the default drafter (DSpark, seven drafts, with one live request, only
while drafts pay), measured with
[RigMark](https://github.com/alexellis/rigmark) `40fabcaf6e96`, protocol 1.1.0,
on one DGX Spark with nothing else serving. Weights:
`thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`; Spark adds
`Enntity/Inkling-2-Mini-Spark-NVFP4` @ `e9df93dc`.

The image build ran the engine's whole CPU workspace suite (8,803 tests
passed, the skips listed in `install/Dockerfile`) and Clippy. `./start.sh`
passed its smoke test in both modes (`raw/img-*.start.log`).

**A labelling error in the receipts.** The metadata file handed to RigMark was
not updated for this image, so the `run` section of each
`raw/img-*.json` names engine commit `878d7a7f3` and image tag
`75fbfa45a9b9`. The image measured is `3f625e2d302e` (engine `6cf40a5a0`):
`raw/img-*.start.log` shows the tag `./start.sh` served, and the receipts are
otherwise unedited.

## What changed since 0.4.0

- **Images.** The checkpoint's vision tower is served: OpenAI `image_url`
  parts with base64 data URIs, one token per 40x40 pixel tile, no resize (an
  image of more than 1,600 tiles is scaled down to fit). Its features match
  the transformers implementation, and token embeddings are now normed once
  at load so image rows skip the embedding norm, as in the reference.
- **Budget forcing.** The engine closes a reasoning block that runs past its
  effort's budget or loops, and the model then answers; a request that names
  no effort reasons at `low`. Measured in
  [`../2026-11-22-reasoning-loops`](../2026-11-22-reasoning-loops/RESULT.md).
- **Tool calls.** Arguments stream as they are generated. The tool guard's
  new `stream` setting (the default) checks each call when it ends; a call it
  blocks finishes `content_filter`. Tool calls at thinking effort 0 and
  forced tool choices (`required`, or a named function) come back as calls
  when streamed.
- **Prefix cache.** A prefill saves a state where its prompt forks from a
  cached one, so a client that rebuilds its last messages each turn resumes
  there.
- **Decode.** Batches and verifies of up to 8 rows read each BF16 weight
  once; a visit's Strict input projections run as one launch; the first
  visit no longer norms its input.

## Results

Medians over the repetitions of each suite (two decode runs per workload, two
cold prefill requests per depth, two rounds per concurrency). Every repetition
is in `raw/`; `CARD.md` holds the two code-suite cards unedited.

| | Strict | Spark | Strict 0.4.0 | Spark 0.4.0 | vLLM, no speculation | vLLM, DSpark |
|---|---:|---:|---:|---:|---:|---:|
| Code decode, tok/s | 54.2 | 68.4 | 49.2 | 66.8 | 35.1 | 69.8 |
| Prose decode | 35.0 | 54.9 | 33.6 | 51.6 | 35.6 | 31.2 |
| Structured decode | 79.9 | 95.3 | 86.4 | 96.4 | 35.6 | 104.3 |
| 32K cold prefill | 3,283 | 3,274 | 3,277 | 3,275 | 2,722 | 2,723 |
| 8K cold prefill | 3,355 | 3,355 | 3,332 | 3,366 | | |
| Short code, aggregate C1 / C2 / C4 / C8 | 36.8 / 53.4 / 84.5 / 121.0 | 51.6 / 76.1 / 105.4 / 135.2 | 35.9 / 49.1 / 78.1 / 119.6 | 50.9 / 72.0 / 101.3 / 134.9 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| Short prose, aggregate C1 / C4 / C8 | 34.5 / 82.4 / 119.5 | 51.5 / 100.9 / 128.9 | 33.8 / 81.3 / 115.1 | 51.9 / 99.6 / 129.5 | 35.3 / 89.2 / 126.4 | 36.0 / 88.2 / 122.1 |
| 32K / 8K immediate replay, time to first token | 0.16 s / 0.14 s | 0.15 s / 0.14 s | 0.16 s / 0.14 s | 0.15 s / 0.14 s | | |
| Basic output gates | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

The vLLM columns are vLLM's own Inkling 2 Mini image
(`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`) on the same Spark with
the same protocol, measured 2026-11-20; receipts in
[`../2026-11-21-release-0.1.0/raw/vllm-*`](../2026-11-21-release-0.1.0/raw/).

## What it shows

- **Spark** is ahead of vLLM without speculation in every cell: 1.95x on
  code, 1.54x on prose, 2.68x on structured output, 1.20x on 32K prefill,
  1.47x at one short-code request and 1.10x at eight. Against vLLM with its
  DSpark drafter it leads on prose (1.76x), prefill and one to four requests
  (1.19x / 1.25x / 1.11x), and trails on code (0.98x), structured output
  (0.91x) and eight requests (0.94x).
- **Strict** is ahead of vLLM without speculation on code (1.54x), structured
  output (2.24x), 32K prefill (1.21x) and one request (1.05x), and within 1-3%
  of it on prose (0.98x) and at two to eight short-code requests (0.99x /
  0.98x / 0.99x). Short prose at four and eight requests is 0.92x and 0.95x.
- **Against 0.4.0**: Strict code +10%, prose +4%, two and four requests +9%
  and +8%; Spark prose +6%, two and four requests +6% and +4%. Prefill and
  replay are level.
- **One cell is lower: Strict structured decode**, 79.9 against 86.4. Its two
  runs read 72.7 and 87.1 (the prose suite's repeat of that workload read 72.3
  and 86.7). The engine log shows that half of the slower run's steps decoded
  without drafts (`serial=0.51` against `0.09`), although the drafts it did
  run accepted 5.4 a step: the rule that turns drafts off for a sequence where
  they stop paying kept them off too long in that run. Not fixed in this
  release.
- **Not here yet**: speculation with more than one live request (vLLM's
  drafter gains 13% at two requests and 18% at eight;
  [issue 1](https://github.com/Enntity/sparkinkling/issues/1)).
- **Gates**: both modes pass all six.

## Functional check on this image

`raw/rc-check.sh` through `./start.sh` in both modes (saver profile, so
measured before the timed runs with other services resident;
`raw/rc-check.out`):

- Task probe (`raw/task_probe.py`, reasoning low, temperature 0): 30/30
  arithmetic and 10/10 tool calls in both modes (`raw/rc-probe-*.json`).
- Tool calls, blocking and streamed, with thinking on and off: all returned
  as tool calls; streamed arguments arrived in 63-83 chunks under the default
  guard (`raw/tooltest.py`, `raw/argstream.py`).
- Forced tool choice, streamed (`raw/forced_stream.py`): a named function
  with thinking on and off and `required` each finished `tool_calls`. A named
  call to a cloud metadata address streamed its arguments (31 chunks) and then
  finished `content_filter` with `guard_stop: tool_call_guard`.
- Images (`raw/vis_chat.py`, the three PNGs in `raw/`, drawn by `raw/mk.py`):
  a five-line invoice transcribed exactly in both modes, a 3x3 grid of
  labelled coloured rectangles read 9/9, a shapes image described correctly.
- A voice-agent turn pattern (`raw/voice_turns.py`: a long system prompt,
  history, three trailing messages rebuilt every turn; Strict): time to first
  token of a new turn 1.70 s on the turn that saves the branch state, then
  0.73-0.77 s; follow-ups 0.40-0.49 s.

A smoke-level check, not a benchmark.

## Files

- `CARD.md`: the RigMark cards of the two code suites, unedited.
- `raw/img-{strict,spark}-{code,prose}.json` and `.card.txt`: RigMark output;
  `raw/img-*.log` the runner output; `raw/img-*.server.log` the engine log;
  `raw/img-*.start.log` the launcher; `raw/metadata-image-*.json` the run
  metadata (see the labelling error above); `raw/run_image.sh`,
  `raw/window-rc.sh` and `raw/window-rc.out` the commands and their times.
- `raw/rc-check.*`, `raw/rc-probe-*.json` and the probe scripts named above:
  the functional check. `raw/vis_ref.py` computes the transformers
  reference features the tower was compared with during development.
- `SHA256SUMS` covers every file.
