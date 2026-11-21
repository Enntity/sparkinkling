# SPDX-License-Identifier: AGPL-3.0-only
"""CPU checks for the Spark-mode model directory (install/spark_overlay.py)
and the download checks (install/check_files.py)."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # spark_overlay imports check_files, as it does when run
import check_files  # noqa: E402
import spark_overlay as overlay  # noqa: E402

sspec = importlib.util.spec_from_file_location('atlas_serve', HERE/'serve.py')
serve = importlib.util.module_from_spec(sspec)
sspec.loader.exec_module(serve)
OVERLAY_TENSORS = ['model.language_model.layers.0.self_attn.q_proj.linear.weight',
                   'model.language_model.layers.0.self_attn.q_proj.linear.weight_scale',
                   'model.language_model.layers.0.self_attn.q_proj.linear.weight_scale_2',
                   'lm_head.weight']


def write_st(path, names):
    head, off = {}, 0
    for k in names:
        head[k] = {'dtype': 'U8', 'shape': [4], 'data_offsets': [off, off + 4]}
        off += 4
    blob = json.dumps(head).encode()
    blob += b' ' * (-len(blob) % 8)
    Path(path).write_bytes(struct.pack('<Q', len(blob)) + blob + bytes(off))


class Assemble(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.ck = self.root/'thinkingmachines--Inkling-2-Mini'
        self.w = self.root/'Enntity--Inkling-2-Mini-Spark-NVFP4'
        self.model = self.root/'thinkingmachines--Inkling-2-Mini+spark-nvfp4'
        self.ck.mkdir()
        self.w.mkdir()
        (self.ck/'config.json').write_text('{}')
        (self.ck/'model-00001-of-00001.safetensors').write_bytes(b'ckpt')
        (self.ck/'mtp.safetensors').write_bytes(b'draft')
        (self.ck/'tiktoken').mkdir()
        (self.ck/'tiktoken'/'tokenizer.model').write_bytes(b'tok')
        (self.ck/'.sparkinkling-revision').write_text('c' * 40 + '\n')
        (self.ck/'.cache').mkdir()
        self.index = {'metadata': {'total_size': 4},
                      'weight_map': {'model.llm.layers.0.attn.wq_du.weight': 'model-00001-of-00001.safetensors',
                                     'lm_head.weight': 'model-00001-of-00001.safetensors'}}
        (self.ck/'model.safetensors.index.json').write_text(json.dumps(self.index))
        self.pin(OVERLAY_TENSORS)

    def pin(self, names, revision='a' * 40, digest=None, count=None):
        write_st(self.w/'spark-nvfp4.safetensors', names)
        real = json.loads((HERE/'checkpoint.json').read_text())
        real['revision'] = 'c' * 40
        real['overlay'].update(revision=revision, tensors=len(OVERLAY_TENSORS) if count is None else count,
                               files={'spark-nvfp4.safetensors': digest or check_files.sha256(self.w/'spark-nvfp4.safetensors')})
        self.pin_path = self.root/'checkpoint.json'
        self.pin_path.write_text(json.dumps(real))

    def build(self):
        return overlay.build(str(self.pin_path), str(self.ck), str(self.w), str(self.model))

    def test_links_the_checkpoint_and_maps_the_overlay(self):
        self.assertTrue(self.build())
        self.assertEqual(os.readlink(self.model/'model-00001-of-00001.safetensors'),
                         '../thinkingmachines--Inkling-2-Mini/model-00001-of-00001.safetensors')
        self.assertEqual(os.readlink(self.model/'spark-nvfp4.safetensors'),
                         '../Enntity--Inkling-2-Mini-Spark-NVFP4/spark-nvfp4.safetensors')
        self.assertEqual((self.model/'tiktoken'/'tokenizer.model').read_bytes(), b'tok')  # a linked directory
        self.assertTrue((self.model/'mtp.safetensors').is_symlink())  # the draft model travels with it
        self.assertFalse(os.path.lexists(self.model/'.sparkinkling-revision'))
        self.assertFalse(os.path.lexists(self.model/'.cache'))
        self.assertFalse((self.model/'model.safetensors.index.json').is_symlink())
        index = json.loads((self.model/'model.safetensors.index.json').read_text())
        wm = index['weight_map']
        self.assertEqual(index['metadata'], self.index['metadata'])
        self.assertEqual(wm['model.llm.layers.0.attn.wq_du.weight'], 'model-00001-of-00001.safetensors')
        for name in OVERLAY_TENSORS:
            self.assertEqual(wm[name], 'spark-nvfp4.safetensors', name)
        self.assertEqual(len(wm), 5)  # the checkpoint's two, plus four overlay tensors (lm_head.weight remapped)
        serve.check_model_dir(self.model, 'spark')
        serve.check_model_dir(self.ck, 'strict')  # the checkpoint itself is untouched
        self.assertEqual(json.loads((self.ck/'model.safetensors.index.json').read_text()), self.index)

    def test_idempotent(self):
        self.assertTrue(self.build())
        before = os.stat(self.model/'model.safetensors.index.json')
        self.assertFalse(self.build())
        self.assertEqual(os.stat(self.model/'model.safetensors.index.json').st_ino, before.st_ino)
        self.assertFalse(os.path.exists(str(self.model) + '.partial'))

    def test_a_new_overlay_revision_rebuilds_it(self):
        self.build()
        self.pin(OVERLAY_TENSORS[:2] + ['lm_head.weight', 'lm_head.weight_scale'], revision='b' * 40)
        self.assertTrue(self.build())
        wm = json.loads((self.model/'model.safetensors.index.json').read_text())['weight_map']
        self.assertEqual(wm['lm_head.weight_scale'], 'spark-nvfp4.safetensors')
        self.assertNotIn(OVERLAY_TENSORS[2], wm)
        self.assertIn('b' * 40, (self.model/'.sparkinkling-overlay').read_text())

    def test_a_partial_build_is_replaced(self):
        Path(str(self.model) + '.partial').mkdir()
        (Path(str(self.model) + '.partial')/'junk').write_text('x')
        self.build()
        self.assertFalse(os.path.lexists(self.model/'junk'))

    def test_an_unpinned_overlay_is_refused(self):
        real = json.loads((HERE/'checkpoint.json').read_text())
        self.pin_path.write_text(json.dumps(real))
        if real['overlay']['revision'] == 'TODO':
            with self.assertRaisesRegex(SystemExit, 'not pinned'):
                self.build()
        self.pin(OVERLAY_TENSORS, revision='TODO')
        with self.assertRaises(SystemExit):
            self.build()
        self.assertFalse(os.path.lexists(self.model))

    def test_a_file_that_does_not_match_its_pin_is_refused(self):
        self.pin(OVERLAY_TENSORS, digest='0' * 64)
        with self.assertRaisesRegex(SystemExit, 'sha256'):
            self.build()
        self.assertFalse(os.path.lexists(self.model))

    def test_the_tensor_count_and_names_are_checked(self):
        self.pin(OVERLAY_TENSORS, count=459)
        with self.assertRaisesRegex(SystemExit, 'tensors'):
            self.build()
        self.pin(OVERLAY_TENSORS[:3] + ['model.llm.layers.0.attn.wq_du.weight'])
        with self.assertRaisesRegex(SystemExit, 'outside'):
            self.build()
        self.assertFalse(os.path.lexists(self.model))

    def test_a_missing_checkpoint_shard_is_refused(self):
        (self.ck/'model-00001-of-00001.safetensors').unlink()
        with self.assertRaisesRegex(SystemExit, 'missing'):
            self.build()

    def test_the_directory_must_sit_next_to_its_sources(self):
        self.model = self.root/'elsewhere'/'model'
        with self.assertRaises(SystemExit):
            self.build()


class CheckFiles(unittest.TestCase):
    def test_matches_the_pin(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'a.bin').write_bytes(b'weights')
            digest = check_files.sha256(Path(d)/'a.bin')
            pin = Path(d)/'pin.json'
            pin.write_text(json.dumps({'files': {'a.bin': digest}, 'k': {'files': {'a.bin': digest, 'b.bin': digest}}}))
            self.assertEqual(check_files.check(pin, d), [])
            self.assertEqual(check_files.check(pin, d, 'k'), ['b.bin'])
            (Path(d)/'a.bin').write_bytes(b'weightz')
            self.assertEqual(check_files.check(pin, d), ['a.bin'])


if __name__ == '__main__':
    unittest.main()
