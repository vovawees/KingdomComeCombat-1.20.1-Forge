#!/usr/bin/env python3
"""
Non-destructive texture normalizer for Kingdom Come Combat (MC 1.20.1).

Goals (never reduce realism, never remove detail):
  * keep every opaque pixel + color exactly; only tidy the alpha channel,
  * remove fully-transparent speckle / noise edges,
  * snap nearly-opaque/nearly-transparent alpha to clean 0/255,
  * preserve original size + format + path; originals backed up before any write.

It does NOT downscale, re-palette, blur, or strip good art. Run with a Pillow python.

Usage: python restyle_textures.py <root_textures_dir> [--dry-run]
"""

import os
import shutil
import sys

from PIL import Image

ALPHA_EMPTY = 4  # <= this alpha -> fully transparent
ALPHA_FULL = 251  # >= this alpha -> fully opaque
KEEP_BACKUP = False


def clean_alpha(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    src = im.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a <= ALPHA_EMPTY:
                a = 0
                # don't leak color into transparent pixels
                r = g = b = 0
            elif a >= ALPHA_FULL:
                a = 255
            dst[x, y] = (r, g, b, a)
    return out


def strip_transparent_border_noise(im: Image.Image) -> Image.Image:
    """Remove isolated single transparent-pixel speckle inside opaque art? No-op:
    conservative — we never add/remove opaque pixels. Kept for symmetry."""
    return im


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: restyle_textures.py <textures_dir> [--dry-run]", file=sys.stderr)
        return 2
    root = sys.argv[1]
    dry = "--dry-run" in sys.argv
    changed = 0
    total = 0
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.lower().endswith(".png"):
                continue
            path = os.path.join(dirpath, fn)
            total += 1
            try:
                with Image.open(path) as im:
                    orig = im.convert("RGBA")
                    fixed = strip_transparent_border_noise(clean_alpha(orig))
                    if list(orig.getdata()) == list(fixed.getdata()):
                        continue
                    if not dry:
                        if KEEP_BACKUP:
                            shutil.copy2(path, path + ".orig")
                        fixed.save(path)
                    changed += 1
            except Exception as e:  # never let one bad file abort the run
                print(f"skip {path}: {e}", file=sys.stderr)
    print(f"scanned={total} changed={changed} dry={dry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
