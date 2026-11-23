# SPDX-License-Identifier: AGPL-3.0-only
"""Quick task probe: 30 arithmetic problems (exact answer) + 10 tool-call prompts (right tool, right args)."""
import json, random, re, sys, urllib.request
port = sys.argv[1]
URL = f"http://127.0.0.1:{port}/v1/chat/completions"
def chat(messages, tools=None, max_tokens=1536):
    body = {"model": "m", "messages": messages, "temperature": 0, "max_tokens": max_tokens, "reasoning_effort": "low"}
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=900))["choices"][0]
rng = random.Random(7)
math = []
for i in range(30):
    a, b, c = rng.randint(12, 99), rng.randint(12, 99), rng.randint(100, 999)
    math.append((f"A crate holds {a} boxes of {b} apples, and {c} loose apples are added. How many apples in total? Answer with the number only.", a * b + c))
WEATHER = {"type": "function", "function": {"name": "get_weather", "description": "Current weather for a city", "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}}, "required": ["city"]}}}
STOCK = {"type": "function", "function": {"name": "get_stock_price", "description": "Latest price of a stock ticker", "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}}}
tools = [(f"What is the weather in {c} right now, in celsius?", "get_weather", "city", c) for c in ["Paris", "Tokyo", "Lima", "Oslo", "Cairo"]] + \
        [(f"What is the current share price of {t}?", "get_stock_price", "ticker", t) for t in ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN"]]
def do_math(q):
    ch = chat([{"role": "user", "content": q[0]}])
    nums = re.findall(r"-?\d+", (ch["message"].get("content") or "").replace(",", ""))
    return bool(nums) and int(nums[-1]) == q[1]
def do_tool(t):
    ch = chat([{"role": "user", "content": t[0]}], tools=[WEATHER, STOCK])
    calls = ch["message"].get("tool_calls") or []
    if not calls:
        return False
    f = calls[0]["function"]
    try:
        args = json.loads(f["arguments"])
    except Exception:
        return False
    return f["name"] == t[1] and str(args.get(t[2], "")).upper() == t[3].upper()
m = [do_math(q) for q in math]
t = [do_tool(x) for x in tools]
print(json.dumps({"port": port, "math": f"{sum(m)}/{len(m)}", "tools": f"{sum(t)}/{len(t)}", "math_ok": m, "tools_ok": t}))
