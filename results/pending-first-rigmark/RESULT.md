<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# First RigMark result (placeholder)

Not measured yet. This directory reserves the layout of the first result:
Strict, and Spark once its overlay is published, on the pinned image, with a
vLLM baseline on the same Spark, by the [benchmark method](../../docs/BENCHMARKS.md).

When it is measured, rename the directory to `<date>-<name>` and record here:

- the image tag and engine commit (`./start.sh status`), mode, profile and
  opt-ins;
- every repetition of both runs, the headline run, and the failures;
- the vLLM version, its settings and its receipts.

`CARD.md` will hold the unedited RigMark card of the headline run, `raw/` the
receipts, and `SHA256SUMS` every file.
