#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Compose the SparkInkling cards from SparkQwen's.

    make_cards.py BASE_DIR FONT.ttf OUT_DIR

BASE_DIR holds SparkQwen's `banner.png` and `social-preview.png`
(Enntity/sparkqwen docs/assets at commit bd26c6d). The frame, starfield,
logo, icons and tunnel are kept as they are; the title, version, subtitle,
lanes, supporting lines and URL are painted out and the new text (a
high-score table where the lanes were) is set in
Press Start 2P (SIL OFL 1.1, not shipped here). Adapted from SparkQwen's
make_cards.py. Needs Pillow. The JPEG is a format export of the social card.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

WHITE, YELLOW, ORANGE = (255, 255, 255), (255, 232, 26), (255, 150, 40)
PURPLE, VIOLET, DIM = (190, 120, 255), (150, 90, 235), (170, 170, 190)
LINK = (160, 120, 255)
STAR_COLORS = [WHITE] * 5 + [YELLOW] * 3 + [(170, 100, 255), (90, 220, 255)]
# The title's two words: top and bottom of the fill gradient, then the shadow.
SPARK = ((255, 236, 60), (255, 120, 20), (190, 60, 0))
INKLING = ((235, 225, 255), (120, 80, 255), (50, 30, 170))


class Card:
    def __init__(self, base, font_path):
        self.im = Image.open(base).convert("RGB")
        self.font_path = font_path
        self.draw = ImageDraw.Draw(self.im)
        self.cleared, self.inked = [], []

    def font(self, size):
        return ImageFont.truetype(self.font_path, size)

    def clear(self, box, stars=True):
        """Paint a region black; `stars` refills it once the text is set."""
        self.draw.rectangle(box, fill=(0, 0, 0))
        if stars:
            self.cleared.append(box)

    def clear_warm(self, box, stars=None):
        """Paint out only a region's warm pixels (the old version and its
        orange glow), so the tunnel's dim blue haze beside it keeps no edge.
        `stars` is the part that gets new stars."""
        region = self.im.crop(box)
        r, _, b = region.split()
        ink = ImageChops.subtract(r, b).point(lambda v: 255 if v > 2 else 0)
        region.paste((0, 0, 0), mask=ink.filter(ImageFilter.MaxFilter(9)))
        self.im.paste(region, box[:2])
        self.draw = ImageDraw.Draw(self.im)
        if stars:
            self.cleared.append(stars)

    def stars(self, seed, pad=14):
        """Scatter stars over the cleared regions at the base card's density, clear of the text."""
        rng = random.Random(seed)
        for x0, y0, x1, y1 in self.cleared:
            if x1 - x0 < 40 or y1 - y0 < 40:
                continue
            for _ in range(max(1, (x1 - x0) * (y1 - y0) // 24000)):
                s = rng.choice([3, 3, 4, 5])
                x, y = rng.randrange(x0 + 6, x1 - s - 6), rng.randrange(y0 + 6, y1 - s - 6)
                if not any(a - pad < x < c + pad and b - pad < y < d + pad for a, b, c, d in self.inked):
                    self.draw.rectangle((x, y, x + s, y + s), fill=rng.choice(STAR_COLORS))

    def text(self, xy, parts, size, color, glow=None, gap=None):
        """Draw `parts` left to right from `xy`, a square dot between them."""
        font = self.font(size)
        gap = size if gap is None else gap
        width = sum(int(font.getlength(p)) for p in parts) + 2 * gap * (len(parts) - 1)
        self.draw.rectangle((xy[0] - 8, xy[1] - 8, xy[0] + width + 8, xy[1] + size + 8), fill=(0, 0, 0))
        layer = Image.new("RGB", self.im.size, (0, 0, 0))
        d = ImageDraw.Draw(layer)
        x, y = xy
        for i, part in enumerate(parts):
            if i:
                dot = max(3, size // 5)
                cy = y + size // 2
                d.rectangle((x + gap - dot // 2, cy - dot // 2, x + gap + dot - dot // 2, cy + dot - dot // 2), fill=color)
                x += 2 * gap
            d.text((x, y), part, font=font, fill=color)
            x += int(font.getlength(part))
        if glow:
            tint = Image.new("RGB", self.im.size, glow)
            mask = layer.convert("L").point(lambda v: 255 if v else 0)
            halo = Image.composite(tint, Image.new("RGB", self.im.size, (0, 0, 0)), mask)
            halo = halo.filter(ImageFilter.GaussianBlur(max(2, size // 5)))
            self.im = ImageChops.screen(self.im, halo)
        self.im = ImageChops.lighter(self.im, layer) if not glow else Image.composite(
            layer, self.im, layer.convert("L").point(lambda v: 255 if v else 0))
        self.draw = ImageDraw.Draw(self.im)
        self.inked.append((xy[0], y, x, y + size))
        return x

    def title(self, xy, words, size):
        """The product name in blocky pixel letters: each word a vertical
        gradient over a stepped drop shadow, in the spirit of the base card's
        lettering."""
        font = self.font(size)
        x, y = xy
        depth = max(4, size // 14)
        for word, (top, bottom, shadow) in words:
            w = int(font.getlength(word))
            mask = Image.new("L", self.im.size, 0)
            ImageDraw.Draw(mask).text((x, y), word, font=font, fill=255)
            for step in range(depth, 0, -1):
                self.im.paste(shadow, mask=ImageChops.offset(mask, step, step))
            fill = Image.new("RGB", self.im.size)
            fd = ImageDraw.Draw(fill)
            for row in range(size + 1):
                t = row / size
                fd.line((x, y + row, x + w, y + row),
                        fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
            self.im.paste(fill, mask=mask)
            x += w
        self.draw = ImageDraw.Draw(self.im)
        self.inked.append((xy[0], y, x + depth, y + size + depth))
        return x

    def rule(self, x, y0, y1):
        self.draw.rectangle((x, y0, x + 2, y1), fill=(170, 60, 230))
        self.inked.append((x, y0, x + 2, y1))


PINK = (255, 70, 120)
# SparkInkling 0.5.0, RigMark 1.1.0, low effort, medians, tok/s
# (results/2026-11-25-release-0.5.0): label, Spark (the default), Strict.
SCORES = [("CODE", "81.4", "70.0"), ("STRUCTURED", "117.4", "103.2"), ("8 REQUESTS", "135.2", "122.7")]


def scores(card, x0, y, k, ky):
    """The high-score table from (x0, y): a row per workload, a column per
    mode with its launch command; k scales the type, ky the leading."""
    head, small, label, num = int(21 * k), int(13 * k), int(23 * k), int(31 * k)
    cols = [("SPARK", "./start.sh", x0 + int(800 * k)), ("STRICT", "--mode strict", x0 + int(1200 * k))]

    def right(xr, yy, s, size, color, glow=None):
        card.text((xr - int(card.font(size).getlength(s)), yy), [s], size, color, glow=glow)

    end = card.text((x0, y), ["HIGH SCORES"], head, PINK, glow=(150, 20, 70))
    card.text((end + int(18 * k), y), ["TOK/S"], head, YELLOW)
    for name, cmd, xr in cols:
        right(xr, y, name, head, WHITE)
        right(xr, y + int(30 * ky), cmd, small, VIOLET)
    line = y + int(54 * ky)
    card.draw.rectangle((x0, line, cols[-1][2], line + 2), fill=(170, 60, 230))
    card.inked.append((x0, line, cols[-1][2], line + 2))
    for row, (name, spark, strict) in enumerate(SCORES):
        yy = y + int(72 * ky) + row * int(42 * ky)
        card.text((x0, yy + (num - label) // 2), [name], label, WHITE)
        for value, (_, _, xr) in zip((spark, strict), cols):
            right(xr, yy, value, num, YELLOW, glow=ORANGE)


LINES = (["Atlas engine", "DFlash2 drafter", "1M context"],
         ["Reasoning, tools, images", "tool-call guard on"],
         ["32K prefill 3,282 tok/s", "6/6 output gates"])
SOURCE = ["0.5.0 benchmarks", "RigMark 1.1.0", "low effort"]
URL = "github.com/Enntity/sparkinkling"


def banner(base, font, out):
    c = Card(base, font)
    c.clear_warm((1062, 60, 1540, 244), (1075, 70, 1480, 240))  # the old version
    c.clear((75, 92, 1062, 244), stars=False)  # the old title
    c.clear((75, 244, 1430, 520))         # subtitle and lanes
    c.clear((150, 521, 1200, 700))        # supporting lines (icons stay)
    c.clear((1550, 636, 2110, 688), stars=False)  # the URL (the GitHub mark stays)
    c.title((88, 112), [("Spark", SPARK), ("Inkling", INKLING)], 112)
    c.text((88, 270), ["Inkling 2 Mini on one NVIDIA DGX Spark", "Atlas"], 23, WHITE)
    scores(c, 100, 326, 1.0, 1.0)
    for y, parts in zip((537, 580, 624), LINES):
        c.text((172, y), parts, 20, WHITE)
    c.text((172, 668), SOURCE, 14, DIM, gap=10)
    c.text((1562, 648), [URL], 17, LINK)
    c.stars(1)
    c.im.save(out, optimize=True)


def social(base, font, out):
    c = Card(base, font)
    c.clear_warm((866, 130, 1215, 250), (880, 140, 1150, 285))  # the old version,
    c.clear_warm((866, 250, 1185, 268))                         # stepped along
    c.clear_warm((866, 268, 1160, 292))                         # the tunnel's edge
    c.clear_warm((1185, 250, 1202, 260))
    c.clear_warm((1160, 268, 1174, 280))
    c.clear((70, 150, 880, 292), stars=False)  # the old title
    c.clear((70, 292, 1136, 585))         # subtitle and lanes
    c.clear((150, 596, 1050, 815))        # supporting lines (icons stay)
    c.clear((1140, 784, 1690, 830), stars=False)  # the URL (the GitHub mark stays)
    c.title((80, 178), [("Spark", SPARK), ("Inkling", INKLING)], 86)
    c.text((82, 312), ["Inkling 2 Mini on one NVIDIA DGX Spark", "Atlas"], 19, WHITE)
    scores(c, 82, 380, 0.84, 1.08)
    for y, parts in zip((618, 668, 718), LINES):
        c.text((170, y), parts, 17, WHITE, gap=12)
    c.text((170, 770), SOURCE, 13, DIM, gap=9)
    c.text((1150, 797), [URL], 16, LINK)
    c.stars(2)
    c.im.save(out, optimize=True)
    c.im.save(Path(out).with_suffix(".jpg"), quality=90)


if __name__ == "__main__":
    base, font, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    banner(base / "banner.png", font, out / "banner.png")
    social(base / "social-preview.png", font, out / "social-preview.png")
