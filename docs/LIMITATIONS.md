<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Limitations

What to know before relying on SparkInkling, on one DGX Spark. This page
describes 0.4.2. Figures here are from its release run
([`results/2026-11-23-release-0.4.2`](../results/2026-11-23-release-0.4.2/RESULT.md))
unless they say they come from a development build.

## Speed

- **Drafts help one or two requests at a time.** Strict drafts for one or two
  live requests and Spark for one; from three the engine decodes plainly, in
  a batch. The engine proposes for every live request in one pass, but a
  verify row still costs more than the drafts it returns at that width: on a
  development build with other services on the Spark, eight short-code
  requests read about 106 tok/s drafting one token each against about 118
  plain (Strict). vLLM's Inkling 2 Mini image drafts under load and is ahead
  at eight short-code requests: 144.0 against 120.7 (Strict) and 135.4
  (Spark) ([issue 1](https://github.com/Enntity/sparkinkling/issues/1)).
- **Drafts do not help prose.** The target accepts about one draft in two on
  prose, and a verify step costs more than that returns, so the engine turns
  drafts off there. Spark's prose lead over vLLM comes from its weights, not
  from drafts.
- **Strict trails vLLM with its drafter on code and structured output.**
  0.4.2 read 65.2 against 69.8 tok/s on code and 92.6 against 104.3 on
  structured output (0.4.1: 54.2 and 79.9). Strict is ahead of vLLM without a
  drafter on both.
- **One Spark.** The image refuses multi-rank flags. The measurements were
  taken with nothing else serving on the Spark; other GPU work on the same
  machine slows it.

## Fidelity

- **Text with drafts matched text without them in our check, not by proof.**
  A verify run attends exactly as a decode row does, and on 8 prompts of 320
  tokens (4 code, 4 prose, reasoning low) greedy text was identical with the
  drafter off and on, with one request and with two at once, in both modes,
  and with drafting forced on for four and eight at once (Strict). That is a
  small sample on a development build; `DRAFTER=none` remains the
  way to rule the drafter out.
- **Expert inputs in decode are BF16.** The checkpoint declares its experts'
  inputs quantized (NVFP4 rows for layers 0-19, MXFP8 rows for 20-23). Prefill
  follows that; decode and verify rows (fewer than 16 at once) give the
  experts BF16 inputs. This holds in both modes.
- **Spark is not the checkpoint.** Its NVFP4 overlay measured a KL of 0.0081
  to Strict's weights with 97.0% top-1 agreement on 224 held-out documents
  ([MODES](MODES.md)). That is a distribution measurement, not a task
  benchmark.
- **Quality evidence is small.** Each release answers a 30-question arithmetic
  and 10-call tool probe in both modes, and the reasoning-effort study ran
  150 MMLU-Pro, 150 GSM8K and 164 HumanEval items
  ([results](../results/2026-11-22-reasoning-loops/RESULT.md)). Nothing here
  is a broad quality qualification.

## Reasoning

- **A request that names no effort reasons at `low`**, not the template's own
  default (`high`), which often loops at temperature 0. A request's own
  `reasoning_effort` still wins.
- **The engine ends a reasoning block that runs past its budget or loops**
  (2K, 4K, 8K, 16K, 32K reasoning tokens from `minimal` to `xhigh`), and the
  model then answers. An answer written after a forced close has had less
  reasoning than the model wanted.

## Images and video

- **Still images only.** Video is refused.
- **Images arrive as base64 data URIs** in OpenAI `image_url` parts. One token
  per 40x40 pixel tile, no resize; an image of more than 1,600 tiles is scaled
  down to fit, which the checkpoint's own processor would not do.
- **The image check is a smoke test**: three synthetic images (an invoice, a
  labelled grid, shapes). It does not establish general image understanding.

## Tools

- **A client that asks for streamed tool calls must read the finish reason.**
  With `stream_tool_arguments: true` (and the default `TOOL_GUARD=stream`), a
  call the guard blocks has already streamed when the response finishes
  `content_filter`; it must not be run. Requests that do not ask get each call
  held until it passes ([TOOL-GUARD](TOOL-GUARD.md)). SparkInkling 0.4.1
  streamed every request's calls; 0.4.2 holds them unless asked.
- **Streamed `return_token_ids` carry rewritten ids** for Inkling's message
  markers, not the model's raw tokens.

## Memory and context

- **KV is about 32 KiB a token** (the 8 global layer visits; the 40
  sliding-window visits keep only their last 1,024 tokens), so one Spark holds
  the model's 1M-token context. `default` and `max` accept requests of up to
  1,048,576 tokens over pools of about 1.8M to 2.0M tokens, and `saver` up to
  786,432 over about 830K to 950K: two full-length requests cannot be
  resident together, and requests the pool cannot hold wait for blocks.
- **A 1M-token prompt is slow**: about 21 minutes to prefill (attention over
  the 8 global visits grows with the square of the context), and decode at
  that length reads about 32 GiB of KV a token.
- **The disk tier keeps full-length KV.** With `PREFIX_CACHE_DIR` set the
  engine cannot bound the sliding-window visits, the pool falls back to 0.4.2's
  size (about 194K to 446K tokens) and a longer request cannot be admitted.
- **A host that runs out of memory hangs** instead of killing a process (GB10
  memory is shared with the host). The container is capped at 114 GiB; keep
  builds and other models off the Spark while it serves, or use `saver`.
- **Cold prefill is about 3,280 tok/s**: a 32K-token prompt waits about 10 s
  before its first token. A replayed or extended prompt resumes from the
  prefix cache (about 0.15 s to the first token for an immediate 32K
  replay).

## Serving

- The API binds to `127.0.0.1` by default. Exposing it is the operator's
  decision and needs its own access control.
- Requests are limited to one hour (`--request-timeout=3600`), and a
  tool-calling request to 32,768 generated tokens.
