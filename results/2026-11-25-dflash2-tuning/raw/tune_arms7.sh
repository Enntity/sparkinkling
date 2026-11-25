#!/bin/bash
cd ~/inkling2
while pgrep -f tune_arms6.sh >/dev/null; do sleep 10; done
CONCS="4" ./tune.sh strict d23334243 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,1000000:0
CONCS="4 6" ./tune.sh strict d23334262 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:2,6:2,1000000:0
CONCS="6" ./tune.sh strict d23334250 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:2,1000000:0
CONCS="3 4" ./tune.sh spark d23 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=2.0
CONCS="4" ./tune.sh spark d2342 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,4:2,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=2.0
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
