<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Reproduce our numbers

Every figure in the README and [BENCHMARKS](BENCHMARKS.md) comes from a
directory under [`results/`](../results/README.md) that holds the commands,
the unedited receipts and their checksums. This page is how to run the same
thing on your own Spark.

## What you need

- One DGX Spark with nothing else using the GPU. The release figures were
  taken that way; other models or builds on the same Spark lower them.
- This repository at the release's commit and `./start.sh` working in the mode
  you want to measure ([INSTALL-MANUAL](INSTALL-MANUAL.md) for the steps by
  hand).
- [RigMark](https://github.com/alexellis/rigmark) at the commit the result
  names (0.4.1: `40fabcaf6e96`, protocol 1.1.0).

Check the receipts you are comparing against first:

```sh
cd results/2026-11-23-release-0.4.1 && sha256sum -c SHA256SUMS
```

## The release run

[`raw/run_image.sh`](../results/2026-11-23-release-0.4.1/raw/run_image.sh) is
the script that produced the 0.4.1 figures. It is kept as it ran, so its paths
are the measuring machine's; these are its commands with the paths left to
you. For each mode:

```sh
MODE=strict ./start.sh          # then again with MODE=spark
cd /path/to/rigmark
EB='{"chat_template_kwargs":{"reasoning_effort":"low"}}'

# code suite: decode, cold and replayed prefill, 1/2/4/8 concurrent requests
./rigmark run --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas \
  --metadata metadata.json --comparison-id inkling2-atlas \
  --runs 2 --prefill-runs 2 --prefill-depths 8192,32768 \
  --concurrency 1,2,4,8 --concurrency-runs 2 --extra-body "$EB" \
  --label sparkinkling-strict-code --output strict-code.json

# prose suite: decode again, 1/4/8 concurrent prose requests
./rigmark run --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas \
  --metadata metadata.json --comparison-id inkling2-atlas \
  --runs 2 --concurrency 1,4,8 --concurrency-runs 2 --extra-body "$EB" \
  --label sparkinkling-strict-prose --concurrency-workload prose --skip-prefill \
  --output strict-prose.json
```

`metadata.json` describes your run (hardware, image tag, drafter, competing
traffic); the files we used are `raw/metadata-image-*.json`. Fill it in
honestly: the 0.4.1 receipts carry a labelling error from a metadata file that
was not updated, which the result discloses.

The run takes about ten minutes a mode. Reasoning effort is `low` and
temperature 0 throughout, as RigMark sets it.

## Reading the result

The tables report the median over each suite's repetitions, and
`RESULT.md` lists the range where it matters. Two things to expect:

- Text is not byte-identical between runs with the drafter on, so run lengths
  and decode rates move a few percent between repetitions
  ([LIMITATIONS](LIMITATIONS.md#fidelity)).
- Decode rates depend on what the model writes. RigMark's code, prose and
  structured prompts accept drafts very differently; do not compare a figure
  across workloads.

A difference of a few percent from our figures is noise. A number is a result
when it comes with its receipts: to report one, use the performance issue
template and attach the RigMark JSON and the engine log
(`docker logs atlas-sparkinkling`).

## The functional check

[`raw/rc-check.sh`](../results/2026-11-23-release-0.4.1/raw/rc-check.sh) ran
the release's smoke-level checks in both modes: the task probe
(`raw/task_probe.py`, 30 arithmetic questions and 10 tool calls), blocking and
streamed tool calls (`raw/tooltest.py`, `raw/argstream.py`), forced tool
choices and a guarded call (`raw/forced_stream.py`), three images
(`raw/vis_chat.py` with the PNGs beside it) and a voice-agent turn pattern
(`raw/voice_turns.py`). Each takes the server's port or uses 8895. Their
output for the release is `raw/rc-check.out`.

## The vLLM columns

The comparison columns are vLLM's own Inkling 2 Mini image
(`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`) on the same Spark with
the same RigMark protocol, with and without its DSpark drafter, measured
2026-11-20. Receipts and the metadata that names its settings are in
[`results/2026-11-21-release-0.1.0/raw/vllm-*`](../results/2026-11-21-release-0.1.0/raw/).
They have not been re-measured since, so a newer vLLM image may differ.
