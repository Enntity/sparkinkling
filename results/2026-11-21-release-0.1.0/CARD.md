<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# RigMark cards: SparkInkling 0.1.0

Unedited, from `raw/img-*-code.card.txt`.

## Strict, code suite

```text
╭──────────────────────────────────────────────────────────────────────────────────────────╮
│  R I G M A R K   //   AGENT WORKLOAD RECEIPT                                             │
│  BENCHMARKS LOCAL AI HOW CODING AGENTS ACTUALLY USE IT                                   │
│  ●  6/6 BASIC OUTPUT GATES PASSED                                                        │
├─ SYSTEM ─────────────────────────────────────────────────────────────────────────────────┤
│  MODEL      inkling-2-mini-atlas                                                         │
│  APPLIANCE  1x NVIDIA DGX Spark (GB10, 128 GB)                                           │
│  RUN        reasoning=low  •  protocol=1.1.0                                             │
│  SOURCE     git:40fabcaf6e96  •  clean                                                   │
├─ REAL OUTPUT ────────────────────────────────────────────────────────────────────────────┤
│  WORKLOAD       DECODE EST.      LAST OUTPUT          RANGE          BASIC GATE          │
│  CODE              52.0 tok/s      63.0s last     51.1–52.9     ✓ 2/2                    │
│  PROSE             22.2 tok/s      53.5s last     22.1–22.3     ✓ 2/2                    │
│  STRUCTURED*       79.2 tok/s      13.2s last     78.9–79.6     ✓ 2/2                    │
│  * predictable-output ceiling; not a proxy for agent speed                               │
├─ CONTEXT ────────────────────────────────────────────────────────────────────────────────┤
│  32K PREFILL   cold 1,455 tok/s  •  immediate replay 1,454 tok/s                         │
├─ CAPPED CONCURRENT GENERATION ───────────────────────────────────────────────────────────┤
│  SHORT CODE • END-TO-END • 256-TOKEN CAP PER AGENT                                       │
│  AGGREGATE   C1 31.7  •  C2 44.4  •  C4 71.4  •  C8 108.7 tok/s                          │
│  C8 OUTPUT STATE   normal stop 0/16  •  visible 0/16  •  reasoning may be included       │
├─ RECEIPT ────────────────────────────────────────────────────────────────────────────────┤
│  JSON       sha256:be5a16d22927b9d1…                                                     │
│  SHARE THE CARD • LINK THE JSON RECEIPT • #RIGMARK                                       │
│  github.com/alexellis/rigmark                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```

## Spark, code suite

```text
╭──────────────────────────────────────────────────────────────────────────────────────────╮
│  R I G M A R K   //   AGENT WORKLOAD RECEIPT                                             │
│  BENCHMARKS LOCAL AI HOW CODING AGENTS ACTUALLY USE IT                                   │
│  ●  6/6 BASIC OUTPUT GATES PASSED                                                        │
├─ SYSTEM ─────────────────────────────────────────────────────────────────────────────────┤
│  MODEL      inkling-2-mini-atlas                                                         │
│  APPLIANCE  1x NVIDIA DGX Spark (GB10, 128 GB)                                           │
│  RUN        reasoning=low  •  protocol=1.1.0                                             │
│  SOURCE     git:40fabcaf6e96  •  clean                                                   │
├─ REAL OUTPUT ────────────────────────────────────────────────────────────────────────────┤
│  WORKLOAD       DECODE EST.      LAST OUTPUT          RANGE          BASIC GATE          │
│  CODE              57.7 tok/s      60.6s last     56.9–58.6     ✓ 2/2                    │
│  PROSE             25.9 tok/s      47.8s last     25.7–26.0     ✓ 2/2                    │
│  STRUCTURED*       86.2 tok/s      12.3s last     85.5–87.0     ✓ 2/2                    │
│  * predictable-output ceiling; not a proxy for agent speed                               │
├─ CONTEXT ────────────────────────────────────────────────────────────────────────────────┤
│  32K PREFILL   cold 1,418 tok/s  •  immediate replay 1,417 tok/s                         │
├─ CAPPED CONCURRENT GENERATION ───────────────────────────────────────────────────────────┤
│  SHORT CODE • END-TO-END • 256-TOKEN CAP PER AGENT                                       │
│  AGGREGATE   C1 42.4  •  C2 60.3  •  C4 86.3  •  C8 117.9 tok/s                          │
│  C8 OUTPUT STATE   normal stop 0/16  •  visible 0/16  •  reasoning may be included       │
├─ RECEIPT ────────────────────────────────────────────────────────────────────────────────┤
│  JSON       sha256:a8ef377030630220…                                                     │
│  SHARE THE CARD • LINK THE JSON RECEIPT • #RIGMARK                                       │
│  github.com/alexellis/rigmark                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```
