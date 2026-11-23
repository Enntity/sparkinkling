<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Tool-call pattern guard

SparkInkling runs the same tool-call guard as SparkQwen and SparkGLM, in both
modes: a bounded CPU filter over each parsed tool call's arguments that blocks
recognizable exfiltration patterns. There is no second model and no GPU pass.
Ordinary prose and reasoning are not scanned.

What it recognizes, what it lets through and what it cannot see are the
engine's and are documented once, in
[SparkQwen's TOOL-GUARD](https://github.com/Enntity/sparkqwen/blob/main/docs/TOOL-GUARD.md):
the argument fields it reads, cloud metadata addresses, the two named callback
hosts, credential-file and token patterns, and the limits of a lexical filter.
Read that page before relying on the guard. It is a pattern filter, not a
sandbox: stronger guarantees need access controls and network policy in the
tool executor.

## What is different here

Inkling reasons before it calls a tool and its calls can be long, so a client
may ask for a call's arguments as they are written: the request body field
`stream_tool_arguments: true` (an Atlas extension to `/v1/chat/completions`).
Only a request that asks gets them; every other request's calls are held until
they pass.

| `TOOL_GUARD` | What a client sees |
|---|---|
| `stream` (default) | A request with `stream_tool_arguments: true`: `function.arguments` streams as it is generated, and the guard checks the call when it ends. A call it blocks, or one cut off before its end, finishes the response with `finish_reason: "content_filter"` and `guard_stop: "tool_call_guard"` instead of `tool_calls`. Any other request: as under `on`. |
| `on` | Each call is held until its complete arguments pass, as in SparkQwen and SparkGLM. A blocked call is never shown. `stream_tool_arguments` is ignored. |
| `off` | No check. |

**A client that asks for streamed arguments is part of the guard.** The
blocked arguments have already been sent when the verdict arrives, so it must
not run any call from a response that finished `content_filter`, nor run a
call before the response finishes. A client that cannot promise that should
not send `stream_tool_arguments`.

SparkInkling 0.4.1 streamed every request's calls under `stream`; a client
that did not read the finish reason could run a call the guard had blocked.
From 0.4.2 that needs the request to ask.

In the 0.4.1 check a streamed call to a cloud metadata address sent its
arguments in 31 chunks and then finished `content_filter` with
`guard_stop: tool_call_guard`
([result](../results/2026-11-23-release-0.4.1/RESULT.md)).

## Configure

Set these in `.env` before starting:

```sh
TOOL_GUARD=stream
TOOL_GUARD_MAX_BYTES=1048576
# Optional comma-separated exact hosts, without schemes, ports or wildcards:
#TOOL_GUARD_ALLOW_HOSTS=uploads.example.org
#TOOL_GUARD_DENY_HOSTS=blocked.example.org
```

Direct container operators use `SPARKINKLING_TOOL_GUARD`,
`SPARKINKLING_TOOL_GUARD_MAX_BYTES`, `SPARKINKLING_TOOL_GUARD_ALLOW_HOSTS` and
`SPARKINKLING_TOOL_GUARD_DENY_HOSTS`. Atlas's flags are `--tool-guard`,
`--tool-guard-max-bytes`, `--tool-guard-allow-host` and
`--tool-guard-deny-host`. Requests cannot change the server's policy, and a
profile may not set these flags. The byte limit is 1 to 67108864.

Each blocked response logs a WARN event with a reason code and without the
rejected arguments.
