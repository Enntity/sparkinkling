#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Reads the launcher's smoke completion on stdin: the answer to 17*23 must
contain 391 and stop normally. Adapted from SparkGLM's; Inkling may wrap the
number in a few words, so the answer is not required to be the bare number."""
import json
import re
import sys

try:
    choice = json.load(sys.stdin)["choices"][0]
    text = (choice.get("message", {}).get("content") or "").strip()
    finish = choice.get("finish_reason")
except (ValueError, KeyError, IndexError, AttributeError, TypeError) as error:
    sys.exit(f"smoke failed: invalid completion response ({error})")
if not re.search(r"(?<![\d.,])391(?![\d,]|\.\d)", text) or len(text) > 200 or finish != "stop":
    sys.exit(f"smoke failed: expected 391 with normal stop; got {text!r}, finish_reason={finish!r}")
print("smoke: 17*23 =", text)
