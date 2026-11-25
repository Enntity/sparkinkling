# SPDX-License-Identifier: AGPL-3.0-only
import json, sys, urllib.request
URL = "http://127.0.0.1:8895/v1/chat/completions"
tools = [{"type": "function", "function": {"name": "Say", "description": "Speak text aloud", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}}]
def req(stream, extra):
    b = {"model": "m", "messages": [{"role": "system", "content": "You talk by calling Say."}, {"role": "user", "content": "Greet me."}], "tools": tools, "max_tokens": 400, "temperature": 0, "stream": stream, **extra}
    r = urllib.request.urlopen(urllib.request.Request(URL, json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=300)
    if not stream:
        d = json.load(r); m = d["choices"][0]["message"]
        return d["choices"][0]["finish_reason"], m.get("tool_calls"), (m.get("content") or "")[:120]
    calls, content, fin = [], "", None
    for line in r:
        line = line.decode().strip()
        if not line.startswith("data: ") or line == "data: [DONE]": continue
        ch = json.loads(line[6:]).get("choices") or []
        if not ch: continue
        dl = ch[0].get("delta", {}); fin = ch[0].get("finish_reason") or fin
        if dl.get("tool_calls"): calls.append(dl["tool_calls"])
        content += dl.get("content") or ""
    return fin, calls[:3], content[:160]
for label, extra in [("low", {"reasoning_effort": "low"}), ("thinking-off", {"chat_template_kwargs": {"enable_thinking": False}})]:
    for s in (False, True):
        print(label, "stream" if s else "plain", req(s, extra))
