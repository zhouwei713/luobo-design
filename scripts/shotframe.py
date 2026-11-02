"""Dress a screenshot for a poster or a note cover: rounded corners, a soft shadow, and optionally
a browser window or a phone around it. The screenshot itself is never stretched or redrawn.

  python shotframe.py shot.png out.png [--frame browser|phone|window|plain] [--dark]

Writes a transparent PNG the layouts place like any other picture (art.image, fit contain).
In a spec: "art": {"screenshot": "shots/app.png", "frame": "phone"} and render.py does this for you.
"""
import argparse
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

FRAMES = ("browser", "phone", "window", "plain")


def _round(im, r):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def _shadow(card, r, spread):
    """card on a transparent sheet with a soft drop shadow under it."""
    pad = spread * 2
    sheet = Image.new("RGBA", (card.width + pad * 2, card.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("L", sheet.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + spread // 3, pad + card.width, pad + card.height + spread // 3), r, fill=90)
    sh = sh.filter(ImageFilter.GaussianBlur(spread * 0.7))
    sheet.putalpha(sh)
    shadow_rgb = Image.new("RGBA", sheet.size, (24, 20, 16, 255))
    shadow_rgb.putalpha(sh)
    sheet = shadow_rgb
    sheet.alpha_composite(card, (pad, pad))
    return sheet


def frame(src, out, kind="browser", dark=False, max_side=1600):
    shot = Image.open(src).convert("RGB")
    if max(shot.size) > max_side:
        shot.thumbnail((max_side, max_side), Image.LANCZOS)
    w, h = shot.size
    s = max(w, h) / 1000  # one unit per thousand pixels of the long side
    chrome = (34, 34, 38) if dark else (238, 236, 232)
    line = (60, 60, 66) if dark else (214, 210, 204)
    if kind == "browser" or kind == "window":
        bar = int(46 * s)
        card = Image.new("RGB", (w, h + bar), chrome)
        d = ImageDraw.Draw(card)
        for i, col in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
            cx, cy, rr = int((26 + i * 24) * s), bar // 2, int(7 * s)
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=col)
        if kind == "browser":  # an empty address pill: no fake URL
            d.rounded_rectangle((int(w * .28), int(bar * .24), int(w * .72), int(bar * .76)), int(bar * .26),
                                fill=(52, 52, 58) if dark else (252, 251, 249))
        d.line((0, bar - 1, w, bar - 1), fill=line, width=max(1, int(s)))
        card.paste(shot, (0, bar))
        card = _round(card, int(18 * s))
        r = int(18 * s)
    elif kind == "phone":
        bez = int(max(w, h) * .028)
        cw, ch = w + bez * 2, h + bez * 2
        r = int(min(cw, ch) * .12)
        card = Image.new("RGB", (cw, ch), (22, 22, 24))
        inner = _round(shot.convert("RGBA"), int(r * .78))
        card = _round(card, r)
        card.alpha_composite(inner, (bez, bez))
        d = ImageDraw.Draw(card)  # a small camera island, kept off the content as far as possible
        iw, ih = int(cw * .26), int(bez * 1.1)
        d.rounded_rectangle(((cw - iw) // 2, bez + int(bez * .35), (cw + iw) // 2, bez + int(bez * .35) + ih), ih // 2, fill=(22, 22, 24))
    else:
        r = int(16 * s)
        card = _round(shot.convert("RGBA"), r)
        bd = Image.new("RGBA", card.size, (0, 0, 0, 0))
        ImageDraw.Draw(bd).rounded_rectangle((0, 0, card.width - 1, card.height - 1), r, outline=line + (255,), width=max(1, int(2 * s)))
        card.alpha_composite(bd)
    if card.mode != "RGBA":
        card = card.convert("RGBA")
    sheet = _shadow(card, r, int(34 * s))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    return out


def framed_path(src, cache_dir, kind, dark=False):
    """Frame once per (file, look); later renders reuse the result."""
    p = Path(src)
    key = hashlib.sha1(f"{p.resolve()}|{p.stat().st_mtime_ns}|{kind}|{dark}".encode()).hexdigest()[:10]
    out = Path(cache_dir) / f"shot-{p.stem[:30]}-{kind}-{key}.png"
    if not out.exists():
        frame(p, out, kind, dark)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--frame", choices=FRAMES, default="browser")
    ap.add_argument("--dark", action="store_true")
    a = ap.parse_args()
    print(frame(a.src, a.out, a.frame, a.dark))


if __name__ == "__main__":
    main()
