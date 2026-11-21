<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Strict and Spark

This page records the contract the two modes are built to and how the
launcher serves them. Their 0.3.0 measurements are in
[`results/2026-11-21-release-0.3.0`](../results/2026-11-21-release-0.3.0/RESULT.md).

Set `MODE=strict` (the default) or `MODE=spark` in `.env`, or run
`./start.sh --mode spark`. The container takes `SPARKINKLING_MODE`.

Both modes run on one DGX Spark with BF16 KV and keep the checkpoint's NVFP4
expert weights in layers 0-19 with their own scales.

| Mode | Target weights | Model directory |
|---|---|---|
| **Strict** | Exactly the checkpoint's formats: NVFP4 experts in layers 0-19, MXFP8 experts in layers 20-23, BF16 attention projections, router, loop controllers and vocabulary head. Unsupported formats fail loading instead of being converted. | The downloaded checkpoint, as shipped. |
| **Spark** | Strict's NVFP4 experts in layers 0-19, plus calibrated NVFP4 copies of the BF16 attention projections and the vocabulary head and of the MXFP8 experts in layers 20-23; together about half of the bytes a token reads. | The checkpoint plus the overlay, assembled by `install/spark_overlay.py`. |

## How Spark mode is served

The overlay is one file, `spark-nvfp4.safetensors` (2.9 GB, 459 tensors),
published as
[`Enntity/Inkling-2-Mini-Spark-NVFP4`](https://huggingface.co/Enntity/Inkling-2-Mini-Spark-NVFP4)
(Apache-2.0, derived from the checkpoint) and pinned by revision and sha256. Its tensors are ModelOpt NVFP4 under
the transformers module names, `model.language_model.*` and `lm_head.*`: the
attention q, k, v, output-gate, output and relative-bias projections of all 24
layers, the vocabulary head, and the routed experts of layers 20-23.

Atlas serves Spark mode from a model directory that holds the checkpoint's
files and the overlay file, with a `model.safetensors.index.json` whose
`weight_map` is the checkpoint's plus every overlay tensor mapped to
`spark-nvfp4.safetensors`. Wherever the index maps an overlay tensor, the
engine serves it in place of the checkpoint's; without one nothing changes.
`./start.sh --mode spark` builds that directory next to the checkpoint,
`<checkpoint>+spark-nvfp4`, with relative links to the checkpoint's files. It
checks the overlay's sha256, tensor count and names against
[`install/checkpoint.json`](../install/checkpoint.json) first, leaves a
directory already built from the same revisions alone, and moves a new one
into place only when it is complete. The checkpoint's own directory is never
changed. Before launching, the image checks that the directory matches the
mode: Strict refuses an index that maps the overlay, Spark one that does not.

It was made by GPTQ per linear with a wide scale search, from Hessians of
the checkpoint as shipped. Its KL to the checkpoint as shipped is 0.0081
[0.0075, 0.0088] over 224 held-out documents (97.0% top-1 agreement, NLL
+0.16%); plain round-to-nearest of the same tensors gives 0.0170. The
receipts are in the overlay repository.

## Speculative decoding

The checkpoint bundles a DSpark draft model (`mtp.safetensors`), and both
modes run it by default (`DRAFTER=dspark`). `./start.sh` assembles the
drafter's directory next to the checkpoint, `<checkpoint>+dspark`
([`install/dspark_drafter.py`](../install/dspark_drafter.py)): the
checkpoint's `mtp.safetensors`, checked against its pinned sha256 and linked
as `model.safetensors`, beside a `config.json` that is the checkpoint's
`mtp_config` plus the tokenizer's vocabulary size. The engine verifies every
draft against the mode's own weights, so the drafter changes speed and not
the model. It drafts while one request is live; from two requests the engine
decodes plainly, which delivers more there. `DRAFTER=none` turns it off.

DSpark pays on predictable text (code, structured output) and costs on
prose, where few drafts are accepted; see the results for both.

## Choosing a mode

Strict is the default and serves the checkpoint's own numerics: its weights
as shipped, and in prefill its experts' inputs quantized as its
`hf_quant_config.json` declares (decode still gives the experts BF16 inputs).
Spark decodes faster in every measured cell (up to 1.52x on prose) for a KL of
0.0081 to Strict's weights, prefills exactly as Strict does (both read the
checkpoint's own tensors there), and both answered the 0.3.0 task probe (30
arithmetic problems, 10 tool calls) without a miss. Neither mode promises identical text
to another engine or numerical reference.
