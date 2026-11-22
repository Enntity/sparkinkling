<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# RigMark cards: SparkInkling 0.4.0

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
│  CODE              49.2 tok/s      70.7s last     47.5–50.9     ✓ 2/2                    │
│  PROSE             33.6 tok/s      37.8s last     33.4–33.8     ✓ 2/2                    │
│  STRUCTURED*       86.4 tok/s      12.1s last     85.3–87.5     ✓ 2/2                    │
│  * predictable-output ceiling; not a proxy for agent speed                               │
├─ CONTEXT ────────────────────────────────────────────────────────────────────────────────┤
│  32K PREFILL   cold 3,277 tok/s  •  immediate replay 208,174 tok/s                       │
├─ CAPPED CONCURRENT GENERATION ───────────────────────────────────────────────────────────┤
│  SHORT CODE • END-TO-END • 256-TOKEN CAP PER AGENT                                       │
│  AGGREGATE   C1 35.9  •  C2 49.0  •  C4 78.1  •  C8 119.6 tok/s                          │
│  C8 OUTPUT STATE   normal stop 0/16  •  visible 0/16  •  reasoning may be included       │
├─ RECEIPT ────────────────────────────────────────────────────────────────────────────────┤
│  JSON       sha256:ee106e9de728e08c…                                                     │
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
│  CODE              66.8 tok/s      53.4s last     64.8–68.8     ✓ 2/2                    │
│  PROSE             51.6 tok/s      24.1s last     51.6–51.7     ✓ 2/2                    │
│  STRUCTURED*       96.4 tok/s      10.9s last     95.1–97.7     ✓ 2/2                    │
│  * predictable-output ceiling; not a proxy for agent speed                               │
├─ CONTEXT ────────────────────────────────────────────────────────────────────────────────┤
│  32K PREFILL   cold 3,275 tok/s  •  immediate replay 213,959 tok/s                       │
├─ CAPPED CONCURRENT GENERATION ───────────────────────────────────────────────────────────┤
│  SHORT CODE • END-TO-END • 256-TOKEN CAP PER AGENT                                       │
│  AGGREGATE   C1 50.9  •  C2 72.0  •  C4 101.3  •  C8 134.9 tok/s                         │
│  C8 OUTPUT STATE   normal stop 0/16  •  visible 0/16  •  reasoning may be included       │
├─ RECEIPT ────────────────────────────────────────────────────────────────────────────────┤
│  JSON       sha256:756287dd82966196…                                                     │
│  SHARE THE CARD • LINK THE JSON RECEIPT • #RIGMARK                                       │
│  github.com/alexellis/rigmark                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```
