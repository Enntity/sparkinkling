# SPDX-License-Identifier: AGPL-3.0-only
"""Version queries work before configuration; recovery commands ignore stale
launch options; bad launch options fail before anything changes."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def checkout(root):
    shutil.copy(HERE.parent/'start.sh', root/'start.sh')
    shutil.copytree(HERE, root/'install', ignore=shutil.ignore_patterns('__pycache__'))


def stubs(root, script):
    bindir = root/'bin'
    bindir.mkdir()
    for name in ('docker', 'curl', 'hf'):
        (bindir/name).write_text('#!/bin/sh\n' + script.replace('NAME', name) + '\n')
        (bindir/name).chmod(0o755)
    return bindir


class VersionQueries(unittest.TestCase):
    def test_checkout_and_image_entrypoint_report_pin_without_configuration(self):
        release = json.loads((HERE/'release.json').read_text())
        pin = json.loads((HERE/'atlas-source.json').read_text())
        self.assertEqual(release['product'], 'SparkInkling')
        self.assertRegex(release['version'], r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'install').mkdir()
            shutil.copy(HERE.parent/'start.sh', root/'start.sh')
            for name in ('serve.py', 'release.json', 'atlas-source.json'):
                shutil.copy(HERE/name, root/'install'/name)
            # The version path must not even source a user's environment file.
            (root/'.env').write_text('exit 97\n')
            env = {'PATH': os.environ['PATH']}
            got = subprocess.check_output(['bash', str(root/'start.sh'), '--version'], env=env, text=True)
            (root/'install'/'atlas-source.json').rename(root/'install'/'source-manifest.json')
            image = subprocess.check_output(['python3', str(root/'install'/'serve.py'), '--version'], env=env, text=True)
            self.assertEqual(got, image)
            self.assertEqual(image, f"SparkInkling {release['version']}\nAtlas {pin['commit']}\nEngine tree {pin['tree']}\n")

    def test_recovery_commands_ignore_stale_launch_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkout(root)
            bindir = stubs(root, f'echo "NAME $*" >> "{root/"calls"}"')
            env = dict(os.environ, PATH=f'{bindir}:{os.environ["PATH"]}', MODEL_ROOT=str(root/'models'),
                       IMAGE='test-image', MODE='old-mode', DRAFTER='eagle', GPU_MEMORY_UTILIZATION='0.99')
            for command in ('stop', 'status'):
                with self.subTest(command=command):
                    (root/'calls').unlink(missing_ok=True)
                    result = subprocess.run(['bash', str(root/'start.sh'), command], env=env,
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('docker ', (root/'calls').read_text())
                    if command == 'status':
                        version = json.loads((HERE/'release.json').read_text())['version']
                        self.assertIn('checkout: SparkInkling ' + version, result.stdout)

    def test_bad_launch_options_fail_before_side_effects(self):
        pin = json.loads((HERE/'checkpoint.json').read_text())
        cases = [({'GPU_MEMORY_UTILIZATION': '0.95'}, 'GPU_MEMORY_UTILIZATION'),
                 ({'MODE': 'fast'}, 'strict or spark'),
                 ({'DRAFTER': 'eagle'}, 'DRAFTER'),
                 ({'DRAFTER': 'eagle'}, 'DRAFTER must be dflash2, dspark or none'),
                 ({'PROFILE': 'nonesuch'}, 'PROFILE'),
                 ({'TOOL_GUARD': 'maybe'}, 'TOOL_GUARD')]
        if pin['overlay']['revision'] == 'TODO':
            cases.append(({'MODE': 'spark'}, 'not published'))
        for extra, message in cases:
            for command in ('up', 'download'):
                with self.subTest(extra=extra, command=command), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    checkout(root)
                    bindir = stubs(root, f'touch "{root/"side-effect"}"; exit 1')
                    env = dict(os.environ, PATH=f'{bindir}:{os.environ["PATH"]}', MODEL_ROOT=str(root/'models'), **extra)
                    result = subprocess.run(['bash', str(root/'start.sh'), command], env=env,
                                            capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0, result.stderr)
                    self.assertIn(message, result.stderr)
                    self.assertFalse((root/'models').exists())
                    self.assertFalse((root/'side-effect').exists())

    def test_mode_flag_is_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkout(root)
            result = subprocess.run(['bash', str(root/'start.sh'), '--mode'], capture_output=True, text=True,
                                    env=dict(os.environ, MODEL_ROOT=str(root/'models')))
            self.assertEqual(result.returncode, 2)
            self.assertIn('--mode requires', result.stderr)


if __name__ == '__main__':
    unittest.main()
