#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Assemble the DSpark drafter directory Atlas loads with --draft-model.

  dspark_drafter.py PIN CHECKPOINT_DIR DRAFTER_DIR

The checkpoint ships its drafter as mtp.safetensors and describes it in
config.json's mtp_config. Atlas reads a drafter as a directory of its own:
DRAFTER_DIR gets model.safetensors, a relative symlink to the checkpoint's
mtp.safetensors (checked against PIN's sha256 first), and a config.json that
is the checkpoint's mtp_config plus vocab_size (the tokenizer vocab,
text_config.unpadded_vocab_size). DRAFTER_DIR must sit next to CHECKPOINT_DIR.

Idempotent: a directory built from the same checkpoint revision is left as it
is. Otherwise it is built beside DRAFTER_DIR and moved into place when
complete. Standard library only."""
import json
import os
import shutil
import sys

from check_files import sha256

DRAFT = 'mtp.safetensors'
MARKER = '.sparkinkling-dspark'


def drafter_config(checkpoint_config):
    """The drafter's config.json: mtp_config plus the tokenizer vocab size."""
    mtp = checkpoint_config.get('mtp_config')
    if not isinstance(mtp, dict) or mtp.get('markov_head_type') != 'rnn_hidden':
        raise SystemExit('config.json has no Inkling 2 DSpark mtp_config (markov_head_type rnn_hidden)')
    vocab = checkpoint_config.get('text_config', {}).get('unpadded_vocab_size')
    if not isinstance(vocab, int) or vocab <= 0:
        raise SystemExit('config.json has no text_config.unpadded_vocab_size')
    return {**mtp, 'vocab_size': vocab}


def build(pin, checkpoint, drafter):
    pin_json = json.load(open(pin))
    drafter = os.path.abspath(drafter)
    stamp = f'{pin_json["revision"]}\n'
    try:
        if open(os.path.join(drafter, MARKER)).read() == stamp:
            return False
    except OSError:
        pass
    if os.path.dirname(drafter) != os.path.dirname(os.path.abspath(checkpoint)):
        raise SystemExit('the drafter directory must sit next to the checkpoint directory')
    digest = pin_json['files'][DRAFT]
    got = sha256(os.path.join(checkpoint, DRAFT))
    if got != digest:
        raise SystemExit(f'{DRAFT}: sha256 {got}, pinned {digest}')
    config = drafter_config(json.load(open(os.path.join(checkpoint, 'config.json'))))

    partial = drafter + '.partial'
    shutil.rmtree(partial, ignore_errors=True)
    os.makedirs(partial)
    # relative to the shared parent, so it holds for the final name and in a
    # container that mounts each directory at its own path
    os.symlink(os.path.relpath(os.path.join(checkpoint, DRAFT), drafter), os.path.join(partial, 'model.safetensors'))
    with open(os.path.join(partial, 'config.json'), 'w') as f:
        json.dump(config, f, indent=1)
    with open(os.path.join(partial, MARKER), 'w') as f:
        f.write(stamp)
    if os.path.lexists(drafter):
        shutil.rmtree(drafter)
    os.rename(partial, drafter)
    return True


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__.split('\n\n')[1].strip())
    print('dspark drafter:', 'assembled' if build(*sys.argv[1:]) else 'up to date', sys.argv[3])
