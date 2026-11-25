<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# LoopCD in SparkInkling's engine: cost and quality (2026-11-25, preliminary)

**Outcome:** SparkInkling offers LoopCD as an opt-in, per-server setting (`LOOPCD`), off by default. These are the measurements behind that choice.

- **Why offer it.** It costs speed, but HumanEval gains at both efforts, and at high effort it
  ends most reasoning loops. Under an 8,192-token cap, MMLU-Pro high goes from 108 to 122 of 150
  and cut answers fall from 25 to 7.
  - That cap sits below the engine's 16K high-effort budget, so budget forcing never acted.
    The MMLU-Pro gain is an upper bound (see Caveats).
- **Why not by default.**
  - At the product's default effort (low), GSM8K and MMLU-Pro don't move.
  - Decode is 15-25% slower in Spark and 22-36% slower in Strict.
  - The KV pool shrinks 10-12%.

## On the published image (2026-11-25)

The image SparkInkling publishes with the `LOOPCD` setting,
`ghcr.io/enntity/atlas-sparkinkling:a9fac42abe15` (engine `6ab2e9c78`), built
with 8,859 engine tests passing and none failing, was checked through
`./start.sh` on one DGX Spark beside two voice engines
(`raw/image-a9fac42abe15/`, `check051.sh` and its output):

- With no `MODE` or `LOOPCD` set it serves Spark with LoopCD off, and greedy
  text for 8 prompts of 320 tokens was identical to the 0.5.0 image's, one
  request and two at once (8/8, 8/8); Strict one request 8/8.
- `LOOPCD=on` and `skip-thinking` start in both modes, change the greedy text
  (0/8 identical to `off`, as intended) and pass the task probe (30/30
  arithmetic, 10/10 tool calls). No errors in any server log.
- `saver` KV pools, tokens (`off` / `on` / `skip-thinking`): Spark 802,016 /
  711,776 / 704,816; Strict 945,968 / 824,560 / 824,064.

## What was built

- **Engine:** Enntity/atlas `inkling2/loopcd-20261124`, commit `6ab2e9c78` on the 0.5.0 engine
  `1559aa4bc` (`inkling2/rc-0.5.0-20261124`). Not proposed upstream yet.
- **Flag:** `spark serve --loopcd off|on|skip-thinking`, default `off`.
- **Method:** LoopCD-Logits with the adaptive rule (arXiv 2610.02185), as oMLX serves it
  (jundot/omlx#5640):
  - The state after the first core pass (hidden plus the attention-residual blocks) runs coda
    layers 18-23 again. Those six reference visits come after the model's 48 and have their own
    paged KV: window-bounded for the five sliding ones, full for layer 23. They also have their
    own conv state.
  - Then come the final block residual, final norm and head.
  - Both logit rows are softcapped at 30. The served logits are `final + w (final - reference)`
    with `w = 0.5 (1 - (p1 - p2))`.
- **skip-thinking:** leaves rows inside a `<|content_thinking|>` message unguided and keeps
  control-token probabilities. The Model entry points stamp each forward row's flag from the
  sequence's tokens.
- **Because the reference visits are ordinary visits,** CUDA-graph decode, verify journals and
  rollback, prefix snapshots and window pins all cover them unchanged.
- **Code:**
  - `crates/spark-model/src/layers/inkling2/loopcd.rs`: first-pass stash, reference visits.
  - `crates/spark-model/src/model/loopcd.rs`, `loopcd_flags.rs`: guided head, thinking flags.
  - `kernels/gb10/inkling-2-mini/nvfp4/inkling2_loopcd.cu`: the guide kernel. GB10 only; a HIP
    target refuses `--loopcd`.
- **Checks:**
  - fmt and Clippy pass, and unit tests pass for the config, the schedule, row mapping and
    thinking flags.
  - All new files are under 500 lines.

## Functional checks (one DGX Spark, both modes, product flags, DFlash2 drafter)

| check | Spark | Strict |
|---|---|---|
| `--loopcd off` greedy text == base binary (3 prompts) | identical | identical |
| `--loopcd off` == base, 20-prompt suite (text hashes) | 20/20 identical | 20/20 identical |
| `on` greedy text differs from `off` | yes (20/20 suite prompts) | yes (20/20) |
| `on` with DFlash2 drafts == `on` with drafts off | identical | identical |
| heads left unguided / forwards unstamped (log) | 0 / 0 | 0 / 0 |

The base binary came from image `55b5e0c067c4`, which was built from the same commit `1559aa4bc`.

## Cost

Setup: one DGX Spark at util 0.5 with nothing else resident, `--max-seq-len 32768` (65536 for the prefill
rows), saver-like flags. Each figure is the median of three runs, or one suite run.

| measurement | Spark off | Spark on | Strict off | Strict on |
|---|---|---|---|---|
| C1 decode, code, thinking off (tok/s) | 86.1 | 64.6 (-25%) | 70.3 | 44.8 (-36%) |
| C1 decode, prose, thinking off | 58.5 | 49.6 (-15%) | 40.8 | 30.3 (-26%) |
| 20-prompt suite C1, effort low (aggregate tok/s) | 72.0 | 60.9 (-15%) | 55.1 | 43.1 (-22%) |
| same, C2 | 71.9 | 61.6 (-14%) | 66.5 | 54.4 (-18%) |
| plain decode, drafts off (tok/s) | 58.8 | 49.4 (-16%) | 35.7 | 28.3 (-21%) |
| step time, drafts off (ms) | 17.0 | 20.2 (+3.2) | 28.0 | 35.4 (+7.4) |
| 32K prefill TTFT (s) | 9.93 | 11.13 (+12%) | 9.97 | 11.14 (+12%) |
| accepted drafts a step (suite) | 2.21 | 1.91 | 2.38 | 2.14 |
| KV pool at util 0.5 (tokens) | 795,008 | 714,416 (-10%) | 939,472 | 826,048 (-12%) |

- **Where the cost comes from.**
  - The six extra visits are paid on every step and every prefill token.
  - The second head pass hurts most in Strict, where the head is BF16 (926 MB). Spark's head is
    NVFP4.
  - With drafts on, acceptance drops 10-13%, because the drafter learned the unguided
    distribution.
- **skip-thinking speed:** suite C1 is 62.7 (Spark) and 45.8 (Strict). Acceptance stays at the
  `off` level (2.19 / 2.35), since reasoning tokens stay unguided.
- **End-to-end time:** guided answers are shorter (see the quality table), so the quality
  suites at concurrency 8 took about as long as `off`.
  - Low effort: GSM8K 384 vs 403 s, HumanEval 937 vs 891 s, MMLU-Pro 986 vs 834 s (`off` vs `on`).
  - High effort: GSM8K 761 vs 771 s, HumanEval 2226 vs 2275 s, MMLU-Pro 3741 vs 3572 s.

## Quality

Setup: Strict, temp 0, 8192-token cap, concurrency 8. The sets are those of the 11-22 loops study
(MMLU-Pro 150, GSM8K 150, HumanEval 164 run by `he_exec.py`).

| suite | effort | off | on | lost, gained | sign test p | cut at cap off/on | mean tokens off/on |
|---|---|---|---|---|---|---|---|
| GSM8K | low | 142/150 | 143/150 | 1, 2 | 1.00 | 0/0 | 274/244 |
| HumanEval | low | 158/164 | 161/164 | 1, 4 | 0.38 | 1/0 | 596/483 |
| MMLU-Pro | low | 125/150 | 124/150 | 8, 7 | 1.00 | 0/0 | 671/481 |
| GSM8K | high | 144/150 | 144/150 | 1, 1 | 1.00 | 1/0 | 529/450 |
| HumanEval | high | 152/164 | 157/164 | 1, 6 | 0.12 | 9/4 | 1397/1210 |
| MMLU-Pro | high | 108/150 | 122/150 | 2, 16 | 0.001 | 25/7 | 2552/2077 |

- **MMLU-Pro, high:** 14 of the 16 gains are questions that `off` lost to a loop at the cap.
  Every question cut under `on` was also cut under `off`.
- **HumanEval:** both efforts pooled give 2 lost and 10 gained (p ≈ 0.04). That is in line with
  oMLX's 152 → 155.
- **GSM8K and low-effort MMLU-Pro:** flat.

## Caveats

- **The loop result is measured below the engine's own loop handling.**
  - Requests were capped at 8,192 tokens, the 11-22 study's setting. The engine's budget forcing
    closes high-effort reasoning at 16,384 tokens, so it never acted.
  - All 25 `off` cuts (and all 7 `on` cuts) stopped at exactly 8,192 tokens, inside reasoning.
  - The thinking-loop watchdog fired 4 times in the `off` server's log. It catches short exact
    repeats, not these long "let me reconsider" cycles.
  - Served with a request cap above the budget, `off` would answer those questions after a
    forced close. So 108 -> 122 is an upper bound on what LoopCD adds there.
  - The fair test reruns the cut questions (25 `off`, 7 `on`) with a cap above the budget, for
    example 20,480 tokens. Not run yet.

- Each arm ran once at temp 0, on one GB10.
- Quality was measured in Strict only. `skip-thinking` quality was not measured.
- An earlier run is void and not counted: its server command dropped the product flags
  (`raw/run-void1.log`).
- `raw/q/claims.py` recomputes the quality table from the raw files.
- These numbers are preliminary until someone cross-checks them, for example on another Spark or in
  Spark mode.

## Follow-ups (not built)

1. **One head pass for the model rows and the reference rows.** A 16-row batch GEMV for the
   verify block, or a two-row pass at decode. The batch tiers are row-exact, so this should save
   about 4 ms a step in Strict (roughly half of LoopCD's step cost).
2. **Quality for `skip-thinking`.** It should keep most of the speed because drafts accept as
   with `off`. Whether it keeps the loop fix is unknown: loops live in the reasoning, which it
   leaves unguided.
3. **Done:** SparkInkling's `LOOPCD=off|on|skip-thinking` passes `--loopcd`, default `off`.
   [docs/LOOPCD.md](../../docs/LOOPCD.md) says what the smaller pool means for each profile.
