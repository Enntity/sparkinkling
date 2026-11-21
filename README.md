<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling

Thinking Machines' [Inkling 2 Mini](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
on one NVIDIA DGX Spark with the Atlas engine.

**Status: in development.** There is no release, image or qualified result yet.
This repository will hold accepted work only: the launcher, the pinned engine,
and receipts for every claim.

## The model

Inkling 2 Mini (Apache-2.0) is a looped mixture-of-experts transformer: 26.4B
parameters, 3.4B active, 24 decoder layers whose middle 12 run three times per
token (48 layer visits), 128 experts with top-8 routing, hybrid sliding-window
and full attention without RoPE, text and image input, and up to 1M tokens of
context. Thinking Machines ships it as one ~20 GB checkpoint with NVFP4 and
MXFP8 experts and BF16 everything else, plus a bundled DSpark draft model.

## Modes

SparkInkling will serve the checkpoint in two modes, described in
[docs/MODES.md](docs/MODES.md): **Strict**, the checkpoint's own weight formats,
and **Spark**, with calibrated NVFP4 copies of the BF16 projections and of the
MXFP8 experts.
