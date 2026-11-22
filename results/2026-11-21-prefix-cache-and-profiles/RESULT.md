<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Prefix cache on disk, and the max and saver profiles (2026-11-21)

Development checks behind the 0.4.0 prefix-cache and profile claims. One DGX
Spark with nothing else serving, Strict weights
(`thinkingmachines/Inkling-2-Mini` @ `ed40e7da625f`), a development build of
Atlas `Enntity/atlas` `inkling2/mini-20261121` at `786d2664d` (later
commits where a table names them) served through
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

## The tail-checkpoint split

The prefix cache splits a prompt's last 17-32 rows into a second pass so the
next turn has a checkpoint below its match. RigMark short prose (Strict, no
drafter, `--runs 1 --concurrency 4,8 --concurrency-runs 2`), aggregate tok/s,
`raw/pcab-*.json`:

| | C4 | C8 |
|---|---:|---:|
| Prefix cache off (two runs) | 79.0, 79.8 | 117.2, 116.9 |
| On, split on every prompt (engine `9c910e27d`) | 77.2, 77.4 | 113.3, 112.2 |
| On, `ATLAS_NO_TAIL_SPLIT=1` | 78.6, 80.0 | 120.0, 118.3 |
| On, no split below 512 tokens (engine `680714d2b`) | 80.0 | 118.4 |

The snapshot saves cost nothing measurable; the split's extra pass (about
0.1 s: 32 rows still read nearly every expert) costs 2-4% on short prompts.
A two-turn chat through the template (`raw/pc_chat.py`,
`raw/chat-and-split.out`) shows what the split buys:

| Turn 1 / turn 2 TTFT | ~400 tokens | ~1.8K tokens | ~7K tokens |
|---|---|---|---|
| Split on every prompt | 0.50 / 0.26 s | 0.72 / 0.29 s | 2.18 / 0.30 s |
| No split | 0.39 / 0.28 s | 0.62 / 0.62 s | 2.08 / 0.99 s |
| No split below 512 tokens | 0.42 / 0.28 s | 0.72 / 0.28 s | 2.18 / 0.29 s |

Without the split a chat's second turn recomputes its whole prompt below the
first 4,096-token checkpoint. With the 512-token rule a replayed 7.5K-token
prompt still answers identically at 0.11 s warm against 2.12 s cold
(`raw/pc_check.py`).

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
- `raw/pcab-*.json`, `raw/pc_chat.py`, `raw/chat-and-split.out`, `raw/pc_check.py`,
  `raw/pc_turns.py`: the tail-split A/B and the in-memory prefix checks.
- `SHA256SUMS` covers every file.
