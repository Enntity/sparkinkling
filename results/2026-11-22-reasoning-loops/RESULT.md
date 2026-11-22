<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Reasoning loops in Inkling 2 Mini, and budget forcing (2026-11-22)

Inkling 2 Mini sometimes keeps re-checking its own work until the token limit
ends the reply, with no answer. Its model card names this among the model's
limitations ("sometimes became stuck in long reasoning loops"). This folder
measures how often that happens, shows that vLLM's own image does the same, and
measures two changes in SparkInkling: budget forcing in the engine and a lower
default reasoning effort. Every number below is recomputed from the files in
`raw/` by `raw/claims.py`.

## Setup

- **Questions.** 150 MMLU-Pro test questions (`raw/mmlu-pro-150.json`, a
  seeded sample of about ten per subject), 150 GSM8K test questions
  (`raw/gsm8k-150.json`, seeded sample) and all 164 HumanEval problems
  (`raw/humaneval-164.json`), from the public datasets on Hugging Face.
- **Requests.** `raw/quality_eval.py`: one user message, the answer parsed
  from the final content only (never the reasoning), 8 requests at a time,
  temperature 0 unless stated, the stated token limit. HumanEval code runs in
  a container with no network (`raw/he_exec.py`). Reasoning effort is the
  request's `reasoning_effort`; without one, Inkling's chat template uses 0.9
  ("high").
- **SparkInkling.** One DGX Spark, the saver profile, Spark weights (the
  checkpoint plus its calibrated NVFP4 overlay), the DSpark drafter. The
  0.4.1 candidate image (engine `c4db7a368`) for the runs without budget
  forcing; a development build of engine `fed29ccdc` (budget forcing) for
  the `tf-*` files. The 32K run without forcing ran on a second Spark with
  the same image, 4 requests at a time.
- **vLLM.** `vllm/vllm-openai:inkling-2-mini` on the same Spark, the
  checkpoint as shipped, `--gpu-memory-utilization 0.5`, otherwise defaults;
  no reasoning parser, so its reasoning arrives in the content.
- **SparkQwen 27B.** Qwen3.8-27B (NVIDIA's NVFP4 QAD checkpoint) through
  SparkQwen's saver mode, its own default thinking.

## The problem

MMLU-Pro, temperature 0, 8,192 tokens, SparkInkling at the template's default
effort (high): 107 of 150 correct, **30 still reasoning at the limit**, 2,707
tokens a reply on average (`raw/ink-spark-mmlu.jsonl`).

The same 30 questions:

| | Correct | Wrong | Still reasoning at the limit |
|---|---:|---:|---:|
| vLLM image, 8,192 tokens | 7 | 2 | 21 |
| SparkInkling rerun, 8,192 tokens | 5 | 2 | 23 |
| SparkInkling, 32,768 tokens | 5 | 3 | 22 |

More room does not help: 22 of the 30 are still reasoning at 32,768 tokens
(`raw/ink-spark-mmlu-cut32k.jsonl`). vLLM's own image leaves 21 of them
unanswered at 8,192 (`raw/vllm-mmlu-cut8k.jsonl`). On question 15 (pricing an
asset-or-nothing put), given 32,768 tokens, vLLM's image wrote the sentence
"If they interpret "down by more than 40%" as S_T < 600? yes." 858 times and
ran out with no answer (`raw/vllm-deep-15.json`). SparkInkling's reply to
question 20 at 32,768 tokens writes "OK, I'll go with C. But let me
reconsider one more time." 32 times (`raw/deep-20.json`); vLLM happened to
answer that one, in 7,629 tokens (`raw/vllm-deep-20.json`).

## Budget forcing

The engine tracks Inkling's reasoning block by the model's own markers and,
once the block passes its effort's budget (minimal 2K, low 4K, medium 8K,
high 16K, xhigh 32K reasoning tokens) or the loop watchdog fires, closes it
with `<|end_message|>` at the next sentence boundary; the model then writes
its answer. The same 30 questions, high effort, 32,768 tokens
(`raw/tf-cut-high32k.jsonl`):

| | Correct | Wrong | Still reasoning at the limit |
|---|---:|---:|---:|
| Without budget forcing | 5 | 3 | 22 |
| With budget forcing | **18** | 11 | **1** |

How the 13 extra correct answers arise: the engine closed 20 replies itself.
Of those, 19 had never answered before: 11 then answered correctly, 7 wrongly,
and 1 kept going after the close. The 20th had been correct and came out
wrong. Ten replies ended on their own: 4 correct both times, 3 wrong both
times, and 3 that had never answered before finished correctly this time
(temperature 0 still varies with batch composition).

At low effort, budget forcing changes nothing measurable: MMLU-Pro 126/150
with no reply cut off (`raw/tf-mmlu-low8k.jsonl`), against 125 with 2 cut
without it. The loop watchdog did not cut normal reasoning short.

## The default effort

SparkInkling now reasons at `low` when a request names no effort. MMLU-Pro,
temperature 0, 8,192 tokens:

| Effort | Correct | Cut | Tokens a reply |
|---|---:|---:|---:|
| high (the template's default) | 107 | 30 | 2,707 |
| medium | 120 | 8 | 1,342 |
| low | 125 | 2 | 691 |
| SparkQwen 27B, its default | 128 | 1 | 950 |

Low against high on the other two sets: GSM8K 142 vs 143 of 150, HumanEval
159 vs 147 of 164 (14 high replies cut off). SparkQwen 27B: GSM8K 146,
HumanEval 160.

## Temperature

The checkpoint's own sampling default is temperature 1.0, and Atlas applies it
when a request names no temperature. These runs use 0 for repeatability, which
is where greedy loops are most likely. Sampling does not make the problem go
away: vLLM's image at temperature 1.0 on the same 30 questions, 8,192 tokens,
left **14 of 30** still reasoning at the limit (12 correct;
`raw/vllm-mmlu-cut8k-t1.jsonl`).

## Caveats

- 150 questions a set: a score is good to about ±6 points (95%).
- Single runs; temperature-0 outputs still vary with batch composition.
- SparkInkling serves Spark weights (NVFP4 overlay, KL 0.0081 to the
  checkpoint); vLLM serves the checkpoint as shipped.
- The answer parser reads the last "Answer:" line; a reply in another format
  counts as wrong for every engine alike.

## Files

`raw/claims.py` recomputes everything above. Results: `ink-spark-*`
(SparkInkling without forcing), `tf-*` (with forcing), `ours-spark-mmlu-cut8k`
(rerun of the 30), `vllm-*` (vLLM image), `sq27b-*` (SparkQwen 27B),
`*-exec.json` (HumanEval runs), `deep-20.json` and `vllm-deep-*.json` (full
replies kept for reading). Scripts: `quality_eval.py`, `he_exec.py`,
`deep.py`, `deep_vllm.py`, and the run scripts (`run_model.sh`,
`run_inkling.sh`, `effort_ab.sh`, `cut_ours.sh`, `low_rest.sh`,
`receipts.sh`). `SHA256SUMS` covers every file.
