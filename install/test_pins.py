# SPDX-License-Identifier: AGPL-3.0-only
"""The engine, checkpoint and overlay pins are whole, the docs name them, and
the repository holds no host names or home paths outside raw receipts."""
import json
import os
from pathlib import Path
import re
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def pin(name):
    return json.loads((HERE/name).read_text())


def text(path):
    return ' '.join((ROOT/path).read_text().split())


class Pins(unittest.TestCase):
    def test_the_engine_pin_is_whole(self):
        p = pin('atlas-source.json')
        self.assertRegex(p['commit'], r'^[0-9a-f]{40}$')
        self.assertRegex(p['tree'], r'^[0-9a-f]{40}$')
        self.assertEqual(p['repository'], 'https://github.com/Enntity/atlas.git')
        self.assertEqual(p['kernel_target'], 'inkling-2-mini')
        self.assertEqual(p['model_type'], 'inkling2_loop')
        self.assertEqual(p['license'], 'AGPL-3.0-only')
        # The one place build.sh and the Dockerfile take the target from.
        self.assertIn('m["kernel_target"]', (HERE/'build.sh').read_text())
        self.assertIn('ARG ATLAS_TARGET_MODEL=inkling-2-mini', (HERE/'Dockerfile').read_text())

    def test_the_checkpoint_pin_is_whole(self):
        p = pin('checkpoint.json')
        self.assertEqual(p['repository'], 'thinkingmachines/Inkling-2-Mini')
        self.assertRegex(p['revision'], r'^[0-9a-f]{40}$')
        self.assertEqual(p['license'], 'apache-2.0')
        self.assertEqual(p['model_type'], pin('atlas-source.json')['model_type'])
        self.assertEqual(p['served_model_name'], 'inkling-2-mini-atlas')
        self.assertEqual(set(p['files']), {'model-00001-of-00001.safetensors', 'mtp.safetensors',
                                           'tokenizer.json', 'tiktoken/tokenizer.model'})
        for name, digest in p['files'].items():
            self.assertRegex(digest, r'^[0-9a-f]{64}$', name)

    def test_the_overlay_pin_is_whole_or_todo(self):
        o = pin('checkpoint.json')['overlay']
        self.assertEqual(o['repository'], 'Enntity/Inkling-2-Mini-Spark-NVFP4')
        self.assertEqual(o['serve'], 'spark-nvfp4.safetensors')
        self.assertEqual(set(o['files']), {'spark-nvfp4.safetensors'})
        self.assertEqual(o['tensors'], 459)
        self.assertEqual(o['prefixes'], ['model.language_model.', 'lm_head.'])
        self.assertEqual(o['license'], 'apache-2.0')
        values = [o['revision'], *o['files'].values()]
        if 'TODO' in values:
            self.assertEqual(set(values), {'TODO'}, 'pin the revision and every sha256 together')
        else:
            self.assertRegex(o['revision'], r'^[0-9a-f]{40}$')
            for digest in o['files'].values():
                self.assertRegex(digest, r'^[0-9a-f]{64}$')

    def test_release_and_image_tag(self):
        self.assertEqual(pin('release.json')['version'], '0.5.1')
        tag = subprocess.run([str(HERE/'build.sh'), '--tag'], capture_output=True, text=True,
                             env={**os.environ, 'SPARKINKLING_IMAGE_REPO': 'ghcr.io/enntity/atlas-sparkinkling'})
        if tag.returncode == 0:  # needs a git checkout
            self.assertRegex(tag.stdout.strip(), r'^ghcr\.io/enntity/atlas-sparkinkling:[0-9a-f]{12}$')

    def test_the_image_ships_what_serve_reads(self):
        dockerfile = (HERE/'Dockerfile').read_text()
        self.assertIn('COPY install/serve.py install/release.json install/checkpoint.json /opt/atlas/', dockerfile)
        self.assertIn('COPY install/atlas-source.json /opt/atlas/source-manifest.json', dockerfile)
        self.assertIn('COPY install/profiles/ /opt/atlas/profiles/', dockerfile)
        self.assertIn('EXPOSE 8895', dockerfile)


class Docs(unittest.TestCase):
    def test_docs_name_the_pins(self):
        engine, ckpt = pin('atlas-source.json'), pin('checkpoint.json')
        for doc in ('docs/ENGINE.md', 'docs/INSTALL-MANUAL.md'):
            with self.subTest(doc=doc):
                self.assertIn(engine['commit'][:9], text(doc))
                self.assertIn(engine['branch'], text(doc))
        for doc in ('README.md', 'docs/INSTALL-MANUAL.md'):
            with self.subTest(doc=doc):
                self.assertIn(ckpt['revision'][:12], text(doc))
                self.assertIn(ckpt['overlay']['repository'], text(doc))

    def test_performance_claims_cite_a_result(self):
        # Every performance table points at a results directory that exists.
        for doc in ('README.md', 'docs/BENCHMARKS.md'):
            with self.subTest(doc=doc):
                cited = re.findall(r'results/(\d{4}-\d{2}-\d{2}-[\w.-]+)', text(doc))
                self.assertTrue(cited, f'{doc} cites no result')
                for name in cited:
                    self.assertTrue((ROOT/'results'/name/'RESULT.md').is_file(), name)
                    self.assertTrue((ROOT/'results'/name/'SHA256SUMS').is_file(), name)

    def test_dflash2_is_the_documented_default(self):
        pin = json.loads((ROOT/'install'/'checkpoint.json').read_text())
        self.assertNotIn('draft', pin)
        d = pin['dflash2']
        self.assertEqual(d['repository'], 'incoai/Inkling-2-Mini-DFlash2')
        self.assertRegex(d['revision'], r'^[0-9a-f]{40}$')
        self.assertEqual(set(d['files']), {'model.safetensors'})
        for digest in d['files'].values():
            self.assertRegex(digest, r'^[0-9a-f]{64}$')
        self.assertEqual(d['license'], 'apache-2.0')
        for doc in ('README.md', 'docs/MODES.md'):
            with self.subTest(doc=doc):
                for drafter in ('DRAFTER=dflash2', 'DRAFTER=none'):
                    self.assertIn(drafter, text(doc))
                self.assertNotIn('DRAFTER=dspark', text(doc))


class Privacy(unittest.TestCase):
    PRIVATE = re.compile(r'/Users/|/home/[a-z]|/Volumes/|\bjmac\b|theroot\.org|\bspark0[1-4]\b|\bencor\b|\bencon\b')

    def test_no_host_names_or_home_paths_outside_raw_receipts(self):
        files = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--cached', '--others', '--exclude-standard'],
                               capture_output=True, text=True)
        if files.returncode != 0:
            self.skipTest('needs a git checkout')
        for name in files.stdout.split():
            if re.match(r'results/[^/]+/raw/', name) or name.endswith(('.png', '.jpg')) or name in ('LICENSE', 'install/test_pins.py'):
                continue
            path = ROOT/name
            if not path.is_file():
                continue
            with self.subTest(file=name):
                self.assertIsNone(self.PRIVATE.search(path.read_text(errors='replace')), name)


if __name__ == '__main__':
    unittest.main()
