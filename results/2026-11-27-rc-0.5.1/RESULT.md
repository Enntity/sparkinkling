<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling 0.5.1 release candidate: SparkModelBench (2026-11-27)

The candidate image `ghcr.io/enntity/atlas-sparkinkling:717bd225a5d6`
(image `sha256:fe0bb350fc1b`; Atlas `Enntity/atlas`
`inkling2/rc-0.5.1-20261126` at `a4dbba378`, the `inkling-2-mini` kernel
target), built on one DGX Spark and served through `./start.sh` with the
default profile (8 sequences of up to 1,048,576 tokens, 0.80 of GPU memory,
BF16 KV with window-bounded sliding-window visits, 8,192-token prefill
chunks, prefix caching) and the default drafter (incoai's DFlash2: seven
drafts with one live request, three each with two, plain decoding from
three). Measured with [SparkModelBench](https://github.com/enntity/sparkmodelbench)
`293a44f` (RigMark protocol 1.3.0, RigMark Quality v0.0.2,
`reasoning_effort: low`) on that Spark with nothing else serving: the voice
services were suspended from 01:44:08Z to 02:27:24Z (`raw/window.out`).
Weights: `thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`; Spark adds
`Enntity/Inkling-2-Mini-Spark-NVFP4` @ `e9df93dc`; drafter
`incoai/Inkling-2-Mini-DFlash2` @ `4f9088ea66c2`.

Serving measurements and quality tasks by **Alex Ellis, OpenFaaS Ltd**
([RigMark](https://github.com/alexellis/rigmark),
[RigMark Quality](https://github.com/alexellis/rigmark-quality)); Enntity
adds the staggered four-request field guide. The suite is pinned as the
`bench/sparkmodelbench` submodule.

The image build ran the engine's whole CPU workspace suite (8,861 tests
passed) and Clippy (`raw/build-summary.log`). The first build of this
candidate (engine `859bcf025`) failed that suite on one test, the PDL
contract `pdl_target_kernels_wait_exactly_when_listed`: the two new fused
kernels declared shared memory before `atlas_pdl_enter()`. `a4dbba378`
moves the call first; nothing else changed.

## What changed since 0.5.0

Engine only, plus the profiles' prefill chunk size (no setting to change):

- **Prefill**: attention's relative bias on the tensor cores and flash
  prefill on per-head CTAs with 64-key tiles; fused prefill norms, conv
  residuals and loop-message gates; the experts' SwiGLU and its quantization
  in the gate_up GEMM's epilogue, byte for byte as the separate pass did;
  CUTLASS BF16 tiles for the large projections.
- **Scheduler**: a prompt that arrives while other sequences decode runs one
  prefill chunk a tick, so the profiles run 8,192-token chunks (was 4,096).
- **Spark decode**: the projections run on Atlas's row-invariant tensor-core
  kernels, and Spark drafts three each for two live requests.

## Results

Medians of SparkModelBench's repetitions (five decode samples a workload,
three cold/replay pairs a prefill depth, three concurrency rounds); every
repetition is in `raw/smb-*`.

| | Spark | Strict |
|---|---:|---:|
| Code decode, tok/s | 88.2 | 68.7 |
| Prose decode | 57.0 | 40.2 |
| Structured decode | 129.9 | 102.3 |
| Decode gates | 15/15 | 15/15 |
| Cold prefill 8K, tok/s (TTFT) | 5,174 (1.58 s) | 5,137 (1.59 s) |
| 32K | 5,024 (6.52 s) | 4,918 (6.66 s) |
| 64K | 4,540 (14.44 s) | 4,481 (14.63 s) |
| 128K | 3,781 (34.67 s) | 3,779 (34.69 s) |
| 256K | 2,824 (92.81 s) | 2,827 (92.71 s) |
| Immediate replay TTFT, 8K / 32K / 256K | 0.13 / 0.15 / 0.36 s | 0.14 / 0.16 / 0.37 s |
| Code, aggregate tok/s at 1 / 2 / 4 / 8 requests | 63.2 / 81.9 / 104.7 / 144.1 | 48.1 / 65.6 / 85.6 / 126.4 |
| RigMark Quality, tasks passed | 3/4 | 3/4 |

Every cold prefill reported zero cached tokens. In RigMark Quality both
modes passed `python-expiry`, `payment-recovery` and `evidence-revisions`
and finished `go-transfer-ledger` with its public tests, regression test and
gofmt passing but its acceptance check failing (Spark 17.6 / 74.0 / 5.3 /
5.2 s, Strict 20.6 / 80.5 / 6.3 / 6.2 s for the four tasks).

**Against 0.5.0, not like for like**: 0.5.0's release run used RigMark
protocol 1.1.0 ([its result](../2026-11-25-release-0.5.0/RESULT.md)): Spark
code 81.4, prose 56.1, structured 117.4 tok/s, 32K cold prefill 3,282 tok/s
(Strict 70.0, 39.6, 103.2, 3,268). The decode workloads differ between the
protocols; prefill at a given depth does not, and 32K cold prefill is 1.53x
in Spark and 1.50x in Strict. Neither 0.5.0 nor another engine was run with
SparkModelBench for this candidate.

## The staggered C4 lane does not apply to Inkling

The lane asks for thinking off (`chat_template_kwargs.enable_thinking:
false`) and 400 output tokens. Inkling 2 Mini has no thinking-off mode: the
engine reads that as reasoning effort `none`, at which the model still
reasons, and SparkInkling does not stream reasoning at `none`. On the field
guide's ~16K-token prompt it reasoned for all 400 tokens, so the lane saw no
visible tokens and marked every round incomplete (`raw/smb-*-full/c4-*.json`).
0.5.0 does the same (checked in Spark mode): on that prompt with 2,000 tokens it reasoned 1,999,
this candidate 1,329 before it answered. On a short prompt the candidate
closes reasoning at `none` after 193 (Spark) and 242 (Strict) tokens. The
lane's wall times (Spark 31.6-32.0 s, Strict 36.2-36.4 s) measure hidden
reasoning, not the field guide, and are not a result.

## Context and memory

KV pools of this candidate (tokens), read from the server's log
(`raw/smb-*.server.log`, `raw/max-*`, `raw/saver-*`); `default` and `max`
with the voice services suspended, `saver` beside them:

| Profile | Strict | Spark | 0.5.0 Strict | 0.5.0 Spark |
|---|---:|---:|---:|---:|
| `default` (0.80) | 1,909,536 | 1,790,944 | 1,969,120 | 1,838,992 |
| `max` (0.85) | 1,872,512 | 1,718,048 | 1,908,256 | 1,746,976 |
| `saver` (0.50) | 882,992 | 741,520 | 964,560 | 799,520 |

The 8,192-token prefill arena costs 2-9% of the pool. No 1M-token recall was
rerun; the engine's KV layout is 0.5.0's.

## Functional check

`raw/smoke.sh` through `./start.sh` on the candidate image in both modes,
voice services resident, 0.50 of GPU memory (`raw/smoke.out`):

- Task probe: 30/30 arithmetic and 10/10 tool calls in both modes.
- Tool calls blocking and streamed, thinking on and off: all returned as tool
  calls; asked-for streamed arguments arrived in 71-78 chunks.
- Forced tool choice: named and `required` calls finished `tool_calls`; a
  named call to a cloud metadata address finished `content_filter` with the
  tool guard, streamed when asked and with no arguments when not.
- Images: invoice transcribed exactly, 3x3 grid and shapes read as in 0.5.0's
  receipts, both modes.
- Voice-agent turns (Strict): new-turn TTFT 3.26, 1.96, 0.68 and 0.73 s;
  follow-ups 0.41-0.42 s.
- **Drafted text is the plain text**: greedy text for 8 prompts of 320 tokens
  with the drafter on equals the drafter off at one, two and four requests,
  8/8 in both modes.

Before the candidate, on development builds of the same engine: prompt
logprobs of 63 prompts (1K-8K tokens) byte-identical across the fused
gate_up change and the row-maxima layout fix; drafted vs plain greedy
identical at 1, 4 and 8 requests after each prefill change.

## Not tested here

Another engine or 0.5.0 under SparkModelBench; 1M-token recall; MMLU-Pro,
GSM8K or HumanEval; video. `raw/` replaces the Spark's home directory with
`~` in logs; nothing else is edited.

## Files

`raw/smb-spark-full/` and `raw/smb-strict-full/` are SparkModelBench's own
result directories (`CARD.md`, RigMark's card and JSON, prefill, C4 and
RigMark Quality receipts, their own `SHA256SUMS`);
`raw/smb-*-concurrency/` the concurrency lane; `raw/meta-*.json` the
metadata RigMark recorded; `raw/window.sh` and `raw/smoke.sh` the scripts
that ran.
