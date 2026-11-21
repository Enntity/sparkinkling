#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Assemble the Spark-mode model directory: the checkpoint's files, linked,
plus the calibrated NVFP4 overlay and an index that maps both.

  spark_overlay.py PIN CHECKPOINT_DIR OVERLAY_DIR MODEL_DIR

PIN is install/checkpoint.json; its "overlay" entry names the overlay file, its
sha256, its tensor count and the name prefixes its tensors may use. The overlay
file in OVERLAY_DIR is checked against the pin before anything is written.
MODEL_DIR gets a relative symlink to every file of CHECKPOINT_DIR (hidden
download state excluded) and to the overlay file, and a
model.safetensors.index.json whose weight_map is the checkpoint's with every
overlay tensor mapped to the overlay file; Atlas serves those tensors in place
of the checkpoint's. MODEL_DIR must sit next to CHECKPOINT_DIR and OVERLAY_DIR.

Idempotent: a directory already built from the same checkpoint and overlay
revisions is left as it is. Otherwise it is built beside MODEL_DIR and moved
into place only when complete. Standard library only."""
import json
import os
import re
import shutil
import struct
import sys

from check_files import sha256

INDEX = 'model.safetensors.index.json'
MARKER = '.sparkinkling-overlay'


def pinned(spec):
    """The overlay pin is filled in: a commit, and a sha256 for every file."""
    return (re.fullmatch(r'[0-9a-f]{40}', spec.get('revision', '')) is not None
            and all(re.fullmatch(r'[0-9a-f]{64}', d) for d in spec['files'].values()))


def tensor_names(path):
    """The tensor names in a safetensors file's header."""
    with open(path, 'rb') as f:
        n = struct.unpack('<Q', f.read(8))[0]
        if n > 1 << 28:
            raise SystemExit(f'{path}: not a safetensors file')
        meta = json.loads(f.read(n))
    return sorted(k for k in meta if k != '__metadata__')


def build(pin, checkpoint, overlay, model):
    pin_json = json.load(open(pin))
    spec = pin_json['overlay']
    if not pinned(spec):
        raise SystemExit(f'{pin}: the Spark overlay {spec["repository"]} is not pinned yet '
                         '(revision and sha256 are TODO); serve MODE=strict')
    model = os.path.abspath(model)
    stamp = f'{pin_json["revision"]} {spec["revision"]}\n'
    try:
        if open(os.path.join(model, MARKER)).read() == stamp:
            return False
    except OSError:
        pass
    if os.path.dirname(model) != os.path.dirname(os.path.abspath(checkpoint)) or \
            os.path.dirname(model) != os.path.dirname(os.path.abspath(overlay)):
        raise SystemExit('the model directory must sit next to the checkpoint and overlay directories')
    for name, digest in spec['files'].items():
        got = sha256(os.path.join(overlay, name))
        if got != digest:
            raise SystemExit(f'{name}: sha256 {got}, pinned {digest}')
    serve = spec['serve']
    names = tensor_names(os.path.join(overlay, serve))
    if len(names) != spec['tensors']:
        raise SystemExit(f'{serve}: {len(names)} tensors, pinned {spec["tensors"]}')
    stray = [t for t in names if not t.startswith(tuple(spec['prefixes']))]
    if stray:
        raise SystemExit(f'{serve}: tensors outside {", ".join(spec["prefixes"])}: {", ".join(stray[:5])}')
    index = json.load(open(os.path.join(checkpoint, INDEX)))
    missing = sorted({f for f in index['weight_map'].values() if not os.path.isfile(os.path.join(checkpoint, f))})
    if missing:
        raise SystemExit(f'{checkpoint}: missing {", ".join(missing)}')
    if serve in os.listdir(checkpoint):
        raise SystemExit(f'{checkpoint} already has a {serve}')

    partial = model + '.partial'
    shutil.rmtree(partial, ignore_errors=True)
    os.makedirs(partial)
    # The links are relative to the shared parent, so they hold for the final
    # name too, and inside a container that mounts each directory at its own path.
    for name in sorted(os.listdir(checkpoint)):
        if name != INDEX and not name.startswith('.'):
            os.symlink(os.path.relpath(os.path.join(checkpoint, name), model), os.path.join(partial, name))
    os.symlink(os.path.relpath(os.path.join(overlay, serve), model), os.path.join(partial, serve))
    index['weight_map'].update({t: serve for t in names})
    with open(os.path.join(partial, INDEX), 'w') as f:
        json.dump(index, f, indent=2)
    with open(os.path.join(partial, MARKER), 'w') as f:
        f.write(stamp)
    if os.path.lexists(model):
        shutil.rmtree(model)
    os.rename(partial, model)
    return True


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit(__doc__.split('\n\n')[1].strip())
    print('spark overlay:', 'assembled' if build(*sys.argv[1:]) else 'up to date', sys.argv[4])
