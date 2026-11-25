#!/bin/bash
cd ~/inkling2
while pgrep -f tune_arms5.sh >/dev/null; do sleep 10; done
CONCS=1 ./tune.sh strict min05 -e ATLAS_DFLASH_ADAPTIVE_MIN=0.5
CONCS=1 ./tune.sh strict noadapt -e ATLAS_DFLASH_ADAPTIVE=0
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
