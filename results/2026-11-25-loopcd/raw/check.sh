#!/bin/bash
# Functional checks: off == base (greedy + 40-prompt hashes), on runs, drafts on == off under LoopCD, per mode.
set -u
cd ~/inkling2-loopcd
mkdir -p res
for mode in ${MODES:-spark strict}; do
  for arm in base off on skip-thinking; do
    b=new; lc=$arm; [ $arm = base ] && { b=base; lc=off; }
    ./serve.sh $mode $lc $b || continue
    python3 -I ~/inkling2-loopcd/tools/parse/greedy3.py res/g3-$mode-$arm.json
    python3 -I ~/inkling2-loopcd/tools/tune_suite.py 1 res/suite-$mode-$arm-c1.json | tail -1
    docker logs inkling2-loopcd 2>&1 | sed "s/\x1b\[[0-9;]*m//g" > res/check-$mode-$arm.log
    echo "  $mode $arm: $(grep -E 'max KV tokens|KV window' res/check-$mode-$arm.log | cut -c60-200 | tr '\n' ' ')"
    echo "  loopcd: $(grep -c 'LoopCD' res/check-$mode-$arm.log) lines, unguided/unstamped: $(grep -c 'runs unguided\|guided throughout' res/check-$mode-$arm.log), errors $(grep -c ' ERROR ' res/check-$mode-$arm.log)"
  done
  # LoopCD with drafts off: the text drafts on must reproduce
  DRAFT= ./serve.sh $mode on && python3 -I ~/inkling2-loopcd/tools/parse/greedy3.py res/g3-$mode-on-nodraft.json
  python3 - $mode <<'PY'
import json, sys, hashlib
m = sys.argv[1]
def g(a):
    try: return json.load(open(f"res/g3-{m}-{a}.json"))
    except Exception: return None
def s(a):
    try: return [x["sha"] for x in json.load(open(f"res/suite-{m}-{a}-c1.json"))]
    except Exception: return None
print(m, "greedy off==base:", g("off") == g("base"), " suite off==base:", s("off") == s("base"))
print(m, "greedy on!=off:", g("on") != g("off"), " on drafts==nodraft:", g("on") == g("on-nodraft"))
print(m, "suite on vs off differ:", sum(a != b for a, b in zip(s("on") or [], s("off") or [])), "of", len(s("off") or []))
PY
done
docker rm -f inkling2-loopcd >/dev/null 2>&1; echo CHECK-DONE $(date -u +%H:%M:%SZ)
