#!/bin/bash
# Check the rebuilt SparkInkling image (Spark default, LoopCD option) on 04, voice resident.
set -u
cd ~/rebuild-20261125/sparkinkling
R=~/rebuild-20261125/check; mkdir -p $R
G=~/inkling2/parse/greedy_eq.py; OLD=~/inkling2/rig
up() { # name, env...
  local n=$1; shift
  env "$@" PULL=0 ./start.sh > $R/$n.start.log 2>&1 || { echo "START-FAILED $n"; tail -5 $R/$n.start.log; return 1; }
  docker logs atlas-sparkinkling > $R/$n.server.log 2>&1
  echo "== $n: $(grep -o 'mode [a-z]*, profile [a-z]*, drafter [a-z0-9]*, LoopCD [a-z-]*' $R/$n.start.log) pool $(sed 's/\x1b\[[0-9;]*m//g' $R/$n.server.log | grep -o '= [0-9]* max KV' | head -1)"
  docker logs atlas-sparkinkling 2>&1 | grep -o '"loopcd":"[a-z-]*"\|"mode":"[a-z]*"' | sort -u | tr '\n' ' '; echo
}
down() { docker logs atlas-sparkinkling > $R/$1.server.log 2>&1; echo "errors: $(grep -c ' ERROR ' $R/$1.server.log)"; ./start.sh stop >/dev/null 2>&1; }
# A: no MODE, no LOOPCD: the default must be Spark, LoopCD off, text == 0.5.0 image
up default GPU_MEMORY_UTILIZATION=0.50 && {
  for c in 1 2; do python3 -I $G $R/greedy-spark-c$c.json 320 $c >/dev/null
    echo "greedy spark c$c vs 0.5.0 image: $(python3 -I $G compare $OLD/greedy050-spark-dflash2-c$c.json $R/greedy-spark-c$c.json | tail -1)"; done
  python3 -I bench/task_probe.py 8895 > $R/probe-spark.json 2>/dev/null; grep -ho '"math"[^}]*\|"tools"[^}]*' $R/probe-spark.json | cut -c1-60
  down default; }
# B: Strict, LoopCD off: text == 0.5.0 image
up strict MODE=strict GPU_MEMORY_UTILIZATION=0.50 && {
  python3 -I $G $R/greedy-strict-c1.json 320 1 >/dev/null
  echo "greedy strict c1 vs 0.5.0 image: $(python3 -I $G compare $OLD/greedy050-strict-dflash2-c1.json $R/greedy-strict-c1.json | tail -1)"
  down strict; }
# C: LoopCD on / skip-thinking, saver (its pool is the profile's share, voice or not)
for l in on skip-thinking; do
  for m in spark strict; do
    up saver-$m-loopcd-$l MODE=$m PROFILE=saver LOOPCD=$l && {
      python3 -I $G $R/greedy-$m-loopcd-$l-c1.json 320 1 >/dev/null
      echo "greedy $m loopcd=$l c1 vs off: $(python3 -I $G compare $OLD/greedy050-$m-dflash2-c1.json $R/greedy-$m-loopcd-$l-c1.json | tail -1)"
      python3 -I bench/task_probe.py 8895 > $R/probe-$m-loopcd-$l.json 2>/dev/null; grep -ho '"math"[^}]*\|"tools"[^}]*' $R/probe-$m-loopcd-$l.json | cut -c1-60
      down saver-$m-loopcd-$l; }
  done
done
# D: saver pools with LoopCD off, same session, for the comparison
for m in spark strict; do up saver-$m-off MODE=$m PROFILE=saver && down saver-$m-off; done
echo CHECK-DONE $(date -u +%H:%M:%SZ)
