#!/bin/bash
cd ~/inkling2
while pgrep -f tune_arms2.sh >/dev/null; do sleep 10; done
CONCS="3 4" ./tune.sh spark d23 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0
CONCS="3 4" ./tune.sh spark d2331 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:1,1000000:0
CONCS="3 4" ./tune.sh spark d2332 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:2,1000000:0
CONCS="3 4" ./tune.sh strict base
CONCS="3 4" ./tune.sh strict d2232 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,3:2,1000000:0
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
