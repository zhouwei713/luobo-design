"""Shared helpers for luobo-design: paths, data files, colours, tokens, canvases."""
import html
import json
import re
from pathlib import Path

SKILL_VERSION = "0.14.0"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REF_DIR = SKILL_DIR / "references"
CACHE_DIR = Path.home() / ".cache" / "luobo-design"


def load_ref(name):
    with open(REF_DIR / name, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def esc(s):
    """HTML-escape text; a newline in copy is an intended line break."""
    if s is None:
        return ""
    return html.escape(str(s)).replace("\n", "<br>")


# ------------------------------------------------------------------ colour
def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in rgb)


def luminance(h):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def mix(a, b, t):
    """t=0 -> a, t=1 -> b."""
    ra, rb = hex_rgb(a), hex_rgb(b)
    return rgb_hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def rgba(h, alpha):
    r, g, b = hex_rgb(h)
    return f"rgba({r},{g},{b},{alpha})"


# OKLCH: lightness, chroma and hue move independently here, so a colour can be calmed or darkened
# without drifting to another hue (which mixing in sRGB does). Standard OKLab maths.
def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return c * 255


def to_oklch(h):
    import math
    r, g, b = (_lin(c) for c in hex_rgb(h))
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def from_oklch(L, C, H):
    """Back to hex; chroma is lowered until the colour fits in sRGB."""
    import math
    for _ in range(40):
        A, B = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
        l_ = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
        m_ = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
        s_ = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3
        rgb = (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
               -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
               -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)
        if all(-0.001 <= c <= 1.001 for c in rgb):
            return rgb_hex([_gam(max(0, min(1, c))) for c in rgb])
        C *= 0.94
    return rgb_hex([_gam(max(0, min(1, c))) for c in rgb])


# A brand colour is the client's: it is only touched when it would visibly fail. Fluorescent picks
# (very light and very saturated, like lime or neon cyan) glare as fills and vanish behind white type,
# so they are pulled down to a strong but printable version of the same hue. Ordinary brand reds,
# yellows and blues pass untouched.
NEON = {"accent": (0.82, 0.14, 0.74, 0.20), "accent2": (0.86, 0.14, 0.78, 0.18)}  # L above, C above -> new L, max C


def fit_color(h, role, bg="#FFFFFF"):
    """(colour, note). Neon brand colours are calmed keeping their hue; ink is darkened or lightened until
    it reads at 7:1 on bg. note is None when the colour is left as it was."""
    if not isinstance(h, str) or not re.fullmatch(r"#?[0-9A-Fa-f]{6}", h.strip()):
        return h, None
    h = "#" + h.strip().lstrip("#").upper()
    L, C, H = to_oklch(h)
    why = []
    if role in NEON:
        lmax, cmin, lnew, cnew = NEON[role]
        if L > lmax and C > cmin and not 70 <= H <= 115:  # yellows are light by nature and fine as they are
            why.append("荧光色，大面积用着刺眼，白字压在上面也看不清")
            L, C = lnew, min(C, cnew)
    elif role == "ink":
        step = 0
        while contrast(from_oklch(L, C, H), bg) < 7 and step < 40:
            L = L - 0.02 if luminance(bg) > 0.4 else L + 0.02
            step += 1
        if step:
            why.append("和底色对比不够，正文会看不清")
    if not why:
        return h, None
    out = from_oklch(L, C, H)
    return out, (None if out == h else "、".join(why))


def readable_on(bg, *cands):
    """Best text colour for background bg among candidates (falls back to black/white)."""
    pool = list(cands) + ["#FFFFFF", "#111111"]
    best = max(pool, key=lambda c: contrast(c, bg))
    for c in cands:  # prefer a brand colour when it is good enough
        if contrast(c, bg) >= 4.5:
            return c
    return best


def is_dark(h):
    return luminance(h) < 0.25


# ------------------------------------------------------------------ tokens
def festival_of(spec_fest):
    """spec.festival may be "spring-festival" or {"id": ..., "mode": "full"|"accent"}."""
    if not spec_fest:
        return None
    fid = spec_fest if isinstance(spec_fest, str) else spec_fest.get("id")
    fests = load_ref("festivals.json")
    if fid not in fests:
        raise SystemExit(f"unknown festival '{fid}'. Known: {', '.join(fests)}")
    f = json.loads(json.dumps(fests[fid]))
    f["_id"] = fid
    f["_mode"] = (spec_fest.get("mode") if isinstance(spec_fest, dict) else None) or f.get("mode", "full")
    return f


def spec_brand(spec):
    """The brand block with the spec's festival attached, as resolve_tokens expects it."""
    b = dict(spec.get("brand") or {})
    if spec.get("festival"):
        b["_festival"] = spec["festival"]
    return b


def resolve_tokens(brand):
    """Direction tokens + brand overrides + derived roles."""
    dirs = load_ref("directions.json")
    did = brand.get("direction") or "clean-minimal"
    if did not in dirs:
        raise SystemExit(f"unknown direction '{did}'. Known: {', '.join(dirs)}")
    d = json.loads(json.dumps(dirs[did]))
    t = dict(d["tokens"])
    fest = festival_of(brand.get("_festival"))
    if fest:
        if fest["_mode"] == "full":
            t.update(fest["tokens"])
        else:  # accent: keep the brand look, borrow the festival's second colour
            t["accent2"] = fest["tokens"]["accent2"] if fest["tokens"]["accent2"] != t["accent"] else fest["tokens"]["accent"]
        if fest.get("pattern") and fest["pattern"] != "none":
            d["pattern"] = fest["pattern"]
        d["festival"] = {"id": fest["_id"], "name": fest["name"], "mode": fest["_mode"], "motifs": fest.get("motifs", [])}
    notes = []
    for k, v in (brand.get("tokens") or {}).items():
        if not v:
            continue
        if not brand.get("exact_colors") and k in ("accent", "accent2", "ink"):
            fixed, why = fit_color(v, k, (brand.get("tokens") or {}).get("bg") or t["bg"])
            if why:
                notes.append({"role": k, "from": v.upper(), "to": fixed, "why": why})
                v = fixed
        t[k] = v
    t["on_accent"] = readable_on(t["accent"], t["ink"], t["surface"], t["bg"])
    light = max((t["surface"], t["bg"], "#FFFFFF"), key=luminance)
    if luminance(t["accent"]) < 0.4 and contrast(light, t["accent"]) >= 3.4:
        t["on_accent"] = light  # light text on a saturated fill reads cleaner; the accent is deepened below if needed
    # text sits on accent fills (stickers, tags, offer bands): nudge the accent until that text reads,
    # unless the user fixed the brand colour on purpose
    if "accent" not in (brand.get("tokens") or {}):
        step = 0
        while contrast(t["on_accent"], t["accent"]) < 4.5 and step < 12:
            toward = "#000000" if luminance(t["on_accent"]) > 0.5 else "#FFFFFF"
            t["accent"] = mix(t["accent"], toward, 0.04)
            step += 1
    t["on_accent2"] = readable_on(t["accent2"], t["ink"], t["surface"], t["bg"])
    t["on_ink"] = readable_on(t["ink"], t["bg"], t["surface"])
    t["line"] = mix(t["bg"], t["ink"], 0.18)
    t["soft"] = mix(t["bg"], t["accent"], 0.14)
    # small text in accent colour must still read on bg: darken until 4.5:1
    hl = t["accent"]
    step = 0
    target = "#000000" if not is_dark(t["bg"]) else "#FFFFFF"
    while contrast(hl, t["bg"]) < 4.5 and step < 20:
        hl = mix(hl, target, 0.06)
        step += 1
    t["accent_text"] = hl
    mu, step = t["muted"], 0  # secondary text must stay readable too
    while contrast(mu, t["bg"]) < 4.6 and step < 20:
        mu = mix(mu, t["ink"], 0.1)
        step += 1
    t["muted"] = mu
    for k in ("display", "body"):
        over = (brand.get("fonts") or {}).get(k)
        if over:
            d[k] = {**d[k], **(over if isinstance(over, dict) else {"font": over})}
    d["tokens"] = t
    d["id"] = did
    d["color_notes"] = notes
    return d


# ------------------------------------------------------------------ canvases
MM_PX = 96 / 25.4


def canvas(size_id):
    plats = load_ref("platforms.json")
    if size_id not in plats:
        m = re.fullmatch(r"(\d+)x(\d+)", size_id)
        if not m:
            raise SystemExit(f"unknown size '{size_id}'. Known: {', '.join(plats)} or WxH")
        w, h = int(m.group(1)), int(m.group(2))
        p = {"label": size_id, "w": w, "h": h, "kind": "screen", "safe": 0.06,
             "min_px": {"body": max(16, round(min(w, h) * 0.022)), "caption": max(12, round(min(w, h) * 0.017))}}
    else:
        p = dict(plats[size_id])
    p["bleed_px"] = 0
    if p["kind"] == "print":
        bleed = p.get("bleed_mm", 0)  # background runs past the trim line so cutting never leaves white edges
        p["page_mm"] = [p["mm"][0] + 2 * bleed, p["mm"][1] + 2 * bleed]
        p["w"] = round(p["page_mm"][0] * MM_PX, 2)
        p["h"] = round(p["page_mm"][1] * MM_PX, 2)
        p["bleed_px"] = bleed * MM_PX
        p["safe_px"] = (p["safe_mm"] + bleed) * MM_PX
        p["scale"] = 300 / 96
    else:
        p["safe_px"] = min(p["w"], p["h"]) * p["safe"]
        p["scale"] = 1
    p["id"] = size_id
    p["u"] = (min(p["w"], p["h"]) - 2 * p["bleed_px"]) / 100
    ar = p["w"] / p["h"]
    p["orient"] = "landscape" if ar > 1.25 else ("portrait" if ar < 0.85 else "square")
    p["ar"] = ar
    return p


def placeholder(s):
    """Text still waiting for a real fact, e.g. 【电话】."""
    return bool(s) and bool(re.search(r"【[^】]*】", str(s)))
