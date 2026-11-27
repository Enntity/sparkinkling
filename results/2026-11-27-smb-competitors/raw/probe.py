import json, sys, urllib.request
base, model = sys.argv[1], sys.argv[2]
def post(path, body):
    r = urllib.request.urlopen(urllib.request.Request(base + path, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=600)
    return json.loads(r.read())
q = "A train leaves at 3:40 pm and the trip takes 2 hours 35 minutes. When does it arrive? Answer briefly."
for eff in ["low", "high"]:
    d = post("/v1/chat/completions", {"model": model, "messages": [{"role": "user", "content": q}], "max_tokens": 4096, "temperature": 0, "reasoning_effort": eff})
    m = d["choices"][0]["message"]; rs = m.get("reasoning_content") or m.get("reasoning") or ""
    print("effort", eff, "completion_tokens", d["usage"]["completion_tokens"], "reasoning_chars", len(rs), "answer", (m.get("content") or "")[:60].replace("\n", " "))
tools = [{"type": "function", "function": {"name": "get_weather", "description": "Weather for a city", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
d = post("/v1/chat/completions", {"model": model, "messages": [{"role": "user", "content": "What is the weather in Lisbon?"}], "tools": tools, "max_tokens": 2048, "temperature": 0, "reasoning_effort": "low"})
c = d["choices"][0]; print("tool", c["finish_reason"], json.dumps(c["message"].get("tool_calls"))[:160])
d = post("/v1/completions", {"model": model, "prompt": [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007], "max_tokens": 4, "temperature": 0})
print("token-id completion ok", d["usage"])
