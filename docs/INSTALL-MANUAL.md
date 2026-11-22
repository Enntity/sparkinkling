<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Install by hand

These are the steps [`./start.sh`](../start.sh) runs, one command at a time,
on the one Spark that serves.

| Component | Pin |
|---|---|
| Engine | [`Enntity/atlas`](https://github.com/Enntity/atlas) `inkling2/mini-20261121` at `f0f0a2c78` ([`install/atlas-source.json`](../install/atlas-source.json), [ENGINE](ENGINE.md)) |
| Model | [`thinkingmachines/Inkling-2-Mini`](https://huggingface.co/thinkingmachines/Inkling-2-Mini) @ `ed40e7da625f594fc9c4990f5f66be24873c22d7` ([`install/checkpoint.json`](../install/checkpoint.json)) |
| Spark overlay | [`Enntity/Inkling-2-Mini-Spark-NVFP4`](https://huggingface.co/Enntity/Inkling-2-Mini-Spark-NVFP4) @ `e9df93dceea2fbf0927caf178104e868452a6292` |
| Build dependencies | CUTLASS `cf064d2e`, NCCL 2.31.2, Rust 1.93.1, CUDA 13.0 |
| Profile | [`install/profiles/default.json`](../install/profiles/default.json) |

## 1. Get the recipe

```sh
git clone https://github.com/Enntity/sparkinkling.git
cd sparkinkling
```

## 2. Build the image

```sh
IMAGE=$(install/build.sh)
```

`install/build.sh --tag` prints the tag without building: the git tree hash of
`install/`. The build needs a clean `install/` directory. It fetches the
pinned engine commit, refuses any other tree, builds the `inkling-2-mini`
kernel target and runs the engine's CPU tests and Clippy. A cold build
downloads the CUDA base images and compiles every kernel; allow 30 to 60
minutes. `ATLAS_BUILD_JOBS` (default 4) trades speed for memory.

## 3. Download the pinned checkpoint

```sh
export MODEL_ROOT=$HOME/models/sparkinkling
hf download thinkingmachines/Inkling-2-Mini --revision ed40e7da625f594fc9c4990f5f66be24873c22d7 \
  --local-dir "$MODEL_ROOT/thinkingmachines--Inkling-2-Mini"
python3 install/check_files.py install/checkpoint.json "$MODEL_ROOT/thinkingmachines--Inkling-2-Mini"
```

About 20 GB, including the bundled DSpark draft model (`mtp.safetensors`).
`check_files.py` compares the weight and tokenizer files with the sha256
values in the pin. Then the drafter's directory (skip with `DRAFTER=none`):

```sh
python3 install/dspark_drafter.py install/checkpoint.json \
  "$MODEL_ROOT/thinkingmachines--Inkling-2-Mini" "$MODEL_ROOT/thinkingmachines--Inkling-2-Mini+dspark"
```

It links `mtp.safetensors` as `model.safetensors` beside a `config.json` that
is the checkpoint's `mtp_config` plus the tokenizer vocabulary size, the
layout the engine loads a drafter from.

## 4. Spark mode only: the overlay

Skip this for Strict.

```sh
hf download Enntity/Inkling-2-Mini-Spark-NVFP4 spark-nvfp4.safetensors --revision e9df93dceea2fbf0927caf178104e868452a6292 \
  --local-dir "$MODEL_ROOT/Enntity--Inkling-2-Mini-Spark-NVFP4"
python3 install/check_files.py install/checkpoint.json "$MODEL_ROOT/Enntity--Inkling-2-Mini-Spark-NVFP4" overlay
python3 install/spark_overlay.py install/checkpoint.json \
  "$MODEL_ROOT/thinkingmachines--Inkling-2-Mini" "$MODEL_ROOT/Enntity--Inkling-2-Mini-Spark-NVFP4" \
  "$MODEL_ROOT/thinkingmachines--Inkling-2-Mini+spark-nvfp4"
```

`spark_overlay.py` checks the overlay against the pin (sha256, 459 tensors,
names under `model.language_model.` and `lm_head.`), then builds
`thinkingmachines--Inkling-2-Mini+spark-nvfp4`: relative links to the
checkpoint's files and the overlay file, and an index mapping both. Rerunning
it is a no-op until a revision changes. See [MODES](MODES.md).

## 5. Serve

Strict:

```sh
ck=$MODEL_ROOT/thinkingmachines--Inkling-2-Mini
mkdir -p ~/.cache/atlas-cuda
docker run -d --name atlas-sparkinkling --network host --ipc host --shm-size 16g --memory 114g \
  --gpus all --security-opt no-new-privileges=true \
  --mount "type=bind,src=$ck,dst=$ck,readonly" --mount "type=bind,src=$ck+dspark,dst=$ck+dspark,readonly" \
  --mount "type=bind,src=$HOME/.cache/atlas-cuda,dst=/atlas-cuda-cache" \
  -e MODEL_PATH="$ck" -e SPARKINKLING_MODE=strict -e DRAFTER_PATH="$ck+dspark" -e HF_HUB_OFFLINE=1 \
  -e CUDA_CACHE_PATH=/atlas-cuda-cache "$IMAGE"
until curl -sf http://127.0.0.1:8895/health; do sleep 10; done
```

For Spark, mount the overlay directory and the assembled directory too (each
at its own path, read-only), and pass `MODEL_PATH` = the assembled directory
and `SPARKINKLING_MODE=spark`. The image refuses a directory that does not
match its mode.

The image's entry point turns those settings into one engine command:

```sh
spark serve --model-from-path=<model dir> --gpu-memory-utilization=0.80 \
  --kernel-target=inkling-2-mini --kv-cache-dtype=bf16 --max-prefill-tokens=4096 \
  --enable-prefix-caching --ssm-cache-slots=128 --oom-guard-mb=4096 --request-timeout=3600 \
  --tool-max-tokens=32768 --max-num-seqs=8 --max-batch-size=8 --max-seq-len=131072 --no-tui \
  --dflash --dflash-gamma=8 --num-drafts=7 --draft-model=<drafter dir> \
  --bind=127.0.0.1 --port=8895 --model-name=inkling-2-mini-atlas --tool-guard=on ...
```

with `ATLAS_DFLASH_BATCH_DEPTH=1:7,1000000:0` in its environment (speculate
with one live request). `-e SPARKINKLING_DRAFTER=none` drops the four drafter
flags.

**Memory share.** `-e SPARKINKLING_GPU_MEMORY_UTILIZATION=0.70` (two decimals,
0.50-0.90) overrides the profile's 0.80. GB10 memory is shared with the host;
the container is capped at 114 GiB because a host that runs out of memory
hangs instead of killing a process.

**Profile.** `-e SPARKINKLING_PROFILE=<name>` picks a file in the image's
`/opt/atlas/profiles/` (`default`, `max`, `saver`); to run your own, mount a JSON file at
`/opt/atlas/profiles/custom.json` and name `custom`. A profile must keep one
`--kernel-target=inkling-2-mini`, BF16 KV and one rank, and may not configure
speculation (that is `SPARKINKLING_DRAFTER`).

**Prefix cache on disk.** Mount a directory on a real disk at `/prefix-cache`
(`--mount type=bind,src=/srv/sparkinkling/prefix-cache,dst=/prefix-cache`) and
pass `-e SPARKINKLING_PREFIX_CACHE_GB=48` (16-100). The engine keeps evicted KV
blocks in `/prefix-cache/<mode>/kv`; create that subdirectory first.

**Stopping.** `docker rm -f atlas-sparkinkling`.

## Troubleshooting

- **The container exits during loading:** `docker logs atlas-sparkinkling`.
  The entry point refuses a directory without `config.json` and
  `model.safetensors.index.json`, or one whose index does not match the mode.
- **The host stops responding under load:** keep builds, other models and
  large processes off the Spark while it serves, or lower the memory share.
