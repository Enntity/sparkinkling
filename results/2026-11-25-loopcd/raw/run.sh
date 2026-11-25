#!/bin/bash
# The whole LoopCD session on 04: build, base binary, functional checks, cost, quality (low then high).
set -u
cd ~/inkling2-loopcd
log() { echo "### $* $(date -u +%H:%M:%SZ)"; }
log build; ./build.sh || exit 1
ls -la base/spark target/release/spark
log check; ./check.sh
log speed; ./speed.sh
log quality-low; EFFORTS=low ./quality.sh
log quality-high; EFFORTS=high SUITES="gsm8k humaneval mmlu" ./quality.sh
log RUN-DONE
