#!/bin/bash
# LoopCD dev server on 8895: serve.sh <strict|spark> <off|on|skip-thinking> [base]
# product flags of the 0.5.0 candidate (tune.sh), DFlash2 drafter, util 0.5 beside the voice engines
set -u
mode=$1; lc=$2; bin=${3:-new}
[ "$bin" = base ] && B=$HOME/inkling2-loopcd/base || B=$HOME/inkling2-loopcd/target/release
if [ "$mode" = spark ]; then M=thinkingmachines--Inkling-2-Mini+spark-nvfp4; ENVM="-e ATLAS_DFLASH_BATCH_DEPTH=1:7,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=2.5"
else M=thinkingmachines--Inkling-2-Mini; ENVM="-e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,1000000:0"; fi
LC=""; [ "$bin" = base ] || LC="--loopcd=$lc"
P="--enable-prefix-caching --ssm-cache-slots=64 --tool-max-tokens=32768 --default-chat-template-kwargs={\"reasoning_effort\":\"low\"} ${DRAFT---dflash --dflash-gamma=8 --num-drafts=7 --draft-model=/drafter/incoai--Inkling-2-Mini-DFlash2} $LC"
E="-e ATLAS_QWEN4EXP_AUX_PINNED=1 -e ATLAS_GLM_PC_BRANCH=1 -e ATLAS_GLM_PC_BRANCH_MIN=512 -e ATLAS_DFLASH_ADAPTIVE=1 -e ATLAS_DFLASH_CONF_WIDTH=1 -e ATLAS_MTP_GATE_FORCE=1 $ENVM"
docker rm -f inkling2-loopcd >/dev/null 2>&1
docker run -d --name inkling2-loopcd --gpus all --ipc=host --network host -v $B:/opt/atlas:ro -v ~/.lloom/models:/models:ro -v ~/inkling2-loopcd/models:/drafter:ro $E -e RUST_LOG=info \
  atlas-release-builder:1.93.1 /opt/atlas/spark serve --model-from-path=/models/$M --kernel-target=inkling-2-mini --port=8895 \
  --gpu-memory-utilization=${GPUUTIL:-0.5} --kv-cache-dtype=bf16 --max-num-seqs=${SEQS:-8} --max-batch-size=${SEQS:-8} \
  --max-seq-len=${MAXLEN:-32768} --max-prefill-tokens=${CHUNK:-4096} --no-tui --request-timeout=3600 $P >/dev/null
for i in $(seq 150); do curl -sf localhost:8895/health >/dev/null && { echo "UP $mode $lc $bin"; exit 0; }; sleep 3; done
echo SERVE-FAILED; docker logs inkling2-loopcd 2>&1 | tail -30; exit 1
