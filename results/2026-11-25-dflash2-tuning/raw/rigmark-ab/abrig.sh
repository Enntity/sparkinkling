#!/bin/bash
# RigMark short-code C2/C4 and short-prose C4 for one drafting arm on the dev build (serving code = 0.5.0's engine):
# abrig.sh <strict|spark> <label> [extra -e flags...]   (product base env per mode; extras override)
set -u
cd ~/inkling2
mode=$1; label=$2; shift 2
if [ "$mode" = spark ]; then M=sparkinkling/thinkingmachines--Inkling-2-Mini+spark-nvfp4; else M=inkling-2-mini; fi
P="--enable-prefix-caching --ssm-cache-slots=64 --tool-max-tokens=32768 --default-chat-template-kwargs={\"reasoning_effort\":\"low\"} --dflash --dflash-gamma=8 --num-drafts=7 --draft-model=/models/sparkinkling/incoai--Inkling-2-Mini-DFlash2"
BASE="-e ATLAS_QWEN4EXP_AUX_PINNED=1 -e ATLAS_GLM_PC_BRANCH=1 -e ATLAS_GLM_PC_BRANCH_MIN=512 -e ATLAS_DFLASH_ADAPTIVE=1 -e ATLAS_DFLASH_CONF_WIDTH=1 -e ATLAS_MTP_GATE_FORCE=1 $*"
up() { for i in $(seq 120); do curl -sf localhost:8895/health >/dev/null && return 0; sleep 3; done; echo SERVE-FAILED; docker logs inkling2-atlas 2>&1 | tail -20; return 1; }
mkdir -p abrig
CHUNK=4096 MAXLEN=32768 MODELDIR=$M EXTRA="$P" INKENV="$BASE" ./serve.sh >/dev/null; up || exit 1
cd ~/qual-20261110/rigmark
EB={\"chat_template_kwargs\":{\"reasoning_effort\":\"low\"}}
M=$HOME/inkling2/rig/metadata-dev.json
./rigmark run --base-url http://127.0.0.1:8895 --model m --metadata $M --comparison-id inkling2-atlas-dev --runs ${RUNS:-1} --concurrency 2,4 --concurrency-runs 2 --extra-body "$EB" --label ab-$mode-$label-code --skip-prefill --output ~/inkling2/abrig/$mode-$label-code.json > ~/inkling2/abrig/$mode-$label.log 2>&1
./rigmark run --base-url http://127.0.0.1:8895 --model m --metadata $M --comparison-id inkling2-atlas-dev --runs ${RUNS:-1} --concurrency 4 --concurrency-runs 2 --extra-body "$EB" --label ab-$mode-$label-prose --concurrency-workload prose --skip-prefill --output ~/inkling2/abrig/$mode-$label-prose.json >> ~/inkling2/abrig/$mode-$label.log 2>&1
echo "== $mode $label: $(grep -h AGGREGATE ~/inkling2/abrig/$mode-$label.log | sed "s/[│ ]\+/ /g" | tr "\n" "|")"
grep -iE "error|usage:" ~/inkling2/abrig/$mode-$label.log | head -3
