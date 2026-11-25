#!/bin/bash
# 0.5.0 release measurement window: voice engines off; RigMark (default profile) both modes, max-profile pools,
# a 1M-token recall in Spark mode, on image 39e8f22fb0d4; voice engines back
set -u
L="$HOME/.local/bin/node $HOME/.local/lib/node_modules/lloom/bin/lloom.mjs"
cd ~/inkling2/sparkinkling
IMG=$(install/build.sh --tag)
python3 -I ~/inkling2/rig/meta050.py
echo "voice-down $(date -u +%H:%M:%SZ)"
for r in drama-tensorfold parakeet-nemo; do $L suspend $r --apply --yes 2>&1 | grep -m1 "\"applied\""; done
for i in $(seq 60); do nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q . || break; sleep 2; done
echo "gpu apps left: $(nvidia-smi --query-compute-apps=process_name,used_memory --format=csv,noheader | tr "\n" ";")"
bash ~/inkling2/rig/run050.sh > ~/inkling2/rig/run050.log 2>&1; tail -1 ~/inkling2/rig/run050.log
for mode in strict spark; do
  grep -hE "KV window|max KV tokens" ~/inkling2/rig/img050-$mode.server.log | sed "s/\x1b\[[0-9;]*m//g" | cut -c1-220 | sed "s/^/default $mode: /"
  MODE=$mode PROFILE=max MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/rig/max050-$mode.start.log 2>&1 || echo START-FAILED max $mode
  docker logs atlas-sparkinkling > ~/inkling2/rig/max050-$mode.server.log 2>&1
  grep -hE "KV window|max KV tokens" ~/inkling2/rig/max050-$mode.server.log | sed "s/\x1b\[[0-9;]*m//g" | cut -c1-220 | sed "s/^/max $mode: /"
  ./start.sh stop >/dev/null 2>&1
done
MODE=spark MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/rig/needle050.start.log 2>&1 || echo START-FAILED needle
echo "needle from $(date -u +%H:%M:%SZ)"
sed "s/\"model\": \"m\"/\"model\": \"inkling-2-mini-atlas\"/" ~/inkling2/parse/needle.py > ~/inkling2/rig/needle050.py
python3 -I ~/inkling2/rig/needle050.py 850000 > ~/inkling2/rig/needle050.out 2>&1; cat ~/inkling2/rig/needle050.out
docker logs atlas-sparkinkling > ~/inkling2/rig/needle050.server.log 2>&1
./start.sh stop >/dev/null 2>&1
for r in drama-tensorfold parakeet-nemo; do $L resume $r --apply --yes 2>&1 | grep -m1 "\"applied\""; done
for i in $(seq 120); do curl -sf localhost:8203/health >/dev/null && curl -sf localhost:8204/health >/dev/null && break; sleep 3; done
echo "voice-up $(date -u +%H:%M:%SZ) drama $(curl -s -o /dev/null -w %{http_code} localhost:8203/health) parakeet $(curl -s -o /dev/null -w %{http_code} localhost:8204/health)"
echo WINDOW-DONE
