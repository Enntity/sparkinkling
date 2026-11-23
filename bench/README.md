<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Benchmark runner and functional-check drivers

## Throughput

`rigmark.sh` runs the two [RigMark](https://github.com/alexellis/rigmark)
suites behind the published figures against the server `./start.sh` started,
in whatever mode it is serving: the code suite (decode, cold and replayed
prefill at 8K and 32K, 1/2/4/8 concurrent requests) and the prose suite
(decode, 1/4/8 concurrent requests), reasoning low. About ten minutes a mode.

```sh
MODE=strict ./start.sh
RIGMARK=/path/to/rigmark bench/rigmark.sh strict metadata.json out/
```

`metadata.json` describes the run (hardware, image tag, drafter, competing
traffic); [REPRODUCE](../docs/REPRODUCE.md) says what goes in it and how to
read the result. It writes `out/strict-code.json` and `out/strict-prose.json`.
`SPARKINKLING_URL` and `SERVED_MODEL_NAME` override the default address and
model name.

## Functional check

The small drivers each release's functional check runs
([REPRODUCE](../docs/REPRODUCE.md#the-functional-check)). They are the scripts
kept under `results/2026-11-23-release-0.4.1/raw/`, with a license line added.
They need only Python 3, talk to the server `./start.sh` starts on
`http://127.0.0.1:8895`, and send greedy requests (temperature 0). Run them
one at a time with nothing else using the Spark. They are smoke checks, not
benchmarks; throughput is measured with
[RigMark](https://github.com/alexellis/rigmark) as REPRODUCE describes.

| Driver | What it checks | Run |
|---|---|---|
| `task_probe.py` | 30 arithmetic problems graded exactly and 10 tool-call prompts graded on tool and arguments, reasoning low | `python3 task_probe.py 8895` (prints one JSON summary) |
| `tooltest.py` | A tool call comes back as an OpenAI tool call, blocking and streamed, with thinking on and off | `python3 tooltest.py` |
| `argstream.py` | A streamed tool call's arguments arrive in many chunks and join to valid JSON | `python3 argstream.py` |
| `forced_stream.py` | Forced tool choices (a named function with thinking on and off, `required`) finish `tool_calls` when streamed; a call to a cloud metadata address streams and then finishes `content_filter` under the default tool guard | `python3 forced_stream.py` |
| `vis_chat.py` | Image input: each image is sent as a base64 data URI with its question | `python3 vis_chat.py images/invoice.png "Transcribe all the text in this image exactly, line by line." images/grid.png "This is a 3x3 grid of labelled coloured rectangles. For each label (A1..C3) give its colour, row by row." images/shapes.png "Describe this image in one sentence."` |
| `voice_turns.py` | A voice-agent prompt shape (a long system prompt, history, three trailing messages rebuilt every turn): time to first token per turn, which shows whether the prefix cache resumes at the fork | `python3 voice_turns.py 4` |

`images/` holds the three synthetic PNGs the image check uses. What each
driver returned for a release is in that release's `raw/rc-check.out`.
