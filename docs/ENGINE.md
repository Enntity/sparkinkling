<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The engine

SparkInkling runs [Atlas](https://github.com/Atlas-Inf/atlas), built from
[Enntity/atlas](https://github.com/Enntity/atlas)
`inkling2/rc-0.5.1-20261126` at
the commit pinned in [`install/atlas-source.json`](../install/atlas-source.json):
`859bcf025` (tree `499212c9`), which is `inkling2/rc-0.5.0-20261124`
(`1559aa4bc`) plus one opt-in commit, LoopCD (below), and eight speed commits
(prefill kernels, Spark decode projections, the prefill scheduler; below), for the kernel target `inkling-2-mini`
(`ATLAS_TARGET_HW=gb10`, `ATLAS_TARGET_QUANT=nvfp4`, model type
`inkling2_loop`). [`install/build.sh`](../install/build.sh) fetches exactly that
commit, refuses any other tree, and takes the kernel target from the same
file. The pin moves only in `install/atlas-source.json` and on this page.

The series went upstream as stacked pull requests. The first two are merged
into Atlas-Inf `main` (401, the serving series, and 404, budget forcing and
streamed tool-call arguments). `inkling2/images-and-serving-20261123` is the
third (405: image input, the streaming tool guard, branch checkpoints; 0.4.1's
engine, `6cf40a5a0`, is tagged `sparkinkling-0.4.1`), and the pinned branch
adds the fourth (408, a draft): drafting with two live requests, verifies
sized by the drafter's confidence, a verify that attends exactly as decode
does, decode batches at their own width, and one launch for a Spark decode
row's input projections. Both branches carry a merge of `main` at
`7a717b659`. The pinned branch merges two branches on 408's (`d3318e087`), neither
proposed upstream yet: window-bounded KV (`inkling2/swa-kv-window-20261124`,
three commits) and incoai's DFlash2 drafter
(`inkling2/dflash2-drafter-20261124`, two commits), both below, plus two
closure-attestation fixes (the first proposed upstream as Atlas-Inf/atlas#419)
that let the image's test suite run `the_baked_attestation_reproduces_from_the_tree`
for this one-model build instead of skipping it. The build fetches by commit.

## What the branch adds

**Speed (eight commits, 0.5.1).** Spark decode's projections run on Atlas's
row-invariant tensor-core kernels, each row computed as the one-row kernel
computes it, so drafted and plain greedy text still match. Prefill attention
computes the relative bias on the tensor cores, on per-head CTAs with 64-key
tiles; the prefill norms, the conv residual add and the loop-message gates are
fused into the passes around them; and the experts' gate_up GEMM applies the
softcapped SwiGLU and quantizes its rows in its own epilogue, byte for byte as
the separate pass did. The scheduler ends a tick after one prefill chunk while
other sequences decode, so an arriving prompt holds their streams for one
chunk at a time (the reason 0.5.1's profiles drop the 4,096-token busy cap and
run 8,192-token chunks).

**LoopCD (one commit, off by default).** `--loopcd on` runs the coda layers
18-23 a second time from the state after the first loop pass (six more layer
visits after the model's 48, with their own KV and conv state), then the final
norm and head, and serves `final + w (final - reference)` with
`w = 0.5 (1 - (p1 - p2))`, both rows softcapped at 30: LoopCD-Logits with the
adaptive rule (arXiv 2610.02185), as oMLX serves it. `--loopcd skip-thinking`
leaves rows inside the reasoning block unguided. Off runs the unchanged
schedule and launches no extra kernel: greedy text with `--loopcd off` was
identical to `1559aa4bc`'s in both modes. SparkInkling sets it with `LOOPCD`
([LOOPCD](LOOPCD.md), [results](../results/2026-11-25-loopcd/RESULT.md)).

**incoai's DFlash2 drafter (two commits).** `incoai/Inkling-2-Mini-DFlash2`
is a standard DFlash2 drafter (five layers, two-tap dynamic convolutions, a
16-candidate selector over the target's vocabulary head) that reads the same
four taps as the bundled DSpark: what enters visits 5, 23 and 41, and the
final-norm output. Atlas's DFlash2 head already loads its tensors; the branch
maps those taps to visit outputs for a DFlash2 drafter on an Inkling target as
it does for DSpark, and applies the target's final norm to the last tap
before the drafter's context projection (on a chunk copy of the rows, so the
accumulator keeps the raw capture). The selector's `after_correction` softcap
is applied after a candidate's score and does not change which candidate
scores highest, so the picks are the reference's. A copy of GLM's confidence
twin of the selector (`dflash2_selector_conf.cu`) lets
`ATLAS_DFLASH_CONF_WIDTH` size its verifies; without it the drafter lost to
DSpark on long code. Observed 2026-11-24 on a development build of these
commits over `d3318e087` (other services resident, 0.5 of GPU memory, product
settings per mode, 40 prompts: 20 HumanEval, 10 GSM8K, 10 MMLU-Pro, reasoning
low, temperature 0, single runs), aggregate tok/s with DSpark and with
DFlash2: Strict one request 53.2 and 64.7, two at once 67.3 and 70.2; Spark
one request 67.4 and 78.8, two at once 71.3 and 71.0 (with 0.4.2's
settings, under which Spark decoded plainly from two). Greedy text for 8
prompts x 320 tokens was identical to plain decode at one and two requests
in both modes. 0.5.0 runs DFlash2 only, with settings retuned for it.

**Window-bounded KV (three commits).** 40 of the 48 layer visits
are sliding-window attention over 1,024 tokens, yet the paged cache held a row
for every token of context in all 48: 192 KiB a token. They now keep their K/V
in a pool of their own, at a local block each KV block maps to, and only for
the blocks a sequence's next forward can read (its window, from the 32-key
tile the prefill kernels start at). So context costs the 8 global visits'
32 KiB a token. A shared prefix shares its window rows; a rejected draft never
moves the window's floor; a prefix-cache snapshot pins the window it resumes
from (pins take up to an eighth of the KV budget, least recently used go
first), and a snapshot whose window is gone is declined, so the prompt is
recomputed rather than read from missing rows. Visit 0 maps each forward's KV
slots and block tables through the window map (one small kernel, inside the
decode graphs); the attention kernels are unchanged and read the same rows in
the same order, so greedy text is identical to `d3318e087`'s. Measured
2026-11-24 on a development build of the pinned commit, against the 0.4.2
image's own engine, product flags, DSpark on:

- **Greedy text identical**, in Strict and Spark mode: the 8-prompt check at
  320 tokens, one request and two at once; at 2,048 tokens (past the window);
  three long prompts of 8K, 34K and 106K tokens; and a two-turn prefix-cache
  resume.
- **Speed level**: decode 57.03 vs 57.01 tok/s on code and 35.93 vs 35.90 on
  prose, 32K cold prefill 9.91 vs 9.90 s.
- **KV pools** (tokens): `default` 2,004,064 Strict and 1,856,048 Spark (was
  about 404K), `max` 1,944,304 and 1,815,120 (was about 446K), `saver`
  952,016 and 830,416 (was about 194K beside the voice engines).
- **Long context**: a code hidden a third of the way into a 1,032,929-token
  prompt was recalled (1,252 s for the prompt, Strict, utilization 0.50).

The engine's disk tier (`ATLAS_KV_NVME_DIR`, which SparkInkling 0.5.0 no longer
offers), `--high-speed-swap` and multi-rank serving still assume one block id addresses every layer, so
with any of them the engine keeps full-length KV and logs why. Swapping a
preempted request to host memory is off with the window; such a request is
prefilled again.

The branch is the Inkling 2 Mini series, first written on Atlas-Inf `main`
`269b533bc` (the merge of #332) and merged up to `main` `7a717b659`
(Atlas-Inf/atlas 401 and 404 merged, 405 and 408 open). In order:

- **Loading.** The config parses as 48 unrolled layer visits (24 physical
  layers; the core 6-17 run three times with shared weights), and the
  checkpoint's layout is checked at load.
- **Kernels.** Decode attention with a learned relative-position bias and
  per-token sinks; static and dynamic short convolutions with FP32 state;
  block attention residuals and loop message retrieval; per-head
  clip/scale/norm epilogues and the loop message gates; routed-expert decode
  read straight from the checkpoint's stacked NVFP4 and MXFP8 tensors. The
  compiled base set is Laguna-S-2.1's (`kernel_source`); the
  `inkling-2-mini` overlay adds the Inkling kernels and the logit softcap.
- **Serving.** Several sequences per decode step; CUDA-graph single-sequence
  decode; decode attention that splits a row's keys over the GPU; prefill
  with the routed experts as grouped GEMMs at the checkpoint's declared
  numerics (below), GQA flash attention that computes the relative-position
  bias where it adds it, and the loop message gates and block residuals fused
  per row tile; decode batches that read each expert once.
- **Expert numerics in prefill.** The checkpoint's `hf_quant_config.json`
  requires its experts' inputs quantized: NVFP4 rows for the NVFP4 experts of
  layers 0-19 (a per-row scale amax / 1536 and, per 16 values, the E4M3 block
  scale that takes the block's maximum to 6 or to 4, whichever reconstructs it
  with the smaller absolute error) and MXFP8 rows for the MXFP8 experts of
  layers 20-23. Prefill runs them that way, as vLLM's Inkling 2 kernels do, on
  the block-scaled tensor cores (W4A4 `kind::mxf4nvf4`, W8A8
  `kind::mxf8f6f4`) against the experts as stored. The Spark overlay's experts
  take BF16 inputs.
- **Chat.** Inkling writes a turn as message blocks of special tokens. The
  server rewrites them before the chat paths see them: reasoning is returned
  separately (reasoning parser `inkling2`) and each JSON tool block becomes an
  OpenAI tool call (through the Hermes parser), the same streamed and
  blocking, on `/v1/chat/completions`, `/v1/responses` and `/v1/messages`.
  The model's own effort token in the prompt is the only thinking control: a
  request's `reasoning_effort` (none, minimal, low, medium, high, xhigh) is
  passed to the checkpoint's template, and an effort-silent request renders
  the template's default. Rendered prompts were checked token-identical to
  transformers for plain, system-plus-effort, tool-declaration and tool-history
  prompts during development; that check is not a qualification.
- **Spark mode.** A model directory whose index also maps the Spark overlay
  (ModelOpt NVFP4 under `model.language_model.*` and `lm_head.*`) serves those
  tensors in place of the checkpoint's for decode and verify rows: attention
  projections through the W4A16 GEMVs, the experts of layers 20-23 as NVFP4
  with a per-expert global scale, and the vocabulary head through Atlas's
  prepacked NVFP4 head. Prefill rows (16 or more at once) read the
  checkpoint's own tensors in both modes, so Spark prefills exactly as Strict
  does; both sets are in the model directory anyway. Without an overlay
  nothing changes. See [MODES](MODES.md).
- **Prefix caching.** A visit's only per-sequence state besides its KV is its
  short-conv state, so the radix prefix cache keeps it on Atlas's Marconi
  snapshots as each layer's aux blob (`ModelConfig::aux_prefix_state`): saved
  at the prompt's tail and interval checkpoints during prefill, copied back on
  a hit before the rest of the prompt prefills. A replayed or extended prompt
  resumes from the deepest checkpoint at or below its match. A prompt under
  512 tokens runs its last chunk as one pass: the split's extra pass still
  reads nearly every expert (about 0.1 s), more than recomputing so short a
  prompt costs (`ModelConfig::tail_split_min_tokens`). Where a prompt forks
  from a cached one at least 512 tokens above its restore point, the prefill
  also saves a checkpoint at the fork (`ATLAS_GLM_PC_BRANCH`, set by the
  profiles), so a client that rebuilds its last few messages every turn
  resumes there next turn instead of far below. With a disk
  tier (`ATLAS_KV_NVME_DIR`) evicted KV blocks are restored from disk only
  up to such a snapshot, as for the SSM models: KV alone cannot resume a
  sequence whose conv state is gone.
- **Images.** The checkpoint's vision tower (`model.visual.*`): a 23-layer
  ViT over 20-pixel patches with a class token, a learned position table
  resampled to each image's grid, axial 2D RoPE and layer scale, then a
  bias-free projector over each 2x2 block of patches. Images are not resized:
  the processor pads to a grid of 40x40 pixel tiles (padding at -1 on the
  0-255 scale, transparency on a checkerboard) and each tile is one token.
  The tower runs on Atlas's shared ViT kernels; its query and key rows are
  permuted per head at load to the kernels' rotation layout and layer scale
  is folded into the output projections. On a test image its features match
  the transformers implementation (mean row norm 5.437 against 5.432 in
  float32). Token embeddings are normed once at load, in place (the first
  visit used to norm its input, which also normed image rows; text output is
  byte-identical). An image of more tiles than the encoder holds (1,600 by
  default) is scaled down first.
- **Budget forcing.** The scheduler tracks the reasoning block by Inkling's
  markers and closes it with `<|end_message|>` at a sentence boundary once
  it passes its effort's budget (minimal 2K, low 4K, medium 8K, high 16K,
  xhigh 32K reasoning tokens) or its loop watchdog fires; the model then
  writes its answer. Inkling loops in its reasoning at high effort (its
  model card says so); the drafter keeps speculating inside the block.
- **Streamed tool calls, on request.** Once a tool block reads
  `{"name":NAME,"args":`, the engine can open the call and pass its argument
  tokens through as they arrive. Under the tool guard's `stream` setting (the
  default) it does so only for a request that sends
  `stream_tool_arguments: true`, and checks the call when it ends: a call it
  blocks ends that response with `content_filter` instead of `tool_calls`, and
  must not be run. Every other request's calls are held until they pass, as
  under `TOOL_GUARD=on`, so a client that does not read the finish reason never
  receives a blocked call.
- **Launch overlap.** The target's kernels always launch with programmatic
  dependent launch, so each one's launch overlaps its predecessor's tail
  (bit-identical; every listed kernel waits for its predecessor first).
- **Batching and speculation.** Multi-sequence decode runs from CUDA graphs,
  its BF16 projections (and a verify's) of up to 8 rows on the batched GEMV,
  each row computed as the one-row GEMV computes it (each visit's conv-state
  table is refreshed before replay; padding rows share one state). With the
  checkpoint's weights (Strict), a visit's input projections (q, k, v,
  relative bias, gate, sinks, dynamic conv taps) run as one launch over a
  per-visit table. Verify rows journal each visit's conv state and inputs so
  rejected drafts roll back exactly. The drafter is incoai's DFlash2 (above);
the target verifies every draft, so the drafts change speed and not the
text. A verify stops where the drafter is unsure
(`ATLAS_DFLASH_CONF_WIDTH=1`): the drafter reports the log-probability of
each draft, the engine learns while serving how often the target accepts a
draft at each confidence, and the step verifies only as far as the block is
still likely right, because every extra verify row reads about 1.7 GB of
expert weights (about 6 ms). Drafts go off for a sequence whose steps stop
paying (`ATLAS_DFLASH_ADAPTIVE=1`), for 32 tokens at first and doubling
while re-probes keep failing; the threshold is what a whole block must
accept, 1.0 in Strict and the engine's 2.0 in Spark, and a shorter step owes
a share of it. That rule stands in for the engine's throughput gate
(`ATLAS_MTP_GATE_FORCE=1`), whose off state carried from one request into
the next. Several live requests draft together: their proposes share one
pass over the vocabulary head and their verifies one batch, and a sequence
whose drafts stop paying decodes plainly in the same batch until its
re-probe. Strict drafts seven tokens alone and three each for two requests,
then decodes plainly (`ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0`); Spark,
whose plain step is a third shorter, drafts seven alone and decodes plainly
from two (`1:7,1000000:0`). The settings were tuned for DFlash2 on 0.5.0's
engine ([results](../results/2026-11-25-dflash2-tuning/RESULT.md)). A verify
runs its rows through the same attention body and key splits as a decode
row, so a verified token is the one plain decode picks: on 8 prompts of 320
tokens greedy text was identical with the drafter off and on, one request at
a time and two at once, in both modes (before 0.4.2, the tensor-core prefill
attention summed a row's keys in another order and text parted at near
ties).

## What it does not do yet

- **Drafting under load.** Strict decodes plainly from three live requests
  and Spark from two. On RigMark's short requests (256 tokens, reasoning low)
  drafting there lost: Strict three each at four requests 76.3 against 86.0
  tok/s plain, Spark three each at two 70.2 against 77.4. On a suite of
  longer answers the same settings gained (Strict up to six requests, Spark
  two), so whether drafts pay in a batch depends on how many are accepted,
  and the per-sequence threshold does not weigh a draft against how cheap a
  plain batched step is ([issue 1](https://github.com/Enntity/sparkinkling/issues/1)).
  Batches decode at their own width (three as three rows, not four).
- **Expert input quantization in decode.** Decode and verify rows (fewer than
  16 at once) still give the experts BF16 inputs, so a token's experts see the
  checkpoint's declared numerics in prefill and BF16 inputs in decode.
- **Video.** The tower serves still images only.
- **Known gap** recorded on the branch: streamed `return_token_ids` carry the
  rewritten ids.

## Build-time gates

The image runs the engine's full CPU workspace tests and Clippy with the
pinned Rust 1.93.1, as SparkQwen's does: 8,747 tests passed in the 0.1.0
build, with the exact-name skips listed in
[`install/Dockerfile`](../install/Dockerfile) (SparkQwen's list for Atlas-Inf
`main`). GPU tests are not part of the build; the engine is qualified on the
hardware separately.

The [tool-call guard](TOOL-GUARD.md)
is on by default, as in SparkQwen and SparkGLM, here in its `stream` setting
(a call streams and is checked when it ends). It runs after tool-call parsing; the 0.1.0 task probe's tool calls passed through it in both modes.
