<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling 0.5.0: DFlash2 drafter, 1M-token context (2026-11-25)

The 0.5.0 image, `ghcr.io/enntity/atlas-sparkinkling:13920bc38fd6` (also
`:0.5.0`, manifest `sha256:d126b3712a1f`; Atlas `Enntity/atlas`
`inkling2/rc-0.5.0-20261124` at `1559aa4bc`, the `inkling-2-mini` kernel
target), served through `./start.sh` with the default profile (8 sequences
of up to 1,048,576 tokens, 0.80 of GPU memory, BF16 KV with window-bounded
sliding-window visits, 4,096-token prefill chunks, prefix caching with 264
conv-state snapshots and branch checkpoints) and the default drafter
(incoai's DFlash2, seven drafts, verifies sized by the drafter's confidence;
three drafts each for two live requests in Strict), measured with
[RigMark](https://github.com/alexellis/rigmark) `40fabcaf6e96`, protocol
1.1.0, on one DGX Spark with nothing else serving. Weights:
`thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`; Spark adds
`Enntity/Inkling-2-Mini-Spark-NVFP4` @ `e9df93dc`; drafter
`incoai/Inkling-2-Mini-DFlash2` @ `4f9088ea66c2`.

The image build ran the engine's whole CPU workspace suite (8,852 tests
passed, now including the closure-attestation test 0.4.2 skipped) and
Clippy, in 287 s on the Spark (`raw/build-summary.log`). `./start.sh` passed
its smoke test in both modes (`raw/img050-*.start.log`), and the metadata
RigMark recorded names this engine and image.

## What changed since 0.4.2

- **incoai's DFlash2 drafter replaces DSpark.** A five-layer block-diffusion
  drafter with a candidate selector over the target's vocabulary head, reading
  the same four target taps as the checkpoint's bundled DSpark. Its drafts are
  accepted more often, so one request decodes faster in both modes. DSpark and
  `DRAFTER=dspark` are gone.
- **Drafting retuned for it** ([tuning runs](../2026-11-25-dflash2-tuning/RESULT.md)):
  a block in Strict keeps drafting while it accepts one token (was two), Spark
  uses the engine's two (was 2.5), Strict drafts three each for two live
  requests (was two). Both modes still decode plainly from three requests in
  Strict and two in Spark, where drafting lost on RigMark's short requests.
- **Window-bounded KV: 1,048,576-token requests.** The 40 sliding-window layer
  visits keep only their last 1,024 tokens, so context costs the 8 global
  visits' 32 KiB a token instead of 192 KiB. `default` and `max` serve
  1,048,576-token requests (was 131,072 and 262,144), `saver` 786,432.
- **The prefix cache's disk tier is gone** (`PREFIX_CACHE_DIR`,
  `PREFIX_CACHE_GB`): it needs full-length KV, which would cost the long
  context. `start.sh` refuses the old settings with a message.

## Results

Medians over the repetitions of each suite (two decode runs per workload, two
cold prefill requests per depth, two rounds per concurrency). Every repetition
is in `raw/`; `CARD.md` holds the two code-suite cards unedited.

| | Strict | Spark | Strict 0.4.2 | Spark 0.4.2 | vLLM, no speculation | vLLM, DSpark |
|---|---:|---:|---:|---:|---:|---:|
| Code decode, tok/s | 70.0 | 81.4 | 65.2 | 77.5 | 35.1 | 69.8 |
| Prose decode | 39.6 | 56.1 | 35.3 | 55.7 | 35.6 | 31.2 |
| Structured decode | 103.2 | 117.4 | 92.6 | 103.6 | 35.6 | 104.3 |
| 32K cold prefill | 3,268 | 3,282 | 3,274 | 3,277 | 2,722 | 2,723 |
| 8K cold prefill | 3,334 | 3,361 | 3,345 | 3,352 | | |
| Short code, aggregate C1 / C2 / C4 / C8 | 46.5 / 62.6 / 85.7 / 122.7 | 58.8 / 77.8 / 103.5 / 135.2 | 41.3 / 63.1 / 85.0 / 120.7 | 53.9 / 77.7 / 105.8 / 135.4 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| Short prose, aggregate C1 / C4 / C8 | 44.6 / 84.3 / 120.0 | 61.4 / 100.9 / 131.7 | 36.9 / 82.7 / 120.6 | 53.2 / 100.4 / 129.1 | 35.3 / 89.2 / 126.4 | 36.0 / 88.2 / 122.1 |
| 32K / 8K immediate replay, time to first token | 0.16 s / 0.14 s | 0.15 s / 0.14 s | 0.16 s / 0.14 s | 0.16 s / 0.14 s | | |
| Basic output gates | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

Each decode cell's two runs: Strict code 69.8 and 70.3, prose 39.1 and 40.2,
structured 103.6 and 102.7; Spark code 82.8 and 80.1, prose 56.2 and 56.1,
structured 118.6 and 116.3.

The 0.4.2 columns are [its release run](../2026-11-23-release-0.4.2/RESULT.md),
same Spark and protocol. The vLLM columns are vLLM's own Inkling 2 Mini image
(`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`) on the same Spark with
the same protocol, measured 2026-11-20; receipts in
[`../2026-11-21-release-0.1.0/raw/vllm-*`](../2026-11-21-release-0.1.0/raw/).

## What it shows

- **Against 0.4.2**: Strict code +7%, prose +12%, structured output +11%, one
  short-code request +13% and one short-prose request +21%; Spark code +5%,
  structured +13%, one short-code request +9% and one short-prose request
  +15%. Prefill, replay and two to eight requests are level (within 2.2%).
- **Spark against vLLM with its DSpark drafter** leads on code (1.17x), prose
  (1.80x), structured output (1.13x, was level), prefill (1.21x) and one to
  four short-code requests (1.35x / 1.28x / 1.09x), and trails at eight
  (0.94x). Against vLLM without speculation it leads in every cell: 2.32x on
  code, 1.58x on prose, 3.30x on structured output.
- **Strict, the checkpoint as shipped, against vLLM with its drafter** is
  level on code (1.00x) and structured output (0.99x), leads on prose (1.27x),
  prefill (1.20x) and one and two requests (1.07x, 1.03x), and trails at four
  (0.90x) and eight (0.85x). Against vLLM without speculation it leads on
  code (1.99x), structured output (2.90x), prose (1.11x), prefill and one and
  two requests (1.32x, 1.16x), and is level at four and eight (0.99x, 1.00x).
- **Still behind**: drafting under load. vLLM's drafter gains 18% at eight
  requests; ours lost on RigMark's short requests from three requests in
  Strict and two in Spark ([tuning](../2026-11-25-dflash2-tuning/RESULT.md),
  [issue 1](https://github.com/Enntity/sparkinkling/issues/1)).
- **Gates**: both modes pass all six.

## Context and memory

On the release candidate `39e8f22fb0d4` (the same engine and profiles; it
differed only in drafting more requests at once), with the voice services
suspended (`raw/window050.out`):

| KV pool, tokens | Strict | Spark | 0.5.0 with DSpark (dev) | 0.4.2 |
|---|---:|---:|---:|---:|
| `default` (0.80) | 1,969,120 | 1,838,992 | 2,004,064 / 1,856,048 | about 404K |
| `max` (0.85) | 1,908,256 | 1,746,976 | 1,944,304 / 1,815,120 | about 446K |
| `saver` (0.50) | 964,560 | 799,520 | 952,016 / 830,416 | about 194K |

The DFlash2 drafter is larger than DSpark (1 GB of weights) and takes 1-4% of
the pool. `saver` was read with the voice services resident; its budget is
the profile's share of total memory, so they do not change it.

**1M-token recall** (Spark mode, default profile, DFlash2 on,
`raw/needle050.*`): a code hidden a third of the way into a 1,032,929-token
prompt was recalled exactly, 1,252.6 s for the request. The same check in
Strict on a development build took 1,252 s.

## Functional check on this image

`raw/rc050.sh` through `./start.sh` in both modes, with the Spark's voice
services resident and 0.50 of GPU memory (`raw/rc050.out`; the candidate's
run is `raw/rc050-39e8f22fb0d4.out`):

- Task probe (`raw/task_probe.py`, reasoning low, temperature 0): 30/30
  arithmetic and 10/10 tool calls in both modes.
- Tool calls, blocking and streamed, with thinking on and off: all returned
  as tool calls (`raw/tooltest.py`); arguments asked for with
  `stream_tool_arguments` arrived in 63-80 chunks (`raw/argstream.py`).
- Forced tool choice (`raw/forced_stream.py`): a named function with thinking
  on and off and `required` each finished `tool_calls`. A named call to a
  cloud metadata address finished `content_filter` with
  `guard_stop: tool_call_guard`, streamed when asked and with no arguments
  sent when not.
- Images (`raw/vis_chat.py`, the three PNGs): the invoice transcribed
  exactly, the 3x3 grid read 9/9 and the shapes image described correctly, in
  both modes.
- A voice-agent turn pattern (`raw/voice_turns.py`, Strict): time to first
  token of a new turn 4.96 s on the first, then 1.69, 0.74 and 0.78 s;
  follow-ups 0.41-0.43 s.
- **Drafted text is the plain text**: greedy text for 8 prompts of 320 tokens
  (`raw/greedy_eq.py`) with the drafter on, at one, two and four requests,
  was identical to one request with `DRAFTER=none`, 8/8 in every case, in
  both modes (`raw/greedy050-*`).

A smoke-level check, not a benchmark. Server logs showed no errors.

## Files

- `CARD.md`: the RigMark cards of the two code suites, unedited.
- `raw/img050-{strict,spark}-{code,prose}.json` and `.card.txt`: RigMark
  output; `raw/img050-*.log` the runner output; `raw/img050-*.server.log`
  the engine log; `raw/img050-*.start.log` the launcher;
  `raw/metadata-image-*.json` the run metadata, written by `raw/meta050.py`;
  `raw/run050.sh` and `raw/window050b.sh` the commands. The window ran from
  12:01:52Z to 12:20:09Z with the voice services suspended through LLooM.
- `raw/window050.sh` and `raw/window050.out`: the candidate's window
  (10:21:50Z to 11:09:08Z): its RigMark (`raw/rc1-39e8f22fb0d4/`), which
  showed the drafting regression at two and four requests, the pools
  (`raw/max050-*`, and `raw/saver050*` after it) and the 1M recall
  (`raw/needle050*`, `raw/needle.py`).
- `raw/rc050*`, `raw/greedy050-*` and the probe scripts named above: the
  functional checks.
- `raw/build-summary.log`: the release image build's test results.
- `SHA256SUMS` covers every file.
