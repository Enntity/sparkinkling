"""Disk prefix-cache check: conversations A-D (about 20K tokens each) push A out of the
GPU pool; A again must restore (low TTFT) with the same greedy text."""
import json, random, time, urllib.request
URL = "http://127.0.0.1:8895/v1/completions"
def run(prompt, n=48):
    body = {"model": "m", "prompt": prompt, "max_tokens": n, "temperature": 0, "stream": True}
    t0 = time.time(); first = None; text = ""
    for line in urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=3600):
        line = line.decode().strip()
        if not line.startswith("data: ") or line == "data: [DONE]": continue
        c = json.loads(line[6:])["choices"][0].get("text", "")
        if c and first is None: first = time.time() - t0
        text += c
    return first, text
vocab = "alpha beta gamma delta epsilon zeta theta kappa lambda sigma omega river stone cloud field forest ember".split()
def conv(seed):
    random.seed(seed)
    return "Notes:\n" + " ".join(random.choice(vocab) for _ in range(16000)) + "\nList the three most frequent words:"
run("warm the cache", 4)
ta, a = run(conv(1))
for s in (2, 3, 4, 5, 6): run(conv(s), 8)
tb, b = run(conv(1))
print("A cold %.2fs, A after B-D %.2fs, identical=%s" % (ta, tb, a == b))
if a != b: print(repr(a[:100])); print(repr(b[:100]))
