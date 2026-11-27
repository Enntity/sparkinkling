<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Limitations

What to know before relying on SparkInkling, on one DGX Spark. This page
describes 0.5.1. Figures are from SparkModelBench on one Spark: the 0.5.1 run
([`results/2026-11-27-rc-0.5.1`](../results/2026-11-27-rc-0.5.1/RESULT.md))
and vLLM and knapcio's recipe beside it
([`results/2026-11-27-smb-competitors`](../results/2026-11-27-smb-competitors/RESULT.md)),
unless they name 0.5.0 (RigMark 1.1.0,
[`results/2026-11-25-release-0.5.0`](../results/2026-11-25-release-0.5.0/RESULT.md))
or a development build.

## Speed

- **knapcio's SGLang recipe is faster.** On the same Spark,
  [knapcio/Inkling-2-Mini-1x-DGX-Spark](https://github.com/knapcio/Inkling-2-Mini-1x-DGX-Spark)
  v2.9.7 decodes code at 97.8 tok/s, prose at 59.7 and structured output at
  147.7 (Spark 88.2, 57.0, 129.9), prefills 32K at 5,399 tok/s (Spark 5,024;
  level at 256K) and reaches 68.9 / 99.2 / 152.0 / 243.4 tok/s at one, two,
  four and eight requests (Spark 63.2 / 81.9 / 104.7 / 144.1). The gap grows
  with concurrency, where SparkInkling stops drafting.
- **Drafts help one or two requests at a time.** From three live requests the
  engine decodes plainly, in a batch (0.5.0's Spark from two).
  On RigMark's short requests (256 tokens, reasoning low) drafting in a batch
  lost: Strict three drafts each at four requests read 76.3 tok/s against 86.0
  plain, Spark three each at two 70.2 against 77.4, on a development build of
  the pinned engine. On longer answers the same settings gained (Strict up to
  six requests, Spark two;
  [tuning](../results/2026-11-25-dflash2-tuning/RESULT.md)); the engine's
  per-sequence threshold does not yet weigh a draft against how cheap a plain
  batched step is. vLLM's Inkling 2 Mini image drafts under load and is ahead
  at four and eight requests: 106.6 and 156.4 tok/s against Spark's 104.7 and
  144.1 and Strict's 85.6 and 126.4
  ([issue 1](https://github.com/Enntity/sparkinkling/issues/1)).
- **Drafts help prose little.** The target accepts about one draft in two on
  prose. Strict keeps drafting there (a block that accepts one token is worth
  it against Strict's slower plain step), and in 0.5.0 its prose decode rose
  from 35.3 to 39.6 tok/s (RigMark 1.1.0); Spark turns drafts off on prose, and its prose lead over
  vLLM comes from its weights, not from drafts.
- **Strict is slightly behind vLLM's drafter on code and structured
  output**: 68.7 against 70.8 tok/s on code and 102.3 against 104.3 on
  structured output, and behind it at two, four and eight requests. It leads
  vLLM on prose (40.2 against 31.1), at one request and in prefill.
- **There is no thinking-off mode.** Inkling 2 Mini always reasons a little:
  `chat_template_kwargs.enable_thinking: false` is read as reasoning effort
  `none`, at which the model still reasons and SparkInkling streams none of
  it. On a short prompt that is about 200 tokens before the answer; on
  SparkModelBench's ~16K-token field guide it was 1,329, so a client
  that sends a long prompt with thinking off and a small `max_tokens` can get
  no visible text.
- **One Spark.** The image refuses multi-rank flags. The measurements were
  taken with nothing else serving on the Spark; other GPU work on the same
  machine slows it.

## Fidelity

- **Text with drafts matched text without them in our check, not by proof.**
  A verify run attends exactly as a decode row does, and on 8 prompts of 320
  tokens (4 code, 4 prose, reasoning low) greedy text on the release image
  with the drafter on, at one, two and four requests, was identical to one
  request with it off, in both modes. That is a small sample;
  `DRAFTER=none` remains the way to rule the drafter out.
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
  streamed every request's calls; since 0.4.2 they are held unless asked.
- **Streamed `return_token_ids` carry rewritten ids** for Inkling's message
  markers, not the model's raw tokens.

## Memory and context

- **KV is about 32 KiB a token** (the 8 global layer visits; the 40
  sliding-window visits keep only their last 1,024 tokens), so one Spark holds
  the model's 1M-token context. `default` and `max` accept requests of up to
  1,048,576 tokens over pools of 1.75M to 1.97M tokens, and `saver` up to
  786,432 over 800K to 965K: two full-length requests cannot be resident
  together, and requests the pool cannot hold wait for blocks. The 1M-token
  recall check is one prompt (a code a third of the way into 1,032,929
  tokens, Spark mode), not a long-context benchmark.
- **A 1M-token prompt is slow**: about 21 minutes to answer (1,253 s) (attention over
  the 8 global visits grows with the square of the context), and decode at
  that length reads about 32 GiB of KV a token.
- **No disk tier for the prefix cache.** 0.4.x could keep evicted prefix-cache
  KV on disk (`PREFIX_CACHE_DIR`); the engine's disk tier needs full-length KV,
  which would cost 1M-token context, so 0.5.0 removed the setting. A
  conversation pushed out of the pool is prefilled again when it returns.
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
