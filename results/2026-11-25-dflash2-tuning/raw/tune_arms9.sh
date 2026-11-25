#!/bin/bash
cd ~/inkling2
while pgrep -f "bash ./tune_final" >/dev/null; do sleep 10; done
CONCS="6" ./tune.sh strict d63 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,5:3,6:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
CONCS="6 8" ./tune.sh strict d53 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,5:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
CONCS="8" ./tune.sh strict d82 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,5:3,6:3,8:2,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
