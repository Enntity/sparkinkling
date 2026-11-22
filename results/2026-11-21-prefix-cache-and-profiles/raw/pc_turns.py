"""Two-turn check: turn 1 decodes an answer; turn 2 sends prompt + answer + a new question."""
import json, random, time, urllib.request
URL = "http://127.0.0.1:8895/v1/completions"
def run(prompt, n):
    body = {"model": "m", "prompt": prompt, "max_tokens": n, "temperature": 0, "stream": True}
    t0 = time.time(); first = None; text = ""
    for line in urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=3600):
        line = line.decode().strip()
        if not line.startswith("data: ") or line == "data: [DONE]": continue
        c = json.loads(line[6:])["choices"][0].get("text", "")
        if c and first is None: first = time.time() - t0
        text += c
    return first, text
run("Hello there, prime the cache with a short request.", 4)
random.seed(11)
vocab = "alpha beta gamma delta epsilon zeta theta kappa lambda sigma omega river stone cloud field forest ember".split()
doc = " ".join(random.choice(vocab) for _ in range(5000))
p1 = "Notes:\n" + doc + "\nWrite a long story that uses these words:"
t1, a1 = run(p1, 1200)
p2 = p1 + a1 + "\nNow give the story a title:"
t2, a2 = run(p2, 32)
print("turn1 TTFT %.2fs (%d chars out), turn2 TTFT %.2fs" % (t1, len(a1), t2), repr(a2[:60]))
