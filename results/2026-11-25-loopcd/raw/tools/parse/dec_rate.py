"""Server-reported decode rate, greedy, thinking off: code and prose, N runs each."""
import json, sys, urllib.request, statistics
URL = "http://127.0.0.1:8895/v1/chat/completions"
P = {"code": "Write a Python module implementing a binary min-heap class with push, pop, peek, heapify and a test suite.",
     "prose": "Write a long, vivid short story about a lighthouse keeper who finds a message in a bottle."}
n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
for k, p in P.items():
    rates = []
    for _ in range(n):
        b = {"model": "m", "messages": [{"role": "user", "content": p}], "max_tokens": 1024, "temperature": 0, "reasoning_effort": "none"}
        r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=600))
        rates.append(r["usage"]["response_token/s"])
    print(k, "median %.2f" % statistics.median(rates), " ".join("%.2f" % x for x in rates), "tokens", r["usage"]["completion_tokens"])
