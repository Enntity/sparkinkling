#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""LoopCD A/B table from the raw files beside this script (Strict, temp 0, 8192 cap):
per suite and effort, correct off/on, paired flips, an exact two-sided sign test on the
flips, answers cut at the cap, and mean completion tokens. Standard library only."""
import json, math, os, sys

HERE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))


def items(arm, effort, suite):
    rows = [json.loads(l) for l in open(os.path.join(HERE, f"strict-{arm}-{effort}-{suite}.jsonl"))]
    summary = next(r for r in rows if r.get("summary"))
    rows = [r for r in rows if not r.get("summary")]
    if suite == "humaneval":
        ex = json.load(open(os.path.join(HERE, f"strict-{arm}-{effort}-{suite}-exec.json")))
        ok = [r["pass"] for r in ex["results"]]
    else:
        ok = [r["ok"] for r in sorted(rows, key=lambda r: r["i"])]
    return ok, summary


def sign_p(a, b):
    n = a + b
    if n == 0:
        return 1.0
    k = min(a, b)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


print("| suite | effort | off | on | flips off->on (lost, gained) | sign-test p | cut off/on | mean tokens off/on |")
print("|---|---|---|---|---|---|---|---|")
for effort in ("low", "high"):
    for suite in ("gsm8k", "humaneval", "mmlu"):
        try:
            off, so = items("off", effort, suite)
            on, sn = items("on", effort, suite)
        except (FileNotFoundError, StopIteration):
            continue
        lost = sum(a and not b for a, b in zip(off, on))
        gained = sum(b and not a for a, b in zip(off, on))
        print(f"| {suite} | {effort} | {sum(off)}/{len(off)} | {sum(on)}/{len(on)} | {lost}, {gained} | "
              f"{sign_p(lost, gained):.2f} | {so['length_cut']}/{sn['length_cut']} | "
              f"{so['mean_completion_tokens']}/{sn['mean_completion_tokens']} |")
