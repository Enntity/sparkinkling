#!/bin/bash
# run_model.sh TAG PORT MODEL: the three suites against one served model on this Spark
set -u
cd ~/inkling2/quality
for suite in gsm8k mmlu humaneval; do
  python3 quality_eval.py --base http://127.0.0.1:$2/v1 --model $3 --suite $suite --out $1-$suite.jsonl --conc 8 --max-tokens 8192 > $1-$suite.summary 2>&1
  echo "$1 $suite $(cat $1-$suite.summary | tail -1)"
done
docker run --rm --network none --entrypoint python3 -v $HOME/inkling2/quality:/w:ro atlas-release-builder:1.93.1 /w/he_exec.py /w/$1-humaneval.jsonl > $1-humaneval-exec.json 2>/dev/null
echo "$1 humaneval-exec $(python3 -c "import json; d=json.load(open(\"$1-humaneval-exec.json\")); print(d[\"passed\"], \"/\", d[\"n\"])")"
