#!/bin/bash
# Build the LoopCD branch (inkling2/loopcd-20261124) into ~/inkling2-loopcd/target.
set -u
docker run --rm --name inkling2-loopcd-build -v ~/inkling2-loopcd/atlas:/build -v ~/inkling2-loopcd/target:/target -w /build \
  -e ATLAS_TARGET_HW=gb10 -e ATLAS_TARGET_MODEL=inkling-2-mini -e ATLAS_TARGET_QUANT=nvfp4 -e CARGO_TARGET_DIR=/target \
  atlas-release-builder:1.93.1 bash -c "cargo build --release -j ${JOBS:-8} -p spark-server 2>&1 | tail -40" || { echo BUILD-FAILED; exit 1; }
ls -la ~/inkling2-loopcd/target/release/spark && echo BUILD-OK
