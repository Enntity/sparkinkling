#!/bin/bash
cd ~/inkling2
while pgrep -f tune_arms4.sh >/dev/null; do sleep 10; done
CONCS="2 3 4" ./tune.sh strict d2332 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:2,1000000:0
CONCS="3 4" ./tune.sh strict d2333 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,1000000:0
CONCS="4" ./tune.sh strict d233242 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:2,4:2,1000000:0
CONCS="4" ./tune.sh strict d233241 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:2,4:1,1000000:0
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
