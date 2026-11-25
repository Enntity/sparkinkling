#!/bin/bash
# Cost of LoopCD: decode (C1 code/prose, 40-prompt suite C1/C2) and 32K prefill, off vs on, per mode.
set -u
cd ~/inkling2-loopcd
for mode in ${MODES:-spark strict}; do
  for arm in ${ARMS:-off on}; do
    ./serve.sh $mode $arm || continue
    echo "== $mode $arm $(date -u +%H:%M:%SZ) $(docker logs inkling2-loopcd 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -oE 'max KV tokens[^,]*' | head -1)"
    python3 -I ~/inkling2-loopcd/tools/parse/sgl_like.py 512 16 99 >/dev/null
    python3 -I ~/inkling2-loopcd/tools/parse/dec_rate.py 3
    for c in 1 2; do echo " suite c$c"; python3 -I ~/inkling2-loopcd/tools/tune_suite.py $c res/speed-$mode-$arm-c$c.json; done
    for s in 1 2; do python3 -I ~/inkling2-loopcd/tools/parse/sgl_like.py 32768 64 $s; done
  done
done
docker rm -f inkling2-loopcd >/dev/null 2>&1; echo SPEED-DONE $(date -u +%H:%M:%SZ)
