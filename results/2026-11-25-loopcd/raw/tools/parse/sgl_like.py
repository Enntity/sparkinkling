"""2K random-token prompt -> 256 tokens, streamed: TTFT and mean TPOT (sglang random-dataset shape)."""
import json, random, sys, time, urllib.request
inp, out = int(sys.argv[1]), int(sys.argv[2])
random.seed(int(sys.argv[3]) if len(sys.argv) > 3 else 0)
ids = [random.randint(1000, 150000) for _ in range(inp)]
body = {"model": "m", "prompt": ids, "max_tokens": out, "temperature": 0, "ignore_eos": True, "stream": True,
        "stream_options": {"include_usage": True}}
usage = None
t0 = time.time(); times = []
r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8895/v1/completions", json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=3600)
for line in r:
    line = line.decode().strip()
    if line.startswith("data: ") and line != "data: [DONE]":
        ch = json.loads(line[6:])
        usage = ch.get("usage") or usage
        if ch.get("choices"): times.append(time.time())
n = (usage or {}).get("completion_tokens", len(times))
ttft = times[0] - t0; tpot = (times[-1] - times[0]) / max(1, n - 1)
print(f"in {inp} out {n} tokens  TTFT {ttft:.2f}s  TPOT {tpot*1000:.1f} ms  decode {1/tpot:.1f} tok/s")
