#!/bin/bash
# The task probe on the SparkInkling image through ./start.sh, Strict then Spark
set -u
cd ~/inkling2/sparkinkling
IMG=$(install/build.sh --tag)
for mode in strict spark; do
  MODE=$mode MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/rig/probe-$mode.start.log 2>&1 || { echo START-FAILED $mode; continue; }
  python3 -I results/2026-11-21-release-0.1.0/raw/task_probe.py 8895 > ~/inkling2/rig/probe-img-$mode.json 2> ~/inkling2/rig/probe-img-$mode.err
done
./start.sh stop >/dev/null 2>&1
echo PROBE-DONE
