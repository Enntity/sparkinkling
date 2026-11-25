<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Benchmark method

SparkInkling uses [RigMark](https://github.com/alexellis/rigmark) by Alex Ellis
(MIT) at commit `40fabcaf6e963ac27ab347f61d54a225dbd07419`, protocol 1.1.0,
with the settings the vLLM baseline on the same Spark was measured with.

## Results

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

## Protocol

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
