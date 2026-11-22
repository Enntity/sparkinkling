#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Recompute every number RESULT.md quotes from the raw files in this folder.

  python3 claims.py

Standard library only. "Cut" = finish_reason length (still reasoning at the
token limit, no answer). A forced close = more than the high budget (16,384)
of completion tokens with an answer after it."""
import collections, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))


def rows(name):
    return [r for r in (json.loads(l) for l in open(os.path.join(HERE, name))) if not r.get("summary")]


def score(name):
    rs = rows(name)
    toks = [r.get("completion_tokens") or 0 for r in rs]
    return {"n": len(rs), "correct": sum(1 for r in rs if r.get("ok")), "cut": sum(1 for r in rs if r.get("finish") == "length"),
            "mean_tokens": round(sum(toks) / max(1, len(toks)))}


def he(name):
    d = json.load(open(os.path.join(HERE, name)))
    return f"{d['passed']}/{d['n']}"


def cls(r):
    return "correct" if r.get("ok") else ("cut" if r.get("finish") == "length" else "wrong")


print("== MMLU-Pro 150, temperature 0, 8,192 tokens, SparkInkling (Spark, saver)")
for label, f in [("default effort (template: high)", "ink-spark-mmlu.jsonl"), ("medium", "ink-spark-mmlu-medium.jsonl"),
                 ("low", "ink-spark-mmlu-low.jsonl"), ("low, budget forcing build", "tf-mmlu-low8k.jsonl")]:
    print(f"  {label:34} {score(f)}")
print(f"  {'SparkQwen 27B (its default)':34} {score('sq27b-mmlu.jsonl')}")

base = rows("ink-spark-mmlu.jsonl")
cut30 = sorted(r["i"] for r in base if r.get("finish") == "length")
print(f"\n== the {len(cut30)} questions still reasoning at 8,192 tokens: {cut30}")

for label, f in [("vLLM image, same 30, 8K, temp 0", "vllm-mmlu-cut8k.jsonl"), ("SparkInkling rerun, same 30, 8K", "ours-spark-mmlu-cut8k.jsonl"),
                 ("SparkInkling, same 30, 32K, no forcing", "ink-spark-mmlu-cut32k.jsonl"), ("budget forcing, same 30, 32K, high", "tf-cut-high32k.jsonl")]:
    s = score(f)
    assert sorted(r["i"] for r in rows(f)) == cut30, f
    print(f"  {label:40} {s}")
if os.path.exists(os.path.join(HERE, "vllm-mmlu-cut8k-t1.jsonl")):
    print(f"  {'vLLM image, same 30, 8K, temperature 1.0':40} {score('vllm-mmlu-cut8k-t1.jsonl')}")

before = {r["i"]: r for r in rows("ink-spark-mmlu-cut32k.jsonl")}
after = {r["i"]: r for r in rows("tf-cut-high32k.jsonl")}
forced = {i for i, r in after.items() if (r.get("completion_tokens") or 0) > 16384}
print(f"\n== 32K before -> after budget forcing: forced closes {len(forced)}, ended on their own {len(after) - len(forced)}")
print("  forced:  ", dict(collections.Counter(f"{cls(before[i])}->{cls(after[i])}" for i in forced)))
print("  natural: ", dict(collections.Counter(f"{cls(before[i])}->{cls(after[i])}" for i in after if i not in forced)))

print("\n== GSM8K 150 and HumanEval 164 (temperature 0, 8,192 tokens)")
print("  SparkInkling high:", score("ink-spark-gsm8k.jsonl"), "HumanEval", he("ink-spark-humaneval-exec.json"))
print("  SparkInkling low: ", score("ink-spark-gsm8k-low.jsonl"), "HumanEval", he("ink-spark-humaneval-low-exec.json"))
print("  SparkQwen 27B:    ", score("sq27b-gsm8k.jsonl"), "HumanEval", he("sq27b-humaneval-exec.json"))

d = json.load(open(os.path.join(HERE, "vllm-deep-15.json")))
text = d["content"] or ""
sents = collections.Counter(s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if len(s.strip()) > 30)
top, count = sents.most_common(1)[0]
print(f"\n== vLLM image, question 15, temperature 0, 32,768 tokens: finish {d['finish']}, {d['usage']['completion_tokens']} tokens")
print(f"  most repeated sentence ({count} times): {top!r}")
