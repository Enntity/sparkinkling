<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# LoopCD (opt-in)

`LOOPCD=on` in `.env` (or `-e SPARKINKLING_LOOPCD=on` on the container)
serves Inkling 2 Mini with LoopCD-Logits, the adaptive rule of
[arXiv 2610.02185](https://arxiv.org/abs/2610.02185) as oMLX serves it. It is
off by default, and SparkInkling's published numbers are measured with it
off.

## What it does

Inkling 2 Mini runs its core layers 6-17 three times. LoopCD also runs the
coda layers 18-23 from the state after the first pass, a reference that has
looped less, and moves each token's logits away from it:
`final + w (final - reference)`, with `w = 0.5 (1 - (p1 - p2))` from the final
row's top two probabilities. The reference visits have their own KV and
short-conv state, so drafting, prefix caching and rollback cover them.

| `LOOPCD` | Effect |
|---|---|
| `off` (default) | The unchanged engine: greedy text identical to the engine without LoopCD. |
| `on` | Every row is guided, reasoning included. |
| `skip-thinking` | Rows inside the reasoning block stay unguided, so drafts are accepted as with `off`; the answer is guided. |

## What it costs and what it changed

Measured on one DGX Spark, 0.50 of GPU memory, both modes with the DFlash2
drafter ([results](../results/2026-11-25-loopcd/RESULT.md); one run per arm,
preliminary):

- **Speed:** one request decodes 15-25% slower in Spark and 22-36% slower in
  Strict; 32K prefill takes 12% longer. Drafts are accepted 10-13% less often
  (guided text is not what the drafter learned). `skip-thinking` keeps more
  of the speed (Spark 62.7 against 72.0 tok/s on the tuning suite, `on` 60.9).
- **Memory:** the KV pool holds 10% fewer tokens in Spark and 12% fewer in
  Strict (one more full-attention layer visit).
- **Quality** (Strict, temperature 0, 8,192-token cap): at high effort
  MMLU-Pro went from 108 to 122 of 150, 14 of the gains being questions lost
  to a reasoning loop at the cap (cut answers 25 to 7), and HumanEval from 152
  to 157 of 164. At low effort, the default, HumanEval went from 158 to 161;
  GSM8K and MMLU-Pro did not move. The high-effort MMLU-Pro gain is an upper
  bound: the cap sat below the engine's own high-effort reasoning budget
  (16K tokens), so budget forcing never acted. Spark mode and
  `skip-thinking` quality were not measured.

## When to use it

For high-effort reasoning, where Inkling 2 Mini can reason in circles (its
model card says so), if answers matter more than speed. At the default low
effort it costs speed for little gain. Budget forcing already closes a
reasoning block that runs past its effort's budget, with or without LoopCD.

## Profiles

LoopCD's KV pool is smaller, so fewer tokens of context fit at once. On the
published image, `saver` (0.50 of GPU memory) beside two voice engines:

| Mode | `off` | `on` | `skip-thinking` |
|---|---:|---:|---:|
| Spark | 802,016 | 711,776 | 704,816 |
| Strict | 945,968 | 824,560 | 824,064 |

That was 0.5.0's `saver`. The reworked `saver` runs at 0.60 and accepts
requests of up to 1,048,576 tokens over a pool of about 1.09M in Spark mode;
LoopCD's 10-13% would bring that to about 950K, so a request longer than the
pool (prompt plus `max_tokens`) is refused at once (the error names the KV
blocks it needs and the blocks the pool has). Use `default` or `max` for
full-length requests with LoopCD, or Strict. `default` and `max` hold well
over 1M tokens with LoopCD (their pools shrink by the same 10-13%, estimated
from `saver`, not measured), so their 1,048,576-token requests still fit.
