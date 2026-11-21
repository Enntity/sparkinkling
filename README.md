<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<p align="center">
  <img src="docs/assets/banner.png" alt="SparkInkling: Inkling 2 Mini on one NVIDIA DGX Spark with the Atlas engine. Strict mode serves the checkpoint as shipped (./start.sh --mode strict); Spark mode adds a calibrated NVFP4 overlay (./start.sh --mode spark). In development; no measured claims yet." width="100%">
</p>

# SparkInkling

**SparkInkling 0.1.0, in development.** Run `./start.sh --version` for this
checkout, or `./start.sh status` for the version and image of a running server.

Thinking Machines' [Inkling 2 Mini](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
on one NVIDIA DGX Spark, served by the [Atlas](https://github.com/Atlas-Inf/atlas)
engine with an OpenAI-compatible API, reasoning and tool calls.

There is no release, published image or qualified result yet. The launcher,
the engine pin and the checkpoint pin are here; the performance section below
is a placeholder until a measured result lands under [`results/`](results/).

## The model

Inkling 2 Mini (Apache-2.0) is a looped mixture-of-experts transformer: 26.4B
parameters, 3.4B active, 24 decoder layers whose middle 12 run three times per
token (48 layer visits), 128 experts with top-8 routing, hybrid sliding-window
and full attention without RoPE, text and image input, and up to 1M tokens of
context. Thinking Machines ships it as one ~20 GB checkpoint with NVFP4 and
MXFP8 experts and BF16 everything else, plus a bundled DSpark draft model.

SparkInkling serves text only for now: the engine target has no vision tower.

## Strict and Spark modes

| | Strict (default) | Spark |
|---|---|---|
| Weights | The checkpoint as shipped: NVFP4 experts in layers 0-19, MXFP8 experts in 20-23, BF16 attention, router and vocabulary head | Strict plus a calibrated NVFP4 overlay for the attention projections, the vocabulary head and the experts of layers 20-23 |
| Start | `./start.sh` (or `--mode strict`) | `./start.sh --mode spark` |
| Extra download | none | [`Enntity/Inkling-2-Mini-Spark-NVFP4`](https://huggingface.co/Enntity/Inkling-2-Mini-Spark-NVFP4), 2.9 GB |
| Status | in development | in development; refused until the overlay is published and pinned |

Spark reads about half the bytes a token reads in Strict, and it changes the
model's numerics, so it ships only after it is measured against a BF16
reference and against Strict on the same image. [The modes in
detail](docs/MODES.md).

## Performance

Not measured yet. The table is a placeholder for the first RigMark result
([method](docs/BENCHMARKS.md)); every figure will link to its raw receipts.

| Mode | C1 code decode | C1 prose decode | C2 / C4 / C8 aggregate | 32K prefill | TTFT |
|---|---:|---:|---:|---:|---:|
| Strict | — | — | — | — | — |
| Spark | — | — | — | — | — |
| vLLM | — | — | — | — | — |

The vLLM baseline is to be measured on the same Spark with RigMark.

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
- About 25 GB free for the checkpoint, plus 2.9 GB for Spark mode's overlay,
  and room for the image build (no image is published yet).
- The default profile takes 0.80 of GPU memory; leave the rest for the host
  and anything else it runs.

## What `./start.sh` does

Each step is skipped when already done, so rerunning it just restarts the
engine.

1. **Image.** Pulls `ghcr.io/enntity/atlas-sparkinkling:<tag>`, where the tag
   is the git tree of [`install/`](install/), so the image always matches your
   checkout. If that tag is not published (none is yet), it builds the image
   from source ([`install/build.sh`](install/build.sh): Atlas at the commit
   and tree pinned in [`install/atlas-source.json`](install/atlas-source.json),
   for the `inkling-2-mini` kernel target; 30-60 minutes cold).
2. **Weights.** Downloads
   [`thinkingmachines/Inkling-2-Mini`](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
   at revision `ed40e7da625f` (pinned in
   [`install/checkpoint.json`](install/checkpoint.json)) and checks its weight
   and tokenizer files' sha256. In Spark mode it also downloads and checks
   the overlay, then assembles the Spark model directory next to the
   checkpoint ([`install/spark_overlay.py`](install/spark_overlay.py)). It
   uses `hf` when installed and a throwaway container otherwise.
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

Reasoning comes back separately from the answer. `reasoning_effort` (`none`,
`minimal`, `low`, `medium`, `high`, `xhigh`) is passed to the model's own
template; without it the template's default applies. The model always thinks
a little, so leave room in `max_tokens`. Tool calls (OpenAI `tools`, streaming
included) are returned as OpenAI tool calls. The tool-call guard SparkQwen and
SparkGLM ship is on by default (`TOOL_GUARD` in `.env`); it has not yet been
checked against Inkling's tool format.

**Settings** (`.env`, see [`.env.example`](.env.example)): `MODE`, `PROFILE`
(the one shipped profile, `default`: 8 concurrent requests of up to 131,072
tokens, not yet sized or qualified, or a JSON file of your own),
`GPU_MEMORY_UTILIZATION` (0.50-0.90), `MODEL_ROOT`, `PULL=0`.

## Speculative decoding

The checkpoint's bundled DSpark draft model is downloaded with it but not
used yet: the pinned engine has no DSpark drafter. `DRAFTER=none` is the only
accepted value until a pinned engine runs it; `DRAFTER=dspark` is reserved
for that.

## Other ways to run it

**By hand:** every step of `./start.sh` as a separate command, in
[docs/INSTALL-MANUAL.md](docs/INSTALL-MANUAL.md).

## The engine

SparkInkling builds Atlas from
[`Enntity/atlas`](https://github.com/Enntity/atlas) `inkling2/mini-20261121`,
the Inkling 2 Mini serving series on Atlas-Inf `main`, pinned by commit and
tree in [`install/atlas-source.json`](install/atlas-source.json). The pin will
move before the first release, and the series goes upstream to Atlas-Inf.
What the branch adds and what it does not do yet:
[docs/ENGINE.md](docs/ENGINE.md).

## Credits

Inkling 2 Mini and its DSpark draft model are by Thinking Machines Lab
(Apache-2.0). Measurement will use [RigMark](https://github.com/alexellis/rigmark)
by Alex Ellis (MIT). The launcher and install directory are adapted from
[SparkQwen](https://github.com/Enntity/sparkqwen) and
[SparkGLM](https://github.com/Enntity/sparkglm).

## License

AGPL-3.0-only ([LICENSE](LICENSE)); third-party components keep their own
licenses ([NOTICE](NOTICE)). The model weights are not distributed here; check
the checkpoint's model card before downloading.
