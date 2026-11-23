#!/bin/bash
# 0.4.2 release measurement window: voice engines off, task probe + RigMark (default profile) on image b1e18bf91437, voice engines back
set -u
L="$HOME/.local/bin/node $HOME/.local/lib/node_modules/lloom/bin/lloom.mjs"
cd ~/inkling2/sparkinkling
python3 -I ~/inkling2/rig/meta042.py
echo "voice-down $(date -u +%H:%M:%SZ)"
for r in drama-tensorfold parakeet-nemo; do $L suspend $r --apply --yes 2>&1 | grep -m1 "\"applied\""; done
for i in $(seq 60); do nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q . || break; sleep 2; done
echo "gpu apps left: $(nvidia-smi --query-compute-apps=process_name,used_memory --format=csv,noheader | tr "\n" ";")"
~/inkling2/rig/probe042.sh > ~/inkling2/rig/probe-042.out 2>&1
grep -h "\"math\"" ~/inkling2/rig/probe042-img-*.json | cut -c1-60
bash ~/inkling2/rig/run042.sh > ~/inkling2/rig/run042.log 2>&1; tail -1 ~/inkling2/rig/run042.log
./start.sh stop >/dev/null 2>&1
for r in drama-tensorfold parakeet-nemo; do $L resume $r --apply --yes 2>&1 | grep -m1 "\"applied\""; done
for i in $(seq 120); do curl -sf localhost:8203/health >/dev/null && curl -sf localhost:8204/health >/dev/null && break; sleep 3; done
echo "voice-up $(date -u +%H:%M:%SZ) drama $(curl -s -o /dev/null -w %{http_code} localhost:8203/health) parakeet $(curl -s -o /dev/null -w %{http_code} localhost:8204/health)"
echo WINDOW-DONE
