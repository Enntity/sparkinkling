#!/bin/bash
cd ~/inkling2
while pgrep -f tune_arms1.sh >/dev/null; do sleep 10; done
./tune.sh spark d22 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,1000000:0
./tune.sh spark d23 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0
./tune.sh spark d27 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:7,1000000:0
./tune.sh strict d23 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0
./tune.sh strict d27 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:7,1000000:0
./tune.sh spark min20 -e ATLAS_DFLASH_ADAPTIVE_MIN=2.0
./tune.sh strict min25 -e ATLAS_DFLASH_ADAPTIVE_MIN=2.5
./tune.sh strict min15 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.5
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
