<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Benchmark method

SparkInkling uses [RigMark](https://github.com/alexellis/rigmark) by Alex Ellis
(MIT) at commit `40fabcaf6e963ac27ab347f61d54a225dbd07419`, protocol 1.1.0,
with the settings the vLLM baseline on the same Spark was measured with.

## Results

From [`results/2026-11-21-release-0.4.0`](../results/2026-11-21-release-0.4.0/RESULT.md),
the 0.4.0 image (`646b6c9dafe6`), default profile and drafter; medians over all
repetitions; vLLM on the same Spark on 2026-11-20. Earlier releases' results are
in [`results/`](../results/).

| Mode | C1 code decode | C1 prose decode | C2 aggregate | C4 aggregate | C8 aggregate | 32K prefill | 8K prefill | Gates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Strict | 49.2 | 33.6 | 49.1 | 78.1 | 119.6 | 3,277 | 3,332 | 6/6 |
| Spark | 66.8 | 51.6 | 72.0 | 101.3 | 134.9 | 3,275 | 3,366 | 6/6 |
| vLLM | 35.1 | 35.6 | 54.0 | 86.6 | 122.4 | 2,722 | | 6/6 |
| vLLM + DSpark | 69.8 | 31.2 | 60.9 | 94.7 | 144.0 | 2,723 | | 6/6 |

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
