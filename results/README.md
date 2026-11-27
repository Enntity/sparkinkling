<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Results

Each directory is one measured configuration: `RESULT.md` says what was run
and what it showed, `raw/` holds the unedited receipts, and `SHA256SUMS`
covers every file.

```sh
cd results/<date>-<name> && sha256sum -c SHA256SUMS
```

To add a result, record the image tag (`./start.sh status`), the mode, the
profile, the opt-ins, and every repetition you ran, including slow ones.
Measure the baseline on the same Spark, and put its receipts in `raw/` too.

- [`2026-11-21-release-0.1.0`](2026-11-21-release-0.1.0/RESULT.md): the 0.1.0
  image, Strict and Spark with DSpark, against vLLM on the same Spark.
- [`2026-11-23-release-0.4.1`](2026-11-23-release-0.4.1/RESULT.md): the 0.4.1
  image (image input, budget forcing, streamed tool calls), both modes against
  0.4.0 and vLLM, with its functional check.
- [`2026-11-23-release-0.4.2`](2026-11-23-release-0.4.2/RESULT.md): the 0.4.2
  image (confidence-sized verifies, exact drafts, two-request drafting, tool
  calls streamed only on request), both modes against 0.4.1 and vLLM, with its
  functional check.
- [`2026-11-25-dflash2-tuning`](2026-11-25-dflash2-tuning/RESULT.md): the
  drafting settings for incoai's DFlash2 drafter, one lever at a time, and the
  RigMark check that chose the shipped depth.
- [`2026-11-25-release-0.5.0`](2026-11-25-release-0.5.0/RESULT.md): the 0.5.0
  image (DFlash2 drafter, 1M-token context), both modes against 0.4.2 and
  vLLM, with its pools, 1M-token recall and functional check.
- [`2026-11-25-loopcd`](2026-11-25-loopcd/RESULT.md): the opt-in LoopCD
  setting, its speed and pool cost in both modes and its quality in Strict.
- [`2026-11-27-rc-0.5.1`](2026-11-27-rc-0.5.1/RESULT.md): the 0.5.1
  candidate (prefill kernels, one prefill chunk a tick, Spark decode on the
  row-invariant tensor cores), both modes on SparkModelBench, with its pools
  and functional check.
