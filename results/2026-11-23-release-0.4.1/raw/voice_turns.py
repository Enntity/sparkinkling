"""Replay the voice rig prompt shape: system | history triples | 3 trailing user blocks rebuilt each turn.
Per turn: a user-turn request, then a follow-up with that turn's Say call + result appended.
Prints client TTFT (first streamed delta) per request."""
import json, sys, time, urllib.request
URL = "http://127.0.0.1:8895/v1/chat/completions"
TURNS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
say = {"type": "function", "function": {"name": "Say", "description": "Speak text aloud.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}}
blurb = "does a careful, specific thing with the given input and returns a structured result. " * 6
tools = [say] + [{"type": "function", "function": {"name": f"tool_{i}", "description": f"Utility number {i}: {blurb}", "parameters": {"type": "object", "properties": {"input": {"type": "string", "description": "The input value."}, "mode": {"type": "string", "enum": ["fast", "full"]}}, "required": ["input"]}}} for i in range(26)]
facts = " ".join(f"Fact {i}: the archive room on level {i % 9} holds ledger {i * 37 % 101}, catalogued by keeper {i * 13 % 47} in season {i % 4}." for i in range(330))
system = "You are a warm, concise voice companion. Always speak by calling Say exactly once.\n\n" + facts
words = ["How was your morning?", "Tell me about the archive.", "Which keeper do you like?", "What season is it there?",
         "Can you remind me of ledger forty?", "Say something kind.", "What did we talk about first?", "Good night for now."]


def stream(msgs):
    b = {"model": "m", "stream": True, "temperature": 0, "max_tokens": 48, "tools": tools, "tool_choice": "auto", "messages": msgs}
    t0 = time.time()
    first = None
    req = urllib.request.Request(URL, json.dumps(b).encode(), {"Content-Type": "application/json"})
    for line in urllib.request.urlopen(req, timeout=600):
        line = line.decode().strip()
        if first is None and line.startswith("data: ") and line != "data: [DONE]":
            d = (json.loads(line[6:]).get("choices") or [{}])[0].get("delta") or {}
            if d.get("content") or d.get("reasoning_content") or d.get("reasoning") or d.get("tool_calls"):
                first = time.time() - t0
    return first or float("nan")


history = []
for k in range(TURNS):
    orient = "Orientation. " + " ".join(f"Note {j}: the call has covered topic {j} and the mood is calm." for j in range(20 + 6 * k))
    trailing = [{"role": "user", "content": orient},
                {"role": "user", "content": f"[voice turn {k}] [speaker: J] [heard at turn {k}]\n{words[k % len(words)]}"},
                {"role": "user", "content": f"Body state: breathing slow, posture relaxed, energy {50 + k}%."}]
    msgs = [{"role": "system", "content": system}] + history + trailing
    t_user = stream(msgs)
    args = json.dumps({"text": f"Reply number {k}, about {words[k % len(words)].lower()} It was lovely to hear from you."})
    call = {"role": "assistant", "content": "", "tool_calls": [{"id": f"c{k}", "type": "function", "function": {"name": "Say", "arguments": args}}]}
    result = {"role": "tool", "tool_call_id": f"c{k}", "content": "spoken"}
    t_follow = stream(msgs + [call, result])
    print(f"turn {k} user-turn ttft {t_user:.3f} follow-up ttft {t_follow:.3f}", flush=True)
    history += [{"role": "user", "content": words[k % len(words)]}, call, result]
