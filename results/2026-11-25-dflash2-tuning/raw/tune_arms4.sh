#!/bin/bash
cd ~/inkling2
while pgrep -f tune_arms3.sh >/dev/null; do sleep 10; done
CONCS=1 ./tune.sh strict min15r -e ATLAS_DFLASH_ADAPTIVE_MIN=1.5
CONCS=1 ./tune.sh strict min10 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.0
CONCS=1 ./tune.sh strict baser
CONCS=1 ./tune.sh spark min15 -e ATLAS_DFLASH_ADAPTIVE_MIN=1.5
CONCS=1 ./tune.sh spark min20r -e ATLAS_DFLASH_ADAPTIVE_MIN=2.0
CONCS=1 ./tune.sh spark baser
docker rm -f inkling2-atlas >/dev/null; echo "end $(date -u +%H:%M:%SZ)"
