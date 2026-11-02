"""Read a photo where the words will sit, and work out the lightest tint that keeps them readable.

The tint takes its colour from the photo itself (deep moss over a forest, dusk rose over a sunset)
and only goes as dark as the words need, so the picture keeps its depth. A plain black wash over
half the poster is what this replaces.

  python imgtone.py photo.jpg 0 0.55 1 0.45 [--ratio 0.75] [--text "#FFFFFF"]
"""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from common import contrast, mix

_CACHE = {}


def _open(src):
    """A local path or file:// URI -> PIL image (RGB), or None for anything we cannot read here."""
    try:
        from PIL import Image
    except ImportError:
        return None
    if not src:
        return None
    s = str(src)
    if s.startswith("file:"):
        s = unquote(urlparse(s).path)
        if len(s) > 2 and s[0] == "/" and s[2] == ":":  # file:///C:/... on Windows
            s = s[1:]
    elif s.startswith(("http:", "https:", "data:")):
        return None
    p = Path(s)
    if not p.exists():
        return None
    key = (str(p), p.stat().st_mtime_ns)
    if key not in _CACHE:
        im = Image.open(p).convert("RGB")
        im.thumbnail((480, 480))
        _CACHE[key] = im
    return _CACHE[key]


def _cover(im, ratio, pos=(0.5, 0.5)):
    """The part of the photo that object-fit: cover shows on a canvas of width/height = ratio."""
    w, h = im.size
    if w / h > ratio:
        cw = h * ratio
        x = (w - cw) * pos[0]
        return im.crop((int(x), 0, int(x + cw), h))
    ch = w / ratio
    y = (h - ch) * pos[1]
    return im.crop((0, int(y), w, int(y + ch)))


def region(src, box, ratio, pos=(0.5, 0.5)):
    """Mean colour, mean luminance and detail (spread of luminance) inside box = (x, y, w, h) fractions of the canvas."""
    im = _open(src)
    if im is None:
        return None
    from PIL import ImageStat
    im = _cover(im, ratio, pos)
    W, H = im.size
    x, y, w, h = box
    crop = im.crop((int(x * W), int(y * H), max(int(x * W) + 1, int((x + w) * W)), max(int(y * H) + 1, int((y + h) * H))))
    st = ImageStat.Stat(crop)
    r, g, b = st.mean
    grey = ImageStat.Stat(crop.convert("L"))
    return {"mean": "#%02X%02X%02X" % (int(r), int(g), int(b)), "lum": grey.mean[0] / 255, "detail": grey.stddev[0] / 255}


def tint(src, box, ratio, text="#FFFFFF", pos=(0.5, 0.5), target=4.5, cap=0.62):
    """(tone, alpha, info) for a gradient behind words of colour `text` inside box. alpha 0 = no tint needed.
    Busy areas (high detail) need more help than calm ones, because the eye reads against the darkest
    and lightest bits, not the average."""
    st = region(src, box, ratio, pos)
    if not st:
        return None
    light_text = contrast(text, "#000000") > contrast(text, "#FFFFFF")
    tone = mix(st["mean"], "#000000" if light_text else "#FFFFFF", 0.62)
    need = target + st["detail"] * 6  # a calm sky needs 4.5, a busy street a good deal more
    alpha = 0.0
    while alpha < cap and contrast(text, mix(st["mean"], tone, alpha)) < need:
        alpha += 0.04
    return tone, round(min(alpha, cap), 2), st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("box", nargs=4, type=float)
    ap.add_argument("--ratio", type=float, default=0.75)
    ap.add_argument("--text", default="#FFFFFF")
    a = ap.parse_args()
    r = tint(a.photo, a.box, a.ratio, a.text)
    print(json.dumps(r and {"tone": r[0], "alpha": r[1], **r[2]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
