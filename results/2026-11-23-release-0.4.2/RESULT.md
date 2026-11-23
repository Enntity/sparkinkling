<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling 0.4.2: faster drafting, exact drafts, tool calls stream only on request (2026-11-23)

The 0.4.2 image, `ghcr.io/enntity/atlas-sparkinkling:b1e18bf91437` (Atlas
`Enntity/atlas` `inkling2/concurrent-spec-20261123` at `d3318e087`, the
`inkling-2-mini` kernel target), served through `./start.sh` with the default
profile (8 sequences, 131,072 tokens, 0.80 of GPU memory, BF16 KV, 4,096-token
prefill chunks, prefix caching with 128 conv-state snapshots and branch
checkpoints) and the default drafter (DSpark, seven drafts, verifies sized by
the drafter's confidence, two drafts each for two live requests in Strict),
measured with [RigMark](https://github.com/alexellis/rigmark) `40fabcaf6e96`,
protocol 1.1.0, on one DGX Spark with nothing else serving. Weights:
`thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`; Spark adds
`Enntity/Inkling-2-Mini-Spark-NVFP4` @ `e9df93dc`.

The image build ran the engine's whole CPU workspace suite (8,819 tests
passed, the skips listed in `install/Dockerfile`) and Clippy. `./start.sh`
passed its smoke test in both modes (`raw/img042-*.start.log`), and the
metadata RigMark recorded names this engine and image.

## What changed since 0.4.1

- **Tool calls stream only for a request that asks.** Under the tool guard's
  `stream` setting (the default) a call's arguments stream only to a request
  that sends `stream_tool_arguments: true`; every other request's calls are
  held until they pass, as under `on`. In 0.4.1 every request's calls
  streamed, so a client that did not read the finish reason could run a call
  the guard had blocked. See [TOOL-GUARD](../../docs/TOOL-GUARD.md).
- **Verifies sized by the drafter's confidence.** The engine learns while
  serving how often each draft confidence is accepted and verifies only as far
  as the block is still likely right; every extra verify row reads about
  1.7 GB of expert weights.
- **Drafts while they pay, per sequence.** A sequence whose drafted steps stop
  paying decodes plainly for 32 tokens at first, doubling while re-probes
  fail (threshold 2.0 accepted a block in Strict, 2.5 in Spark). This replaces
  the engine's throughput gate, whose off state carried from one request into
  the next and made 0.4.1's Strict structured-output cell read 72.7 and 87.1
  in two runs.
- **Two requests draft in Strict**, two drafts each, their proposes sharing
  one pass over the drafter's vocabulary head. The engine proposes for every
  live request in one pass, but from three requests both modes decode
  plainly, because drafting there still cost more than it returned (see
  LIMITATIONS).
- **Drafted text is the plain text.** A verify attends through the same
  attention body and key splits as a decode row, and a verify run keeps the
  decode kernels' row-by-row arithmetic, so greedy text with drafts matched
  text without them in our checks at one to eight requests in both modes.
- **Decode batches at their own width** (three to seven requests no longer
  pad to eight), and a Spark decode row's input projections run as one
  launch.

## Results

Medians over the repetitions of each suite (two decode runs per workload, two
cold prefill requests per depth, two rounds per concurrency). Every repetition
is in `raw/`; `CARD.md` holds the two code-suite cards unedited.

| | Strict | Spark | Strict 0.4.1 | Spark 0.4.1 | vLLM, no speculation | vLLM, DSpark |
|---|---:|---:|---:|---:|---:|---:|
| Code decode, tok/s | 65.2 | 77.5 | 54.2 | 68.4 | 35.1 | 69.8 |
| Prose decode | 35.3 | 55.7 | 35.0 | 54.9 | 35.6 | 31.2 |
| Structured decode | 92.6 | 103.6 | 79.9 | 95.3 | 35.6 | 104.3 |
| 32K cold prefill | 3,274 | 3,277 | 3,283 | 3,274 | 2,722 | 2,723 |
| 8K cold prefill | 3,345 | 3,352 | 3,355 | 3,355 | | |
| Short code, aggregate C1 / C2 / C4 / C8 | 41.3 / 63.1 / 85.0 / 120.7 | 53.9 / 77.7 / 105.8 / 135.4 | 36.8 / 53.4 / 84.5 / 121.0 | 51.6 / 76.1 / 105.4 / 135.2 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| Short prose, aggregate C1 / C4 / C8 | 36.9 / 82.7 / 120.6 | 53.2 / 100.4 / 129.1 | 34.5 / 82.4 / 119.5 | 51.5 / 100.9 / 128.9 | 35.3 / 89.2 / 126.4 | 36.0 / 88.2 / 122.1 |
| 32K / 8K immediate replay, time to first token | 0.16 s / 0.14 s | 0.16 s / 0.14 s | 0.16 s / 0.14 s | 0.15 s / 0.14 s | | |
| Basic output gates | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

Each decode cell's two runs: Strict code 65.3 and 65.0, prose 35.1 and 35.4,
structured 91.7 and 93.4; Spark code 78.7 and 76.2, prose 55.8 and 55.5,
structured 104.3 and 102.9.

The vLLM columns are vLLM's own Inkling 2 Mini image
(`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`) on the same Spark with
the same protocol, measured 2026-11-20; receipts in
[`../2026-11-21-release-0.1.0/raw/vllm-*`](../2026-11-21-release-0.1.0/raw/).

## What it shows

- **Against 0.4.1**: Strict code +20%, structured output +16%, one and two
  short-code requests +12% and +18%, short prose at one request +7%; Spark
  code +13%, structured +9%, one short-code request +4%. Prose decode,
  prefill, replay and four to eight requests are level (within 1%).
- **Spark against vLLM with its DSpark drafter** now leads on code (1.11x),
  prose (1.78x), prefill (1.20x) and one to four short-code requests (1.24x /
  1.28x / 1.12x), is level on structured output (0.99x), and trails at eight
  requests (0.94x). Against vLLM without speculation it leads in every cell:
  2.21x on code, 1.56x on prose, 2.91x on structured output.
- **Strict against vLLM without speculation** leads on code (1.86x),
  structured output (2.60x), prefill (1.20x) and one and two requests (1.18x,
  1.17x), and is within 1-2% on prose (0.99x) and at four and eight requests
  (0.98x, 0.99x). Against vLLM with its drafter it leads on prose (1.13x) and
  two requests (1.04x), and trails on code (0.93x), structured output (0.89x),
  one request (0.95x), four (0.90x) and eight (0.84x).
- **0.4.1's unsteady cell is steady**: Strict structured output read 91.7 and
  93.4 (0.4.1: 72.7 and 87.1).
- **Still behind**: drafting with three or more live requests (vLLM's drafter
  gains 18% at eight; [issue 1](https://github.com/Enntity/sparkinkling/issues/1)).
- **Gates**: both modes pass all six.

## Functional check on this image

`raw/rc-check.sh` through `./start.sh` in both modes, before the timed runs,
with the Spark's voice services resident and 0.50 of GPU memory
(`raw/rc-check.out`):

- Task probe (`raw/task_probe.py`, reasoning low, temperature 0): 30/30
  arithmetic and 10/10 tool calls in both modes. The window's probe
  (`raw/probe042.sh`, `raw/task_probe-window.py`, default profile) read the
  same (`raw/probe042-img-*.json`).
- Tool calls, blocking and streamed, with thinking on and off: all returned
  as tool calls (`raw/tooltest.py`); arguments asked for with
  `stream_tool_arguments` arrived in 63-80 chunks (`raw/argstream.py`).
- Forced tool choice (`raw/forced_stream.py`): a named function with
  thinking on and off and `required` each finished `tool_calls` with
  streamed arguments. A named call to a cloud metadata address, asked for
  streamed, sent its arguments in 31 chunks and finished `content_filter`
  with `guard_stop: tool_call_guard`. The same two calls without
  `stream_tool_arguments` (Strict, `raw/neg-check.out`): the benign one
  arrived whole in one chunk, and the blocked one sent no arguments and
  finished `content_filter`.
- Images (`raw/vis_chat.py`, the three PNGs in `raw/`): the five-line invoice
  transcribed exactly in both modes, the 3x3 grid read 9/9, the shapes image
  described correctly.
- A voice-agent turn pattern (`raw/voice_turns.py`, Strict): time to first
  token of a new turn 4.98 s on the first turn, then 1.68, 0.75 and 0.79 s;
  follow-ups 0.40-0.47 s.

A smoke-level check, not a benchmark. Server logs showed no errors.

## Files

- `CARD.md`: the RigMark cards of the two code suites, unedited.
- `raw/img042-{strict,spark}-{code,prose}.json` and `.card.txt`: RigMark
  output; `raw/img042-*.log` the runner output; `raw/img042-*.server.log`
  the engine log; `raw/img042-*.start.log` the launcher;
  `raw/metadata-image-*.json` the run metadata, written by `raw/meta042.py`;
  `raw/run042.sh`, `raw/probe042.sh` and `raw/window042.sh` the commands.
  The window ran from 15:46:28Z to 16:07:23Z with the voice services
  suspended through LLooM.
- `raw/rc-check.*`, `raw/neg-check.out`, `raw/probe042-*` and the probe
  scripts named above: the functional checks.
- `SHA256SUMS` covers every file.
