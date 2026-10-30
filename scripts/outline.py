"""Turn text into SVG paths so logos stay vector and look the same on any computer.

outline_text("茶小满", "qingke", 400, size=100) -> (path_d, width, height, ascent)

Fonts: the npm web fonts in the cache (woff2 subsets, the right subset is found per character
through the CSS unicode-range) or the system CJK fonts through fc-match. woff2 needs the brotli
module; without it, or without a usable font file, None is returned and the caller keeps live text.
"""
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from common import load_ref

FC_WEIGHT = {300: "light", 400: "regular", 500: "medium", 700: "bold", 900: "black"}


@lru_cache(maxsize=64)
def _font(path, index=0):
    from fontTools.ttLib import TTFont
    return TTFont(path, fontNumber=index, lazy=True)


@lru_cache(maxsize=16)
def _css_blocks(fid):
    """[(weight, [(lo, hi)], woff2 path)] for an npm font."""
    from fonts import _pkg_dir
    spec = load_ref("fonts.json")[fid]
    base = _pkg_dir(fid, spec)
    out = []
    for name in spec.get("css", []):
        p = base / name
        if not p.exists():
            continue
        for block in re.findall(r"@font-face\s*{([^}]*)}", p.read_text(encoding="utf-8")):
            w = re.search(r"font-weight:\s*(\d+)", block)
            src = re.search(r"url\(['\"]?\./([^'\")]+\.woff2)", block)
            rng = re.search(r"unicode-range:\s*([^;]+);", block)
            if not src:
                continue
            ranges = []
            for part in (rng.group(1).split(",") if rng else ["U+0-10FFFF"]):
                part = part.strip().replace("U+", "")
                if "-" in part:
                    lo, hi = part.split("-")
                    ranges.append((int(lo, 16), int(hi, 16)))
                elif "?" in part:
                    ranges.append((int(part.replace("?", "0"), 16), int(part.replace("?", "F"), 16)))
                elif part:
                    ranges.append((int(part, 16), int(part, 16)))
            out.append((int(w.group(1)) if w else 400, ranges, str(base / src.group(1))))
    return out


def _system_file(family, weight):
    fw = {300: 50, 400: 80, 500: 100, 600: 180, 700: 200, 900: 210}.get(weight, 80)
    try:
        r = subprocess.run(["fc-match", "-f", "%{file}:%{index}", f"{family}:weight={fw}"],
                           capture_output=True, text=True, timeout=10)
        f, idx = r.stdout.rsplit(":", 1)
        return f, int(idx or 0)
    except Exception:  # noqa: BLE001
        return None, 0


def _file_for(fid, ch, weight):
    spec = load_ref("fonts.json").get(fid) or load_ref("fonts.json")["sans"]
    if spec["source"] == "npm":
        blocks = _css_blocks(fid)
        cp = ord(ch)
        cands = [b for b in blocks if any(lo <= cp <= hi for lo, hi in b[1])]
        if cands:
            best = min(cands, key=lambda b: abs(b[0] - weight))
            return best[2], 0
        spec = load_ref("fonts.json")["sans"]  # character missing from the web font: fall back like the browser
    return _system_file(spec["family"], weight)


def outline_text(text, fid, weight=400, size=100, tracking=0.0):
    """Returns (d, width, height, ascent) in px for font-size `size`, baseline at y=ascent."""
    try:
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen
    except ImportError:
        return None
    parts, x = [], 0.0
    asc = size * 0.88
    for ch in text:
        if ch == " ":
            x += size * 0.3 + tracking * size
            continue
        path, idx = _file_for(fid, ch, weight)
        if not path or not Path(path).exists():
            return None
        try:
            f = _font(path, idx)
            cmap = f.getBestCmap()
            g = cmap.get(ord(ch))
            if g is None:
                spec = load_ref("fonts.json")["sans"]
                path, idx = _system_file(spec["family"], weight)
                f = _font(path, idx)
                cmap = f.getBestCmap()
                g = cmap.get(ord(ch))
                if g is None:
                    return None
            gs = f.getGlyphSet()
            upm = f["head"].unitsPerEm
            s = size / upm
            pen = SVGPathPen(gs)
            gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, asc)))
            parts.append(pen.getCommands())
            x += f["hmtx"][g][0] * s + tracking * size
        except Exception:  # noqa: BLE001  (brotli missing, damaged file, ...)
            return None
    width = max(0.0, x - tracking * size)
    return " ".join(p for p in parts if p), width, size * 1.12, asc
