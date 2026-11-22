#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-only
# SparkInkling: Thinking Machines' Inkling 2 Mini on one DGX Spark, served by
# Atlas on 127.0.0.1:8895. Adapted from SparkQwen's single-Spark launcher.
#
#   ./start.sh                     prepare whatever is missing, then serve
#   ./start.sh --version           checkout product version and pinned engine
#   ./start.sh --mode strict|spark [command]
#   ./start.sh stop | status | logs
#   ./start.sh build | download    run one preparation step
#
# Settings (environment or .env): MODEL_ROOT (default ~/models/sparkinkling),
# MODE (strict, the default, or spark), PROFILE (default, or a JSON file of your
# own), DRAFTER (dspark, the default: the checkpoint's own drafter; or none),
# GPU_MEMORY_UTILIZATION (0.50-0.90), PREFIX_CACHE_DIR and PREFIX_CACHE_GB (16-100,
# default 48: keep evicted prefix-cache KV on this disk), IMAGE, PULL=0 (always
# build), TOOL_GUARD*.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if [[ ${1:-} == --version ]]; then exec python3 install/serve.py --version; fi
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi
MODE=${MODE:-strict}
if [[ ${1:-} == --mode ]]; then
  [[ $# -ge 2 ]] || { echo '--mode requires strict or spark' >&2; exit 2; }
  MODE=$2; shift 2
fi
MODEL_ROOT=${MODEL_ROOT:-$HOME/models/sparkinkling}
PROFILE=${PROFILE:-default}
DRAFTER=${DRAFTER:-dspark}
NAME=atlas-sparkinkling
API=http://127.0.0.1:8895

# shellcheck source=install/common.sh
. install/common.sh
read -r CHECKPOINT_REPO CHECKPOINT_REVISION SERVED OVERLAY_REPO OVERLAY_REVISION OVERLAY_FILE < <(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); o=m["overlay"]; print(m["repository"], m["revision"], m["served_model_name"], o["repository"], o["revision"], o["serve"])' install/checkpoint.json)

# Launch-only checks must not prevent inspecting or stopping an older deployment.
if [[ ${1:-up} == up || ${1:-} == download ]]; then
  [[ $MODE == strict || $MODE == spark ]] || { echo '--mode (MODE) must be strict or spark' >&2; exit 2; }
  if [[ $MODE == spark && ! $OVERLAY_REVISION =~ ^[0-9a-f]{40}$ ]]; then
    echo "MODE=spark: the overlay $OVERLAY_REPO is not published yet (install/checkpoint.json pins no revision); use MODE=strict" >&2
    exit 2
  fi
  [[ -f $PROFILE || -f install/profiles/$PROFILE.json ]] || { echo "PROFILE: no $PROFILE or install/profiles/$PROFILE.json" >&2; exit 2; }
  [[ $DRAFTER =~ ^(none|dspark)$ ]] || { echo 'DRAFTER must be none or dspark' >&2; exit 2; }
  [[ -z ${GPU_MEMORY_UTILIZATION:-} || $GPU_MEMORY_UTILIZATION =~ ^0\.([5-8][0-9]|90)$ ]] ||
    { echo 'GPU_MEMORY_UTILIZATION must be 0.50 to 0.90' >&2; exit 2; }
  if [[ -n ${PREFIX_CACHE_DIR:-} || -n ${PREFIX_CACHE_GB:-} ]]; then
    PREFIX_CACHE_GB=${PREFIX_CACHE_GB:-48}
    [[ ${PREFIX_CACHE_DIR:-} == /* && $PREFIX_CACHE_DIR != *,* ]] ||
      { echo 'PREFIX_CACHE_DIR must be set to an absolute path without commas' >&2; exit 2; }
    [[ $PREFIX_CACHE_GB =~ ^[1-9][0-9]{1,2}$ ]] && (( PREFIX_CACHE_GB >= 16 && PREFIX_CACHE_GB <= 100 )) ||
      { echo 'PREFIX_CACHE_GB must be a whole number from 16 to 100' >&2; exit 2; }
  fi
  SPARKINKLING_TOOL_GUARD="${TOOL_GUARD:-on}" SPARKINKLING_TOOL_GUARD_MAX_BYTES="${TOOL_GUARD_MAX_BYTES:-1048576}" \
  SPARKINKLING_TOOL_GUARD_ALLOW_HOSTS="${TOOL_GUARD_ALLOW_HOSTS:-}" SPARKINKLING_TOOL_GUARD_DENY_HOSTS="${TOOL_GUARD_DENY_HOSTS:-}" \
    python3 -c 'import os,sys; sys.path.insert(0,"install"); import serve; serve.tool_guard_args(os.environ, [])'
fi
IMAGE=${IMAGE:-$(install/build.sh --tag)}
mkdir -p "$MODEL_ROOT"; MODEL_ROOT=$(realpath "$MODEL_ROOT")
checkpoint=$MODEL_ROOT/${CHECKPOINT_REPO/\//--}
weights=$MODEL_ROOT/${OVERLAY_REPO/\//--}
# Spark mode's model directory: the checkpoint's files linked, the overlay
# mapped in (install/spark_overlay.py). It sits next to $checkpoint.
spark_model=$checkpoint+spark-nvfp4
# The DSpark drafter's directory: mtp.safetensors linked beside its config
# (install/dspark_drafter.py), next to $checkpoint too.
drafter=$checkpoint+dspark

# The image for this checkout is pulled from ghcr.io/enntity/atlas-sparkinkling
# (its tag is the install/ tree); if that tag is not published, it is built
# from source. PULL=0 always builds.
build() {
  say "image $IMAGE"
  docker image inspect "$IMAGE" >/dev/null 2>&1 && return
  if [[ ${PULL:-1} != 1 ]] || ! docker pull "$IMAGE"; then
    say "building $IMAGE from source (a cold build takes 30-60 minutes)"
    IMAGE=$(install/build.sh)
  fi
}

# Each download is checked against its pin before its marker is written.
download() {
  if [[ $(cat "$checkpoint/.sparkinkling-revision" 2>/dev/null) != "$CHECKPOINT_REVISION" ]]; then
    say "download $CHECKPOINT_REPO @ $CHECKPOINT_REVISION (sha256 checked)"
    hf_download "$CHECKPOINT_REPO" "$CHECKPOINT_REVISION" "$checkpoint"
    python3 install/check_files.py install/checkpoint.json "$checkpoint"
    echo "$CHECKPOINT_REVISION" > "$checkpoint/.sparkinkling-revision"
  fi
  if [[ $DRAFTER == dspark ]]; then
    python3 install/dspark_drafter.py install/checkpoint.json "$checkpoint" "$drafter"
  fi
  [[ $MODE == spark ]] || return 0
  if [[ $(cat "$weights/.sparkinkling-revision" 2>/dev/null) != "$OVERLAY_REVISION" ]]; then
    say "download $OVERLAY_REPO @ $OVERLAY_REVISION (sha256 checked)"
    hf_download "$OVERLAY_REPO" "$OVERLAY_REVISION" "$weights" "$OVERLAY_FILE"
    python3 install/check_files.py install/checkpoint.json "$weights" overlay
    echo "$OVERLAY_REVISION" > "$weights/.sparkinkling-revision"
  fi
  python3 install/spark_overlay.py install/checkpoint.json "$checkpoint" "$weights" "$spark_model"
}

stop() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }

state() { docker inspect -f '{{.State.Status}}' "$NAME" 2>/dev/null || echo absent; }

# Only a product semantic version is a SparkInkling release number.
running_identity() {
  local identity version image_id
  identity=$(docker inspect -f '{{index .Config.Labels "org.opencontainers.image.version"}}|{{.Image}}' "$NAME" 2>/dev/null) || return 0
  IFS='|' read -r version image_id <<< "$identity"
  [[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+([+-].*)?$ ]] || version=unversioned
  printf 'running: version=%s image=%s\n' "$version" "$image_id"
}

serve() {
  local model=$checkpoint profile=$PROFILE profile_mount=()
  local mounts=(--mount "type=bind,src=$checkpoint,dst=$checkpoint,readonly")
  if [[ $MODE == spark ]]; then
    model=$spark_model
    mounts+=(--mount "type=bind,src=$weights,dst=$weights,readonly"
             --mount "type=bind,src=$spark_model,dst=$spark_model,readonly")
  fi
  if [[ $DRAFTER == dspark ]]; then
    mounts+=(--mount "type=bind,src=$drafter,dst=$drafter,readonly")
  fi
  if [[ -f $profile ]]; then
    profile_mount=(--mount "type=bind,src=$(realpath "$profile"),dst=/opt/atlas/profiles/custom.json,readonly")
    profile=custom
  fi
  # Evicted prefix-cache KV on this disk, one directory per mode. The engine
  # unlinks its cache files while they are open and sweeps any a crash left
  # behind, so nothing carries over a restart.
  local pc_args=()
  if [[ -n ${PREFIX_CACHE_DIR:-} ]]; then
    mkdir -p "$PREFIX_CACHE_DIR/$MODE/kv"
    local pc_dir free_kb
    pc_dir=$(realpath "$PREFIX_CACHE_DIR")
    case $(stat -f -c %T "$pc_dir" 2>/dev/null) in
      tmpfs | ramfs | overlayfs) echo "PREFIX_CACHE_DIR $pc_dir is not on a disk" >&2; exit 2 ;;
    esac
    free_kb=$(df -Pk "$pc_dir" | awk 'NR == 2 {print $4}')
    (( free_kb >= PREFIX_CACHE_GB * 1048576 )) ||
      { echo "PREFIX_CACHE_DIR $pc_dir has $((free_kb / 1048576)) GiB free; PREFIX_CACHE_GB needs $PREFIX_CACHE_GB" >&2; exit 2; }
    pc_args=(--mount "type=bind,src=$pc_dir,dst=/prefix-cache" -e SPARKINKLING_PREFIX_CACHE_GB="$PREFIX_CACHE_GB")
  fi
  mkdir -p "$HOME/.cache/atlas-cuda"
  stop
  say "serving $CHECKPOINT_REPO on this Spark (mode $MODE, profile $PROFILE, drafter $DRAFTER)"
  # GB10 memory is shared with the host, and a host that runs out of it hangs
  # instead of killing a process: the container is capped at 114 GiB.
  docker run -d --name "$NAME" --restart no --network host --ipc host \
    --shm-size 16g --memory 114g --gpus all --security-opt no-new-privileges=true --stop-timeout 60 \
    "${mounts[@]}" --mount "type=bind,src=$HOME/.cache/atlas-cuda,dst=/atlas-cuda-cache" \
    ${profile_mount[@]+"${profile_mount[@]}"} ${pc_args[@]+"${pc_args[@]}"} \
    -e MODEL_PATH="$model" -e SPARKINKLING_MODE="$MODE" -e SPARKINKLING_DRAFTER="$DRAFTER" -e DRAFTER_PATH="$drafter" \
    -e SPARKINKLING_PROFILE="$profile" -e SERVED_MODEL_NAME="$SERVED" \
    -e SPARKINKLING_TOOL_GUARD="${TOOL_GUARD:-on}" -e SPARKINKLING_TOOL_GUARD_MAX_BYTES="${TOOL_GUARD_MAX_BYTES:-1048576}" \
    -e SPARKINKLING_TOOL_GUARD_ALLOW_HOSTS="${TOOL_GUARD_ALLOW_HOSTS:-}" -e SPARKINKLING_TOOL_GUARD_DENY_HOSTS="${TOOL_GUARD_DENY_HOSTS:-}" \
    ${GPU_MEMORY_UTILIZATION:+-e SPARKINKLING_GPU_MEMORY_UTILIZATION="$GPU_MEMORY_UTILIZATION"} \
    -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
    -e CUDA_CACHE_PATH=/atlas-cuda-cache -e CUDA_CACHE_MAXSIZE=4294967296 \
    "$IMAGE" >/dev/null
  say "loading (the first start also compiles CUDA kernels)"
  for ((i = 0; i < 90; i++)); do
    if curl -sf "$API/health" >/dev/null; then
      curl -fsS --max-time 300 "$API/v1/chat/completions" -H 'Content-Type: application/json' -d '{"model": "'"$SERVED"'",
        "max_tokens": 1024, "temperature": 0, "top_p": 1, "reasoning_effort": "low",
        "messages": [{"role": "user", "content": "What is 17*23? Answer with the number."}]}' |
        python3 install/smoke.py
      say "ready: $API/v1 model $SERVED"
      return
    fi
    [[ $(state) == running ]] || { docker logs --tail 40 "$NAME"; echo 'the server stopped' >&2; exit 1; }
    sleep 10
  done
  echo 'not ready after 15 minutes; see ./start.sh logs' >&2; exit 1
}

case ${1:-up} in
  up) build; download; serve ;;
  build | download | stop) "$1" ;;
  status)
    echo "checkout: $(python3 install/serve.py --version | head -1)"
    running_identity
    echo "image  $IMAGE"
    echo "server $(state)"
    curl -sf "$API/health" >/dev/null && echo "health ok ($API)" || echo 'health: not serving' ;;
  logs) docker logs -f --tail 100 "$NAME" ;;
  *) sed -n '5,10p' "$0" >&2; exit 2 ;;
esac
