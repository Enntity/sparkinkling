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

`pending-first-rigmark/` is a placeholder for the first measured result. It
holds no measurements; replace it with a dated directory.
