<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Benchmark method

SparkInkling will use the measurement protocol SparkQwen and SparkGLM publish:
[RigMark](https://github.com/alexellis/rigmark) by Alex Ellis (MIT) at commit
`40fabcaf6e963ac27ab347f61d54a225dbd07419`, protocol 1.1.0. Nothing has been
measured on a release candidate yet.

## Results

Performance is not measured yet. This table is a placeholder; it is filled
from a dated directory under [`results/`](../results/) with every repetition
and raw receipt, never from development notes.

| Mode | C1 code decode | C1 prose decode | C2 aggregate | C4 aggregate | C8 aggregate | 32K prefill | TTFT |
|---|---:|---:|---:|---:|---:|---:|---:|
| Strict | — | — | — | — | — | — | — |
| Spark | — | — | — | — | — | — | — |
| vLLM (baseline) | — | — | — | — | — | — | — |

The vLLM baseline is to be measured on the same Spark with RigMark, the
same day, with its version and settings recorded beside it.

## Protocol

- Two complete runs per configuration, with all repetitions retained. Headline
  figures come from the first complete run that passes the protocol's basic
  output gates; no cells are selected from different runs.
- Each run has three code, prose and structured-output repetitions, each with
  a 4,096-token allowance; ten cold prefill requests, each immediately
  replayed; and two short-code rounds at concurrency 1, 2, 4 and 8 with a
  256-token allowance per request.
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
./rigmark run --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas \
  --label sparkinkling-strict-round1 --comparison-id sparkinkling-ROUND1 \
  --metadata metadata.json --runs 3 --decode-tokens 4096 \
  --prefill-runs 10 --prefill-depths 32768 \
  --concurrency 1,2,4,8 --concurrency-runs 2 \
  --extra-body '{"reasoning_effort":"low"}' \
  --output round1.json
```

Use a second label, comparison ID and output path for the second run, so its
cold prompts are not served from the first run's cached prefixes. Preserve
every response, receipt and command under `results/<date>-<name>/raw/` with a
`SHA256SUMS`.
