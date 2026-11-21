<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SparkInkling cards

`banner.png` is the README hero (2172 × 724). `social-preview.png` is the
matching social card (1733 × 907); `social-preview.jpg` is its same-dimension
JPEG export, below 1 MB.

The cards name the product and its two modes: Strict, the default, which
serves the checkpoint as shipped (`./start.sh`), and Spark, which adds the
calibrated NVFP4 overlay (`./start.sh --mode spark`; the overlay is pending
publication). They carry no version number and no measured figure: nothing
has been benchmarked yet.

They were composed on 2026-11-21 by [`make_cards.py`](make_cards.py) from
SparkQwen's cards (Enntity/sparkqwen `docs/assets` at commit `bd26c6d`). The
script keeps the purple arcade frame, starfield, Enntity logo, icons, wireframe
tunnel and GitHub mark, paints out the title, version, subtitle, lanes,
supporting lines and URL, and sets the new text, the title included, in Press
Start 2P (SIL Open Font License 1.1; the font is not shipped here):

```sh
python3 docs/assets/make_cards.py SPARKQWEN_CARDS_DIR PressStart2P-Regular.ttf docs/assets
```

Both cards were visually checked. The guard line describes the default-on
pattern filter SparkQwen and SparkGLM ship, not protection from all
exfiltration. Committing these files does not itself set GitHub's social
preview.
