#!/bin/bash
cd ~/inkling2
while ! grep -q WINDOW-DONE ~/inkling2/rig/window050.out; do sleep 10; done
./abrig.sh strict ship -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,5:3,6:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
./abrig.sh strict d22 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
./abrig.sh strict d23 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
./abrig.sh strict old -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,1000000:0
./abrig.sh spark ship -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0
./abrig.sh spark plain2 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,1000000:0
./abrig.sh spark d22 -e ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,1000000:0
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
