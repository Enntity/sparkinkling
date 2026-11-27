#!/bin/bash
# 0.5.1 RC measurement window: voice engines off; default profile both modes: pool + SparkModelBench (full + concurrency); max pools; voice back
set -u
L="$HOME/.local/bin/node $HOME/.local/lib/node_modules/lloom/bin/lloom.mjs"
R=~/inkling2/rig/r051; S=~/inkling2/smb
cd ~/inkling2/sparkinkling
pool() { docker logs atlas-sparkinkling 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -o "[0-9]* max KV tokens" | tail -1; }
echo "voice-down $(date -u +%H:%M:%SZ)"
for r in drama-tensorfold parakeet-nemo; do $L suspend $r --apply --yes 2>&1 | grep -m1 "\"applied\""; done
for i in $(seq 60); do nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q . || break; sleep 2; done
echo "gpu apps left: $(nvidia-smi --query-compute-apps=process_name,used_memory --format=csv,noheader | tr "\n" ";")"
for mode in spark strict; do
  MODE=$mode PULL=0 ./start.sh > $R/smb-$mode.start.log 2>&1 || { echo START-FAILED $mode; tail -5 $R/smb-$mode.start.log; continue; }
  echo "pool default $mode: $(pool)  $(date -u +%H:%M:%SZ)"
  (cd $S && python3 run.py --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas --metadata $R/meta-$mode.json \
     --comparison-id sparkinkling-0.5.1 --effort low --out $R/smb-$mode-full > $R/smb-$mode-full.log 2>&1); echo "full $mode exit $? $(date -u +%H:%M:%SZ)"
  (cd $S && python3 run.py --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas --metadata $R/meta-$mode.json \
     --comparison-id sparkinkling-0.5.1 --effort low --out $R/smb-$mode-concurrency --lanes concurrency > $R/smb-$mode-conc.log 2>&1); echo "concurrency $mode exit $? $(date -u +%H:%M:%SZ)"
  docker logs atlas-sparkinkling > $R/smb-$mode.server.log 2>&1
  ./start.sh stop >/dev/null 2>&1
done
for mode in spark strict; do
  MODE=$mode PROFILE=max PULL=0 ./start.sh > $R/max-$mode.start.log 2>&1 || { echo START-FAILED max $mode; continue; }
  echo "pool max $mode: $(pool)"; docker logs atlas-sparkinkling > $R/max-$mode.server.log 2>&1
  ./start.sh stop >/dev/null 2>&1
done
for r in drama-tensorfold parakeet-nemo; do $L resume $r --apply --yes 2>&1 | grep -m1 "\"applied\""; sleep 5; done
for i in $(seq 120); do curl -sf localhost:8203/health >/dev/null && curl -sf localhost:8204/health >/dev/null && break; sleep 3; done
curl -sf localhost:8204/health >/dev/null || $L resume parakeet-nemo --apply --yes 2>&1 | grep -m1 "\"applied\""
curl -sf localhost:8203/health >/dev/null || $L resume drama-tensorfold --apply --yes 2>&1 | grep -m1 "\"applied\""
echo "voice-up $(date -u +%H:%M:%SZ) drama $(curl -s -o /dev/null -w %{http_code} localhost:8203/health) parakeet $(curl -s -o /dev/null -w %{http_code} localhost:8204/health)"
echo WINDOW-DONE
