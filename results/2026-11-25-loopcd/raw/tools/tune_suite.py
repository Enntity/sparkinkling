# throughput by kind over the fixed 40-prompt suite, one request at a time (C1) or two at once (C2); temp 0, effort low
import json, sys, time, urllib.request, concurrent.futures as cf, hashlib
conc = int(sys.argv[1]); out = sys.argv[2]
S = json.load(open("/home/enntitysparkadmin/inkling2-loopcd/tools/tune_suite.json"))
def ask(p):
    b = {"model": "m", "messages": [{"role": "user", "content": p["text"]}], "temperature": 0, "max_tokens": 512, "reasoning_effort": "low"}
    t = time.time()
    r = json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8895/v1/chat/completions", json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=3600))
    m = r["choices"][0]["message"]; txt = (m.get("reasoning_content") or "") + "|" + (m.get("content") or "")
    return {"kind": p["kind"], "tokens": r["usage"]["completion_tokens"], "sec": time.time() - t, "sha": hashlib.sha256(txt.encode()).hexdigest()[:12]}
t0 = time.time()
with cf.ThreadPoolExecutor(conc) as ex: res = list(ex.map(ask, S))
wall = time.time() - t0
json.dump(res, open(out, "w"))
for k in ("code", "math", "mmlu", "prose"):
    rs = [x for x in res if x["kind"] == k]; tok = sum(x["tokens"] for x in rs); sec = sum(x["sec"] for x in rs)
    print(f"  {k}: {tok} tokens, {tok/sec*conc:.1f} tok/s")
tok = sum(x["tokens"] for x in res); print(f"  all: {tok} tokens in {wall:.0f}s = {tok/wall:.1f} tok/s aggregate")
