#!/bin/bash
set -u
cd ~/inkling2/sparkinkling
PROFILE=saver MODE=spark MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$(install/build.sh --tag) PULL=0 ./start.sh > ~/inkling2/quality/effort.start.log 2>&1 || { echo START-FAILED; exit 1; }
cd ~/inkling2/quality
for eff in medium low; do
  python3 quality_eval.py --base http://127.0.0.1:8895/v1 --model inkling-2-mini-atlas --suite mmlu --out ink-spark-mmlu-$eff.jsonl --conc 8 --max-tokens 8192 --extra "{\"reasoning_effort\": \"$eff\"}" | tail -1
done
echo EFFORT-DONE
