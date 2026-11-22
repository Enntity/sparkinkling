#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Small quality comparison over an OpenAI-compatible chat endpoint.

  quality_eval.py --base URL --model ID --suite gsm8k|mmlu|humaneval --out FILE.jsonl
                  [--conc 8] [--max-tokens 8192] [--extra JSON] [--only 3,7,...]

Temperature 0, each model's default thinking (no reasoning arguments unless
--extra adds them). Answers are parsed from the final content only, never the
reasoning. GSM8K: the number after the last "Answer:". MMLU-Pro: the letter
after the last "Answer:". HumanEval: the last ```python block, written out for
he_exec.py to run. One JSON line per item; a summary line at the end.
Standard library only."""
import argparse, concurrent.futures as cf, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def chat(base, model, prompt, max_tokens, extra, key):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": max_tokens, "stream": False, **extra}
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    t = time.time()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", json.dumps(body).encode(), headers)
    d = json.load(urllib.request.urlopen(req, timeout=3600))
    c = d["choices"][0]
    return {"content": c["message"].get("content") or "", "finish": c.get("finish_reason"),
            "completion_tokens": (d.get("usage") or {}).get("completion_tokens"), "seconds": round(time.time() - t, 2)}


def num(s):
    s = s.replace(",", "").replace("$", "").strip()
    m = re.findall(r"-?\d+(?:\.\d+)?", s)
    return float(m[-1]) if m else None


def gsm8k_items():
    for i, r in enumerate(json.load(open(os.path.join(HERE, "gsm8k-150.json")))):
        gold = num(r["answer"].split("####")[-1])
        prompt = r["question"] + "\n\nSolve the problem. End your reply with a line 'Answer: <number>'."
        yield i, prompt, gold


def gsm8k_score(content, gold):
    tail = content.rsplit("Answer:", 1)[-1] if "Answer:" in content else content[-200:]
    got = num(tail)
    return got is not None and gold is not None and abs(got - gold) < 1e-6, got


LETTERS = "ABCDEFGHIJ"


def mmlu_items():
    for i, r in enumerate(json.load(open(os.path.join(HERE, "mmlu-pro-150.json")))):
        opts = "\n".join(f"{LETTERS[j]}. {o}" for j, o in enumerate(r["options"]))
        prompt = (f"The following is a multiple-choice question about {r['category']}.\n\n{r['question']}\n\n{opts}\n\n"
                  "Think it through, then end your reply with a line 'Answer: <letter>'.")
        yield i, prompt, r["answer"]


def mmlu_score(content, gold):
    m = re.findall(r"Answer:\s*\(?([A-J])\b", content)
    got = m[-1] if m else None
    return got == gold, got


def humaneval_items():
    for i, r in enumerate(json.load(open(os.path.join(HERE, "humaneval-164.json")))):
        prompt = ("Complete the following Python function. Reply with the complete function (with any imports it needs) "
                  "in a single ```python code block.\n\n```python\n" + r["prompt"] + "```")
        yield i, prompt, {"task_id": r["task_id"], "prompt": r["prompt"], "test": r["test"], "entry_point": r["entry_point"]}


def humaneval_score(content, gold):
    blocks = re.findall(r"```(?:python)?\n(.*?)```", content, re.S)
    code = blocks[-1] if blocks else content
    # a reply that is only the body keeps the prompt's signature
    if f"def {gold['entry_point']}" not in code:
        code = gold["prompt"] + code
    program = code + "\n\n" + gold["test"] + f"\n\ncheck({gold['entry_point']})\n"
    return None, {"task_id": gold["task_id"], "program": program}


SUITES = {"gsm8k": (gsm8k_items, gsm8k_score), "mmlu": (mmlu_items, mmlu_score), "humaneval": (humaneval_items, humaneval_score)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True); ap.add_argument("--model", required=True)
    ap.add_argument("--suite", required=True, choices=SUITES); ap.add_argument("--out", required=True)
    ap.add_argument("--conc", type=int, default=8); ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--extra", default="{}"); ap.add_argument("--key-env", default="")
    ap.add_argument("--only", default="", help="comma-separated item indices (a rerun of some items)")
    a = ap.parse_args()
    items_fn, score = SUITES[a.suite]
    extra = json.loads(a.extra); key = os.environ.get(a.key_env, "") if a.key_env else ""
    items = list(items_fn())
    if a.only:
        keep = {int(x) for x in a.only.split(',')}
        items = [it for it in items if it[0] in keep]

    def one(item):
        i, prompt, gold = item
        try:
            r = chat(a.base, a.model, prompt, a.max_tokens, extra, key)
        except Exception as e:  # recorded as a miss
            return {"i": i, "ok": False, "error": str(e)[:200]}
        ok, got = score(r["content"], gold)
        return {"i": i, "ok": ok, "got": got, "gold": gold if a.suite != "humaneval" else gold["task_id"], **r}

    t = time.time(); rows = []
    with cf.ThreadPoolExecutor(a.conc) as ex, open(a.out, "w") as f:
        for row in ex.map(one, items):
            rows.append(row); f.write(json.dumps(row) + "\n"); f.flush()
        n = len(rows); ok = sum(1 for r in rows if r.get("ok"))
        summary = {"summary": True, "suite": a.suite, "model": a.model, "n": n, "correct": ok,
                   "errors": sum(1 for r in rows if "error" in r), "length_cut": sum(1 for r in rows if r.get("finish") == "length"),
                   "mean_completion_tokens": round(sum(r.get("completion_tokens") or 0 for r in rows) / max(1, n)),
                   "wall_seconds": round(time.time() - t), "extra": extra}
        f.write(json.dumps(summary) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
