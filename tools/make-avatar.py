#!/usr/bin/env python3
"""Render a PNG/JPEG avatar as a truecolor ANSI half-block banner (no deps beyond PIL)."""
import sys
from PIL import Image

W = int(sys.argv[3]) if len(sys.argv) > 3 else 44
BG = (18, 13, 32)  # dark terminal background
im = Image.open(sys.argv[1])
if im.mode in ("RGBA", "LA", "P"):
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, BG + (255,))
    im = Image.alpha_composite(bg, im).convert("RGB")
else:
    im = im.convert("RGB")
w, h = im.size
H = max(1, round(h / w * W / 2))
im = im.resize((W, H * 2), Image.LANCZOS)
px = im.load()
out = []
for y in range(0, H * 2, 2):
    line = []
    for x in range(W):
        r1, g1, b1 = px[x, y]
        r2, g2, b2 = px[x, y + 1]
        line.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
    out.append("".join(line) + "\033[0m")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"wrote {sys.argv[2]} ({W}x{H} cells)")
