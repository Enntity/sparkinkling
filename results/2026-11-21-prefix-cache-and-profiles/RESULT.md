<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Prefix cache on disk, and the max and saver profiles (2026-11-21)

Development checks behind the 0.4.0 prefix-cache and profile claims. One DGX
Spark with nothing else serving, Strict weights
(`thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`), a development build of
Atlas `Enntity/atlas` `inkling2/mini-20261121` at `786d2664d` served through
`raw/serve.sh` (BF16 KV, CUDA graphs, `ATLAS_INKLING2_PDL=1`,
`--enable-prefix-caching`, `ATLAS_QWEN4EXP_AUX_PINNED=1`, no drafter).
Single runs: checks, not benchmarks.

## Disk tier under eviction

`raw/pc_disk.py`: conversation A (16,000 random words, about 20K tokens) is
sent, then five others like it push it out of a pool held small
(utilization 0.30, 5,373 blocks, about 86K tokens), then A is sent again.
Greedy, 48 tokens each. `raw/disk-tier.out` holds both runs and the engine's
log lines.

| | A cold, TTFT | A again, TTFT | Same answer |
|---|---:|---:|---|
| Tier off | 5.82 s | 5.82 s | yes |
| Tier on (`ATLAS_KV_NVME_DIR`, 16 GiB, `ATLAS_GLM_NVME_FAST=1`) | 5.82 s | 0.90 s | yes |

With the tier on, the engine restored A's 1,237 blocks (19,792 tokens) from
disk in 403 ms (371 ms of reads, about 10.5 GB/s) and resumed from the
conv-state snapshot at token 19,776, replaying 21 tokens. It set 388 MiB of
host memory aside for the tier, out of the KV budget.

## Profiles

`raw/profiles.out`: each profile's serving flags on the development build
(`raw/burst.py`: N concurrent short code requests, greedy, up to 1,024
tokens; `raw/needle.py`: a code hidden a third of the way into filler).

| | Utilization | KV pool | Start | Burst | Long context |
|---|---:|---:|---:|---|---|
| saver | 0.50 | 13,292 blocks, 212,672 tokens | 38 s | 8 of 8 stopped normally | |
| max (checked at 0.88) | 0.88 | 29,136 blocks, 466,176 tokens | 42 s | 32 of 32 stopped normally, 148 tok/s aggregate | 182,100-token prompt: code recalled, 81.8 s |

At 0.88 the host kept about 8 GB available under the full batch, so the
shipped `max` profile takes 0.85 (SparkQwen 27B's share), about 446K tokens.

## Files

- `raw/serve.sh`: the development server (`GPUUTIL`, `SEQS`, `MAXLEN`,
  `CHUNK`, `INKENV`, `EXTRA`).
- `raw/pc_disk.py`, `raw/disk-tier.out`: the eviction check.
- `raw/burst.py`, `raw/needle.py`, `raw/profiles.out`: the profile checks.
- `raw/pc_check.py`, `raw/pc_turns.py`: the in-memory prefix checks
  (replayed, extended and two-turn prompts).
- `SHA256SUMS` covers every file.
