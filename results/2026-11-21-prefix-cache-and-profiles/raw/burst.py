"""N concurrent short code requests; all must finish with stop."""
import json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
URL = "http://127.0.0.1:8895/v1/chat/completions"
def one(i):
    body = {"model": "m", "messages": [{"role": "user", "content": f"Write a Python function that returns the {i+2}th prime. Code only."}], "max_tokens": 1024, "temperature": 0, "reasoning_effort": "low"}
    r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=3600))
    return r["choices"][0]["finish_reason"], r["usage"]["completion_tokens"]
n = int(sys.argv[1]); t = time.time()
with ThreadPoolExecutor(n) as ex: res = list(ex.map(one, range(n)))
toks = sum(c for _, c in res)
print("C%d" % n, "stops %d/%d" % (sum(f == "stop" for f, _ in res), n), "%d tok in %.1fs = %.1f tok/s" % (toks, time.time() - t, toks / (time.time() - t)))
