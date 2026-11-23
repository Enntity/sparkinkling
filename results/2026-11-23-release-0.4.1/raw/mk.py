from PIL import Image, ImageDraw, ImageFont
f = ImageFont.load_default(size=22)
im = Image.new("RGB", (760, 300), "white"); d = ImageDraw.Draw(im)
for i, line in enumerate(["Invoice 48213 - Harbor Street Bakery", "3 x sourdough loaf      18.75", "12 x almond croissant   41.40", "Delivery to dock 7      6.00", "TOTAL DUE              66.15"]):
    d.text((24, 20 + i * 52), line, fill="black", font=f)
im.save("/vis/invoice.png")
im = Image.new("RGB", (1280, 960), (245, 245, 245)); d = ImageDraw.Draw(im)
cols = {"red": (220, 40, 40), "green": (40, 160, 70), "blue": (40, 80, 220), "yellow": (240, 210, 40)}
layout = [["red", "green", "blue"], ["yellow", "blue", "red"], ["green", "yellow", "green"]]
for r in range(3):
    for c in range(3):
        x, y = 80 + c * 400, 60 + r * 300
        d.rectangle([x, y, x + 300, y + 220], fill=cols[layout[r][c]])
        d.text((x + 120, y + 90), f"{chr(65 + r)}{c + 1}", fill="black", font=ImageFont.load_default(size=40))
im.save("/vis/grid.png")
