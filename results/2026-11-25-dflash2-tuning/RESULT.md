<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# DFlash2 drafting settings for 0.5.0 (2026-11-25)

Which drafter settings SparkInkling 0.5.0 ships, and the runs that chose
them. These are tuning runs, not the release measurement: one Spark beside
other services, single runs per arm, one suite. The release's own
measurement is in [`../2026-11-25-release-0.5.0`](../2026-11-25-release-0.5.0/RESULT.md).

## Setup

- **Engine**: a development build of the pinned engine's serving code
  (`inkling2/rc-0.5.0-20261124`: window-bounded KV plus incoai's DFlash2
  drafter over `d3318e087`; its serving code is identical to `1559aa4bc`,
  which adds two build-time attestation fixes), run with `raw/serve.sh`.
- **Drafter**: `incoai/Inkling-2-Mini-DFlash2` at `4f9088ea66c2`, `--dflash
  --dflash-gamma=8 --num-drafts=7`.
- **Server**: BF16 KV, `--max-seq-len=32768`, 4,096-token prefill chunks,
  prefix caching with 64 snapshots, utilization 0.50, 8 sequences, reasoning
  low by default. Two voice engines stayed resident on the same GB10.
- **Base settings** (the 0.5.0 candidate, tuned with DSpark in 0.4.2):
  `ATLAS_DFLASH_ADAPTIVE=1`, `ATLAS_DFLASH_CONF_WIDTH=1`,
  `ATLAS_MTP_GATE_FORCE=1`. Strict `ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,1000000:0`;
  Spark `1:7,1000000:0` with `ATLAS_DFLASH_ADAPTIVE_MIN=2.5`. Each arm
  changes one setting from that base, except the final rows.
- **Suite** (`raw/tune_suite.json`, `raw/tune_suite.py`): 20 prompts, 8
  HumanEval-style code completions, 4 GSM8K, 4 MMLU-Pro and 4 prose writing
  tasks; temperature 0, reasoning low, `max_tokens` 512. All 20 run at the
  stated concurrency (C1 one at a time, C2 two at once, and so on), and the
  figure is aggregate completion tokens over wall time. A kind's figure is
  its tokens over its requests' summed time, times the concurrency.
- **Repeatability**: the Strict base read 55.8 and 55.7 tok/s at C1, the
  Spark base 72.8, 72.8 and 72.7 (arms identical at C1). At C4-C8 two runs of
  one setting differed by up to 4%.

Greedy text at C1 was byte-identical across every arm in a mode (the drafts
change speed, not the text). At two or more requests, batches of different
composition parted at a few near ties, as plain batched decode does; the
release checks greedy text against plain decode on the image.

## What did not pay

At C1 and C2 in Strict, aggregate tok/s against base 55.8 / 66.8:

| Setting (as SparkGLM ships it) | C1 | C2 |
|---|---:|---:|
| Tensor-core NVFP4 drafter twins (`ATLAS_W4A16_TC=1`, `ATLAS_DFLASH_NVFP4_TC=1`) | 55.9 | 67.0 |
| NVFP4 drafter vocabulary head (`ATLAS_DFLASH_NVFP4_HEAD=1`) | 55.8 | 67.0 |
| NVFP4 context projection (`ATLAS_DFLASH_CTX_NVFP4=1`) | 55.9 | 66.0 |
| NVFP4 conv projections (`ATLAS_DFLASH_CONV_TWIN=nvfp4`) | 55.9 | 67.0 |
| Stream-ordered uploads (`ATLAS_DFLASH_CTX_ASYNC_POS=1`, `ATLAS_DFLASH_ASYNC_UPLOADS=1`) | 55.9 | 67.1 |
| Copy drafts (`ATLAS_DFLASH_COPY_DRAFTS=1`, reply match 16, miss max 3) | 54.5 | 66.3 |
| No first append (`ATLAS_DFLASH_FIRST_APPEND=none`) | 56.2 | 66.8 |
| Masked verify (`ATLAS_DFLASH_MASKED_VERIFY=1`) | 55.7 | 66.3 |
| Adaptive width (`ATLAS_DFLASH_ADAPTIVE_WIDTH=1`) | 55.9 | 67.0 |
| Confidence probe 256 (`ATLAS_DFLASH_CONF_PROBE=256`) | 56.0 | 66.9 |

Inkling's drafter is small (five layers at 2,304 wide); the engine already
serves its projections from NVFP4 twins on the batch-8 GEMV, and a propose
costs about 14 ms against a verify's 57 ms, so the precision and upload
levers have little to take. None ships.

## Threshold: what a block must accept to keep drafting

C1 aggregate tok/s (`ATLAS_DFLASH_ADAPTIVE_MIN`):

| Mode | 2.5 | 2.0 | 1.5 | 1.0 | 0.5 | adaptive off |
|---|---:|---:|---:|---:|---:|---:|
| Strict | 54.8 | 55.8, 55.7 | 57.2, 57.3 | 57.9 | 58.0 | 58.1 |
| Spark | 72.8, 72.8 | 73.3, 73.4 | 73.1 | | | |

Strict ships 1.0: as fast as never turning drafts off, and a sequence whose
drafts are nearly all rejected still decodes plainly. Spark ships the
engine's default, 2.0 (the 2.5 override goes).

## Drafts by live requests

Aggregate tok/s by concurrency. A depth `n:d` drafts `d` tokens per request
while at most `n` requests are live; `1000000:0` decodes plainly beyond the
last entry.

**Spark**

| Depth | C2 | C3 | C4 |
|---|---:|---:|---:|
| `1:7,1000000:0` (base) | 72.0 | 83.0, 83.2 (plain) | 92.4, 92.6 (plain) |
| `…,2:2,…` | 76.0 | | |
| **`…,2:3,…`** | **79.5** | | |
| `…,2:7,…` | 72.0 | | |
| `…,2:3,3:1,…` | | 73.1 | 89.5 |
| `…,2:3,3:2,…` | | 80.6 | 89.4 |
| `…,2:3,4:2,…` | | | 87.4 |
| `…,2:3,4:3,…` | | | 91.1 |

**Strict**

| Depth | C2 | C3 | C4 | C5 | C6 | C8 |
|---|---:|---:|---:|---:|---:|---:|
| `1:7,2:2,1000000:0` (base) | 66.8 | 65.4 | 75.3 | | | |
| `…,2:3,…` | 70.9 | | | | | |
| `…,2:7,…` | 60.3 | | | | | |
| `…,2:2,3:2,…` | | 72.7 | 74.0 | | | |
| `…,2:3,3:2,…` | 70.7 | 71.2 | 73.7 | | | |
| `…,2:3,3:3,…` | | 75.1 | 73.4 | | | |
| `…,2:3,3:4,4:4,…` ¹ | | 76.2 | 82.4 | | | |
| `…,2:3,3:3,4:1,…` | | | 74.1 | | | |
| `…,2:3,3:3,4:2,…` | | | 79.8 | | 87.9 (plain) | |
| `…,2:3,3:3,4:3,…` | | | 83.9 | | | |
| `…,4:2,6:2,…` | | | 79.0 | | 88.9 | |
| `…,4:3,5:3,…` ¹ | | | 83.9 | 88.1 | 84.3 (plain) | 97.1 (plain) |
| `…,4:3,5:3,6:3,…` ¹ | | | | | 91.9 | |
| `…,5:3,6:3,8:2,…` ¹ | | | | | | 95.6 |

¹ with Strict's threshold at 1.0.

Drafting at three or more requests trades prose for code and math: at C4
Strict's `4:3` read 97.1 tok/s on code and 79.9 on prose against plain
decode's 78.0 and 85.8. The aggregate gain is what ships; the release
measurement reports prose at four and eight requests on its own.

## What ships

Strict `ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,3:3,4:3,5:3,6:3,1000000:0`,
`ATLAS_DFLASH_ADAPTIVE_MIN=1.0`; Spark `1:7,2:3,1000000:0` at the engine's
threshold. Combined, against the base:

| Mode | C1 | C2 | C3 | C4 | C5 | C6 | C8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Strict, base | 55.8 | 66.8 | 65.4 | 75.3 | 80.9 ² | 87.9, 84.3 ² | 98.7 ² |
| Strict, shipped | 58.0 (+4%) | 71.1 (+6%) | 75.3 (+15%) | 84.3 (+12%) | 88.6 (+10%) | 91.9 (+5-9%) | 98.7 (plain) |
| Spark, base | 72.8 | 72.0 | 83.0 | 92.4 | | | |
| Spark, shipped | 73.6 (+1%) | 79.8 (+11%) | 82.6 (plain) | 92.5 (plain) | | | 111.2 (plain) |

² plain decode, which is what the base does from three requests (measured
with settings that draft only below five or six requests). C5, C6 and C8
shipped come from the runs in the depth table with the shipped depth at
that concurrency.

## Files

`raw/`: the scripts (`tune.sh` serves one arm and runs the suite,
`tune_*.sh` the batches in order), the suite, each arm's per-request
results (`<mode>-<arm>-c<n>.json`: kind, tokens, seconds, a hash of the
text), the batch logs, and a startup summary of each arm's server log (the
full logs, with a line per step, stay on the Spark). `SHA256SUMS` covers
`raw/`.
