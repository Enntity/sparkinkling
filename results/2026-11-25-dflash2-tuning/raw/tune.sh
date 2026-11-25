#!/bin/bash
# one DFlash2 tuning arm: tune.sh <strict|spark> <label> [extra -e flags...]; product base env per mode, then the extras override
set -u
cd ~/inkling2
mode=$1; label=$2; shift 2
if [ "$mode" = spark ]; then M=sparkinkling/thinkingmachines--Inkling-2-Mini+spark-nvfp4; ENVM="-e ATLAS_DFLASH_BATCH_DEPTH=1:7,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=2.5"
else M=inkling-2-mini; ENVM="-e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,1000000:0"; fi
P="--enable-prefix-caching --ssm-cache-slots=64 --tool-max-tokens=32768 --default-chat-template-kwargs={\"reasoning_effort\":\"low\"} --dflash --dflash-gamma=${GAMMA:-8} --num-drafts=${NDRAFTS:-7} --draft-model=/models/sparkinkling/incoai--Inkling-2-Mini-DFlash2"
BASE="-e ATLAS_QWEN4EXP_AUX_PINNED=1 -e ATLAS_GLM_PC_BRANCH=1 -e ATLAS_GLM_PC_BRANCH_MIN=512 -e ATLAS_DFLASH_ADAPTIVE=1 -e ATLAS_DFLASH_CONF_WIDTH=1 -e ATLAS_MTP_GATE_FORCE=1 $ENVM $*"
up() { for i in $(seq 120); do curl -sf localhost:8895/health >/dev/null && return 0; sleep 3; done; echo SERVE-FAILED; docker logs inkling2-atlas 2>&1 | tail -20; return 1; }
mkdir -p tune
CHUNK=4096 MAXLEN=32768 MODELDIR=$M EXTRA="$P" INKENV="$BASE" ./serve.sh >/dev/null; up || exit 1
curl -s localhost:8895/v1/chat/completions -H content-type:application/json -d "{\"model\":\"m\",\"messages\":[{\"role\":\"user\",\"content\":\"Write a Python function that reverses a list.\"}],\"max_tokens\":128}" >/dev/null
for c in ${CONCS:-1 2}; do echo "== $mode $label c$c"; python3 -I tune_suite.py $c tune/$mode-$label-c$c.json; done
docker logs inkling2-atlas 2>&1 | sed "s/\x1b\[[0-9;]*m//g" > tune/$mode-$label.server.log
echo "  errors: $(grep -c " ERROR " tune/$mode-$label.server.log)"
