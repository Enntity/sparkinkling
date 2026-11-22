"""Prefix-cache check: the same long prompt cold then warm (identical greedy text expected,
warm TTFT far lower), then the prompt extended (a multi-turn shape)."""
import json, random, sys, time, urllib.request
URL = "http://127.0.0.1:8895/v1/completions"
def run(prompt, n=64):
    body = {"model": "m", "prompt": prompt, "max_tokens": n, "temperature": 0, "stream": True}
    t0 = time.time(); first = None; text = ""
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    for line in urllib.request.urlopen(req, timeout=3600):
        line = line.decode().strip()
        if not line.startswith("data: ") or line == "data: [DONE]": continue
        d = json.loads(line[6:]); c = d["choices"][0].get("text", "")
        if c and first is None: first = time.time() - t0
        text += c
    return first, text
words = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
random.seed(7)
vocab = "alpha beta gamma delta epsilon zeta theta kappa lambda sigma omega river stone cloud field forest ember".split()
doc = " ".join(random.choice(vocab) for _ in range(words))
base = "Summarize the following notes in one sentence.\n" + doc + "\nSummary:"
t1, a = run(base); t2, b = run(base)
print("cold TTFT %.2fs warm TTFT %.2fs identical=%s" % (t1, t2, a == b))
if a != b: print("COLD:", repr(a[:120])); print("WARM:", repr(b[:120]))
t3, c = run(base + a + "\nNow list three words from the notes:")
print("extended TTFT %.2fs" % t3, repr(c[:80]))
