"""Shared helpers for luobo-design: paths, data files, colours, tokens, canvases."""
import html
import json
import re
from pathlib import Path

SKILL_VERSION = "0.10.1"
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
    t.update({k: v for k, v in (brand.get("tokens") or {}).items() if v})
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
