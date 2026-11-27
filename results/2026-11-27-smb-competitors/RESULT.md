<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# vLLM and knapcio on SparkModelBench, beside SparkInkling 0.5.1 (2026-11-27)

Two other ways to serve Inkling 2 Mini on one DGX Spark, measured with the
same [SparkModelBench](https://github.com/enntity/sparkmodelbench) commit
(`293a44f`: RigMark protocol 1.3.0, RigMark Quality v0.0.2,
`reasoning_effort: low`, comparison ID `sparkinkling-0.5.1`) on the same Spark
that measured SparkInkling 0.5.1
([its result](../2026-11-27-rc-0.5.1/RESULT.md)):

- **vLLM + DSpark**: vLLM's own Inkling 2 Mini image
  (`vllm/vllm-openai:inkling-2-mini@sha256:c2dc759f5984`, the image this
  repository's earlier vLLM columns used) with the checkpoint's bundled DSpark
  drafter, 7 draft tokens, probabilistic draft sampling,
  `--gpu-memory-utilization 0.80` (SparkInkling's default profile uses 0.80),
  `--reasoning-parser inkling --enable-auto-tool-choice --tool-call-parser inkling`.
  It is vLLM's faster configuration in our earlier runs; vLLM without a
  drafter was not run.
- **knapcio v2.9.7**: [knapcio/Inkling-2-Mini-1x-DGX-Spark](https://github.com/knapcio/Inkling-2-Mini-1x-DGX-Spark)
  at tag `v2.9.7` (`09febfe`), SGLang
  (`lmsysorg/sglang@sha256:efac853b4681`) with its overlays and incoai's
  DFlash2 drafter, started by its `scripts/launch.sh up` with its defaults.

Both served the checkpoint as shipped (`thinkingmachines/Inkling-2-Mini` @
`ed40e7da625f`), the same weights as SparkInkling's Strict mode. Both ran with
a 270,336-token context (`--max-model-len`, `CTX`) so that SparkModelBench's
256K prefill depth fits: it skips a depth whose prompt plus 8 output tokens
exceeds the context, and both recipes default to 262,144.

## Results

Medians of SparkModelBench's repetitions; every repetition is in `raw/smb-*`.
The SparkInkling columns are from the 0.5.1 run.

| | Spark | Strict | vLLM + DSpark | knapcio v2.9.7 |
|---|---:|---:|---:|---:|
| Code decode, tok/s | 88.2 | 68.7 | 70.8 | **97.8** |
| Prose decode | 57.0 | 40.2 | 31.1 | **59.7** |
| Structured decode | 129.9 | 102.3 | 104.3 | **147.7** |
| Decode gates | 15/15 | 15/15 | 15/15 | 15/15 |
| Cold prefill 8K, tok/s | 5,174 | 5,137 | 2,862 | **5,818** |
| 32K | 5,024 | 4,918 | 2,735 | **5,399** |
| 64K | 4,540 | 4,481 | 2,480 | **4,812** |
| 128K | 3,781 | 3,779 | 2,083 | **3,973** |
| 256K | **2,824** | **2,827** | 1,586 | 2,815 |
| Same prompt sent again, 32K / 256K, time to first token | **0.15 / 0.36 s** | 0.16 / 0.37 s | 0.16 / 0.41 s | 1.69 / 4.62 s |
| Code, aggregate at 1 / 2 / 4 / 8 requests | 63.2 / 81.9 / 104.7 / 144.1 | 48.1 / 65.6 / 85.6 / 126.4 | 43.6 / 69.2 / 106.6 / 156.4 | **68.9 / 99.2 / 152.0 / 243.4** |
| RigMark Quality, tasks passed | 3/4 | 3/4 | **4/4** | 3/4 |
| Longest request as run, tokens | 1,048,576 | 1,048,576 | 270,336 | 270,336 |
| KV pool, tokens (GPU memory fraction) | 1,790,944 (0.80) | 1,909,536 (0.80) | 1,238,747 (0.80) | 1,591,168 (0.85) |

- **knapcio leads SparkInkling** on every decode workload and at every
  concurrency. Spark reaches 0.90x its code, 0.96x its prose and 0.88x its
  structured decode, 0.93x its 32K prefill and level at 256K, and 0.92x,
  0.83x, 0.69x and 0.59x its aggregate at one, two, four and eight requests.
  SparkInkling's sent-again prompts start more than 10x sooner, and its requests run to
  1,048,576 tokens.
- **Spark leads vLLM + DSpark** on decode (1.25x code, 1.83x prose, 1.25x
  structured), on prefill at every depth (1.84x at 32K, 1.78x at 256K) and at
  one and two requests (1.45x, 1.18x). It trails it at four requests (0.98x),
  eight (0.92x) and on RigMark Quality.
- **RigMark Quality** ran once per engine. vLLM passed `go-transfer-ledger`'s
  acceptance check; Spark, Strict and knapcio finished the task with its
  public tests passing and missed the acceptance check. One run each does not
  separate the engines' quality.
- Output lengths agree: the median code answer was 3,276 tokens (Spark),
  3,503 (Strict), 3,477 (vLLM) and 3,275 (knapcio), so `reasoning_effort: low`
  reached every engine.
- **The staggered C4 lane is not a result for any of them.** It asks for
  thinking off; Inkling 2 Mini has none, and the model reasons anyway
  without the reasoning being streamed, so no engine completed a round with
  all four streams (`raw/smb-*-full/c4-*.json`;
  [why](../2026-11-27-rc-0.5.1/RESULT.md#the-staggered-c4-lane-does-not-apply-to-inkling)).
- Cold prefill cache evidence reads "unverified" for both engines: neither
  reports cached prompt tokens the way SparkModelBench checks.

## Conditions, and what differs from the SparkInkling run

- **Not the same window.** SparkInkling was measured 01:44-02:27Z, these two
  08:26-09:25Z (`raw/window.out`), on the same Spark with the voice services
  suspended through LLooM both times.
- **An idle 20 GB process was resident here.** LLooM's suspend of the Drama 3
  voice engine at 08:26Z left that engine's server process running (a LLooM
  fault: its launcher exited without stopping the server's unit). It served no
  requests and showed 0% SM in `nvidia-smi pmon` during the vLLM run; it held
  20 GB of memory. Neither engine was refused memory: vLLM ran at 0.80 and
  knapcio at 0.85.
- **Metadata corrections.** The metadata vLLM's first run recorded says
  `competing_traffic: none`; the files were then edited to name the idle
  process, which vLLM's concurrency run and both knapcio runs recorded. The
  knapcio metadata also says `MEM_FRACTION 0.80`: to leave room for the idle
  process I edited `scripts/launch.sh` (`raw/knapcio-launch.diff`), but a later
  rule in the same script sets 0.85 for contexts above 262,144 and that is what
  ran (`raw/smb-knapcio.up.log`: `--mem-fraction-static 0.85`). So knapcio ran
  with its own setting for this context; the edit had no effect.
- **Preflight.** Before the window each engine was started at reduced memory
  beside the voice services and checked for reasoning effort, tool calls and
  token-ID prompts (`raw/probe.py`, `raw/preflight.txt`).

## Files

`raw/smb-vllm-dspark-full/`, `raw/smb-knapcio-full/` and the `-concurrency`
directories are SparkModelBench's own result directories (`CARD.md`, RigMark's
card and JSON, prefill, C4 and RigMark Quality receipts, their own
`SHA256SUMS`); `raw/smb-*.log` the runner output; `raw/smb-*.server.log` the
servers' logs; `raw/smb-knapcio.up.log` knapcio's launcher output;
`raw/meta-*.json` the metadata as the runs ended; `raw/window.sh` the script
that ran. Logs outside SparkModelBench's directories replace the Spark's home
directory with `~`; nothing else is edited.
