<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The engine

SparkInkling runs [Atlas](https://github.com/Atlas-Inf/atlas), built from
[Enntity/atlas](https://github.com/Enntity/atlas) `inkling2/mini-20261121` at
the commit pinned in [`install/atlas-source.json`](../install/atlas-source.json):
`c4db7a368` (tree `f2ff739f`), for the kernel target `inkling-2-mini`
(`ATLAS_TARGET_HW=gb10`, `ATLAS_TARGET_QUANT=nvfp4`, model type
`inkling2_loop`). [`install/build.sh`](../install/build.sh) fetches exactly that
commit, refuses any other tree, and takes the kernel target from the same
file. The pin moves only in `install/atlas-source.json` and on this page.

## What the branch adds

`inkling2/mini-20261121` is the Inkling 2 Mini series on Atlas-Inf `main`
`269b533bc` (the merge of #332), proposed upstream as one pull request. In
order:

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
  prompt costs (`ModelConfig::tail_split_min_tokens`). With a disk
  tier (`ATLAS_KV_NVME_DIR`) evicted KV blocks are restored from disk only
  up to such a snapshot, as for the SSM models: KV alone cannot resume a
  sequence whose conv state is gone.
- **Launch overlap.** `ATLAS_INKLING2_PDL=1` (set by the profile) launches the
  target's kernels with programmatic dependent launch, so each one's launch
  overlaps its predecessor's tail.
- **Batching and speculation.** Multi-sequence decode runs from CUDA graphs,
  its BF16 projections (and a verify's) of up to 8 rows on the batched GEMV,
  each row computed as the one-row GEMV computes it
  (each visit's conv-state table is refreshed before replay; padding rows
  share one state). Verify rows journal each visit's conv state and inputs so
  rejected drafts roll back exactly. The checkpoint's DSpark drafter runs as a
  variant of Atlas's DFlash head: each draft layer mixes four target taps
  (the inputs of visits 5, 23 and 41 and the final-norm output) with its own
  weights, the block is the anchor's embedding plus mask rows, and a
  recurrent Markov head corrects the drafts, its latent folded into the
  vocabulary head at load. The target verifies every draft, so the drafts
  change speed and not the text (in development an NVFP4 and a BF16 drafter
  gave byte-identical greedy text). The image speculates only while drafts
  pay (`ATLAS_DFLASH_ADAPTIVE=1`: under two accepted a step over twelve steps,
  a sequence decodes plainly until a re-probe 256 tokens later). A verify runs the target over 8 rows at
  once, and those kernels round differently from single-row decode, so
  greedy text with and without speculation can part at a near tie.

## What it does not do yet

- **Batched DSpark.** The drafter proposes for one sequence at a time, so
  SparkInkling speculates only while one request is live and decodes plainly
  from two (`ATLAS_DFLASH_BATCH_DEPTH=1:7,1000000:0`, set by the image).
- **Expert input quantization in decode.** Decode and verify rows (fewer than
  16 at once) still give the experts BF16 inputs, so a token's experts see the
  checkpoint's declared numerics in prefill and BF16 inputs in decode.
- **Images.** The target has no vision tower. Inkling 2 Mini takes image
  input; SparkInkling serves text only.
- **Known gaps** recorded on the branch: `usage.reasoning_tokens` reads 0, and
  streamed `return_token_ids` carry the rewritten ids.

## Build-time gates

The image runs the engine's full CPU workspace tests and Clippy with the
pinned Rust 1.93.1, as SparkQwen's does: 8,747 tests passed in the 0.1.0
build, with the exact-name skips listed in
[`install/Dockerfile`](../install/Dockerfile) (SparkQwen's list for Atlas-Inf
`main`). GPU tests are not part of the build; the engine is qualified on the
hardware separately.

The [tool-call guard](https://github.com/Enntity/sparkqwen/blob/main/docs/TOOL-GUARD.md)
is on by default, as in SparkQwen and SparkGLM. It runs after tool-call
parsing; the 0.1.0 task probe's tool calls passed through it in both modes.
