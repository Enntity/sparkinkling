<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Benchmark method

From 0.5.1, SparkInkling is measured with
[SparkModelBench](https://github.com/enntity/sparkmodelbench), pinned here as
[`bench/sparkmodelbench`](../bench/sparkmodelbench) at `293a44f`. It runs
[RigMark](https://github.com/alexellis/rigmark) (protocol 1.3.0) and
[RigMark Quality](https://github.com/alexellis/rigmark-quality) (v0.0.2) by
Alex Ellis, OpenFaaS Ltd (MIT), with fixed settings, and adds Enntity's
staggered four-request field guide. Its README describes every lane.

## Results (0.5.1, SparkModelBench)

From [`results/2026-11-27-rc-0.5.1`](../results/2026-11-27-rc-0.5.1/RESULT.md),
the 0.5.1 release candidate (`717bd225a5d6`; the release tag `a96a89ab0b29`
differs only in the profiles' notes), default profile and drafter (DFlash2);
medians over all repetitions.

| Mode | Code decode | Prose decode | Structured | Cold prefill 8K / 32K / 64K / 128K / 256K | Code aggregate C1 / C2 / C4 / C8 | Gates | Quality |
|---|---:|---:|---:|---:|---:|---:|---:|
| Spark | 88.2 | 57.0 | 129.9 | 5,174 / 5,024 / 4,540 / 3,781 / 2,824 | 63.2 / 81.9 / 104.7 / 144.1 | 15/15 | 3/4 |
| Strict | 68.7 | 40.2 | 102.3 | 5,137 / 4,918 / 4,481 / 3,779 / 2,827 | 48.1 / 65.6 / 85.6 / 126.4 | 15/15 | 3/4 |

## Protocol (0.5.1)

- SparkModelBench's default lanes (RigMark decode and prefill, RigMark
  Quality, the staggered C4) in one invocation, then its optional RigMark
  concurrency lane in a second, per mode, with `--effort low`.
- Five code, prose and structured-output decode samples, each with an
  8,192-token cap; cold prefill at 8K, 32K, 64K, 128K and 256K on RigMark's
  exact token-ID workload, three cold/immediate-replay pairs a depth; four
  RigMark Quality tasks with a 180-second agent budget each; three rounds of
  1, 2, 4 and 8 code requests released together, 256 tokens each.
- The staggered C4 lane asks for thinking off. Inkling 2 Mini has none, so the
  lane is not a result for it
  ([why](../results/2026-11-27-rc-0.5.1/RESULT.md#the-staggered-c4-lane-does-not-apply-to-inkling)).
- One Spark, nothing else serving, building or copying images during timed
  measurement.

## Results (0.5.0, RigMark 1.1.0)

SparkInkling 0.5.0 and the vLLM comparison used RigMark alone, at commit
`40fabcaf6e963ac27ab347f61d54a225dbd07419`, protocol 1.1.0, with the settings
the vLLM baseline on the same Spark was measured with.

From [`results/2026-11-25-release-0.5.0`](../results/2026-11-25-release-0.5.0/RESULT.md),
the 0.5.0 image (`13920bc38fd6`), default profile and drafter (DFlash2);
medians over all repetitions; vLLM on the same Spark on 2026-11-20. Earlier
releases' results are in [`results/`](../results/).

| Mode | C1 code decode | C1 prose decode | C1 structured | C2 aggregate | C4 aggregate | C8 aggregate | 32K prefill | 8K prefill | Gates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Strict | 70.0 | 39.6 | 103.2 | 62.6 | 85.7 | 122.7 | 3,268 | 3,334 | 6/6 |
| Spark | 81.4 | 56.1 | 117.4 | 77.8 | 103.5 | 135.2 | 3,282 | 3,361 | 6/6 |
| Strict 0.4.2 | 65.2 | 35.3 | 92.6 | 63.1 | 85.0 | 120.7 | 3,274 | 3,345 | 6/6 |
| Spark 0.4.2 | 77.5 | 55.7 | 103.6 | 77.7 | 105.8 | 135.4 | 3,277 | 3,352 | 6/6 |
| vLLM | 35.1 | 35.6 | 35.6 | 54.0 | 86.6 | 122.4 | 2,722 | | 6/6 |
| vLLM + DSpark | 69.8 | 31.2 | 104.3 | 60.9 | 94.7 | 144.0 | 2,723 | | 6/6 |

The aggregates are the short-code workload. The drafting settings behind
these numbers were chosen in
[`results/2026-11-25-dflash2-tuning`](../results/2026-11-25-dflash2-tuning/RESULT.md),
where the tuning suite and RigMark disagreed about drafting under load.

## Protocol (0.5.0)

- Two invocations per configuration: a code suite (decode, prefill, short-code
  concurrency) and a prose suite (decode, short-prose concurrency), with every
  repetition retained. The cards in the results are RigMark's own.
- Each suite has two code, prose and structured-output decode repetitions,
  each with a 4,096-token allowance; the code suite adds two cold prefill
  requests at 8,192 and at 32,768 tokens, each immediately replayed, and two
  short-code rounds at concurrency 1, 2, 4 and 8 with a 256-token allowance
  per request; the prose suite two short-prose rounds at 1, 4 and 8.
- Temperature 0, top-p 1, seed 20260905, explicit `reasoning_effort=low` on
  every chat request. Inkling always reasons a little, so decode includes
  reasoning tokens.
- One Spark, nothing else serving, building or copying images during timed
  measurement. Telemetry records clocks, host memory, swap and pressure.

Decode estimates use RigMark's streamed timing and tokenizer evidence, with
medians and ranges over all repetitions. Cold prefill is prompt tokens divided
by time to first token; immediate replay is a cache measurement, not prefill.
Structured output is a predictable-output ceiling, not an estimate of agent
speed. A 256-token capped stream is not necessarily a completed answer. Basic
output gates check properties of these prompts, not broad model quality.

## Reproduction

0.5.1: [REPRODUCE](REPRODUCE.md#the-release-run). 0.5.0, RigMark alone:

```sh
EB='{"chat_template_kwargs":{"reasoning_effort":"low"}}'
./rigmark run --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas --metadata metadata.json \
  --comparison-id inkling2-atlas --runs 2 --prefill-runs 2 --concurrency 1,2,4,8 --concurrency-runs 2 \
  --extra-body "$EB" --label sparkinkling-strict-code --prefill-depths 8192,32768 --output strict-code.json
./rigmark run --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas --metadata metadata.json \
  --comparison-id inkling2-atlas --runs 2 --concurrency 1,4,8 --concurrency-runs 2 \
  --extra-body "$EB" --label sparkinkling-strict-prose --concurrency-workload prose --skip-prefill \
  --output strict-prose.json
```

The default profile caches prefixes, so the immediate replay measures a prefix-cache hit (from 0.4.0; earlier releases replayed cold).
Preserve every response, receipt and command under `results/<date>-<name>/raw/`
with a `SHA256SUMS`.
