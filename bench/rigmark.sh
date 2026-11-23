#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-only
# Run the RigMark suites behind SparkInkling's published figures against the
# server ./start.sh started, in the mode it is serving. Nothing else should be
# using the Spark. See docs/REPRODUCE.md.
#
#   RIGMARK=/path/to/rigmark bench/rigmark.sh LABEL METADATA.json [OUTDIR]
#
# LABEL names the run (for example "strict"); METADATA.json describes it
# (hardware, image tag, drafter, competing traffic); OUTDIR defaults to the
# current directory. Writes LABEL-code.json and LABEL-prose.json there.
set -euo pipefail
[[ $# -ge 2 && $# -le 3 ]] || { sed -n '3,12p' "$0" >&2; exit 2; }
label=$1 metadata=$(realpath "$2") out=$(realpath "${3:-.}")
: "${RIGMARK:?set RIGMARK to a RigMark checkout}"
url=${SPARKINKLING_URL:-http://127.0.0.1:8895}
model=${SERVED_MODEL_NAME:-inkling-2-mini-atlas}
extra='{"chat_template_kwargs":{"reasoning_effort":"low"}}'
curl -sf "$url/health" >/dev/null || { echo "no server at $url; run ./start.sh first" >&2; exit 1; }
cd "$RIGMARK"
# code suite: decode, cold and replayed prefill, 1/2/4/8 concurrent requests
./rigmark run --base-url "$url" --model "$model" --metadata "$metadata" --comparison-id inkling2-atlas \
  --runs 2 --prefill-runs 2 --prefill-depths 8192,32768 --concurrency 1,2,4,8 --concurrency-runs 2 \
  --extra-body "$extra" --label "sparkinkling-$label-code" --output "$out/$label-code.json"
# prose suite: decode again, 1/4/8 concurrent prose requests
./rigmark run --base-url "$url" --model "$model" --metadata "$metadata" --comparison-id inkling2-atlas \
  --runs 2 --concurrency 1,4,8 --concurrency-runs 2 --concurrency-workload prose --skip-prefill \
  --extra-body "$extra" --label "sparkinkling-$label-prose" --output "$out/$label-prose.json"
echo "wrote $out/$label-code.json and $out/$label-prose.json"
