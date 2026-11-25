#!/bin/bash
# After run.sh: 32K prefill (64K cap) and plain decode with drafts off, off vs on, both modes.
set -u
cd ~/inkling2-loopcd
while pgrep -f "[r]un.sh" >/dev/null; do sleep 30; done
for mode in spark strict; do
  for arm in off on; do
    MAXLEN=65536 ./serve.sh $mode $arm || continue
    echo "== prefill $mode $arm $(date -u +%H:%M:%SZ)"
    python3 -I tools/parse/sgl_like.py 512 16 99 >/dev/null
    for s in 1 2; do python3 -I tools/parse/sgl_like.py 32768 64 $s; done
    DRAFT= ./serve.sh $mode $arm || continue
    echo "== nodraft $mode $arm"
    python3 -I tools/parse/dec_rate.py 3
  done
done
docker rm -f inkling2-loopcd >/dev/null 2>&1; echo EXTRA-DONE $(date -u +%H:%M:%SZ)
