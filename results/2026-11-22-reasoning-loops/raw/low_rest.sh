#!/bin/bash
# after cut_ours: GSM8K and HumanEval at reasoning_effort low, SparkInkling Spark saver
set -u
while pgrep -f "[c]ut_ours.sh" >/dev/null; do sleep 20; done
cd ~/inkling2/sparkinkling
PROFILE=saver MODE=spark MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$(install/build.sh --tag) PULL=0 ./start.sh > ~/inkling2/quality/low.start.log 2>&1 || { echo START-FAILED; exit 1; }
cd ~/inkling2/quality
for s in gsm8k humaneval; do
  python3 quality_eval.py --base http://127.0.0.1:8895/v1 --model inkling-2-mini-atlas --suite $s --out ink-spark-$s-low.jsonl --conc 8 --max-tokens 8192 --extra "{\"reasoning_effort\": \"low\"}" | tail -1
done
docker run --rm --network none --entrypoint python3 -v $HOME/inkling2/quality:/w:ro atlas-release-builder:1.93.1 /w/he_exec.py /w/ink-spark-humaneval-low.jsonl > ink-spark-humaneval-low-exec.json
python3 -c "import json; d=json.load(open(\"ink-spark-humaneval-low-exec.json\")); print(\"humaneval low exec\", d[\"passed\"], \"/\", d[\"n\"])"
cd ~/inkling2/sparkinkling && ./start.sh stop >/dev/null 2>&1; echo LOW-DONE
