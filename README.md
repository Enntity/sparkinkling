<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<p align="center">
  <img src="docs/assets/banner.png" alt="SparkInkling: Inkling 2 Mini on one NVIDIA DGX Spark with the Atlas engine. Strict mode serves the checkpoint as shipped (./start.sh --mode strict); Spark mode adds a calibrated NVFP4 overlay (./start.sh --mode spark)." width="100%">
</p>

# SparkInkling

**SparkInkling 0.2.0.** Run `./start.sh --version` for this checkout, or
`./start.sh status` for the version and image of a running server.

Thinking Machines' [Inkling 2 Mini](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
on one NVIDIA DGX Spark, served by the [Atlas](https://github.com/Atlas-Inf/atlas)
engine with an OpenAI-compatible API, reasoning and tool calls.

0.2.0 prefills a 32K-token prompt in 10 s, 1.2x vLLM, by running the
checkpoint's experts at its declared low-precision numerics on the
block-scaled tensor cores. Both modes, the checkpoint's own DSpark drafter, and
measured results with their receipts are under [`results/`](results/); vLLM
still leads most decode cells, see [Performance](#performance).

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
| Fidelity | the checkpoint's own numerics | KL 0.0081 to Strict's weights (97.0% top-1 agreement, 224 held-out documents) |

Spark reads about half the bytes a token reads in Strict. [The modes in
detail](docs/MODES.md).

## Performance

Measured on the 0.2.0 image with RigMark (reasoning low, temperature 0), one
Spark, the default profile and drafter, against vLLM's own Inkling 2 Mini image
on the same Spark: [the result, with every receipt](results/2026-11-21-release-0.2.0/RESULT.md).

| | Strict | Spark | vLLM | vLLM + DSpark |
|---|---:|---:|---:|---:|
| 32K cold prefill, tok/s | **3,271** | **3,128** | 2,722 | 2,723 |
| Code decode, tok/s | 50.0 | 60.9 | 35.1 | 69.8 |
| Prose decode | 22.8 | 25.7 | 35.6 | 31.2 |
| Structured decode | 79.5 | 87.3 | 35.6 | 104.3 |
| Short code, C1 / C2 / C4 / C8 aggregate | 32.0 / 44.1 / 72.2 / 105.3 | 35.8 / 63.1 / 90.0 / 115.5 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / 144.0 |
| Basic output gates | 6/6 | 5/6 | 6/6 | 6/6 |

Prefill leads vLLM in both modes (0.1.0: 1,455 tok/s at 32K in Strict). Code
and structured output decode faster than vLLM without speculation; vLLM with
its DSpark drafter is still faster on every decode workload. Prose is the
drafter's weak case (few drafts are accepted there): `DRAFTER=none` decodes it
at about 30 tok/s in Strict. Spark's missing gate is one code answer that
reasoned past RigMark's 4,096-token allowance. The vLLM receipts were measured
the day before.

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

Reasoning comes back separately from the answer. `reasoning_effort` (`none`,
`minimal`, `low`, `medium`, `high`, `xhigh`) is passed to the model's own
template; without it the template's default applies. The model always thinks
a little, so leave room in `max_tokens`. Tool calls (OpenAI `tools`, streaming
included) are returned as OpenAI tool calls. The tool-call guard SparkQwen and
SparkGLM ship is on by default (`TOOL_GUARD` in `.env`).

**Settings** (`.env`, see [`.env.example`](.env.example)): `MODE`, `PROFILE`
(the one shipped profile, `default`: 8 concurrent requests of up to 131,072
tokens at 0.80 of GPU memory, or a JSON file of your own), `DRAFTER`,
`GPU_MEMORY_UTILIZATION` (0.50-0.90), `MODEL_ROOT`, `PULL=0`. At 0.80 the KV
pool holds about 404K tokens (three full-length requests); more wait for
blocks rather than fail.

## Speculative decoding

Both modes run the checkpoint's bundled DSpark drafter by default
(`DRAFTER=dspark`): it proposes seven tokens a step and the mode's own weights
verify them, so it changes speed, not the model. It speculates while one
request is live; from two requests the engine decodes plainly, which delivers
more there. It pays on code and structured output and costs on prose (few
drafts are accepted there); `DRAFTER=none` turns it off.

## Other ways to run it

**By hand:** every step of `./start.sh` as a separate command, in
[docs/INSTALL-MANUAL.md](docs/INSTALL-MANUAL.md).

## The engine

SparkInkling builds Atlas from
[`Enntity/atlas`](https://github.com/Enntity/atlas) `inkling2/mini-20261121`,
the Inkling 2 Mini serving series on Atlas-Inf `main`, pinned by commit and
tree in [`install/atlas-source.json`](install/atlas-source.json), and proposed
upstream as [Atlas-Inf/atlas#401](https://github.com/Atlas-Inf/atlas/pull/401).
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
