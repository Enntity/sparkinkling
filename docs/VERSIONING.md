<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Product versions

SparkInkling uses its own semantic version, starting at `0.1.0`, as SparkQwen
and SparkGLM do. The number identifies the distribution: its Atlas pin, launch
recipe and profiles. It is separate from the model's name and the Atlas engine
version.

[`install/release.json`](../install/release.json) is the source of truth.
`./start.sh --version` prints the checkout's version and its exact pinned
engine without needing Docker, weights, `.env` or a running server.
`./start.sh status` also reads the version label and image of the running
container, so an older deployment is distinguishable from a newer checkout.

For an image already on the Spark, `docker run --rm IMAGE --version` prints its
product version and engine pin without loading the model. OCI
`org.opencontainers.image.version` records the product version and the
install-tree label its exact recipe.

Before publishing a changed distribution, bump the version in
`install/release.json`:

- Patch: compatible fixes to the engine, recipe or packaging.
- Minor: new functionality; during `0.x`, also changes requiring user action.
- Major: incompatible changes once the product reaches `1.0.0`.

Documentation-only changes do not need a version bump. Do not reuse a
published version for different distribution contents. Tag GitHub releases
`vMAJOR.MINOR.PATCH` and record the product commit, the full install tree, the
Atlas commit and tree, and the registry digest in the release. Engine pins and
image digests remain the immutable identities; versions do not replace them.
Image tags are the first 12 characters of the `install/` tree hash, and
`start.sh` selects that exact tag.

A version number is not a new model-quality or performance qualification.
Each release links its actual checks and evidence under
[`results/`](../results/README.md), including what it did not test.

A successful image build is one acceptance check: it runs the pinned engine's
CPU workspace tests and Clippy ([ENGINE](ENGINE.md#build-time-gates)). It does
not run GPU tests. Before publishing a release, run this repository's checks
([CONTRIBUTING](../CONTRIBUTING.md)), `./start.sh` in both modes on a Spark,
and the measurements the release claims, and keep the receipts with it.
