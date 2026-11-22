#!/bin/bash
# 0.4.0 candidate: build the image, then the task probe (Strict with the disk prefix cache) and RigMark in both modes
cd ~/inkling2/sparkinkling
install/build.sh > ~/inkling2/rig/img-build-040.log 2>&1 || { echo BUILD-FAILED; exit 1; }
echo BUILT $(install/build.sh --tag)
~/inkling2/rig/probe_image.sh
grep -h "\"math\"" ~/inkling2/rig/probe-img-*.json | cut -c1-60
bash ~/inkling2/rig/run_image.sh > ~/inkling2/rig/run_image-040.log 2>&1
echo RC-DONE
