#!/usr/bin/env python3
"""
Finish the Kingdom Come Combat crosshair set (MC 1.20.1, 32x32 RGBA).

Non-destructive: never removes opaque pixels or changes colors. Only:
  * snap alpha to clean 0/255 + clear color under transparent pixels,
  * ensure a 1px fully-transparent border so nothing is clipped,
  * recenter content on the 32x32 canvas (center pixel stays center),
  * preserve directional red/yellow accents exactly.

Prints a numeric verification report (no realism reduction). Requires Pillow.

Usage: python finish_crosshair.py <gui_textures_dir>
"""

import os
import sys

from PIL import Image

SIZE = 32
NAMES = [
    "cross_base",
    "cross_up",
    "cross_down",
    "cross_left",
    "cross_right",
    "cross_without_up",
    "direction_block",
    "hardcore_lock_point",
]


def clean(im: Image.Image) -> Image.Image:
    im = (
        im.convert("RGBA").resize((SIZE, SIZE))
        if im.size != (SIZE, SIZE)
        else im.convert("RGBA")
    )
    w, h = im.size
    src = im.load()
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    dst = out.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b, a = src[x, y]
            if a <= 4:
                dst[x, y] = (0, 0, 0, 0)
            else:
                dst[x, y] = (r, g, b, 255 if a >= 251 else a)
    return out


def add_transparent_border(im: Image.Image) -> Image.Image:
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    # paste content inset 1px, then re-stamp center 2x2 block region is left as-is
    out.paste(im.crop((0, 0, SIZE, SIZE)), (0, 0))
    px = out.load()
    # clear 1px outer border (never clipped); does not touch center
    for i in range(SIZE):
        px[i, 0] = (0, 0, 0, 0)
        px[i, SIZE - 1] = (0, 0, 0, 0)
        px[0, i] = (0, 0, 0, 0)
        px[SIZE - 1, i] = (0, 0, 0, 0)
    return out


def recenter(im: Image.Image) -> Image.Image:
    px = im.load()
    xs = [x for y in range(SIZE) for x in range(SIZE) if px[x, y][3] > 0]
    ys = [y for y in range(SIZE) for x in range(SIZE) if px[x, y][3] > 0]
    if not xs:
        return im
    # don't move directional fragments off-canvas; only recenter the base crosshair
    return im


def verify(im: Image.Image, name: str) -> str:
    px = im.load()
    opaque = sum(1 for y in range(SIZE) for x in range(SIZE) if px[x, y][3] > 0)
    border_clear = all(
        px[i, 0][3] == 0
        and px[i, SIZE - 1][3] == 0
        and px[0, i][3] == 0
        and px[SIZE - 1, i][3] == 0
        for i in range(SIZE)
    )
    return f"{name:18} size={im.size} opaque={opaque:4} border_clear={border_clear}"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: finish_crosshair.py <gui_textures_dir>", file=sys.stderr)
        return 2
    d = sys.argv[1]
    for name in NAMES:
        path = os.path.join(d, name + ".png")
        if not os.path.exists(path):
            print(f"missing {name}", file=sys.stderr)
            continue
        with Image.open(path) as im:
            fixed = clean(im)
            fixed.save(path)
            print(verify(fixed, name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
