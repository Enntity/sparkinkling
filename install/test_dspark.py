# SPDX-License-Identifier: AGPL-3.0-only
"""CPU checks for the DSpark drafter directory (install/dspark_drafter.py)."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dspark_drafter as dspark  # noqa: E402

MTP = {'hidden_size': 2304, 'num_hidden_layers': 3, 'block_size': 8, 'markov_head_type': 'rnn_hidden',
       'local_layer_ids': [0, 2], 'target_layer_ids': [5, 23, 41, 48]}


class Assemble(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.ck = self.root/'thinkingmachines--Inkling-2-Mini'
        self.ck.mkdir()
        (self.ck/'mtp.safetensors').write_bytes(b'drafter')
        (self.ck/'config.json').write_text(json.dumps(
            {'mtp_config': MTP, 'text_config': {'unpadded_vocab_size': 200058, 'vocab_size': 201024}}))
        self.pin = self.root/'checkpoint.json'
        self.write_pin(hashlib.sha256(b'drafter').hexdigest())
        self.out = self.root/'thinkingmachines--Inkling-2-Mini+dspark'

    def write_pin(self, digest, revision='a' * 40):
        self.pin.write_text(json.dumps({'revision': revision, 'files': {'mtp.safetensors': digest}}))

    def test_builds_config_and_link(self):
        self.assertTrue(dspark.build(self.pin, self.ck, self.out))
        cfg = json.loads((self.out/'config.json').read_text())
        self.assertEqual(cfg, {**MTP, 'vocab_size': 200058})
        link = self.out/'model.safetensors'
        self.assertTrue(link.is_symlink())
        self.assertFalse(os.path.isabs(os.readlink(link)))
        self.assertEqual(link.read_bytes(), b'drafter')

    def test_idempotent_then_rebuilt_on_new_revision(self):
        self.assertTrue(dspark.build(self.pin, self.ck, self.out))
        self.assertFalse(dspark.build(self.pin, self.ck, self.out))
        self.write_pin(hashlib.sha256(b'drafter').hexdigest(), revision='b' * 40)
        self.assertTrue(dspark.build(self.pin, self.ck, self.out))

    def test_wrong_digest_refused(self):
        self.write_pin('0' * 64)
        with self.assertRaises(SystemExit):
            dspark.build(self.pin, self.ck, self.out)
        self.assertFalse(self.out.exists())

    def test_config_without_mtp_refused(self):
        with self.assertRaises(SystemExit):
            dspark.drafter_config({'text_config': {'unpadded_vocab_size': 1}})
        with self.assertRaises(SystemExit):
            dspark.drafter_config({'mtp_config': MTP, 'text_config': {}})

    def test_must_sit_next_to_checkpoint(self):
        with self.assertRaises(SystemExit):
            dspark.build(self.pin, self.ck, self.root/'elsewhere'/'drafter')


if __name__ == '__main__':
    unittest.main()
