# Working in this repository

SparkInkling is SparkQwen's distribution model applied to Inkling 2 Mini:
Atlas on one DGX Spark, one entry point, a pinned engine, receipts for every
claim.

- Keep it simple: one entry point (`start.sh`), one install directory, one
  results tree. Prefer removing code to adding it.
- Qualify the actual pinned product checkpoint and image. Atlas benchmarks
  of other model families are separate engine evidence; they cannot qualify
  SparkInkling.
- The image tag will be the git tree of `install/`. Anything that changes the
  image must live in `install/`, and nothing else should.
- Engine changes belong upstream: branch in `Enntity/atlas`, then open a PR to
  Atlas-Inf `main` with the owner's go-ahead. Never push to Atlas-Inf.
- This repository holds accepted work only. Plans, porting logs, WIP and
  host-specific notes go to the private notes repository. Keep host names,
  user names, private addresses and home paths out of everything here except
  the unedited receipts in `results/*/raw/`.
- A performance claim needs raw receipts and `SHA256SUMS` under `results/`,
  with its baseline measured on the same Spark. Report every repetition, and
  say which opt-ins were on.
- Keep lossy or quality-affecting optimizations off by default. Say
  "bit-exact" only for what was measured; never call a recipe lossless.
- New files carry an SPDX header. Credit ideas and code taken from other
  projects (origin, license) in code and docs.
