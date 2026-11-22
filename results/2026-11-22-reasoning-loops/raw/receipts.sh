#!/bin/bash
# receipts queue after the forcing cut30 run: forcing build full 150 at low and at high (32K), then vLLM temperature 1.0 on the 30
set -u
cd ~/inkling2/quality
while pgrep -f '[q]uality_eval.py' >/dev/null; do sleep 20; done
mv quality_eval.py.next quality_eval.py
python3 quality_eval.py --base http://127.0.0.1:8895/v1 --model m --suite mmlu --max-tokens 8192 --conc 8 --extra '{"reasoning_effort": "low"}' --out tf-mmlu-low8k.jsonl | tail -1
python3 quality_eval.py --base http://127.0.0.1:8895/v1 --model m --suite mmlu --max-tokens 32768 --conc 8 --extra '{"reasoning_effort": "high"}' --out tf-mmlu-high32k.jsonl | tail -1
docker rm -f inkling2-atlas >/dev/null 2>&1
docker run -d --name vllm-inkling-ctl --gpus all --ipc host --network host -v $HOME/models/inkling-2-mini:/model:ro vllm/vllm-openai:inkling-2-mini --model /model --served-model-name inkling-2-mini --gpu-memory-utilization 0.5 --max-model-len 40000 --port 8000 >/dev/null
for i in $(seq 120); do curl -sf localhost:8000/health >/dev/null && break; sleep 5; done
python3 quality_eval.py --base http://127.0.0.1:8000/v1 --model inkling-2-mini --suite mmlu --only 4,15,20,21,28,35,43,56,58,59,65,71,72,84,88,89,90,91,92,93,94,96,98,103,105,110,112,119,126,127 --max-tokens 8192 --conc 8 --temperature 1.0 --out vllm-mmlu-cut8k-t1.jsonl | tail -1
docker rm -f vllm-inkling-ctl >/dev/null 2>&1
echo RECEIPTS-DONE
