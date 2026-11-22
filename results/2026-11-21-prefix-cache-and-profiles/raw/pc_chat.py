"""Two-turn chat through the template: turn 1 a long user message (~N words), turn 2 the
history plus a short question. Prints turn-1 and turn-2 TTFT and whether turn 2 repeats."""
import json, random, sys, time, urllib.request
URL = "http://127.0.0.1:8895/v1/chat/completions"
def ask(msgs, n=64):
    b = {"model": "m", "messages": msgs, "max_tokens": n, "temperature": 0, "stream": True, "reasoning_effort": "low"}
    t0 = time.time(); first = None; text = ""
    for line in urllib.request.urlopen(urllib.request.Request(URL, json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=3600):
        line = line.decode().strip()
        if not line.startswith("data: ") or line == "data: [DONE]": continue
        d = json.loads(line[6:])["choices"][0].get("delta", {})
        c = (d.get("content") or "") + (d.get("reasoning_content") or "")
        if c and first is None: first = time.time() - t0
        text += d.get("content") or ""
    return first, text
n = int(sys.argv[1]); random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
vocab = "harbor lantern winter ship market bread copper road garden river".split()
doc = " ".join(random.choice(vocab) for _ in range(n))
m1 = [{"role": "user", "content": "Here are my notes:\n" + doc + "\nIn one sentence, what are they about?"}]
t1, a1 = ask(m1)
m2 = m1 + [{"role": "assistant", "content": a1}, {"role": "user", "content": "Name one word that appears in them."}]
t2, a2 = ask(m2)
print("words %d turn1 %.2fs turn2 %.2fs" % (n, t1, t2))
