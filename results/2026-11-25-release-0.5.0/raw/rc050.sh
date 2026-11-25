#!/bin/bash
# functional check of the release candidate image through ./start.sh, both modes (voice resident, util 0.5)
set -u
cd ~/inkling2/sparkinkling
B=bench
run() {
  MODE=$1 GPU_MEMORY_UTILIZATION=0.50 PULL=0 ./start.sh >/tmp/smoke050-start-$1.log 2>&1 &
  for i in $(seq 200); do curl -sf localhost:8895/health >/dev/null && break; sleep 3; done
  echo "== $1 $(./start.sh status 2>&1 | head -2 | tr '\n' ' ')"
  python3 -I $B/task_probe.py 8895 > ~/inkling2/dbg/smoke050-probe-$1.json 2>/dev/null; grep -ho "\"math\"[^}]*\|\"tools\"[^}]*" ~/inkling2/dbg/smoke050-probe-$1.json | cut -c1-60
  python3 -I $B/tooltest.py 2>&1 | cut -c1-70
  python3 -I $B/argstream.py | cut -c1-80
  python3 -I $B/forced_stream.py | cut -c1-150
  (cd $B && python3 -I vis_chat.py images/invoice.png "Transcribe all the text in this image exactly, line by line." images/grid.png "This is a 3x3 grid of labelled coloured rectangles. For each label (A1..C3) give its colour, row by row." images/shapes.png "Describe this image in one sentence.") | cut -c1-330
  [ "$1" = strict ] && python3 -I $B/voice_turns.py 4 | cut -c1-120
  echo "errors: $(docker logs atlas-sparkinkling 2>&1 | grep -c " ERROR ")"
  ./start.sh stop >/dev/null 2>&1
}
greedy() {
  for d in none dflash2; do
    MODE=$1 DRAFTER=$d GPU_MEMORY_UTILIZATION=0.50 PULL=0 ./start.sh >/tmp/greedy050-start-$1-$d.log 2>&1 || { echo START-FAILED $1 $d; continue; }
    for c in 1 2 4; do python3 -I ~/inkling2/parse/greedy_eq.py ~/inkling2/rig/greedy050-$1-$d-c$c.json 320 $c >/dev/null; done
    ./start.sh stop >/dev/null 2>&1
  done
  for c in 1 2 4; do echo "greedy $1 c$c drafts vs none: $(python3 -I ~/inkling2/parse/greedy_eq.py compare ~/inkling2/rig/greedy050-$1-none-c1.json ~/inkling2/rig/greedy050-$1-dflash2-c$c.json | tail -1)"; done
}
run strict
run spark
greedy strict
greedy spark
echo SMOKE-DONE; date -u +%H:%M:%SZ
