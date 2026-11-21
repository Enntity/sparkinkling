<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# RigMark cards: SparkInkling 0.2.0

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
│  CODE              50.0 tok/s      70.3s last     47.8–52.3     ✓ 2/2                    │
│  PROSE             22.8 tok/s      51.6s last     22.4–23.2     ✓ 2/2                    │
│  STRUCTURED*       79.5 tok/s      13.1s last     78.6–80.4     ✓ 2/2                    │
│  * predictable-output ceiling; not a proxy for agent speed                               │
├─ CONTEXT ────────────────────────────────────────────────────────────────────────────────┤
│  32K PREFILL   cold 3,271 tok/s  •  immediate replay 3,272 tok/s                         │
├─ CAPPED CONCURRENT GENERATION ───────────────────────────────────────────────────────────┤
│  SHORT CODE • END-TO-END • 256-TOKEN CAP PER AGENT                                       │
│  AGGREGATE   C1 32.0  •  C2 44.1  •  C4 72.2  •  C8 105.3 tok/s                          │
│  C8 OUTPUT STATE   normal stop 0/16  •  visible 0/16  •  reasoning may be included       │
├─ RECEIPT ────────────────────────────────────────────────────────────────────────────────┤
│  JSON       sha256:aab88312ff3a69d4…                                                     │
│  SHARE THE CARD • LINK THE JSON RECEIPT • #RIGMARK                                       │
│  github.com/alexellis/rigmark                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```

## Spark, code suite

```text
╭──────────────────────────────────────────────────────────────────────────────────────────╮
│  R I G M A R K   //   AGENT WORKLOAD RECEIPT                                             │
│  BENCHMARKS LOCAL AI HOW CODING AGENTS ACTUALLY USE IT                                   │
│  ▲  5/6 BASIC OUTPUT GATES PASSED — DO NOT HEADLINE                                      │
├─ SYSTEM ─────────────────────────────────────────────────────────────────────────────────┤
│  MODEL      inkling-2-mini-atlas                                                         │
│  APPLIANCE  1x NVIDIA DGX Spark (GB10, 128 GB)                                           │
│  RUN        reasoning=low  •  protocol=1.1.0                                             │
│  SOURCE     git:40fabcaf6e96  •  clean                                                   │
├─ REAL OUTPUT ────────────────────────────────────────────────────────────────────────────┤
│  WORKLOAD       DECODE EST.      LAST OUTPUT          RANGE          BASIC GATE          │
│  CODE              60.9 tok/s      56.1s last     57.7–64.2     ✗ 1/2                    │
│  PROSE             25.7 tok/s      49.3s last     25.5–26.0     ✓ 2/2                    │
│  STRUCTURED*       87.3 tok/s      12.1s last     87.1–87.5     ✓ 2/2                    │
│  * predictable-output ceiling; not a proxy for agent speed                               │
├─ CONTEXT ────────────────────────────────────────────────────────────────────────────────┤
│  32K PREFILL   cold 3,128 tok/s  •  immediate replay 3,125 tok/s                         │
├─ CAPPED CONCURRENT GENERATION ───────────────────────────────────────────────────────────┤
│  SHORT CODE • END-TO-END • 256-TOKEN CAP PER AGENT                                       │
│  AGGREGATE   C1 35.8  •  C2 63.1  •  C4 90.0  •  C8 115.5 tok/s                          │
│  C8 OUTPUT STATE   normal stop 0/16  •  visible 0/16  •  reasoning may be included       │
├─ RECEIPT ────────────────────────────────────────────────────────────────────────────────┤
│  JSON       sha256:d34579c3ec17a2fc…                                                     │
│  SHARE THE CARD • LINK THE JSON RECEIPT • #RIGMARK                                       │
│  github.com/alexellis/rigmark                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```
