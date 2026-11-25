#!/bin/bash
cd ~/inkling2
CONCS="1 2 3 4 5 8" ./tune.sh strict final -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
CONCS="5" ./tune.sh strict final53 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,5:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
CONCS="1 2 3 4 8" ./tune.sh spark final -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=2.0
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
