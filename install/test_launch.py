# SPDX-License-Identifier: AGPL-3.0-only
"""CPU checks for the single-Spark launch contract (install/serve.py and the
docker run that start.sh makes)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location('atlas_serve', HERE/'serve.py')
serve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serve)
CHECKPOINT = '/models/thinkingmachines--Inkling-2-Mini'


def profile():
    return json.loads((HERE/'profiles'/'default.json').read_text())


def flag(argv, name):
    hits = [a.split('=', 1)[1] for a in argv if a.startswith(name + '=')]
    return hits[0] if len(hits) == 1 else None


DRAFTER = CHECKPOINT + '+dspark'


def launch(**env):
    return serve.launch({'MODEL_PATH': CHECKPOINT, 'DRAFTER_PATH': DRAFTER, **env}, profile())


class Launch(unittest.TestCase):
    def test_one_engine_on_the_inkling_kernel_target(self):
        argv, env = launch()
        self.assertEqual(argv[:2], ['/usr/local/bin/spark', 'serve'])
        self.assertEqual(flag(argv, '--kernel-target'), 'inkling-2-mini')
        self.assertEqual(flag(argv, '--model-from-path'), CHECKPOINT)
        for multi in serve.MULTI_RANK_FLAGS:
            self.assertIsNone(flag(argv, multi), multi)
        self.assertFalse(any(k.startswith('NCCL_') for k in env))

    def test_the_development_serving_flags(self):
        argv, _ = launch()
        self.assertEqual(flag(argv, '--kv-cache-dtype'), 'bf16')
        self.assertEqual(flag(argv, '--max-prefill-tokens'), '2048')
        self.assertEqual(flag(argv, '--gpu-memory-utilization'), '0.80')
        self.assertEqual(flag(argv, '--max-num-seqs'), flag(argv, '--max-batch-size'))
        self.assertIn('--no-tui', argv)

    def test_serves_loopback_8895_under_its_own_name_with_the_guard(self):
        argv, _ = launch()
        self.assertEqual(flag(argv, '--bind'), '127.0.0.1')
        self.assertEqual(flag(argv, '--port'), '8895')  # SparkQwen and SparkGLM use 8893 (and 8894)
        self.assertEqual(flag(argv, '--model-name'), 'inkling-2-mini-atlas')
        self.assertIn('--tool-guard=on', argv)
        argv, _ = launch(SPARKINKLING_TOOL_GUARD='off', SPARKINKLING_TOOL_GUARD_DENY_HOSTS='a.example,b.example')
        self.assertIn('--tool-guard=off', argv)
        self.assertIn('--tool-guard-deny-host=b.example', argv)
        for bad in ({'SPARKINKLING_TOOL_GUARD': 'maybe'}, {'SPARKINKLING_TOOL_GUARD_ALLOW_HOSTS': 'https://x'},
                    {'SPARKINKLING_TOOL_GUARD_MAX_BYTES': '0'}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                launch(**bad)

    def test_modes(self):
        self.assertEqual(launch()[1]['SPARKINKLING_MODE'], 'strict')  # the default
        self.assertEqual(launch(SPARKINKLING_MODE='spark')[1]['SPARKINKLING_MODE'], 'spark')
        with self.assertRaises(ValueError):
            launch(SPARKINKLING_MODE='fast')

    def test_dspark_by_default_speculating_alone(self):
        argv, env = launch()
        self.assertEqual(env['SPARKINKLING_DRAFTER'], 'dspark')
        self.assertIn('--dflash', argv)
        self.assertEqual(flag(argv, '--draft-model'), DRAFTER)
        self.assertEqual(flag(argv, '--dflash-gamma'), '8')
        self.assertEqual(flag(argv, '--num-drafts'), '7')
        self.assertEqual(env['ATLAS_DFLASH_BATCH_DEPTH'], '1:7,1000000:0')
        with self.assertRaises(ValueError):
            launch(DRAFTER_PATH='relative/dir')

    def test_no_drafter(self):
        argv, env = launch(SPARKINKLING_DRAFTER='none')
        self.assertEqual(env['SPARKINKLING_DRAFTER'], 'none')
        for spec_flag in serve.SPECULATION_FLAGS:
            self.assertIsNone(flag(argv, spec_flag), spec_flag)
        self.assertNotIn('ATLAS_DFLASH_BATCH_DEPTH', env)
        with self.assertRaises(ValueError):
            launch(SPARKINKLING_DRAFTER='eagle')

    def test_a_profile_cannot_speculate_go_multi_rank_or_change_target(self):
        for extra in (['--dflash'], ['--draft-model=/m/mtp.safetensors'], ['--world-size=2'], ['--tp-size=2'],
                      ['--kernel-target=laguna-s-2.1'], ['--kv-cache-dtype=fp8']):
            bad = profile()
            bad['server_argv'] += extra
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                serve.launch({'MODEL_PATH': CHECKPOINT}, bad)

    def test_memory_share_override(self):
        argv, _ = launch(SPARKINKLING_GPU_MEMORY_UTILIZATION='0.55')
        self.assertEqual(flag(argv, '--gpu-memory-utilization'), '0.55')
        argv, _ = launch(SPARKINKLING_GPU_MEMORY_UTILIZATION='0.90')
        self.assertEqual(flag(argv, '--gpu-memory-utilization'), '0.90')
        for bad in ('0.49', '0.91', '0.95', '1', '0.8'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                launch(SPARKINKLING_GPU_MEMORY_UTILIZATION=bad)

    def test_ambient_engine_switches_cannot_change_the_profile(self):
        _, env = launch(ATLAS_INKLING2_DUMP='/tmp/x', ATLAS_LOG_LEVEL='debug')
        self.assertNotIn('ATLAS_INKLING2_DUMP', env)
        self.assertEqual(env['ATLAS_LOG_LEVEL'], 'debug')

    def test_model_path_and_name_are_checked(self):
        for bad in ({'MODEL_PATH': ''}, {'MODEL_PATH': 'models/x'}, {'MODEL_PATH': '/m\n--x'},
                    {'SERVED_MODEL_NAME': '-x'}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                launch(**bad)


class ModelDir(unittest.TestCase):
    def make(self, files):
        d = Path(tempfile.mkdtemp())
        (d/'config.json').write_text('{}')
        (d/'model.safetensors.index.json').write_text(json.dumps({'weight_map': {
            f'w{i}': name for i, name in enumerate(files)}}))
        for name in files:
            (d/name).write_bytes(b'')
        return d

    def test_strict_is_the_checkpoint_as_shipped(self):
        serve.check_model_dir(self.make(['model-00001-of-00001.safetensors']), 'strict')
        with self.assertRaises(ValueError):
            serve.check_model_dir(self.make(['model-00001-of-00001.safetensors', serve.OVERLAY_FILE]), 'strict')

    def test_spark_needs_the_overlay_mapped_and_present(self):
        serve.check_model_dir(self.make(['model-00001-of-00001.safetensors', serve.OVERLAY_FILE]), 'spark')
        with self.assertRaises(ValueError):
            serve.check_model_dir(self.make(['model-00001-of-00001.safetensors']), 'spark')
        d = self.make(['model-00001-of-00001.safetensors', serve.OVERLAY_FILE])
        (d/serve.OVERLAY_FILE).unlink()
        with self.assertRaises(ValueError):
            serve.check_model_dir(d, 'spark')

    def test_an_incomplete_checkpoint_is_refused(self):
        d = self.make(['m.safetensors'])
        (d/'config.json').unlink()
        with self.assertRaises(ValueError):
            serve.check_model_dir(d, 'strict')


class StartScript(unittest.TestCase):
    """./start.sh up with docker, curl and python's smoke input stubbed."""

    def run_up(self, **extra):
        root = Path(tempfile.mkdtemp())
        shutil.copy(ROOT/'start.sh', root/'start.sh')
        shutil.copytree(HERE, root/'install', ignore=shutil.ignore_patterns('__pycache__'))
        bindir = root/'bin'
        bindir.mkdir()
        (bindir/'docker').write_text('#!/bin/sh\necho "docker $*" >> "' + str(root/'calls') + '"\n'
                                     'case "$1" in inspect) echo running;; esac\n')
        (bindir/'curl').write_text('#!/bin/sh\necho \'{"choices":[{"message":{"content":"391"},"finish_reason":"stop"}]}\'\n')
        for name in ('docker', 'curl'):
            (bindir/name).chmod(0o755)
        pin = json.loads((HERE/'checkpoint.json').read_text())
        models = root/'models'
        checkpoint = models/'thinkingmachines--Inkling-2-Mini'
        checkpoint.mkdir(parents=True)
        (checkpoint/'.sparkinkling-revision').write_text(pin['revision'] + '\n')
        env = dict(os.environ, PATH=f'{bindir}:{os.environ["PATH"]}', HOME=str(root/'home'),
                   MODEL_ROOT=str(models), IMAGE='test-image', **extra)
        result = subprocess.run(['bash', str(root/'start.sh')], env=env, capture_output=True, text=True)
        return result, (root/'calls').read_text() if (root/'calls').exists() else '', checkpoint.resolve()

    def test_strict_serves_the_checkpoint_read_only_with_a_memory_cap(self):
        result, calls, checkpoint = self.run_up(DRAFTER='none')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('smoke: 17*23 = 391', result.stdout)
        run = next(line for line in calls.splitlines() if line.startswith('docker run '))
        self.assertIn(f'--mount type=bind,src={checkpoint},dst={checkpoint},readonly', run)
        self.assertIn(f'-e MODEL_PATH={checkpoint} ', run)
        for part in ('--name atlas-sparkinkling', '--memory 114g', '-e SPARKINKLING_MODE=strict',
                     '-e SPARKINKLING_DRAFTER=none', '-e SERVED_MODEL_NAME=inkling-2-mini-atlas',
                     '-e SPARKINKLING_TOOL_GUARD=on', '-e HF_HUB_OFFLINE=1', 'test-image'):
            self.assertIn(part, run)
        self.assertNotIn('spark-nvfp4', run)
        self.assertNotIn('SPARKINKLING_GPU_MEMORY_UTILIZATION', run)

    def test_the_utilization_override_reaches_the_container(self):
        result, calls, _ = self.run_up(GPU_MEMORY_UTILIZATION='0.60', DRAFTER='none')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('-e SPARKINKLING_GPU_MEMORY_UTILIZATION=0.60', calls)

    def test_start_mounts_the_assembled_drafter(self):
        start = (ROOT/'start.sh').read_text()
        self.assertIn('DRAFTER=${DRAFTER:-dspark}', start)
        self.assertIn('drafter=$checkpoint+dspark', start)
        self.assertIn('python3 install/dspark_drafter.py install/checkpoint.json "$checkpoint" "$drafter"', start)
        self.assertIn('--mount "type=bind,src=$drafter,dst=$drafter,readonly"', start)
        self.assertIn('-e DRAFTER_PATH="$drafter"', start)

    def test_start_serves_the_assembled_overlay_in_spark_mode(self):
        start = (ROOT/'start.sh').read_text()
        self.assertIn('spark_model=$checkpoint+spark-nvfp4', start)
        self.assertIn('python3 install/spark_overlay.py install/checkpoint.json "$checkpoint" "$weights" "$spark_model"', start)
        self.assertIn('python3 install/check_files.py install/checkpoint.json "$weights" overlay', start)
        for path in ('$weights', '$spark_model'):
            self.assertIn(f'--mount "type=bind,src={path},dst={path},readonly"', start)


class Smoke(unittest.TestCase):
    def smoke(self, content, finish='stop'):
        body = json.dumps({'choices': [{'message': {'content': content}, 'finish_reason': finish}]})
        return subprocess.run(['python3', str(HERE/'smoke.py')], input=body, capture_output=True, text=True).returncode

    def test_the_answer_must_be_391_with_a_normal_stop(self):
        for good in ('391', ' 391\n', '**391**', '17*23 = 391.', 'The answer is 391.'):
            with self.subTest(good=good):
                self.assertEqual(self.smoke(good), 0)
        for bad in ('3910', '1391', '391.5', '3,391', '', 'x' * 300 + ' 391'):
            with self.subTest(bad=bad):
                self.assertNotEqual(self.smoke(bad), 0)
        self.assertNotEqual(self.smoke('391', 'length'), 0)


if __name__ == '__main__':
    unittest.main()
