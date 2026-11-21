#!/bin/bash
# RigMark on the SparkInkling image through ./start.sh, Strict then Spark (default profile, DSpark)
set -u
cd ~/inkling2/sparkinkling
IMG=$(install/build.sh --tag)
for mode in strict spark; do
  MODE=$mode MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/rig/img-$mode.start.log 2>&1 || { echo START-FAILED $mode; continue; }
  cd ~/qual-20261110/rigmark
  EB={\"chat_template_kwargs\":{\"reasoning_effort\":\"low\"}}
  M=$HOME/inkling2/rig/metadata-image-$mode.json
  ./rigmark run --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas --metadata $M --comparison-id inkling2-atlas --runs 2 --prefill-runs 2 --concurrency 1,2,4,8 --concurrency-runs 2 --extra-body "$EB" --label sparkinkling-$mode-code --prefill-depths 8192,32768 --output ~/inkling2/rig/img-$mode-code.json > ~/inkling2/rig/img-$mode.log 2>&1
  ./rigmark run --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas --metadata $M --comparison-id inkling2-atlas --runs 2 --concurrency 1,4,8 --concurrency-runs 2 --extra-body "$EB" --label sparkinkling-$mode-prose --concurrency-workload prose --skip-prefill --output ~/inkling2/rig/img-$mode-prose.json >> ~/inkling2/rig/img-$mode.log 2>&1
  docker logs atlas-sparkinkling > ~/inkling2/rig/img-$mode.server.log 2>&1
  cd ~/inkling2/sparkinkling
done
./start.sh stop
echo IMAGE-RIG-DONE
