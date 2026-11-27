#!/bin/bash
# 0.5.1 RC functional check through ./start.sh, both modes, voice resident (util 0.5); saver pools; greedy drafts vs none
set -u
cd ~/inkling2/sparkinkling
B=bench; R=~/inkling2/rig/r051
pool() { docker logs atlas-sparkinkling 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -o "[0-9]* max KV tokens" | tail -1; }
run() {
  MODE=$1 GPU_MEMORY_UTILIZATION=0.50 PULL=0 ./start.sh > $R/smoke-$1.start.log 2>&1 || { echo START-FAILED $1; tail -5 $R/smoke-$1.start.log; return; }
  echo "== $1 $(./start.sh status 2>&1 | head -2 | tr '\n' ' ')"
  python3 -I $B/task_probe.py 8895 > $R/smoke-probe-$1.json 2>/dev/null; grep -ho "\"math\"[^}]*\|\"tools\"[^}]*" $R/smoke-probe-$1.json | cut -c1-60
  python3 -I $B/tooltest.py 2>&1 | cut -c1-70
  python3 -I $B/argstream.py | cut -c1-80
  python3 -I $B/forced_stream.py | cut -c1-150
  (cd $B && python3 -I vis_chat.py images/invoice.png "Transcribe all the text in this image exactly, line by line." images/grid.png "This is a 3x3 grid of labelled coloured rectangles. For each label (A1..C3) give its colour, row by row." images/shapes.png "Describe this image in one sentence.") | cut -c1-330
  [ "$1" = strict ] && python3 -I $B/voice_turns.py 4 | cut -c1-120
  echo "errors: $(docker logs atlas-sparkinkling 2>&1 | grep -c " ERROR ")"
  docker logs atlas-sparkinkling > $R/smoke-$1.server.log 2>&1
  ./start.sh stop >/dev/null 2>&1
}
saver() {
  MODE=$1 PROFILE=saver PULL=0 ./start.sh > $R/saver-$1.start.log 2>&1 || { echo START-FAILED saver $1; return; }
  echo "pool saver $1: $(pool)"; docker logs atlas-sparkinkling > $R/saver-$1.server.log 2>&1
  ./start.sh stop >/dev/null 2>&1
}
greedy() {
  for d in none dflash2; do
    MODE=$1 DRAFTER=$d GPU_MEMORY_UTILIZATION=0.50 PULL=0 ./start.sh > $R/greedy-start-$1-$d.log 2>&1 || { echo START-FAILED $1 $d; continue; }
    for c in 1 2 4; do python3 -I ~/inkling2/parse/greedy_eq.py $R/greedy-$1-$d-c$c.json 320 $c >/dev/null; done
    ./start.sh stop >/dev/null 2>&1
  done
  for c in 1 2 4; do echo "greedy $1 c$c drafts vs none: $(python3 -I ~/inkling2/parse/greedy_eq.py compare $R/greedy-$1-none-c1.json $R/greedy-$1-dflash2-c$c.json | tail -1)"; done
}
date -u +%H:%M:%SZ
run strict; run spark
saver strict; saver spark
greedy strict; greedy spark
echo SMOKE-DONE; date -u +%H:%M:%SZ
