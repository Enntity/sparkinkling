"""Greedy text of three prompts (300 tokens each) to a file, for bit-identity A/B."""
import json, sys, urllib.request
URL = "http://127.0.0.1:8895/v1/chat/completions"
P = ["Write a Python class for an LRU cache with get and put, with docstrings.", "Describe a walk along a foggy coastline at dawn in vivid prose.", "Return a JSON array of 12 objects with fields id, name, and score for a fictional leaderboard."]
out = []
for p in P:
    b = {"model": "m", "messages": [{"role": "user", "content": p}], "max_tokens": 300, "temperature": 0, "reasoning_effort": "low"}
    r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=600))
    m = r["choices"][0]["message"]; out.append((m.get("reasoning_content") or "") + "|" + (m.get("content") or ""))
json.dump(out, open(sys.argv[1], "w"))
