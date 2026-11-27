<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<p align="center">
  <img src="docs/assets/banner.png" alt="SparkInkling: Inkling 2 Mini on one NVIDIA DGX Spark with the Atlas engine. High scores in tokens per second, Spark (./start.sh, the default) and Strict (--mode strict): code 88.2 and 68.7, structured output 129.9 and 102.3, eight requests 144.1 and 126.4. 1M-token context, 32K prefill 5,024 tokens per second, 15 of 15 output gates. SparkInkling 0.5.1, SparkModelBench, low effort." width="100%">
</p>

# SparkInkling

**SparkInkling 0.5.1.** Run `./start.sh --version` for this checkout, or
`./start.sh status` for the version and image of a running server.

Thinking Machines' [Inkling 2 Mini](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
on one NVIDIA DGX Spark, served by the [Atlas](https://github.com/Atlas-Inf/atlas)
engine with an OpenAI-compatible API, image input, reasoning and tool calls.

0.5.1 is a speed release: the same weights, drafter and context as 0.5.0,
on a faster engine. A cold 32K-token prompt prefills about 1.5x as fast as on
0.5.0 (5,024 tok/s in Spark), and Spark decodes code at 88.2 tok/s,
structured output at 129.9 and eight concurrent code requests at 144.1 in
aggregate. Spark mode, SparkInkling's calibrated NVFP4 overlay, is the
default. Requests run to 1,048,576 tokens: the 40 sliding-window layer visits
keep only their last 1,024 tokens, so a token of context costs 32 KiB, and the
default profile's pool holds about 1.79M tokens in Spark mode. Greedy text
with the drafter on matched text with it off in our checks. The figures are
[SparkModelBench](https://github.com/enntity/sparkmodelbench)'s, which runs
Alex Ellis's RigMark and RigMark Quality. On the same Spark, Spark mode leads
vLLM's own Inkling 2 Mini image with its DSpark drafter on decode and prefill
and trails it at four and eight requests; knapcio's SGLang recipe leads
SparkInkling on decode, prefill to 128K and every concurrency. See
[Performance](#performance); every result has its receipts under
[`results/`](results/).

## The model

Inkling 2 Mini (Apache-2.0) is a looped mixture-of-experts transformer: 26.4B
parameters, 3.4B active, 24 decoder layers whose middle 12 run three times per
token (48 layer visits), 128 experts with top-8 routing, hybrid sliding-window
and full attention without RoPE, text and image input, and up to 1M tokens of
context. Thinking Machines ships it as one ~20 GB checkpoint with NVFP4 and
MXFP8 experts and BF16 everything else, plus a bundled DSpark draft model.

SparkInkling serves text and images. Video is not supported.

## Spark and Strict modes

| | Spark (default) | Strict |
|---|---|---|
| Weights | The checkpoint plus a calibrated NVFP4 overlay for the attention projections, the vocabulary head and the experts of layers 20-23 | The checkpoint as shipped: NVFP4 experts in layers 0-19, MXFP8 experts in 20-23, BF16 attention, router and vocabulary head |
| Start | `./start.sh` (or `--mode spark`) | `./start.sh --mode strict` |
| Extra download | [`Enntity/Inkling-2-Mini-Spark-NVFP4`](https://huggingface.co/Enntity/Inkling-2-Mini-Spark-NVFP4), 2.9 GB | none |
| Fidelity | KL 0.0081 to Strict's weights (97.0% top-1 agreement, 224 held-out documents) | the checkpoint's own numerics |

Spark reads about half the bytes a token reads in Strict and decodes faster
in every measured cell. Strict is there when you want the checkpoint's own
numerics. [The modes in detail](docs/MODES.md).

## Performance

Measured on the 0.5.1 release candidate with
[SparkModelBench](https://github.com/enntity/sparkmodelbench) `293a44f`
(RigMark protocol 1.3.0 and RigMark Quality v0.0.2, reasoning low, temperature
0, medians of every repetition), one Spark with nothing else serving, the
default profile and drafter:
[the result, with every receipt](results/2026-11-27-rc-0.5.1/RESULT.md). The
release image differs from the measured one only in the profiles' notes, and
its greedy text was the same.

Beside it, on the same Spark and SparkModelBench commit: vLLM's own Inkling 2
Mini image with the checkpoint's DSpark drafter, and
[knapcio's recipe](https://github.com/knapcio/Inkling-2-Mini-1x-DGX-Spark)
v2.9.7 (SGLang with its overlays and the DFlash2 drafter), both serving the
checkpoint as shipped with their own settings and a 270,336-token context
([the result](results/2026-11-27-smb-competitors/RESULT.md), which also
lists how its window differed from SparkInkling's).

| | Spark | Strict | vLLM + DSpark | knapcio v2.9.7 |
|---|---:|---:|---:|---:|
| Code decode, tok/s | 88.2 | 68.7 | 70.8 | **97.8** |
| Prose decode | 57.0 | 40.2 | 31.1 | **59.7** |
| Structured decode | 129.9 | 102.3 | 104.3 | **147.7** |
| Cold prefill 8K, tok/s (time to first token) | 5,174 (1.58 s) | 5,137 (1.59 s) | 2,862 (2.86 s) | **5,818** (1.41 s) |
| 32K | 5,024 (6.52 s) | 4,918 (6.66 s) | 2,735 (11.98 s) | **5,399** (6.07 s) |
| 128K | 3,781 (34.67 s) | 3,779 (34.69 s) | 2,083 (62.91 s) | **3,973** (32.99 s) |
| 256K | **2,824** (92.81 s) | **2,827** (92.71 s) | 1,586 (165.31 s) | 2,815 (93.14 s) |
| Same prompt sent again, 32K / 256K, time to first token | **0.15 / 0.36 s** | 0.16 / 0.37 s | 0.16 / 0.41 s | 1.69 / 4.62 s |
| Code, aggregate at 1 / 2 / 4 / 8 requests | 63.2 / 81.9 / 104.7 / 144.1 | 48.1 / 65.6 / 85.6 / 126.4 | 43.6 / 69.2 / 106.6 / 156.4 | **68.9 / 99.2 / 152.0 / 243.4** |
| Decode gates | 15/15 | 15/15 | 15/15 | 15/15 |
| RigMark Quality, tasks passed | 3/4 | 3/4 | **4/4** | 3/4 |
| Longest request | **1,048,576** | **1,048,576** | 270,336 as run | 270,336 as run |

Against 0.5.0, cold 32K prefill is 1.53x in Spark and 1.50x in Strict. The
prefill workload is the same in both RigMark protocols and the decode
workloads are not, so decode is not compared across them.

- **knapcio leads.** Spark reaches 0.90x its code decode, 0.96x prose and
  0.88x structured, 0.93x its 32K prefill and is level at 256K; at one, two,
  four and eight requests it reaches 0.92x, 0.83x, 0.69x and 0.59x. Spark
  starts a prompt it has just seen more than 10x sooner and serves 1M-token
  requests.
- **Against vLLM + DSpark**, Spark leads decode (1.25x code, 1.83x prose,
  1.25x structured), prefill at every depth (1.84x at 32K) and one and two
  requests, and trails at four (0.98x) and eight (0.92x) requests.
- **RigMark Quality** ran once per engine; only vLLM passed
  `go-transfer-ledger`'s acceptance check, the others passed its public tests.
- **SparkModelBench's staggered four-request lane does not apply**: it asks
  for thinking off, which Inkling 2 Mini does not have
  ([why](results/2026-11-27-rc-0.5.1/RESULT.md#the-staggered-c4-lane-does-not-apply-to-inkling)).

### 0.5.0 against vLLM (RigMark 1.1.0)

Measured on the 0.5.0 image with RigMark (reasoning low, temperature 0), one
Spark, the default profile and drafter, against 0.4.2 and vLLM's own Inkling 2
Mini image on the same Spark:
[the result, with every receipt](results/2026-11-25-release-0.5.0/RESULT.md).

| | Spark | Strict | Spark 0.4.2 | Strict 0.4.2 | vLLM | vLLM + DSpark |
|---|---:|---:|---:|---:|---:|---:|
| Code decode, tok/s | **81.4** | 70.0 | 77.5 | 65.2 | 35.1 | 69.8 |
| Prose decode | **56.1** | 39.6 | 55.7 | 35.3 | 35.6 | 31.2 |
| Structured decode | **117.4** | 103.2 | 103.6 | 92.6 | 35.6 | 104.3 |
| 32K cold prefill, tok/s | **3,282** | 3,268 | 3,277 | 3,274 | 2,722 | 2,723 |
| Short code, C1 / C2 / C4 / C8 aggregate | **58.8 / 77.8 / 103.5** / 135.2 | 46.5 / 62.6 / 85.7 / 122.7 | 53.9 / 77.7 / 105.8 / 135.4 | 41.3 / 63.1 / 85.0 / 120.7 | 35.1 / 54.0 / 86.6 / 122.4 | 43.4 / 60.9 / 94.7 / **144.0** |
| Short prose, C1 / C4 / C8 aggregate | **61.4 / 100.9 / 131.7** | 44.6 / 84.3 / 120.0 | 53.2 / 100.4 / 129.1 | 36.9 / 82.7 / 120.6 | 35.3 / 89.2 / 126.4 | 36.0 / 88.2 / 122.1 |
| 32K prompt sent again, time to first token | 0.15 s | 0.16 s | 0.16 s | 0.16 s | | |
| Longest request | 1,048,576 | 1,048,576 | 131,072 | 131,072 | | |
| Basic output gates | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

Spark leads vLLM without speculation everywhere, and vLLM with its drafter on
code (1.17x), prose (1.80x), structured output (1.13x), prefill (1.21x) and
one to four requests, and trails it at eight short-code requests (0.94x).
Strict reads the checkpoint's BF16 attention weights as shipped, about twice
the bytes a Spark token reads. 0.5.0 drafted for one live request in Spark,
or two in Strict, and decoded plainly from there: on these short requests
drafting in a batch lost (see [LIMITATIONS](docs/LIMITATIONS.md#speed)),
while vLLM's drafter gains under load. Prefix caching costs a cold prompt of
512 tokens or more one short extra pass (about 0.1 s), which is what lets the
next turn resume. The vLLM receipts were measured on 2026-11-20.

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
- About 25 GB free for the checkpoint and the DFlash2 drafter (1 GB), plus 2.9 GB for Spark mode's overlay.
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
   for the `inkling-2-mini` kernel target; the 0.5.0 image built in under
   5 minutes on a Spark with Docker's build cache warm, and a first build also
   downloads the CUDA base images).
2. **Weights.** Downloads
   [`thinkingmachines/Inkling-2-Mini`](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
   at revision `ed40e7da625f` (pinned in
   [`install/checkpoint.json`](install/checkpoint.json)) and checks its weight
   and tokenizer files' sha256, then downloads and checks the drafter,
   [`incoai/Inkling-2-Mini-DFlash2`](https://huggingface.co/incoai/Inkling-2-Mini-DFlash2)
   at revision `4f9088ea66c2` (about 1 GB). In
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
SparkGLM ship is on by default (`TOOL_GUARD` in `.env`), and holds each call
until its complete arguments pass. A request that sends
`stream_tool_arguments: true` gets its calls' arguments as they are written
instead; the guard then checks each call when it ends, and a call it blocks
finishes `content_filter`, not `tool_calls`, which such a client must not run
([docs/TOOL-GUARD.md](docs/TOOL-GUARD.md)).

**Settings** (`.env`, see [`.env.example`](.env.example)): `MODE`, `PROFILE`
(below), `DRAFTER`, `GPU_MEMORY_UTILIZATION` (0.50-0.92),
`MODEL_ROOT`, `PULL=0`, and `LOOPCD`, an opt-in that trades decode speed for
fewer reasoning loops at high effort ([docs/LOOPCD.md](docs/LOOPCD.md)), off
by default.

### Profiles

| `PROFILE` | For | Requests | Tokens each | GPU memory | KV pool, Spark (Strict) |
|---|---|---:|---:|---:|---:|
| `default` | One Spark, general use | 8 | 1,048,576 | 0.80 | 1.79M tokens (1.91M) |
| `max` | A Spark of its own: everything on, the most memory | 32 | 1,048,576 | 0.92 | about 1.96M (2.12M) |
| `saver` | A Spark shared with embeddings, speech or image services | 8 | 1,048,576 | 0.60 | about 1.09M (1.22M) |
| `swarm` | Many shorter conversations at once | 64 | 131,072 | 0.90 | about 1.56M (1.76M) |

`default`'s pools were read from the 0.5.1 release run's server. The others
are estimates from the engine's own budget arithmetic in that run's logs, not
yet read from a server running them. Every profile but `swarm` serves the
model's whole 1,048,576-token window, and each pool holds at least one
full-length request. `max` at 0.92 is past what this product has run: 0.4.x
at 0.88 kept about 8 GB of host memory free under 32 concurrent requests.
`swarm`'s 64 requests have not been measured (32 have). All four keep BF16 KV, 8,192-token prefill chunks, prefix caching,
hour-long requests and up to 32,768 generated tokens a tool-calling request
(the model reasons before it calls). Requests the pool cannot hold yet wait
for blocks rather than fail. KV costs about 32 KiB a token: the 40
sliding-window layer visits keep only their last 1,024 tokens
([ENGINE](docs/ENGINE.md)). On the 0.5.0 candidate in Spark mode, a code
hidden a third of the way into a 1,032,929-token prompt was recalled (1,253 s
for the request). In a check on 2026-11-21, `max` ran 32
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

## Speculative decoding

Both modes run incoai's DFlash2 drafter for Inkling 2 Mini by default
(`DRAFTER=dflash2`,
[`incoai/Inkling-2-Mini-DFlash2`](https://huggingface.co/incoai/Inkling-2-Mini-DFlash2),
Apache-2.0): it proposes up to seven tokens a step and the mode's own weights
verify them, so it changes speed, not the model. It replaces the checkpoint's
bundled DSpark drafter, which 0.4.2 ran. Greedy text with the drafter on, at
one, two and four requests, matched text with it off in our check
([LIMITATIONS](docs/LIMITATIONS.md#fidelity)).

- **A verify stops where the drafter is unsure.** The drafter reports how
  confident it is in each draft, the engine learns while serving how often
  drafts at each confidence are accepted, and a step verifies only as far as
  the block is still likely right.
- **Drafts go off where they do not pay.** A request whose drafts stop being
  accepted decodes plainly for a short stretch (32 tokens at first, longer
  while re-probes keep failing), so code and structured output draft and
  prose mostly does not.
- **Concurrent requests.** Both modes draft three tokens each for two live
  requests and decode plainly, in a batch, from three (0.5.0's Spark drafted
  for one). The settings were tuned for this drafter
  ([results](results/2026-11-25-dflash2-tuning/RESULT.md)).

`DRAFTER=none` turns the drafter off.

## Reproduce our numbers

Every figure above has its commands, unedited receipts and checksums under
[`results/`](results/README.md). [docs/REPRODUCE.md](docs/REPRODUCE.md) is how
to run the same SparkModelBench suite (pinned here as
[`bench/sparkmodelbench`](bench/sparkmodelbench)) and the functional check on
your own Spark.
What SparkInkling does not do, and what its evidence does not cover, is in
[docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Other ways to run it

**By hand:** every step of `./start.sh` as a separate command, in
[docs/INSTALL-MANUAL.md](docs/INSTALL-MANUAL.md).

**Versions:** how releases are numbered and identified, in
[docs/VERSIONING.md](docs/VERSIONING.md).

## The engine

SparkInkling builds Atlas from
[`Enntity/atlas`](https://github.com/Enntity/atlas)
`inkling2/rc-0.5.1-20261126` (`inkling2/rc-0.5.0-20261124` plus the opt-in
LoopCD commit and nine speed commits), the Inkling 2 Mini serving series on
Atlas-Inf `main`, pinned by commit and tree in
[`install/atlas-source.json`](install/atlas-source.json). The first two parts
are in Atlas upstream
([Atlas-Inf/atlas 401](https://github.com/Atlas-Inf/atlas/pull/401) and
[404](https://github.com/Atlas-Inf/atlas/pull/404), merged 2026-11-23); the
next are proposed as [414](https://github.com/Atlas-Inf/atlas/pull/414) to
[418](https://github.com/Atlas-Inf/atlas/pull/418) and
[408](https://github.com/Atlas-Inf/atlas/pull/408) (a draft), and the two
closure-attestation fixes as [419](https://github.com/Atlas-Inf/atlas/pull/419)
and [420](https://github.com/Atlas-Inf/atlas/pull/420). Window-bounded KV and
the DFlash2 drafter and LoopCD are not proposed upstream yet.
What the branch adds and what it does not do yet:
[docs/ENGINE.md](docs/ENGINE.md).

## Credits

Inkling 2 Mini and its DSpark draft model are by Thinking Machines Lab
(Apache-2.0). The DFlash2 draft model is by Inco AI (Apache-2.0). Measurement uses
[SparkModelBench](https://github.com/enntity/sparkmodelbench), which runs
[RigMark](https://github.com/alexellis/rigmark) and
[RigMark Quality](https://github.com/alexellis/rigmark-quality) by Alex Ellis,
OpenFaaS Ltd (MIT). The launcher and install directory are adapted from
[SparkQwen](https://github.com/Enntity/sparkqwen) and
[SparkGLM](https://github.com/Enntity/sparkglm).

## License

AGPL-3.0-only ([LICENSE](LICENSE)); third-party components keep their own
licenses ([NOTICE](NOTICE), [docs/LICENSING.md](docs/LICENSING.md)). The model weights are not distributed here; check
the checkpoint's model card before downloading.
