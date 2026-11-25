#!/bin/bash
cd ~/inkling2
while pgrep -f tune_base.sh >/dev/null; do sleep 10; done
m=strict
./tune.sh $m tc -e ATLAS_W4A16_TC=1 -e ATLAS_DFLASH_NVFP4_TC=1
./tune.sh $m head -e ATLAS_DFLASH_NVFP4_HEAD=1
./tune.sh $m ctx -e ATLAS_DFLASH_CTX_NVFP4=1
./tune.sh $m conv -e ATLAS_DFLASH_CONV_TWIN=nvfp4
./tune.sh $m async -e ATLAS_DFLASH_CTX_ASYNC_POS=1 -e ATLAS_DFLASH_ASYNC_UPLOADS=1
./tune.sh $m copy -e ATLAS_DFLASH_COPY_DRAFTS=1 -e ATLAS_DFLASH_COPY_REPLY_MATCH=16 -e ATLAS_DFLASH_COPY_MISS_MAX=3
./tune.sh $m first -e ATLAS_DFLASH_FIRST_APPEND=none
./tune.sh $m masked -e ATLAS_DFLASH_MASKED_VERIFY=1
./tune.sh $m awidth -e ATLAS_DFLASH_ADAPTIVE_WIDTH=1
./tune.sh $m probe -e ATLAS_DFLASH_CONF_PROBE=256
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
