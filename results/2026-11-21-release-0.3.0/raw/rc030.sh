#!/bin/bash
# 0.3.0 candidate: wait for the image, then the task probe and RigMark in both modes
until grep -q "naming to ghcr.io/enntity/atlas-sparkinkling:75c0c6f7962f done" ~/inkling2/rig/img-build-030.log; do
  grep -qE "ERROR|test result: FAILED|error: could not compile" ~/inkling2/rig/img-build-030.log && { echo BUILD-FAILED; exit 1; }
  sleep 30
done
~/inkling2/rig/probe_image.sh
bash ~/inkling2/rig/run_image.sh > ~/inkling2/rig/run_image-030.log 2>&1
echo RC-DONE
