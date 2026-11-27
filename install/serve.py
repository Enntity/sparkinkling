#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Translate the container contract (start.sh) into the Atlas launch of
Inkling 2 Mini on one DGX Spark. Adapted from SparkQwen's single-Spark path."""
import json
import os
from pathlib import Path
import re
import sys

KERNEL_TARGET = 'inkling-2-mini'
PORT = 8895
SERVED_MODEL_NAME = 'inkling-2-mini-atlas'
MODES = ('strict', 'spark')
OVERLAY_FILE = 'spark-nvfp4.safetensors'
# SPARKINKLING_DRAFTER: 'dflash2' (the default) runs incoai's DFlash2 drafter
# for Inkling 2 Mini (incoai/Inkling-2-Mini-DFlash2, at DRAFTER_PATH); 'none'
# decodes without speculation.
DRAFTERS = ('dflash2', 'none')
# SPARKINKLING_LOOPCD: 'off' (the default), 'on' or 'skip-thinking'. LoopCD
# (arXiv 2610.02185) runs the coda layers a second time from the first loop
# pass and moves the logits away from that reference; it breaks reasoning
# loops at high effort but costs 15-36% of decode speed and 10-12% of the KV
# pool (results/2026-11-25-loopcd). skip-thinking leaves reasoning unguided.
LOOPCD = ('off', 'on', 'skip-thinking')
# The drafter's block is 8: seven drafts a step.
DRAFT_ARGS = ('--dflash', '--dflash-gamma=8', '--num-drafts=7')
# How the drafter is run. Tuned for DFlash2 on GB10, 2026-11-25, with the 0.5.0
# engine beside the voice engines (results/2026-11-25-dflash2-tuning):
# - A verify stops where the drafter is unsure (ATLAS_DFLASH_CONF_WIDTH: the
#   engine learns, while serving, how often the target accepts a draft at each
#   confidence, and cuts the block where the chance it is still right falls
#   under 0.3).
# - Drafts go off for a sequence whose steps stop paying, for 32 tokens at
#   first and doubling while re-probes keep failing (ATLAS_DFLASH_ADAPTIVE).
#   The threshold is what a whole block must accept: 1.0 in Strict, where a
#   plain step reads the BF16 attention weights and nearly any accepted draft
#   pays (at one request +4% over 2.0, the same as never turning drafts off),
#   and the engine's 2.0 in Spark. That per-sequence rule replaces the
#   engine's throughput gate (ATLAS_MTP_GATE_FORCE), which carries its off
#   state from one request into the next.
# - Drafts by live requests (`n:drafts`, up to n requests): seven alone and
#   three each for two requests in both modes, plain decode from three. Chosen
#   on RigMark's short requests (256 tokens, reasoning low): Strict two at once
#   64.6 tok/s against 61.9 with 0.4.2's two each, drafting at four lost 11%
#   (76.3 against 86.0 plain). Spark drafts at two since its projections run on
#   the tensor cores (SPARK_ENV), which made a verify cheaper: short code at two
#   requests 81.4 tok/s against 73.9 plain; at four and eight drafting still
#   loses (99.8 against 108.7, 123.8 against 149.1;
#   results/2026-11-26-spark-tensor-cores). On a suite of longer answers
#   drafting gained up to six requests in Strict, so the setting follows what
#   the release measures.
_DRAFT_COMMON = {'ATLAS_DFLASH_ADAPTIVE': '1', 'ATLAS_DFLASH_CONF_WIDTH': '1', 'ATLAS_MTP_GATE_FORCE': '1'}
DRAFT_ENV = {
    'strict': {**_DRAFT_COMMON, 'ATLAS_DFLASH_BATCH_DEPTH': '1:7,2:3,1000000:0', 'ATLAS_DFLASH_ADAPTIVE_MIN': '1.0'},
    'spark': {**_DRAFT_COMMON, 'ATLAS_DFLASH_BATCH_DEPTH': '1:7,2:3,1000000:0'},
}
# Spark's NVFP4 projections and vocabulary head on the engine's row-invariant
# tensor-core kernels (ATLAS_SKINNY_MMA): a row's bits do not depend on how many
# rows share the launch, so decode and verify rows stay exact twins and text with
# drafts is still the text without, at about twice the scalar batch GEMV's speed
# on a verify. Strict's projections are BF16 and keep the engine's kernels.
SPARK_ENV = {'ATLAS_SKINNY_MMA': '1'}
SPECULATION_FLAGS = ('--speculative', '--dflash', '--draft-model', '--draft-model-alt', '--dflash-gamma',
                     '--num-drafts', '--self-speculative', '--ngram-speculative')
MULTI_RANK_FLAGS = ('--world-size', '--tp-size', '--ep-size', '--rank', '--master-addr', '--master-port')


def tool_guard_args(environ, profile_args):
    """Operator policy is explicit and independent of model/performance profiles."""
    if any(arg.split('=', 1)[0].startswith('--tool-guard') for arg in profile_args):
        raise ValueError('Configure the tool guard with SPARKINKLING_TOOL_GUARD variables, not profile arguments')
    mode = environ.get('SPARKINKLING_TOOL_GUARD', 'stream')
    if mode not in ('stream', 'on', 'off'):
        raise ValueError('SPARKINKLING_TOOL_GUARD must be stream, on or off')
    limit = environ.get('SPARKINKLING_TOOL_GUARD_MAX_BYTES', '1048576')
    if not re.fullmatch(r'[1-9][0-9]{0,7}', limit) or int(limit) > 67108864:
        raise ValueError('SPARKINKLING_TOOL_GUARD_MAX_BYTES must be 1 to 67108864')
    result = [f'--tool-guard={mode}', f'--tool-guard-max-bytes={limit}']
    for action in ('ALLOW', 'DENY'):
        value = environ.get(f'SPARKINKLING_TOOL_GUARD_{action}_HOSTS', '')
        for host in value.split(',') if value else []:
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*|\[[A-Fa-f0-9:.]+\]', host):
                raise ValueError(f'SPARKINKLING_TOOL_GUARD_{action}_HOSTS requires comma-separated exact hosts, without schemes, ports or wildcards')
            result.append(f'--tool-guard-{action.lower()}-host={host}')
    return result


def _flag_values(args, flag):
    return [a.split('=', 1)[1] if '=' in a else None for a in args if a.split('=', 1)[0] == flag]


def _engine_env(environ, profile):
    # Profile values win over ambient optimization flags; only the reviewed
    # logging knobs and the loop-recovery escape hatch pass through.
    env = {key: value for key, value in environ.items()
           if not key.startswith('ATLAS_') or key.startswith('ATLAS_LOG_')
           or key == 'ATLAS_LOOP_NO_SUPPRESS'}
    env.update(profile['environment'])
    return env


def _memory_share(environ, args):
    """The SPARKINKLING_GPU_MEMORY_UTILIZATION override, 0.50 to 0.90."""
    util = environ.get('SPARKINKLING_GPU_MEMORY_UTILIZATION')
    if not util:
        return args
    if not re.fullmatch(r'0\.([5-8][0-9]|90)', util):
        raise ValueError('SPARKINKLING_GPU_MEMORY_UTILIZATION must be 0.50 to 0.90')
    return [f'--gpu-memory-utilization={util}' if a.startswith('--gpu-memory-utilization=') else a for a in args]


def launch(environ, profile):
    """One engine process on one Spark: no ranks, no fabric."""
    args = list(profile['server_argv'])
    if _flag_values(args, '--kernel-target') != [KERNEL_TARGET]:
        raise ValueError(f'the profile requires --kernel-target={KERNEL_TARGET} exactly once')
    if _flag_values(args, '--kv-cache-dtype') != ['bf16']:
        raise ValueError('the profile requires --kv-cache-dtype=bf16 exactly once')
    if _flag_values(args, '--model-from-path') != ['${model}']:
        raise ValueError('the profile requires --model-from-path=${model} exactly once')
    for flag in MULTI_RANK_FLAGS:
        if _flag_values(args, flag):
            raise ValueError(f'SparkInkling runs on one Spark; {flag} is not allowed')
    for flag in SPECULATION_FLAGS:
        if _flag_values(args, flag):
            raise ValueError(f'{flag}: speculation is selected with SPARKINKLING_DRAFTER, not the profile')
    if _flag_values(args, '--loopcd'):
        raise ValueError('--loopcd: LoopCD is selected with SPARKINKLING_LOOPCD, not the profile')
    loopcd = environ.get('SPARKINKLING_LOOPCD', 'off')
    if loopcd not in LOOPCD:
        raise ValueError('SPARKINKLING_LOOPCD must be off, on or skip-thinking')
    mode = environ.get('SPARKINKLING_MODE', 'spark')
    if mode not in MODES:
        raise ValueError('SPARKINKLING_MODE must be spark or strict')
    drafter = environ.get('SPARKINKLING_DRAFTER', 'dflash2')
    if drafter not in DRAFTERS:
        raise ValueError(f'SPARKINKLING_DRAFTER must be one of {", ".join(DRAFTERS)}')
    model = environ.get('MODEL_PATH', '')
    if not Path(model).is_absolute() or any(c in model for c in '\r\n\0'):
        raise ValueError('MODEL_PATH must be an absolute path')
    env = _engine_env(environ, profile)
    env.update(SPARKINKLING_MODE=mode, SPARKINKLING_DRAFTER=drafter, SPARKINKLING_LOOPCD=loopcd)
    if mode == 'spark':
        env.update(SPARK_ENV)
    args = _memory_share(environ, [str(a).replace('${model}', model) for a in args])
    if loopcd != 'off':
        args.append(f'--loopcd={loopcd}')
    if drafter != 'none':
        draft = environ.get('DRAFTER_PATH', '')
        if not Path(draft).is_absolute() or any(c in draft for c in '\r\n\0'):
            raise ValueError('DRAFTER_PATH must be an absolute path')
        args += [*DRAFT_ARGS, f'--draft-model={draft}']
        env.update(DRAFT_ENV[mode])
    name = environ.get('SERVED_MODEL_NAME', SERVED_MODEL_NAME)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,127}', name):
        raise ValueError('Invalid SERVED_MODEL_NAME')
    args += ['--bind=127.0.0.1', f'--port={PORT}', f'--model-name={name}']
    args += tool_guard_args(environ, args)
    return ['/usr/local/bin/spark', *args], env


def check_model_dir(model, mode):
    """The model directory serves the requested mode: Strict is the checkpoint
    as shipped, Spark maps the overlay (install/spark_overlay.py). Atlas serves
    whatever the index maps, so a wrong mount must not pass for the other mode."""
    model = Path(model)
    if not (model/'config.json').is_file() or not (model/'model.safetensors.index.json').is_file():
        raise ValueError(f'Incomplete checkpoint at {model}')
    files = set(json.loads((model/'model.safetensors.index.json').read_text())['weight_map'].values())
    if mode == 'strict' and OVERLAY_FILE in files:
        raise ValueError(f'Strict mode serves the checkpoint as shipped; {model} maps {OVERLAY_FILE}')
    if mode == 'spark' and (OVERLAY_FILE not in files or not (model/OVERLAY_FILE).is_file()):
        raise ValueError(f'Spark mode needs {OVERLAY_FILE} mapped and present in {model}')


def profile_path(environ, here):
    """The launch profile named by SPARKINKLING_PROFILE (default: default)."""
    name = environ.get('SPARKINKLING_PROFILE', 'default')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', name):
        raise ValueError('Invalid SPARKINKLING_PROFILE')
    return here/'profiles'/f'{name}.json'


def release_info(here):
    release = json.loads((here/'release.json').read_text())
    source_path = here/'source-manifest.json'
    if not source_path.is_file():
        source_path = here/'atlas-source.json'
    source = json.loads(source_path.read_text())
    return {'product': release['product'], 'version': release['version'],
            'engine_commit': source['commit'], 'engine_tree': source['tree']}


def print_version(here):
    info = release_info(here)
    print(f"{info['product']} {info['version']}")
    print(f"Atlas {info['engine_commit']}")
    print(f"Engine tree {info['engine_tree']}")


def main():
    here = Path(__file__).resolve().parent
    if sys.argv[1:] == ['--version']:
        print_version(here)
        return
    profile = profile_path(os.environ, here)
    argv, env = launch(os.environ, json.loads(profile.read_text()))
    check_model_dir(env['MODEL_PATH'], env['SPARKINKLING_MODE'])
    source = json.loads((here/'source-manifest.json').read_text())
    print(json.dumps({'event': 'atlas-recipe-start', **release_info(here), 'profile': profile.stem,
                      'mode': env['SPARKINKLING_MODE'], 'drafter': env['SPARKINKLING_DRAFTER'],
                      'loopcd': env['SPARKINKLING_LOOPCD'],
                      'source': f"{source['repository']}@{source['commit']}"}), flush=True)
    os.execve(argv[0], argv, env)


if __name__ == '__main__':
    main()
