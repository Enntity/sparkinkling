#!/bin/bash
# SparkInkling saver (0.4.1 candidate image), Spark then Strict, the three suites each
set -u
cd ~/inkling2/sparkinkling
IMG=$(install/build.sh --tag)
for mode in spark strict; do
  PROFILE=saver MODE=$mode MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/quality/ink-$mode.start.log 2>&1 || { echo START-FAILED $mode; continue; }
  ~/inkling2/quality/run_model.sh ink-$mode 8895 inkling-2-mini-atlas
done
./start.sh stop >/dev/null 2>&1
echo INK-DONE
