#!/bin/bash
# Atlas Inkling 2 Mini, Strict (port 8895); SEQS=<n> sequences (default 8)
docker rm -f inkling2-atlas >/dev/null 2>&1
docker run -d --name inkling2-atlas --gpus all --ipc=host --network host \
  -v ~/inkling2/atlas-target/release:/opt/atlas:ro -v ~/models:/models:ro \
  -v $HOME/inkling2/dbg:/dump ${DUMP:+-e ATLAS_INKLING2_DUMP=/dump/h.bin${TAP:+@$TAP}} ${INKENV:-} -e RUST_LOG=info atlas-release-builder:1.93.1 \
  /opt/atlas/spark serve --model-from-path=/models/${MODELDIR:-inkling-2-mini} --kernel-target=inkling-2-mini --port=8895 \
    --gpu-memory-utilization=${GPUUTIL:-0.5} --kv-cache-dtype=bf16 --max-num-seqs=${SEQS:-8} --max-batch-size=${SEQS:-8} \
    --max-seq-len=${MAXLEN:-8192} --max-prefill-tokens=${CHUNK:-2048} --no-tui --request-timeout=3600 ${EXTRA:-}
