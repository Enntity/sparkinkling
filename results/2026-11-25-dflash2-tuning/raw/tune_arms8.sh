#!/bin/bash
cd ~/inkling2
while pgrep -f "bash ./tune_arms7" >/dev/null; do sleep 10; done
CONCS="3 4" ./tune.sh strict d2344 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:4,4:4,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
CONCS="4 5" ./tune.sh strict d233353 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,5:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
CONCS="4" ./tune.sh spark d2343 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,4:3,1000000:0
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
