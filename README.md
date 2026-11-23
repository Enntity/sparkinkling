<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<p align="center">
  <img src="docs/assets/banner.png" alt="SparkInkling: Inkling 2 Mini on one NVIDIA DGX Spark with the Atlas engine. High scores in tokens per second, Strict (./start.sh) and Spark (--mode spark): code 54.2 and 68.4, prose 35.0 and 54.9, eight requests 121.0 and 135.2. 32K prefill 3,283 tok/s, 6 of 6 output gates. SparkInkling 0.4.1, RigMark 1.1.0, low effort." width="100%">
</p>

# SparkInkling

**SparkInkling 0.4.1.** Run `./start.sh --version` for this checkout, or
`./start.sh status` for the version and image of a running server.

Thinking Machines' [Inkling 2 Mini](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
on one NVIDIA DGX Spark, served by the [Atlas](https://github.com/Atlas-Inf/atlas)
engine with an OpenAI-compatible API, image input, reasoning and tool calls.

0.4.1 adds image input, ends Inkling's reasoning loops (the engine closes a
reasoning block that runs past its effort's budget or repeats itself, and a
request that names no effort reasons at `low`), streams tool-call arguments
while the tool guard still checks every call, and lets a client that rebuilds
its last messages each turn resume from the prefix cache. Spark is ahead of
vLLM's own Inkling 2 Mini image without speculation in every measured cell
(1.95x on code, 1.54x on prose, 1.2x on 32K prefill), and Strict, the
checkpoint as shipped, is ahead on code, structured output, prefill and one
request and within 1-3% of it on prose and two to eight short-code requests.
See [Performance](#performance); every result has its receipts under
[`results/`](results/).

## The model

Inkling 2 Mini (Apache-2.0) is a looped mixture-of-experts transformer: 26.4B
parameters, 3.4B active, 24 decoder layers whose middle 12 run three times per
token (48 layer visits), 128 experts with top-8 routing, hybrid sliding-window
and full attention without RoPE, text and image input, and up to 1M tokens of
context. Thinking Machines ships it as one ~20 GB checkpoint with NVFP4 and
MXFP8 experts and BF16 everything else, plus a bundled DSpark draft model.

SparkInkling serves text and images. Video is not supported.

## Strict and Spark modes

| | Strict (default) | Spark |
|---|---|---|
| Weights | The checkpoint as shipped: NVFP4 experts in layers 0-19, MXFP8 experts in 20-23, BF16 attention, router and vocabulary head | Strict plus a calibrated NVFP4 overlay for the attention projections, the vocabulary head and the experts of layers 20-23 |
| Start | `./start.sh` (or `--mode strict`) | `./start.sh --mode spark` |
| Extra download | none | [`Enntity/Inkling-2-Mini-Spark-NVFP4`](https://huggingface.co/Enntity/Inkling-2-Mini-Spark-NVFP4), 2.9 GB |
| Fidelity | the checkpoint's own numerics | KL 0.0081 to Strict's weights (97.0% top-1 agreement, 224 held-out documents) |

Spark reads about half the bytes a token reads in Strict. [The modes in
detail](docs/MODES.md).

## Performance

Measured on the 0.4.1 image with RigMark (reasoning low, temperature 0), one
Spark, the default profile and drafter, against vLLM's own Inkling 2 Mini image
on the same Spark: [the result, with every receipt](results/2026-11-23-release-0.4.1/RESULT.md).

| | Strict | Spark | vLLM | vLLM + DSpark |
|---|---:|---:|---:|---:|
| Code decode, tok/s | 54.2 | **68.4** | 35.1 | 69.8 |
| Prose decode | 35.0 | **54.9** | 35.6 | 31.2 |
| Structured decode | 79.9 | **95.3** | 35.6 | 104.3 |
| 32K cold prefill, tok/s | **3,283** | **3,274** | 2,722 | 2,723 |
| Short code, C1 / C2 / C4 / C8 aggregate | 36.8 / 53.4 / 84.5 / 121.0 | **51.6 / 76.1 / 105.4 / 135.2** | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| 32K prompt sent again, time to first token | 0.16 s | 0.15 s | | |
| Basic output gates | 6/6 | 6/6 | 6/6 | 6/6 |

Spark leads vLLM without speculation everywhere and vLLM with its drafter on
prose, prefill and one to four requests; vLLM's drafter is ahead on code,
structured output and eight requests. Strict reads the checkpoint's BF16
attention weights as shipped, about twice the bytes a Spark token reads.
SparkInkling drafts only while one request is live
([issue 1](https://github.com/Enntity/sparkinkling/issues/1)); vLLM's drafter
also runs under load.
Prefix caching costs a cold prompt of 512 tokens or more one short extra pass
(about 0.1 s: about 2% at 32K and 5-6% at 8K against 0.3.0), which is what lets the
next turn resume. The vLLM receipts were measured the day before.

## Quick start

```sh
git clone https://github.com/Enntity/sparkinkling.git
cd sparkinkling
cp .env.example .env      # optional: every setting has a default
./start.sh
```

## Requirements

- One DGX Spark (GB10, 128 GB unified memory) with Docker and the NVIDIA
  runtime.
- About 25 GB free for the checkpoint, plus 2.9 GB for Spark mode's overlay.
- The default profile takes 0.80 of GPU memory; leave the rest for the host
  and anything else it runs.

## What `./start.sh` does

Each step is skipped when already done, so rerunning it just restarts the
engine.

1. **Image.** Pulls `ghcr.io/enntity/atlas-sparkinkling:<tag>`, where the tag
   is the git tree of [`install/`](install/), so the image always matches your
   checkout. If that tag is not published, it builds the image
   from source ([`install/build.sh`](install/build.sh): Atlas at the commit
   and tree pinned in [`install/atlas-source.json`](install/atlas-source.json),
   for the `inkling-2-mini` kernel target; 30-60 minutes cold).
2. **Weights.** Downloads
   [`thinkingmachines/Inkling-2-Mini`](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
   at revision `ed40e7da625f` (pinned in
   [`install/checkpoint.json`](install/checkpoint.json)) and checks its weight
   and tokenizer files' sha256, then assembles the DSpark drafter's directory
   next to it ([`install/dspark_drafter.py`](install/dspark_drafter.py)). In
   Spark mode it also downloads and checks the overlay, then assembles the
   Spark model directory ([`install/spark_overlay.py`](install/spark_overlay.py)).
   It uses `hf` when installed and a throwaway container otherwise.
3. **Serve.** Starts the container, waits for health, then answers one
   smoke-test question.

Other commands: `./start.sh stop | status | logs | build | download`.

## Use it

The API listens on `http://127.0.0.1:8895/v1`, model `inkling-2-mini-atlas`,
with no authentication. Put your own authenticated proxy in front of it
before exposing it.

```sh
curl -s http://127.0.0.1:8895/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model": "inkling-2-mini-atlas", "max_tokens": 1024, "reasoning_effort": "low",
  "messages": [{"role": "user", "content": "Write a haiku about one small computer."}]}'
```

**Images** go in as OpenAI `image_url` parts with a base64 `data:` URI (PNG,
JPEG, WebP, GIF, BMP, TIFF):

```sh
curl -s http://127.0.0.1:8895/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model": "inkling-2-mini-atlas", "max_tokens": 1024,
  "messages": [{"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,'"$(base64 -w0 photo.png)"'"}},
    {"type": "text", "text": "What is in this picture?"}]}]}'
```

Inkling does not resize an image: each 40x40 pixel tile is one token, so a
1280x960 image is 768 tokens. An image of more than 1,600 tiles (about
1600x1600 pixels) is scaled down to fit, which the checkpoint's own processor
does not do. `http(s)` image URLs are refused unless the engine is started
with remote fetching allowed.

Reasoning comes back separately from the answer. `reasoning_effort` (`none`,
`minimal`, `low`, `medium`, `high`, `xhigh`) is passed to the model's own
template; a request that names none reasons at `low`. The template's own
default, `high`, often reasons in loops at temperature 0 (the model card warns
of it): on 150 MMLU-Pro questions with an 8,192-token cap, `high` scored 107
with 30 answers cut off, `medium` 120 with 8 and `low` 125 with 2. The model
always thinks a little, even at `none`, so leave room in `max_tokens`. Tool calls (OpenAI `tools`, streaming
included) are returned as OpenAI tool calls. The tool-call guard SparkQwen and
SparkGLM ship is on by default (`TOOL_GUARD` in `.env`). Here it streams: a
call's arguments arrive as they are written and the guard checks the call
when it ends; a call it blocks finishes `content_filter`, not `tool_calls`.
`TOOL_GUARD=on` holds each call until it passes, as SparkQwen and SparkGLM do.

**Settings** (`.env`, see [`.env.example`](.env.example)): `MODE`, `PROFILE`
(below), `DRAFTER`, `GPU_MEMORY_UTILIZATION` (0.50-0.90), `PREFIX_CACHE_DIR`
and `PREFIX_CACHE_GB` (below), `MODEL_ROOT`, `PULL=0`.

### Profiles

| `PROFILE` | Requests | Tokens each | GPU memory | KV pool | Prefix-cache snapshots |
|---|---:|---:|---:|---:|---:|
| `default` | 8 | 131,072 | 0.80 | about 404K tokens | 128 |
| `max` | 32 | 262,144 | 0.85 | about 446K tokens | 256 |
| `saver` | 8 | 131,072 | 0.50 | about 213K tokens | 64 |

All three keep BF16 KV, 4,096-token prefill chunks, prefix caching,
hour-long requests and up to 32,768 generated tokens a tool-calling request
(the model reasons before it calls). Requests the pool cannot hold yet wait
for blocks rather than fail. `saver` is the smallest footprint that still
serves eight full-length requests. In a check on 2026-11-21, `max` ran 32
concurrent short code requests to a normal stop and recalled a code hidden a
third of the way into a 182,100-token prompt (82 s for the prompt;
[receipts](results/2026-11-21-prefix-cache-and-profiles/RESULT.md)). A JSON file
of your own works too (`PROFILE=/path/to/profile.json`, same schema as
[`install/profiles/`](install/profiles/)).

### Prefix caching

A request that repeats an earlier prompt's beginning (a chat's next turn, a
shared system prompt) skips prefilling what the cache still holds. Inkling's
short convolutions carry state from token to token, so the cache saves each
visit's state (about 4.8 MB a sequence, in host memory) every 4,096 tokens and
at the end of each prompt, and a hit resumes from the deepest one it matches.
On a 7.5K-token prompt the time to first token went from about 2.4 s cold to
0.12 s warm, with byte-identical answers.

Some clients rebuild their last few messages every turn (a voice agent's
context blocks after the history). Each such turn forks from the previous
prompt before its end, so the cache also saves a state where a prompt forks
from a cached one by 512 tokens or more, and the next turn resumes there. On a
replay of a voice call (16-17K-token prompts, three rebuilt trailing messages)
the time to first token of a new turn went from 1.3-1.7 s to 0.6-0.8 s (one
run on a development build).

### Prefix cache on disk

When the KV pool fills, the prefix cache drops the conversations used least
recently, and one that comes back is prefilled again from the start. With
`PREFIX_CACHE_DIR` set, the engine writes the KV blocks it drops to that disk
instead and reads them back when the conversation returns; the engine tier
and settings are SparkQwen's and SparkGLM's.

```sh
PREFIX_CACHE_DIR=/srv/sparkinkling/prefix-cache
PREFIX_CACHE_GB=48                            # GiB, 16-100 (default 48)
```

`start.sh` creates `<mode>/kv/` in the directory, refuses one on tmpfs or
without that much space free, and mounts it into the container. KV takes
192 KiB a token (all 48 layer visits), so 48 GiB holds about 262K tokens. In one check on 2026-11-21 (Strict, a pool
held to 5,373 blocks, ~20K-token conversations pushed out by five others), a
returning conversation's time to first token went from 5.82 s to 0.90 s: the
engine read its 1,237 blocks back in 403 ms and resumed from the snapshot at
token 19,776, and the answer was identical to a run with the tier off
([receipts](results/2026-11-21-prefix-cache-and-profiles/RESULT.md)).
The engine takes the tier's staging buffers and on-disk index out of the KV
pool (388 MiB at 16 GiB). The state snapshots a restore starts from stay in
host memory: a conversation
comes back from disk while its snapshot is still among the profile's
snapshots. Nothing is kept across a restart: the engine deletes its files as
soon as it has them open, and clears a crash's leftovers when it starts.

## Speculative decoding

Both modes run the checkpoint's bundled DSpark drafter by default
(`DRAFTER=dspark`): it proposes seven tokens a step and the mode's own weights
verify them, so it changes speed, not the model. It speculates while one
request is live; from two requests the engine decodes plainly, which delivers
more there. And only while it pays: a request whose drafts average under two
accepted a step decodes plainly and re-probes 256 tokens later, so code and
structured output speculate and prose mostly does not. `DRAFTER=none` turns
it off.

## Other ways to run it

**By hand:** every step of `./start.sh` as a separate command, in
[docs/INSTALL-MANUAL.md](docs/INSTALL-MANUAL.md).

## The engine

SparkInkling builds Atlas from
[`Enntity/atlas`](https://github.com/Enntity/atlas) `inkling2/mini-20261121`,
the Inkling 2 Mini serving series on Atlas-Inf `main`, pinned by commit and
tree in [`install/atlas-source.json`](install/atlas-source.json), and proposed
upstream as [Atlas-Inf/atlas#401](https://github.com/Atlas-Inf/atlas/pull/401),
[#404](https://github.com/Atlas-Inf/atlas/pull/404) and
[#405](https://github.com/Atlas-Inf/atlas/pull/405).
What the branch adds and what it does not do yet:
[docs/ENGINE.md](docs/ENGINE.md).

## Credits

Inkling 2 Mini and its DSpark draft model are by Thinking Machines Lab
(Apache-2.0). Measurement uses [RigMark](https://github.com/alexellis/rigmark)
by Alex Ellis (MIT). The launcher and install directory are adapted from
[SparkQwen](https://github.com/Enntity/sparkqwen) and
[SparkGLM](https://github.com/Enntity/sparkglm).

## License

AGPL-3.0-only ([LICENSE](LICENSE)); third-party components keep their own
licenses ([NOTICE](NOTICE)). The model weights are not distributed here; check
the checkpoint's model card before downloading.
