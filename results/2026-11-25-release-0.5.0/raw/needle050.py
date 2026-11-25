"""Long-context recall: a code hidden a third of the way into ~N words of filler."""
import json, random, sys, time, urllib.request
URL = "http://127.0.0.1:8895/v1/chat/completions"
n = int(sys.argv[1]); random.seed(7)
words = "the quiet harbor kept its lamps lit through every winter storm while ships waited".split()
filler = [random.choice(words) for _ in range(n)]
filler.insert(n // 3, " The vault code is 7391-KESTREL. ")
msg = " ".join(filler) + "\n\nWhat is the vault code? Answer with the code only."
body = {"model": "inkling-2-mini-atlas", "messages": [{"role": "user", "content": msg}], "max_tokens": 512, "temperature": 0, "reasoning_effort": "low"}
t = time.time()
r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=3600))
print("prompt_tokens", r["usage"]["prompt_tokens"], "%.1fs" % (time.time() - t), "found" if "7391-KESTREL" in (r["choices"][0]["message"].get("content") or "") else "MISSING", repr((r["choices"][0]["message"].get("content") or "")[:80]))
