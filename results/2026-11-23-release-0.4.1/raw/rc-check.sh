#!/bin/bash
# RC functional check through ./start.sh (saver profile so the voice engines can stay up)
set -u
cd ~/inkling2/sparkinkling
until grep -q "BUILD-EXIT" ~/inkling2/build-rc.log; do sleep 20; done
IMG=$(install/build.sh --tag); docker image inspect $IMG >/dev/null 2>&1 || { echo BUILD-FAILED; tail -8 ~/inkling2/build-rc.log; exit 1; }
echo "image $IMG"; grep -E "test result" ~/inkling2/build-rc.log | grep -oE "ok\. [0-9]+ passed; [0-9]+ failed" | awk "{p+=\$2; f+=\$4} END {print \"build tests\", p, \"passed\", f, \"failed\"}"
for mode in strict spark; do
  PROFILE=saver MODE=$mode MODEL_ROOT=$HOME/models/sparkinkling IMAGE=$IMG PULL=0 ./start.sh > ~/inkling2/rig/rc-$mode.start.log 2>&1 || { echo START-FAILED $mode; tail -5 ~/inkling2/rig/rc-$mode.start.log; continue; }
  echo "== $mode"
  python3 -I results/2026-11-21-release-0.1.0/raw/task_probe.py 8895 > ~/inkling2/rig/rc-probe-$mode.json 2>/dev/null; grep -ho "\"math\"[^}]*\|\"tools\"[^}]*" ~/inkling2/rig/rc-probe-$mode.json | cut -c1-50
  python3 -I ~/inkling2/parse/tooltest.py 2>&1 | cut -c1-60
  python3 -I ~/inkling2/parse/argstream.py | cut -c1-70
  python3 -I ~/inkling2/parse/forced_stream.py | cut -c1-150
  (cd ~/inkling2 && python3 -I vis/vis_chat.py vis/invoice.png "Transcribe all the text in this image exactly, line by line." vis/grid.png "This is a 3x3 grid of labelled coloured rectangles. For each label (A1..C3) give its colour, row by row." vis/shapes.png "Describe this image in one sentence.")
  [ $mode = strict ] && python3 -I ~/inkling2/parse/voice_turns.py 4
  ./start.sh stop >/dev/null 2>&1
done
echo RC-CHECK-DONE
