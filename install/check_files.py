#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Check a downloaded repository against its pin: every file the pin lists
must be in DIR with that sha256.

  check_files.py PIN DIR [KEY]   e.g. install/checkpoint.json ~/models/... overlay

Without KEY the pin's own "files" are checked (the checkpoint); with KEY, the
"files" of that entry. Exit 0 when every file matches, 1 (naming the files)
otherwise. Standard library only. Adapted from SparkQwen's."""
import hashlib
import json
import sys
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 26), b''):
            h.update(block)
    return h.hexdigest()


def check(pin, root, key=None):
    spec = json.loads(Path(pin).read_text())
    files = (spec[key] if key else spec)['files']
    return [name for name, digest in files.items()
            if not (Path(root)/name).is_file() or sha256(Path(root)/name) != digest]


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    bad = check(*sys.argv[1:])
    if bad:
        sys.exit(f'{sys.argv[2]}: sha256 does not match the pin for {", ".join(bad)}')
