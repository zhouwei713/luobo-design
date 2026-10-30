"""Repair glyphs whose holes are drawn in the same direction as their outline.

Some open fonts ship a few glyphs (ZCOOL XiaoWei's 回, for example) where every contour runs the
same way. Browsers fill with the nonzero rule, so the counters fill in and the character prints as
a solid block. This walks the cached woff2 files once, finds glyphs where all contours share one
direction although some sit inside others, and reverses the nested ones so holes are holes again.
Glyphs that already mix directions are left untouched.

  python fontfix.py DIR          # repair every woff2 under DIR, print what changed
"""
import sys
from pathlib import Path

SENTINEL = ".luobo-winding-fixed"


def _area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2


def _inside(p, poly):
    x, y = p
    hit = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            hit = not hit
        j = i
    return hit


def _fix_glyph(g):
    ends = list(g.endPtsOfContours)
    if len(ends) < 2:
        return False
    coords = list(g.coordinates)
    flags = list(g.flags)
    spans, s = [], 0
    for e in ends:
        spans.append((s, e + 1))
        s = e + 1
    polys = [coords[a:b] for a, b in spans]
    areas = [_area(p) for p in polys]
    if any(abs(a) < 1 for a in areas):
        return False
    if not (all(a > 0 for a in areas) or all(a < 0 for a in areas)):
        return False  # already has holes drawn the other way: trust the designer
    depth = []
    for i, p in enumerate(polys):
        probe = p[0]
        depth.append(sum(1 for j, q in enumerate(polys)
                         if j != i and abs(areas[j]) > abs(areas[i]) and all(_inside(pt, q) for pt in p[:: max(1, len(p) // 8)] + [probe])))
    if not any(depth):
        return False
    outer_sign = 1 if areas[0] > 0 else -1
    changed = False
    for i, (a, b) in enumerate(spans):
        want = outer_sign if depth[i] % 2 == 0 else -outer_sign
        if (1 if areas[i] > 0 else -1) != want:
            coords[a:b] = coords[a:b][::-1]
            flags[a:b] = flags[a:b][::-1]
            changed = True
    if changed:
        from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
        g.coordinates = GlyphCoordinates(coords)
        g.flags = type(g.flags)(g.flags.typecode, flags) if hasattr(g.flags, "typecode") else bytearray(flags)
        if hasattr(g, "program"):
            from fontTools.ttLib.tables import ttProgram
            g.program = ttProgram.Program()
            g.program.fromBytecode(b"")
    return changed


def fix_file(path):
    from fontTools.ttLib import TTFont
    f = TTFont(str(path))
    if "glyf" not in f:
        return []
    glyf = f["glyf"]
    cmap = {v: k for k, v in f.getBestCmap().items()}
    fixed = []
    for name in glyf.keys():
        g = glyf[name]
        if g.isComposite() or g.numberOfContours < 2:
            continue
        g.expand(glyf)
        if _fix_glyph(g):
            fixed.append(chr(cmap[name]) if name in cmap else name)
    if fixed:
        f.flavor = f.flavor or "woff2"
        f.save(str(path))
    return fixed


def fix_dir(folder, quiet=True):
    """Repair every woff2 under folder once; a marker file records that it was done."""
    folder = Path(folder)
    mark = folder / SENTINEL
    if mark.exists():
        return None
    try:
        import brotli  # noqa: F401  (woff2 needs it)
        import fontTools  # noqa: F401
    except ImportError:
        return None
    fixed = []
    for p in sorted(folder.rglob("*.woff2")):
        try:
            fixed += fix_file(p)
        except Exception as e:  # noqa: BLE001
            if not quiet:
                print(f"  skip {p.name}: {e}")
    mark.write_text("".join(fixed), encoding="utf-8")
    return fixed


if __name__ == "__main__":
    for d in sys.argv[1:]:
        out = fix_dir(d, quiet=False)
        print(d, "already done" if out is None else f"fixed {len(out)}: {''.join(out)[:200]}")
