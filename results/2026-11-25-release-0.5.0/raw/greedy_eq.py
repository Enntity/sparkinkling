"""Greedy text hashes for a fixed prompt set: greedy_eq.py OUT.json [TOKENS=320] [CONCURRENCY=1]
8 prompts (4 code, 4 prose), reasoning low, temperature 0. Compare two OUT files with `compare A B`."""
import concurrent.futures as cf, hashlib, json, sys, urllib.request
URL = "http://127.0.0.1:8895/v1/chat/completions"
BASE = {"code": "Write a Go package implementing a token-bucket rate limiter with a fake clock and table-driven tests.",
        "prose": "Write an internal engineering memo arguing for or against buying local AI hardware instead of using hosted models. Plain paragraphs."}
PROMPTS = [(k, i) for k in ("code", "prose") for i in range(4)]
def ask(p, toks):
    kind, i = p
    body = {"model": "m", "messages": [{"role": "user", "content": BASE[kind] + " Variant %d." % i}], "temperature": 0, "max_tokens": toks,
            "chat_template_kwargs": {"reasoning_effort": "low"}}
    r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=3600))
    m = r["choices"][0]["message"]
    text = (m.get("reasoning_content") or "") + "|" + (m.get("content") or "")
    return {"prompt": f"{kind}-{i}", "tokens": r["usage"]["completion_tokens"], "sha": hashlib.sha256(text.encode()).hexdigest()[:12], "text": text}
if sys.argv[1] == "compare":
    a, b = (json.load(open(p)) for p in sys.argv[2:4])
    same = 0
    for x, y in zip(a, b):
        eq = x["sha"] == y["sha"]; same += eq
        n = next((i for i, (p, q) in enumerate(zip(x["text"], y["text"])) if p != q), min(len(x["text"]), len(y["text"])))
        print(x["prompt"], "same" if eq else f"DIFFERS after {n} of {len(x['text'])} chars")
    print(f"{same}/{len(a)} identical")
else:
    out, toks, conc = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 320, int(sys.argv[3]) if len(sys.argv) > 3 else 1
    with cf.ThreadPoolExecutor(conc) as ex:
        res = list(ex.map(lambda p: ask(p, toks), PROMPTS))
    json.dump(res, open(out, "w"))
    print(out, " ".join(r["sha"][:6] for r in res))
