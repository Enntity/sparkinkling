<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Strict and Spark (planned)

Nothing here is implemented or qualified yet. This page records the contract
the two modes are being built to.

Both modes run on one DGX Spark, keep the checkpoint's NVFP4 expert weights in
layers 0-19 with their own scales, and use the bundled DSpark draft model with
target verification. Strict does not mean serial execution: request-level
serial decode stays available for comparisons. A missing or incompatible draft
model is a startup error when a mode is selected.

| Mode | Target weights |
|---|---|
| **Strict** | Exactly the checkpoint's formats: NVFP4 experts in layers 0-19, MXFP8 experts in layers 20-23, BF16 attention projections, router, loop controllers and vocabulary head. Unsupported formats fail loading instead of being converted. |
| **Spark** | Strict's NVFP4 experts in layers 0-19, plus calibrated NVFP4 copies of the BF16 attention projections and the vocabulary head and of the MXFP8 experts in layers 20-23; together about half of the bytes a token reads. |

Spark changes the model's numerics, so it ships only after it is measured
against a BF16 reference (KL and task probes) and against Strict on the same
image. Until then Strict is the only mode, and it stays the default until a
release says otherwise. Neither mode promises identical text to another engine
or numerical reference.
