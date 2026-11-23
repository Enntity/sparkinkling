#!/bin/bash
# The task probe on the SparkInkling image through ./start.sh, Strict then Spark
set -u
cd ~/inkling2/sparkinkling
IMG=$(install/build.sh --tag)
for mode in strict spark; do
  PC=; [[ $mode == strict ]] && PC="PREFIX_CACHE_DIR=$HOME/inkling2/pcache PREFIX_CACHE_GB=16"; env $PC MODE=$mode MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/rig/probe042-$mode.start.log 2>&1 || { echo START-FAILED $mode; continue; }
  python3 -I task_probe-window.py 8895 > ~/inkling2/rig/probe042-img-$mode.json 2> ~/inkling2/rig/probe042-img-$mode.err
  docker logs atlas-sparkinkling > ~/inkling2/rig/probe042-$mode.server.log 2>&1
done
./start.sh stop >/dev/null 2>&1
echo PROBE-DONE
