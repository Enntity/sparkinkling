#!/bin/bash
# Quality A/B: quality_eval.py suites (MMLU-Pro 150, GSM8K 150, HumanEval 164) at reasoning low and high, temp 0, 8192 cap.
# usage: MODE=spark ARMS="off on" EFFORTS="low high" SUITES="gsm8k humaneval mmlu" quality.sh
set -u
cd ~/inkling2-loopcd; mkdir -p q
Q=~/inkling2-loopcd/quality
for arm in ${ARMS:-off on}; do
  ./serve.sh ${MODE:-strict} $arm || continue
  for e in ${EFFORTS:-low high}; do
    for s in ${SUITES:-gsm8k humaneval mmlu}; do
      out=q/${MODE:-strict}-$arm-$e-$s.jsonl
      [ -s $out ] && grep -q '"summary"' $out && continue
      echo "== $arm $e $s $(date -u +%H:%M:%SZ)"
      python3 -I $Q/quality_eval.py --base http://127.0.0.1:8895/v1 --model m --suite $s --out $out --conc 8 --max-tokens 8192 --extra "{\"reasoning_effort\": \"$e\"}" | tail -1
      if [ $s = humaneval ]; then
        docker run --rm --network none --entrypoint python3 -v $HOME/inkling2-loopcd/q:/w -v $Q:/q:ro atlas-release-builder:1.93.1 /q/he_exec.py /w/$(basename $out) > ${out%.jsonl}-exec.json
        python3 -c "import json; d=json.load(open('${out%.jsonl}-exec.json')); print('  exec', d['passed'], '/', d['n'])"
      fi
    done
  done
  docker logs inkling2-loopcd 2>&1 | sed "s/\x1b\[[0-9;]*m//g" > q/${MODE:-strict}-$arm.server.log
done
docker rm -f inkling2-loopcd >/dev/null 2>&1; echo QUALITY-DONE $(date -u +%H:%M:%SZ)
