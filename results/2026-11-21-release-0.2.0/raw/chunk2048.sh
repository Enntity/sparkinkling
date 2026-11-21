#!/bin/bash
# The 0.2.0 image's prefill cells with 2,048-token chunks (the 0.1.0 profile's), Strict
set -u
cd ~/inkling2/sparkinkling
IMG=$(install/build.sh --tag)
P=$HOME/inkling2/rig/profile-chunk2048.json
sed 's/--max-prefill-tokens=4096/--max-prefill-tokens=2048/' install/profiles/default.json > "$P"
grep -q 'max-prefill-tokens=2048' "$P" || { echo PROFILE-EDIT-FAILED; exit 1; }
M=$HOME/inkling2/rig/metadata-image-strict-chunk2048.json
sed 's/prefill chunks 4096/prefill chunks 2048 (custom profile: the default with --max-prefill-tokens=2048)/' ~/inkling2/rig/metadata-image-strict.json > "$M"
MODE=strict PROFILE=$P MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/rig/img-strict-chunk2048.start.log 2>&1 || { echo START-FAILED; exit 1; }
cd ~/qual-20261110/rigmark
EB={\"chat_template_kwargs\":{\"reasoning_effort\":\"low\"}}
./rigmark run --base-url http://127.0.0.1:8895 --model inkling-2-mini-atlas --metadata $M --comparison-id inkling2-atlas --runs 1 --prefill-runs 2 --skip-concurrency --extra-body "$EB" --label sparkinkling-strict-chunk2048 --prefill-depths 8192,32768 --output ~/inkling2/rig/img-strict-chunk2048.json > ~/inkling2/rig/img-strict-chunk2048.log 2>&1
docker logs atlas-sparkinkling > ~/inkling2/rig/img-strict-chunk2048.server.log 2>&1
cd ~/inkling2/sparkinkling && ./start.sh stop > /dev/null 2>&1
echo CHUNK-DONE
