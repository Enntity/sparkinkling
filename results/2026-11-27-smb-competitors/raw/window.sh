#!/bin/bash
# SparkModelBench of vLLM (DSpark) and knapcio v2.9.7 on this Spark, voice engines suspended for the window
set -u
L="$HOME/.local/bin/node $HOME/.local/lib/node_modules/lloom/bin/lloom.mjs"
C=~/inkling2/smbcomp; R=$C/out; S=~/inkling2/smb
health() { for i in $(seq 360); do curl -sf localhost:8000/health >/dev/null && return 0; sleep 5; done; return 1; }
smb() { # label meta
  (cd $S && python3 run.py --base-url http://127.0.0.1:8000 --model inkling-2-mini --metadata $C/$2 \
     --comparison-id sparkinkling-0.5.1 --effort low --out $R/smb-$1-full > $R/smb-$1-full.log 2>&1); echo "full $1 exit $? $(date -u +%H:%M:%SZ)"
  (cd $S && python3 run.py --base-url http://127.0.0.1:8000 --model inkling-2-mini --metadata $C/$2 \
     --comparison-id sparkinkling-0.5.1 --effort low --out $R/smb-$1-concurrency --lanes concurrency > $R/smb-$1-conc.log 2>&1); echo "concurrency $1 exit $? $(date -u +%H:%M:%SZ)"
}
echo "voice-down $(date -u +%H:%M:%SZ)"
for r in drama-tensorfold parakeet-nemo; do $L suspend $r --apply --yes 2>&1 | grep -m1 "\"applied\""; done
for i in $(seq 60); do nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q . || break; sleep 2; done
echo "gpu apps left: $(nvidia-smi --query-compute-apps=process_name,used_memory --format=csv,noheader | tr "\n" ";")"
M=~/models/sparkinkling/thinkingmachines--Inkling-2-Mini
docker run -d --name smb-vllm-inkling --gpus all --ipc host --network host -v $M:/model:ro vllm/vllm-openai:inkling-2-mini \
  --model /model --served-model-name inkling-2-mini --max-model-len 270336 --reasoning-parser inkling --enable-auto-tool-choice \
  --tool-call-parser inkling --gpu-memory-utilization 0.80 \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}' --port 8000 >/dev/null
if health; then echo "vllm up $(date -u +%H:%M:%SZ)"; smb vllm-dspark meta-vllm-dspark.json; else echo START-FAILED vllm; fi
docker logs smb-vllm-inkling > $R/smb-vllm-dspark.server.log 2>&1; docker rm -f smb-vllm-inkling >/dev/null
cd $C/knapcio
export MODEL_DIR=$M DFLASH2_DIR=$C/dflash2 CTX=270336 PORT=8000
scripts/launch.sh up > $R/smb-knapcio.up.log 2>&1
if health; then echo "knapcio up $(date -u +%H:%M:%SZ)"; smb knapcio meta-knapcio.json; else echo START-FAILED knapcio; tail -5 $R/smb-knapcio.up.log; fi
docker logs inkling-2-mini > $R/smb-knapcio.server.log 2>&1; scripts/launch.sh down > /dev/null 2>&1
for r in drama-tensorfold parakeet-nemo; do $L resume $r --apply --yes 2>&1 | grep -m1 "\"applied\""; sleep 5; done
for i in $(seq 120); do curl -sf localhost:8203/health >/dev/null && curl -sf localhost:8204/health >/dev/null && break; sleep 3; done
curl -sf localhost:8204/health >/dev/null || $L resume parakeet-nemo --apply --yes 2>&1 | grep -m1 "\"applied\""
curl -sf localhost:8203/health >/dev/null || $L resume drama-tensorfold --apply --yes 2>&1 | grep -m1 "\"applied\""
echo "voice-up $(date -u +%H:%M:%SZ) drama $(curl -s -o /dev/null -w %{http_code} localhost:8203/health) parakeet $(curl -s -o /dev/null -w %{http_code} localhost:8204/health)"
echo WINDOW-DONE
