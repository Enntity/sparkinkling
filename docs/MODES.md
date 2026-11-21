<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Strict and Spark

Nothing here is qualified yet. This page records the contract the two modes
are built to, and what the launcher does today.

Set `MODE=strict` (the default) or `MODE=spark` in `.env`, or run
`./start.sh --mode spark`. The container takes `SPARKINKLING_MODE`.

Both modes run on one DGX Spark with BF16 KV and keep the checkpoint's NVFP4
expert weights in layers 0-19 with their own scales.

| Mode | Target weights | Model directory |
|---|---|---|
| **Strict** | Exactly the checkpoint's formats: NVFP4 experts in layers 0-19, MXFP8 experts in layers 20-23, BF16 attention projections, router, loop controllers and vocabulary head. Unsupported formats fail loading instead of being converted. | The downloaded checkpoint, as shipped. |
| **Spark** | Strict's NVFP4 experts in layers 0-19, plus calibrated NVFP4 copies of the BF16 attention projections and the vocabulary head and of the MXFP8 experts in layers 20-23; together about half of the bytes a token reads. | The checkpoint plus the overlay, assembled by `install/spark_overlay.py`. |

## How Spark mode is served

The overlay is one file, `spark-nvfp4.safetensors` (2.9 GB, 459 tensors), to
be published as
[`Enntity/Inkling-2-Mini-Spark-NVFP4`](https://huggingface.co/Enntity/Inkling-2-Mini-Spark-NVFP4)
(Apache-2.0, derived from the checkpoint). Its tensors are ModelOpt NVFP4 under
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

The overlay is not published yet: its revision and sha256 are `TODO` in the
pin, and `MODE=spark` is refused until they are filled in.

## Speculative decoding

The checkpoint bundles a DSpark draft model (`mtp.safetensors`). The pinned
engine does not run DSpark yet, so both modes decode without a drafter today
(`DRAFTER=none`, the only value accepted). When the engine supports it,
`DRAFTER=dspark` will select it with target verification in both modes, and a
missing or incompatible draft model will be a startup error. Strict does not
mean serial execution: request-level serial decode stays available for
comparisons.

## Before Spark ships

Spark changes the model's numerics, so it ships only after it is measured
against a BF16 reference (KL and task probes) and against Strict on the same
image. Until then Strict is the default, and it stays the default until a
release says otherwise. Neither mode promises identical text to another engine
or numerical reference.
