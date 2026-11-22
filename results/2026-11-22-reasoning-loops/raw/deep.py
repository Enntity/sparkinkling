import json, sys, urllib.request
d = json.load(open("/tmp/mmlu.json"))[int(sys.argv[1])]
L = "ABCDEFGHIJ"
opts = "\n".join(f"{L[j]}. {o}" for j, o in enumerate(d["options"]))
p = (f"The following is a multiple-choice question about {d['category']}.\n\n{d['question']}\n\n{opts}\n\n"
     "Think it through, then end your reply with a line 'Answer: <letter>'.")
b = {"model": "inkling-2-mini-atlas", "messages": [{"role": "user", "content": p}], "temperature": 0, "max_tokens": int(sys.argv[2])}
r = json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8895/v1/chat/completions", json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=3600))
m = r["choices"][0]["message"]; rc = m.get("reasoning_content") or ""
json.dump({"reasoning": rc, "content": m.get("content"), "finish": r["choices"][0]["finish_reason"], "usage": r["usage"]}, open(f"/tmp/deep-{sys.argv[1]}.json", "w"))
n = len(rc); print("finish", r["choices"][0]["finish_reason"], "tokens", r["usage"]["completion_tokens"], "chars", n, "gold", d["answer"])
for frac in (0.15, 0.3, 0.45, 0.6, 0.8, 0.98):
    k = int(n * frac); print(f"--- at {frac:.0%}:", repr(rc[k:k+260]))
