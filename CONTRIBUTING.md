<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Contributing

Small, focused changes are welcome: fixes, documentation, launch reliability
and measured improvements. You don't need a Spark for most of them.

Run the same checks as CI before opening a pull request:

```sh
python3 -m unittest discover -s install -p 'test_*.py'
shellcheck -S warning -e SC2054 start.sh install/*.sh
python3 -m py_compile install/*.py docs/assets/make_cards.py
```

**Changes to `install/`** change the image. Before merging, test them with
`./start.sh` from a clean clone on a Spark.

**Performance changes** need raw receipts under `results/`, with the baseline
run on the same Spark (see [results/README.md](results/README.md)).

**Engine changes** go to [Enntity/atlas](https://github.com/Enntity/atlas)
and upstream to [Atlas-Inf/atlas](https://github.com/Atlas-Inf/atlas); here you
then update the pin in `install/atlas-source.json` and `docs/ENGINE.md`.

Credit other people's work with a `Provenance:` line naming the source and
its license. Use `Co-authored-by` only for someone who actually wrote part of
the commit.
