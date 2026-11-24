<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Licensing

SparkInkling is AGPL-3.0-only ([LICENSE](../LICENSE)). Work it builds on is
credited in the README's [Credits](../README.md#credits) and in
[NOTICE](../NOTICE).

## In this repository

| Material | License |
|---|---|
| `start.sh`, `install/`, `bench/`, docs and results | AGPL-3.0-only |
| `start.sh` and `install/` as adapted from [SparkQwen](https://github.com/Enntity/sparkqwen) and [SparkGLM](https://github.com/Enntity/sparkglm) | AGPL-3.0-only, the same contributors |

The scripts under `results/*/raw/` are the ones that produced each receipt,
kept unedited. `docs/assets/make_cards.py` sets text in Press Start 2P by
CodeMan38 (SIL Open Font License 1.1); the font file is not in this
repository.

## Fetched while building the image

| Component | License |
|---|---|
| Atlas engine, [`Enntity/atlas`](https://github.com/Enntity/atlas) (a fork of [`Atlas-Inf/atlas`](https://github.com/Atlas-Inf/atlas)) at the pinned commit | AGPL-3.0-only |
| CUTLASS | BSD-3-Clause |
| The engine's Rust dependencies (`Cargo.lock`) | mostly MIT, Apache-2.0 or BSD |
| Other models' chat templates in the engine's `jinja-templates/`, copied into the image | their model vendors' terms |
| CUDA base images and Ubuntu packages | their own terms |

FFmpeg is installed in the build stage only, for the engine's tests; the
runtime image does not carry it.

The engine's Inkling 2 drafter and vision kernels follow the numerics of
vLLM's Inkling 2 implementation (Apache-2.0) and of the transformers
`Inkling2` classes (Apache-2.0); the kernels are Atlas's own
([ENGINE](ENGINE.md)).

The image ships the CUTLASS notice under `/opt/atlas/notices/` and the
engine's license at `/LICENSE`. The license, copying and notice files of the
third-party Rust crates compiled into the engine are under
`/opt/atlas/notices/rust/` (`INDEX.tsv` lists each crate, its declared license
and its source; `install/rust-notices.py` collects them at build time). Its
complete corresponding source is:

- this repository at the commit whose `install/` tree matches the image tag;
- the Atlas commit recorded in `/opt/atlas/source-manifest.json`;
- the upstream revisions pinned in `install/`.

If you modify the engine and let others use it over a network, AGPL section 13
requires you to offer them your modified source.

## Model

No weights are distributed here. `./start.sh` downloads
[`thinkingmachines/Inkling-2-Mini`](https://huggingface.co/thinkingmachines/Inkling-2-Mini)
from its publisher at the revision pinned in
[`install/checkpoint.json`](../install/checkpoint.json), including its bundled
DSpark draft model (`mtp.safetensors`): by Thinking Machines Lab, Inc., under
the Apache License 2.0. Read the model card before use, and before
redistributing anything derived from it.

The default drafter,
[`incoai/Inkling-2-Mini-DFlash2`](https://huggingface.co/incoai/Inkling-2-Mini-DFlash2),
is downloaded from its publisher at the revision pinned in the same file: by
Inco AI, under the Apache License 2.0.

Spark mode also downloads
[`Enntity/Inkling-2-Mini-Spark-NVFP4`](https://huggingface.co/Enntity/Inkling-2-Mini-Spark-NVFP4):
NVFP4 copies of the checkpoint's attention projections, vocabulary head and
layer 20-23 experts, quantized by us from those weights and published under
the Apache License 2.0 ([MODES](MODES.md)). `install/spark_overlay.py` checks
its sha256, tensor count and names against the pin and links it beside the
checkpoint; the checkpoint's own directory is never changed.

Files the engine writes while serving (the CUDA compile cache, the prefix
cache's disk tier) are derived from the checkpoint's weights or from your
prompts; they stay on your Spark.
