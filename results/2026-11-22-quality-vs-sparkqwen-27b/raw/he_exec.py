#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Run the HumanEval programs quality_eval.py wrote, one subprocess each with
a 10 s limit, and print pass@1. Run it inside a container with no network:

  docker run --rm --network none -v DIR:/w:ro IMAGE python3 /w/he_exec.py /w/humaneval-MODEL.jsonl

Standard library only."""
import json, subprocess, sys, tempfile

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
rows = [r for r in rows if not r.get("summary")]
passed = 0
results = []
for r in rows:
    prog = (r.get("got") or {}).get("program") if isinstance(r.get("got"), dict) else None
    ok = False
    if prog:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog)
        try:
            ok = subprocess.run([sys.executable, f.name], capture_output=True, timeout=10).returncode == 0
        except subprocess.TimeoutExpired:
            ok = False
    passed += ok
    results.append({"task_id": (r.get("got") or {}).get("task_id") if isinstance(r.get("got"), dict) else r.get("gold"), "pass": ok})
print(json.dumps({"n": len(rows), "passed": passed, "results": results}))
