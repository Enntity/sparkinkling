"""Send images to the chat endpoint and print the answers."""
import base64, json, sys, time, urllib.request
URL = "http://127.0.0.1:8895/v1/chat/completions"
def ask(path, question, effort="low"):
    uri = "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
    b = {"model": "m", "temperature": 0, "max_tokens": 400, "reasoning_effort": effort,
         "messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": uri}}, {"type": "text", "text": question}]}]}
    t0 = time.time()
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=600))
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()[:300]}"
    u = r.get("usage", {})
    return f"[{time.time()-t0:.2f}s prompt={u.get('prompt_tokens')}] " + (r["choices"][0]["message"].get("content") or "")[:500]
for path, q in zip(sys.argv[1::2], sys.argv[2::2]):
    print(path.split("/")[-1], "->", ask(path, q), flush=True)
