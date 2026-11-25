<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# RigMark cards: SparkInkling 0.5.0

Unedited, from `raw/img050-*-code.card.txt`.

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
│  CODE              70.0 tok/s      52.6s last     69.8–70.3     ✓ 2/2                    │
│  PROSE             39.6 tok/s      29.7s last     39.1–40.1     ✓ 2/2                    │
│  STRUCTURED*      103.2 tok/s      10.2s last    102.7–103.6    ✓ 2/2                    │
│  * predictable-output ceiling; not a proxy for agent speed                               │
├─ CONTEXT ────────────────────────────────────────────────────────────────────────────────┤
│  32K PREFILL   cold 3,268 tok/s  •  immediate replay 209,871 tok/s                       │
├─ CAPPED CONCURRENT GENERATION ───────────────────────────────────────────────────────────┤
│  SHORT CODE • END-TO-END • 256-TOKEN CAP PER AGENT                                       │
│  AGGREGATE   C1 46.5  •  C2 62.6  •  C4 85.7  •  C8 122.7 tok/s                          │
│  C8 OUTPUT STATE   normal stop 0/16  •  visible 0/16  •  reasoning may be included       │
├─ RECEIPT ────────────────────────────────────────────────────────────────────────────────┤
│  JSON       sha256:8d668e5ab22f8748…                                                     │
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
│  CODE              81.4 tok/s      39.1s last     80.0–82.8     ✓ 2/2                    │
│  PROSE             56.1 tok/s      20.2s last     56.1–56.2     ✓ 2/2                    │
│  STRUCTURED*      117.4 tok/s       9.0s last    116.3–118.6    ✓ 2/2                    │
│  * predictable-output ceiling; not a proxy for agent speed                               │
├─ CONTEXT ────────────────────────────────────────────────────────────────────────────────┤
│  32K PREFILL   cold 3,282 tok/s  •  immediate replay 212,228 tok/s                       │
├─ CAPPED CONCURRENT GENERATION ───────────────────────────────────────────────────────────┤
│  SHORT CODE • END-TO-END • 256-TOKEN CAP PER AGENT                                       │
│  AGGREGATE   C1 58.8  •  C2 77.8  •  C4 103.5  •  C8 135.2 tok/s                         │
│  C8 OUTPUT STATE   normal stop 0/16  •  visible 0/16  •  reasoning may be included       │
├─ RECEIPT ────────────────────────────────────────────────────────────────────────────────┤
│  JSON       sha256:3153c8302a2b7924…                                                     │
│  SHARE THE CARD • LINK THE JSON RECEIPT • #RIGMARK                                       │
│  github.com/alexellis/rigmark                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────╯
```
