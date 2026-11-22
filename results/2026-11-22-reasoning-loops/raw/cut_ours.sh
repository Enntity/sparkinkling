#!/bin/bash
# after the vLLM control: our engine on the same 30 questions, Spark then Strict (saver, 0.4.1 candidate), C8, 8192
set -u
while pgrep -f '[q]uality_eval.py --base http://127.0.0.1:8000' >/dev/null || pgrep -f '[d]eep_vllm.py' >/dev/null; do sleep 20; done
docker rm -f vllm-inkling-ctl >/dev/null 2>&1
cd ~/inkling2/sparkinkling; IMG=$(install/build.sh --tag)
for mode in spark strict; do
  PROFILE=saver MODE=$mode MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/quality/cut-$mode.start.log 2>&1 || { echo START-FAILED $mode; continue; }
  (cd ~/inkling2/quality && python3 quality_eval.py --base http://127.0.0.1:8895/v1 --model inkling-2-mini-atlas --suite mmlu --only 4,15,20,21,28,35,43,56,58,59,65,71,72,84,88,89,90,91,92,93,94,96,98,103,105,110,112,119,126,127 --max-tokens 8192 --conc 8 --out ours-$mode-mmlu-cut8k.jsonl | tail -1)
done
./start.sh stop >/dev/null 2>&1; echo CUT-DONE
