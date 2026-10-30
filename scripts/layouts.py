"""HTML layouts. One function per (item type, layout); each re-lays itself out per orientation.

Every visible text node carries class "t" plus
  data-role  headline | sub | body | caption | price | badge | label
  data-c     token name of its colour, data-on token name of what it sits on ("image" for photos)
so check.py can test size, contrast and safe zone without guessing.
Boxes marked data-fit shrink their font-size (data-max -> data-min px) until the text fits.
"""
import re

import art
from common import esc, placeholder, rgba, mix
from fonts import stack

LAYOUTS = {
    "poster": ["product-hero", "type-hero", "editorial", "photo-full", "notice"],
    "menu": ["list", "cards"],
}


class Ctx:
    def __init__(self, item, brand, direction, cv, facts):
        self.item, self.brand, self.d, self.cv, self.facts = item, brand, direction, cv, facts
        self.t = direction["tokens"]
        self.u = cv["u"]
        self.safe = cv["safe_px"]
        self.W, self.H = cv["w"], cv["h"]
        self.o = cv["orient"]
        self.minb = cv["min_px"]["body"]
        self.minc = cv["min_px"]["caption"]
        self.uid = item.get("_uid0", 0)  # h5 screens share one document, so their ids must not collide

    def px(self, n):
        return f"{n * self.u:.1f}px"

    def nid(self, p):
        self.uid += 1
        return f"{p}{self.uid}"


def rich(s):
    """esc + **emphasis** -> accent span."""
    out = esc(s)
    return re.sub(r"\*\*(.+?)\*\*", r'<em class="hl">\1</em>', out)


def plain(s):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", str(s or ""))


# characters a display font draws so oddly that people misread them (QingKe's 卜 reads as 八)
BAD_GLYPHS = {"qingke": "卜"}


def T(ctx, role, text, c="ink", on="bg", cls="", style="", fit=None, tag="div", nowrap=None, eid=None):
    """A text node. fit=(max_px, min_px) makes it a shrink-to-fit box."""
    if text is None or text == "":
        return ""
    eid = eid or ctx.nid(role[:2])
    attrs = [f'id="{eid}"', f'class="{("t " + role + " " + cls).strip()}"', f'data-role="{role}"',
             f'data-c="{c}"', f'data-on="{on}"']
    st = style
    if fit:
        attrs.append(f'data-fit="1" data-max="{fit[0]:.1f}" data-min="{fit[1]:.1f}"')
        st += f"font-size:{fit[0]:.1f}px;"
    if nowrap is None:
        nowrap = "\n" in str(text) and role == "headline"
    if nowrap:
        st += "white-space:nowrap;"
    if placeholder(text):
        attrs.append('data-placeholder="1"')
    bad = BAD_GLYPHS.get((ctx.d.get("display") or {}).get("font"), "")
    if bad and any(ch in str(text) for ch in bad) and ("d" in cls.split() or role == "headline"):
        st += f"font-family:{stack('sans')};font-weight:900;"  # this display font draws these characters wrong
    color = ctx.t.get(c, c)
    st = f"color:{color};" + st
    html = rich(text)
    name = esc((ctx.brand or {}).get("name") or "")
    if 2 <= len(name) <= 8 and name in html and role not in ("headline",):  # never break the brand name across lines
        html = html.replace(name, f'<span style="white-space:nowrap">{name}</span>')
    return f'<{tag} {" ".join(attrs)} style="{st}">{html}</{tag}>'


# ------------------------------------------------------------------ base page
def base_css(ctx, fonts_css):
    t, d, u = ctx.t, ctx.d, ctx.u
    disp, body = d["display"], d["body"]
    tex = d.get("texture", "none")
    tex_css = ""
    if tex in ("paper", "grain"):
        dark = luminance_dark(t["bg"])
        uri = art.noise_uri(fine=(tex == "grain"), opacity=0.55 if tex == "paper" else 0.7)
        blend = "screen" if dark else "multiply"
        op = 0.18 if tex == "paper" else (0.12 if dark else 0.22)
        if dark:
            uri = uri  # noise is black; screen on dark bg would vanish, use soft-light
            blend = "soft-light"
            op = 0.5
        tex_css = (f".texture{{position:absolute;inset:0;pointer-events:none;z-index:50;"
                   f"background-image:url('{uri}');background-size:300px 300px;mix-blend-mode:{blend};opacity:{op}}}")
    italic = "font-style:italic;" if disp.get("italic") else ""
    return f"""
{fonts_css}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{ctx.W}px;height:{ctx.H}px;overflow:hidden;background:{t['bg']}}}
body{{font-family:{stack(body['font'])};font-weight:{body.get('weight', 400)};color:{t['ink']};
  -webkit-font-smoothing:antialiased;line-break:strict;font-kerning:normal}}
.canvas{{position:relative;width:{ctx.W}px;height:{ctx.H}px;overflow:hidden;background:{t['bg']}}}
.pattern{{position:absolute;inset:0;z-index:0;{art.pattern_css(d.get('pattern', 'none'), t, u)}}}
{tex_css}
.d{{font-family:{stack(disp['font'])};font-weight:{disp.get('weight', 700)};letter-spacing:{disp.get('tracking', 0)}em;{italic}}}
.t{{position:relative;z-index:5}}
.headline{{line-height:1.18;text-wrap:balance}}
.sub{{line-height:1.45;text-wrap:balance}}
.body{{line-height:1.55;text-wrap:pretty}}
.caption{{line-height:1.45}}
[data-fit]{{overflow:hidden}}
em.hl{{font-style:normal;color:{t['accent_text'] if not luminance_dark(t['bg']) else t['accent']}}}
.on-accent em.hl{{color:inherit;text-decoration:underline;text-decoration-thickness:.08em;text-underline-offset:.15em}}
img{{display:block}}
"""


def luminance_dark(h):
    from common import is_dark
    return is_dark(h)


FIT_JS = """
<script>
window.__fitDone = false;
async function fitAll(){
  try { await document.fonts.ready; } catch(e) {}
  // data-justify: one line set so its ink spans the whole width of its parent (type-stack posters)
  for (const el of Array.from(document.querySelectorAll('[data-justify]'))) {
    el.style.whiteSpace = 'nowrap'; el.style.fontSize = '100px'; el.style.display = 'inline-block';
    const ps = getComputedStyle(el.parentElement);
    const inner = el.parentElement.clientWidth - parseFloat(ps.paddingLeft) - parseFloat(ps.paddingRight);
    const w = el.getBoundingClientRect().width, target = inner * (parseFloat(el.dataset.justify) || 1);
    if (w > 0) el.style.fontSize = (100 * target / w).toFixed(2) + 'px';
    const cap = parseFloat(el.dataset.capPx || 0); if (cap && parseFloat(el.style.fontSize) > cap) el.style.fontSize = cap + 'px';
  }
  // a wall of justified lines that came out too tall shrinks as a whole, keeping its proportions
  for (const wall of Array.from(document.querySelectorAll('[data-wall]'))) {
    const maxh = parseFloat(wall.dataset.wall), h = wall.scrollHeight;
    if (maxh && h > maxh) { const k = maxh / h * 0.99;
      wall.querySelectorAll('[data-justify]').forEach(el => { el.style.fontSize = (parseFloat(el.style.fontSize) * k).toFixed(2) + 'px'; }); }
  }
  const els = Array.from(document.querySelectorAll('[data-fit]'));
  // CJK fonts draw taller than a tight line-height, so allow a little ink overflow vertically;
  // .nw children (menu dish names) must never be clipped sideways
  const over = el => { const fs = parseFloat(el.style.fontSize) || 16;
    return el.scrollHeight > el.clientHeight + Math.max(2, fs * 0.16) || el.scrollWidth > el.clientWidth + 1
      || Array.from(el.querySelectorAll('.nw')).some(n => n.scrollWidth > n.clientWidth + 1)
      || (el.dataset.colsTry && (() => { const r = el.getBoundingClientRect();  // CSS columns spill sideways unseen
           return Array.from(el.children).some(c => { const b = c.getBoundingClientRect();
             return b.right > r.right + 1 || b.bottom > r.bottom + fs * 0.3; }); })()); };
  const shrink = (el, start, min) => { let f = start; el.style.fontSize = f + 'px';
    while (over(el) && f > min) { f = Math.max(min, f * 0.96); el.style.fontSize = f + 'px'; } return f; };
  for (let pass = 0; pass < 2; pass++) {
    for (const el of els) {
      const max = parseFloat(el.dataset.max), min = parseFloat(el.dataset.min);
      if (el.dataset.colsTry && pass === 0) {
        // menus: try each column count, keep the one that allows the biggest type
        let best = null;
        for (const n of el.dataset.colsTry.split(',')) {
          el.style.columnCount = n; const f = shrink(el, max, min); const ok = !over(el);
          if (!best || (ok && !best.ok) || (ok === best.ok && f > best.f + 0.5)) best = {n, f, ok};
        }
        el.style.columnCount = best.n; el.style.fontSize = best.f + 'px';
        // spare height left over: open up the rows so the list fills the page evenly
        if (!over(el)) { let p = 0.42;
          while (p < 0.95) { el.style.setProperty('--rowpad', (p + 0.04) + 'em');
            if (over(el)) { el.style.setProperty('--rowpad', p + 'em'); break; } p += 0.04; } }
      } else {
        shrink(el, pass === 0 ? max : parseFloat(el.style.fontSize), min);
      }
    }
    try { await document.fonts.ready; } catch(e) {}
  }
  // short copy on a tall page: scale a marked block's type up (data-grow = largest factor)
  // until its column would overflow, so the page does not end in a big empty band
  for (const g of Array.from(document.querySelectorAll('[data-grow]'))) {
    const box = g.closest('[data-grow-box]') || g.parentElement;
    const kids = [g, ...g.querySelectorAll('*')].filter(n => n.style && n.style.fontSize);
    const base = kids.map(n => parseFloat(n.style.fontSize));
    const fits = Array.from(g.querySelectorAll('[data-fit]'));
    const bad = () => box.scrollHeight > box.clientHeight + 1 || fits.some(over)
      || [g, ...g.querySelectorAll('.t')].some(n => n.scrollWidth > n.clientWidth + 1);
    const set = k => kids.forEach((n, i) => { n.style.fontSize = (base[i] * k) + 'px'; });
    const top = parseFloat(g.dataset.grow) || 1.3; let k = 1;
    const pb = box.style.paddingBottom; box.style.paddingBottom = (parseFloat(g.dataset.keep) || 0) + 'px';  // leave some air
    if (!bad()) {
      while (k < top) { const nk = Math.min(top, k + 0.03); set(nk); if (bad()) { set(k); break; } k = nk; }
    }
    box.style.paddingBottom = pb; g.dataset.grown = k.toFixed(2);
  }
  window.__fit = els.map(el => ({id: el.id, fs: parseFloat(el.style.fontSize), min: parseFloat(el.dataset.min),
                                  max: parseFloat(el.dataset.max), overflow: over(el), cols: el.style.columnCount || null}));
  window.__fitDone = true;
}
window.addEventListener('load', fitAll);
</script>
"""


def page(ctx, fonts_css, body, css):
    tex = '<div class="texture"></div>' if ctx.d.get("texture") in ("paper", "grain") else ""
    pg = (f"@page{{size:{ctx.cv['mm'][0]}mm {ctx.cv['mm'][1]}mm;margin:0}}" if ctx.cv["kind"] == "print" else "")
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{pg}{base_css(ctx, fonts_css)}
{css}</style></head>
<body><div class="canvas" id="canvas"><div class="pattern"></div>{body}{tex}</div>{FIT_JS}</body></html>"""


# ------------------------------------------------------------------ shared parts
def brand_mark(ctx, size_u, on="bg"):
    b = ctx.brand
    if b.get("logo"):
        return (f'<img class="logo" src="{b["logo"]}" style="height:{ctx.px(size_u * 1.6)};width:auto" '
                f'data-role="logo">')
    if not b.get("name"):
        return ""
    c = "ink" if on in ("bg", "surface") else ("on_accent" if on == "accent" else "ink")
    return T(ctx, "label", b["name"], c=c, on=on, cls="d brand",
             style=f"font-size:{max(size_u * ctx.u, ctx.minb):.1f}px;line-height:1.1;white-space:nowrap;")


def badge(ctx, offer, size_u):
    """Offer sticker. Style follows the direction's deco."""
    if not offer or not offer.get("big"):
        return ""
    t, u = ctx.t, ctx.u
    deco = ctx.d["shape"].get("deco", "sticker")
    big, small = offer.get("big"), offer.get("small")
    if "\n" not in big and len(plain(big)) > 4:  # two balanced lines read bigger than one long one
        k = (len(big) + 1) // 2
        big = big[:k] + "\n" + big[k:]
    s = size_u * u
    inner = (T(ctx, "badge", big, c="on_accent", on="accent", cls="d on-accent",
               style=f"line-height:1.1;text-align:center;width:100%;max-height:{s * 0.46:.1f}px;flex:none;",
               fit=(s * 0.21, ctx.minb), eid=ctx.nid("bgb"), nowrap=True)
             + T(ctx, "caption", small, c="on_accent", on="accent", nowrap=len(plain(small or "")) <= 9,
                 style=f"line-height:1.25;text-align:center;width:100%;max-height:{s * 0.22:.1f}px;margin-top:{s * 0.03:.1f}px;flex:none;text-wrap:balance;",
                 fit=(max(ctx.minc, s * 0.085), ctx.minc)))
    base = (f"width:{s:.1f}px;height:{s:.1f}px;display:flex;flex-direction:column;align-items:center;"
            f"justify-content:center;padding:{s * 0.16:.1f}px;background:{t['accent']};")
    if deco == "sticker":
        shape = f"clip-path:{art.starburst_polygon(18, 0.88)};transform:rotate(-10deg);"
    elif deco == "seal":
        shape = (f"border-radius:{s * 0.06:.1f}px;box-shadow:inset 0 0 0 {s * 0.025:.1f}px {t['accent']},"
                 f"inset 0 0 0 {s * 0.04:.1f}px {t['on_accent']};")
    elif deco == "soft":
        shape = "border-radius:50%;"
    else:  # line
        shape = f"border-radius:50%;box-shadow:0 0 0 {s * 0.02:.1f}px {t['bg']},0 0 0 {s * 0.03:.1f}px {t['accent']};"
    # data-grp: texts inside one rotated sticker are laid out together; their tilted boxes may touch
    return f'<div class="badge on-accent" data-grp="{ctx.nid("grp")}" style="{base}{shape}">{inner}</div>'


def details_block(ctx, details, on="surface", cols=1, size=None):
    if not details:
        return ""
    fs = size or max(ctx.minb, 2.5 * ctx.u)
    rows = []
    for d in details:
        k, v = d.get("k") or d.get("label", ""), d.get("v") or d.get("value", "")
        rows.append(f'<div class="drow" style="display:flex;gap:{ctx.px(1.4)};align-items:baseline;">'
                    + T(ctx, "caption", k, c="accent_text" if on != "accent" else "on_accent", on=on,
                        style=f"font-size:{max(ctx.minc, fs * 0.82):.1f}px;font-weight:700;white-space:nowrap;letter-spacing:.06em;")
                    + T(ctx, "body", v, c="ink" if on != "accent" else "on_accent", on=on,
                        style=f"font-size:{fs:.1f}px;line-height:1.4;")
                    + "</div>")
    grid = f"display:grid;grid-template-columns:repeat({cols},1fr);gap:{ctx.px(1.1)} {ctx.px(3)};"
    return f'<div class="details" style="{grid}">{"".join(rows)}</div>'


def qr_block(ctx, qr, size_u, on="surface"):
    if not qr:
        return ""
    s = ctx.px(size_u)
    muted = "#FFFFFF" if on == "image" else ctx.t["muted"]
    if qr.get("src"):
        img = f'<img src="{qr["src"]}" style="width:{s};height:{s};object-fit:contain;background:#fff;padding:{ctx.px(0.6)};border-radius:{ctx.px(0.8)}">'
    else:
        img = (f'<div class="t caption" data-role="caption" data-c="muted" data-on="{on}" data-placeholder="1" '
               f'style="width:{s};height:{s};border:{ctx.px(0.3)} dashed {muted};border-radius:{ctx.px(0.8)};'
               f'display:flex;align-items:center;justify-content:center;font-size:{max(ctx.minc, 1.8 * ctx.u):.1f}px;white-space:nowrap;'
               f'color:{muted}">【二维码】</div>')
    lab = T(ctx, "caption", qr.get("label"), c=("#FFFFFF" if on == "image" else "muted") if on != "accent" else "on_accent", on=on,
            style=f"font-size:{max(ctx.minc, 1.8 * ctx.u):.1f}px;text-align:center;margin-top:{ctx.px(0.6)};white-space:nowrap;")
    return f'<div class="qr" style="display:flex;flex-direction:column;align-items:center;flex:none">{img}{lab}</div>'


def art_on_fill(ctx, a):
    """Motif drawn on an accent-coloured panel: its accent parts switch colour so they stay visible."""
    from common import contrast
    a = a or {}
    if a.get("image") or not a.get("motif"):
        return art_block(ctx, a)
    t = dict(ctx.t)
    t["accent"] = ctx.t["accent2"] if contrast(ctx.t["accent2"], ctx.t["accent"]) > 1.8 else ctx.t["surface"]
    t["on_accent"] = readable_on_local(t["accent"], ctx.t)
    return f'<div class="art motif" style="width:100%;height:100%">{art.motif(a["motif"], t, ctx.nid("mf"), a.get("drink"))}</div>'


def readable_on_local(bg, t):
    from common import readable_on
    return readable_on(bg, t["ink"], t["surface"])


def art_block(ctx, a, mode="contain", radius_u=0):
    """Product image (AI) or procedural motif. Fills its parent box."""
    a = a or {}
    if a.get("image"):
        fit = a.get("image_fit", mode)
        r = f"border-radius:{ctx.px(radius_u)};" if radius_u else ""
        return (f'<img class="art" src="{a["image"]}" data-role="image" '
                f'style="width:100%;height:100%;object-fit:{fit};{r}">')
    name = a.get("motif") or "gift"
    draw = art.motif(name, ctx.t, ctx.nid("m"), a.get("drink"))
    st = a.get("style")
    if st and st != "flat":  # any layout can take an art style for its drawing
        import artstyle
        if st in artstyle.STYLES:
            uid = ctx.nid("st")
            extra = artstyle.css(st, ctx.t, uid)
            return (artstyle.defs(st, ctx.t, uid) + (f"<style>{extra}</style>" if extra else "")
                    + f'<div class="art motif" style="position:relative;width:100%;height:100%">{artstyle.dress(st, draw, ctx.t, uid)}</div>')
    return f'<div class="art motif" style="width:100%;height:100%">{draw}</div>'


def sparkles(ctx, spots):
    out = []
    for x, y, s, c in spots:
        out.append(f'<div style="position:absolute;left:{x}%;top:{y}%;width:{ctx.px(s)};height:{ctx.px(s)};z-index:3">'
                   f'{art.sparkle(ctx.t.get(c, c), "100%")}</div>')
    return "".join(out)


def product_stage(ctx, offer, bsize_u):
    """Square 'disc' centred in the free space: rays, a plate, the product, the offer sticker on its shoulder.
    Uses container query units so the disc is always round whatever box it lands in."""
    t = ctx.t
    a = ctx.item.get("art") or {}
    cover = bool(a.get("image")) and a.get("image_fit") == "cover"
    rays = ("" if cover else
            f'<div style="position:absolute;inset:-18%;border-radius:50%;'
            f'background:repeating-conic-gradient(from 0deg, {rgba(t["surface"], .5)} 0deg 7deg, transparent 7deg 14deg);'
            f'-webkit-mask:radial-gradient(circle, #000 30%, transparent 68%);mask:radial-gradient(circle, #000 30%, transparent 68%)"></div>'
            f'<div style="position:absolute;inset:6%;border-radius:50%;background:{t["surface"]};opacity:.92"></div>')
    prod = (f'<div style="position:absolute;inset:{"0" if cover else "8% 12% 4%"};z-index:2">'
            + art_block(ctx, a, radius_u=ctx.d["shape"]["radius"]) + "</div>")
    b = badge(ctx, offer, bsize_u)
    # a photo cut-out usually has its face or most telling part at the top, so the sticker goes low
    pos = (offer or {}).get("pos") or ("bottom-right" if a.get("image") and not cover else "top-right")
    spot = {"top-right": "right:-4%;top:-2%", "bottom-right": "right:-4%;bottom:4%",
            "top-left": "left:-4%;top:-2%", "bottom-left": "left:-4%;bottom:4%"}.get(pos, "right:-4%;top:-2%")
    disc = (f'<div class="disc" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);'
            f'width:min(100cqw,100cqh);aspect-ratio:1">{rays}{prod}'
            f'<div style="position:absolute;{spot};z-index:6">{b}</div></div>')
    return (f'<div class="stage" style="position:relative;flex:1 1 auto;min-height:0;min-width:0;container-type:size">{disc}'
            + sparkles(ctx, [(6, 18, 4.2, "accent2"), (12, 74, 2.6, "accent"), (86, 82, 3.2, "accent2")])
            + "</div>")


# ------------------------------------------------------------------ poster: product-hero
def poster_product_hero(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    head_max = {"portrait": 12.5, "square": 10.5, "landscape": 11}[o] * u
    if ctx.cv["ar"] < 0.6:
        head_max = 13.5 * u
    top = (f'<div class="top" style="display:flex;justify-content:space-between;align-items:center;gap:{ctx.px(2)}">'
           + brand_mark(ctx, 3.4)
           + T(ctx, "label", c.get("kicker"), c="on_ink", on="ink",
               style=f"background:{t['ink']};padding:{ctx.px(0.7)} {ctx.px(1.8)};border-radius:{ctx.px(4)};"
                     f"font-size:{max(ctx.minc, 2 * u):.1f}px;font-weight:700;letter-spacing:.12em;white-space:nowrap;")
           + "</div>")
    headline = T(ctx, "headline", c.get("headline"), cls="d", fit=(head_max, max(ctx.minb * 1.6, 4.5 * u)),
                 style="max-height:100%;")
    sub = T(ctx, "sub", c.get("sub"), c="muted", fit=(3.3 * u, ctx.minb),
            style=f"margin-top:{ctx.px(1.6)};max-height:{ctx.px(9)};")
    stage = product_stage(ctx, c.get("offer"), {"portrait": 25, "square": 21, "landscape": 26}[o])
    info_inner = (f'<div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:{ctx.px(1.4)}">'
                  + details_block(ctx, c.get("details"), on="surface")
                  + T(ctx, "body", c.get("cta"), c="accent_text", on="surface",
                      style=f"font-size:{max(ctx.minb, 2.7 * u):.1f}px;font-weight:700;")
                  + "</div>" + qr_block(ctx, c.get("qr"), 13 if o != "landscape" else 12))
    r = ctx.px(ctx.d["shape"]["radius"])
    bw = ctx.d["shape"].get("border", 0.3)
    info = (f'<div class="info" style="position:relative;z-index:5;background:{t["surface"]};border-radius:{r};'
            f'border:{ctx.px(bw)} solid {t["ink"] if ctx.d["shape"].get("deco") == "sticker" else t["line"]};'
            f'padding:{ctx.px(2.6)} {ctx.px(3)};display:flex;gap:{ctx.px(3)};align-items:center">{info_inner}</div>')
    if not (c.get("details") or c.get("cta") or c.get("qr")):
        info = ""  # nothing to say: an empty card reads as a broken input box
    if o == "landscape":
        body = (f'<div style="position:absolute;inset:{pad:.1f}px;display:grid;grid-template-columns:1.08fr 1fr;gap:{ctx.px(4)}">'
                f'<div style="display:flex;flex-direction:column;min-height:0;gap:{ctx.px(2.4)}">{top}'
                f'<div style="flex:1 1 auto;min-height:0;display:flex;flex-direction:column;justify-content:center">'
                f'<div style="height:{ctx.px(34)}">{headline}</div>{sub}</div>{info}</div>'
                f'<div style="display:flex;flex-direction:column;min-height:0">{stage}</div></div>')
    elif o == "square":
        body = (f'<div style="position:absolute;inset:{pad:.1f}px;display:flex;flex-direction:column;gap:{ctx.px(2.4)}">{top}'
                f'<div style="flex:1 1 auto;min-height:0;display:grid;grid-template-columns:1fr 1fr;gap:{ctx.px(2)}">'
                f'<div style="display:flex;flex-direction:column;justify-content:center;min-height:0">'
                f'<div style="height:{ctx.px(30)}">{headline}</div>{sub}</div>'
                f'<div style="display:flex;flex-direction:column;min-height:0">{stage}</div></div>{info}</div>')
    else:
        hh = 25 if ctx.cv["ar"] > 0.6 else 34
        body = (f'<div style="position:absolute;inset:{pad:.1f}px;display:flex;flex-direction:column;gap:{ctx.px(2.4)}">{top}'
                f'<div style="height:{ctx.px(hh)};margin-top:{ctx.px(1.5)}">{headline}</div>{sub}{stage}{info}</div>')
    return page(ctx, fonts_css, body, "")


# ------------------------------------------------------------------ poster: type-hero
def poster_type_hero(ctx, fonts_css):
    """Big type first. The product sits in the free middle band, never under text."""
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    a = ctx.item.get("art") or {}
    offer = c.get("offer") or {}
    head_max = {"portrait": 15.5, "square": 10.5, "landscape": 14}[o] * u
    kicker = T(ctx, "label", c.get("kicker"), c="accent_text", on="bg",
               style=f"font-size:{max(ctx.minc, 2.3 * u):.1f}px;font-weight:700;letter-spacing:.2em;white-space:nowrap;")
    hmax = {"portrait": 40, "square": 28, "landscape": 40}[o] if ctx.cv["ar"] > 0.6 else 46
    headline = T(ctx, "headline", c.get("headline"), cls="d", fit=(head_max, max(ctx.minb * 1.6, 5 * u)),
                 style=f"max-height:{ctx.px(hmax)};")
    sub = T(ctx, "sub", c.get("sub"), c="muted", fit=(3.3 * u, ctx.minb),
            style=f"max-height:{ctx.px(9)};{'max-width:60%;' if o != 'landscape' else ''}")
    r = ctx.px(ctx.d["shape"]["radius"])
    offer_band = ""
    if offer.get("big"):
        offer_band = (f'<div class="offer on-accent" style="position:relative;z-index:4;background:{t["accent"]};border-radius:{r};'
                      f'padding:{ctx.px(2)} {ctx.px(3)};display:flex;align-items:center;gap:{ctx.px(3)};justify-content:space-between">'
                      + T(ctx, "badge", offer.get("big"), c="on_accent", on="accent", cls="d on-accent", nowrap=True,
                          fit=(8.5 * u, ctx.minb * 1.4), style=f"flex:1 1 auto;min-width:0;max-height:{ctx.px(11)};line-height:1.15;")
                      + T(ctx, "caption", offer.get("small"), c="on_accent", on="accent",
                          style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;flex:none;max-width:40%;text-align:right;")
                      + "</div>")
    lift = 0 if o == "landscape" else 9
    motif = (f'<div style="flex:1 1 auto;min-height:{ctx.px(24 if o != "square" else 22)};position:relative;z-index:2;'
             f'margin:{ctx.px(-lift)} 0 {ctx.px(-lift * 0.7)}">'
             f'<div style="position:absolute;inset:0;display:flex;justify-content:flex-end">'
             f'<div style="height:100%;aspect-ratio:.85;transform:rotate(6deg)">{art_block(ctx, a)}</div></div>'
             + sparkles(ctx, [(44, 20, 3.6, "accent2"), (58, 78, 2.4, "accent")]) + "</div>")
    info = (f'<div style="display:flex;gap:{ctx.px(3)};align-items:flex-end;position:relative;z-index:5">'
            f'<div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:{ctx.px(1.2)}">'
            + details_block(ctx, c.get("details"), on="bg")
            + T(ctx, "body", c.get("cta"), c="ink", on="bg", style=f"font-size:{max(ctx.minb, 2.6 * u):.1f}px;font-weight:700;")
            + "</div>" + qr_block(ctx, c.get("qr"), 12, on="bg") + "</div>")
    top = (f'<div style="display:flex;justify-content:space-between;align-items:center;gap:{ctx.px(2)}">'
           f'{brand_mark(ctx, 3.2)}{kicker}</div>')
    if o == "landscape":
        body = (f'<div style="position:absolute;inset:{pad:.1f}px;display:grid;grid-template-columns:1.3fr 1fr;gap:{ctx.px(5)}">'
                f'<div style="display:flex;flex-direction:column;gap:{ctx.px(2.2)};min-height:0;justify-content:center">'
                f'{top}<div style="height:{ctx.px(2)}"></div>{headline}{sub}<div style="height:{ctx.px(1)}"></div>{offer_band}</div>'
                f'<div style="display:flex;flex-direction:column;min-height:0">{motif}{info}</div></div>')
    else:
        body = (f'<div style="position:absolute;inset:{pad:.1f}px;display:flex;flex-direction:column;gap:{ctx.px(2)}">'
                f'{top}<div style="height:{ctx.px(1.5)}"></div>{headline}{sub}{motif}{offer_band}{info}</div>')
    return page(ctx, fonts_css, body, "")


# ------------------------------------------------------------------ poster: editorial
def editorial_offer(ctx, offer):
    """The offer as a quiet centred line pair: no sticker, the accent colour does the shouting."""
    if not offer or not offer.get("big"):
        return ""
    u = ctx.u
    return (f'<div style="display:flex;flex-direction:column;align-items:center;margin-top:{ctx.px(2.2)};flex:none">'
            + T(ctx, "badge", offer["big"].replace("\n", ""), c="accent_text", cls="d", nowrap=True,
                style=f"font-size:{ctx.px(6.2)};line-height:1.1;letter-spacing:.06em;")
            + T(ctx, "caption", offer.get("small"), c="muted",
                style=f"font-size:{max(ctx.minc, 2 * u):.1f}px;letter-spacing:.12em;margin-top:{ctx.px(0.6)};")
            + "</div>")


def poster_editorial(ctx, fonts_css):
    """Framed, centred, quiet. Good for talks, invitations, premium brands."""
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    a = ctx.item.get("art") or {}
    has_art = bool(a.get("motif") or a.get("image"))
    frame = (f'<div style="position:absolute;inset:{pad * 0.55:.1f}px;border:{ctx.px(0.25)} solid {t["ink"]};z-index:1"></div>'
             f'<div style="position:absolute;inset:{pad * 0.55 + 0.9 * u:.1f}px;border:{ctx.px(0.12)} solid {t["line"]};z-index:1"></div>')
    rule = f'<div style="width:{ctx.px(10)};height:{ctx.px(0.3)};background:{t["accent"]};margin:{ctx.px(2)} auto;flex:none"></div>'
    big = c.get("big_number")  # e.g. "10.18"
    tall = ctx.cv["ar"] < 0.6  # phone-screen posters have height to spare: bigger headline
    head_max = ({"portrait": 10, "square": 8.5, "landscape": 9}[o] + (2.5 if tall else 0)) * u
    hmax = {"portrait": 28, "square": 18, "landscape": 24}[o] + (8 if tall else 0)
    headline = T(ctx, "headline", c.get("headline"), cls="d", fit=(head_max, max(ctx.minb * 1.5, 4 * u)),
                 style=f"max-height:{ctx.px(hmax)};text-align:center;width:100%;flex:none;")
    art_flex = (f'<div style="flex:1 1 auto;min-height:{ctx.px(8)};width:100%;position:relative;margin:{ctx.px(2)} 0">'
                f'<div style="position:absolute;inset:0">{art_block(ctx, a)}</div></div>') if has_art else '<div style="flex:1 1 auto"></div>'
    det = c.get("details") or []
    det_html = "".join(
        f'<div style="display:flex;gap:{ctx.px(1.2)};align-items:baseline">'
        + T(ctx, "caption", d.get("k"), c="muted", style=f"font-size:{max(ctx.minc, 2 * u):.1f}px;letter-spacing:.1em;white-space:nowrap;")
        + T(ctx, "body", d.get("v"), style=f"font-size:{max(ctx.minb, 2.4 * u):.1f}px;")
        + "</div>" for d in det)
    foot = (f'<div style="display:flex;gap:{ctx.px(3)};align-items:center;justify-content:center;flex:none;margin-top:{ctx.px(1.5)}">'
            f'<div style="display:flex;flex-direction:column;gap:{ctx.px(0.6)}">{det_html}'
            + T(ctx, "body", c.get("cta"), c="accent_text", style=f"font-size:{max(ctx.minb, 2.5 * u):.1f}px;font-weight:700;margin-top:{ctx.px(0.6)};")
            + "</div>" + qr_block(ctx, c.get("qr"), 10.5, on="bg") + "</div>")
    head_parts = (brand_mark(ctx, 2.8)
                  + T(ctx, "label", c.get("kicker"), c="accent_text", style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;letter-spacing:.32em;margin-top:{ctx.px(1.6)};font-weight:700;"))
    text_parts = (headline + rule
                  + T(ctx, "sub", c.get("sub"), c="muted", fit=(3 * u, ctx.minb), style=f"max-height:{ctx.px(9)};text-align:center;width:86%;flex:none;")
                  + (T(ctx, "headline", big, c="accent_text", cls="d", style=f"font-size:{ctx.px(8)};line-height:1;margin-top:{ctx.px(2.4)};letter-spacing:.04em;")
                     if big else editorial_offer(ctx, c.get("offer"))))
    inset = pad + 1.8 * u
    col = "display:flex;flex-direction:column;align-items:center;"
    if o == "landscape" and has_art:
        body = (f'{frame}<div style="position:absolute;inset:{inset:.1f}px;display:grid;grid-template-columns:1fr 1.5fr;gap:{ctx.px(4)}">'
                f'<div style="position:relative">{art_block(ctx, a)}</div>'
                f'<div style="{col}justify-content:center">{head_parts}<div style="height:{ctx.px(3)}"></div>{text_parts}{foot}</div></div>')
    else:
        body = (f'{frame}<div style="position:absolute;inset:{inset:.1f}px;{col}">'
                f'{head_parts}{art_flex}{text_parts}{foot}</div>')
    return page(ctx, fonts_css, body, "")

# ------------------------------------------------------------------ poster: photo-full
def poster_photo_full(ctx, fonts_css):
    a = ctx.item.get("art") or {}
    if not a.get("image"):
        return poster_product_hero(ctx, fonts_css)  # no photo -> product stage instead
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    scrim_c = mix(t["ink"], "#000000", .35) if not luminance_dark(t["ink"]) else t["ink"]
    if luminance_dark(t["bg"]):
        scrim_c = t["bg"]
    photo = (f'<img src="{a["image"]}" data-role="image" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:1">'
             f'<div style="position:absolute;inset:0;z-index:2;background:linear-gradient(to top, {rgba(scrim_c, .92)} 0%, '
             f'{rgba(scrim_c, .75)} 32%, {rgba(scrim_c, 0)} 62%)"></div>')
    light = "#FFFFFF"
    head_max = {"portrait": 11, "square": 9.5, "landscape": 10}[o] * u
    block = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;bottom:{pad:.0f}px;z-index:5;display:flex;flex-direction:column;gap:{ctx.px(1.6)}">'
             + T(ctx, "label", c.get("kicker"), c=t["accent"], on="image", style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;letter-spacing:.18em;font-weight:700;")
             + f'<div style="height:{ctx.px(24 if o != "landscape" else 22)};width:{"100%" if o != "landscape" else "62%"}">'
             + T(ctx, "headline", c.get("headline"), c=light, on="image", cls="d", fit=(head_max, 5 * u), style="height:100%;display:flex;align-items:flex-end;")
             + "</div>"
             + T(ctx, "sub", c.get("sub"), c=light, on="image", style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;opacity:.92;")
             + f'<div style="display:flex;gap:{ctx.px(3)};align-items:flex-end;margin-top:{ctx.px(1)}">'
             + f'<div style="flex:1 1 auto">' + "".join(
                 f'<div style="display:flex;gap:{ctx.px(1.2)}">'
                 + T(ctx, "caption", d.get("k"), c=t["accent"], on="image", style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;font-weight:700;")
                 + T(ctx, "body", d.get("v"), c=light, on="image", style=f"font-size:{max(ctx.minb, 2.5 * u):.1f}px;")
                 + "</div>" for d in (c.get("details") or []))
             + T(ctx, "body", c.get("cta"), c=t["accent"], on="image",
                 style=f"font-size:{max(ctx.minb, 2.6 * u):.1f}px;font-weight:700;margin-top:{ctx.px(0.8)};")
             + "</div>" + qr_block(ctx, c.get("qr"), 11, on="image") + "</div></div>")
    top = (f'<div style="position:absolute;left:{pad:.0f}px;top:{pad:.0f}px;z-index:5">'
           + brand_mark(ctx, 3.2, on="image").replace(f'color:{t["ink"]}', "color:#FFFFFF") + "</div>"
           + f'<div style="position:absolute;right:{pad:.0f}px;top:{pad * 1.2:.0f}px;z-index:6">'
           + badge(ctx, c.get("offer"), 22) + "</div>")
    return page(ctx, fonts_css, photo + top + block, "")


# ------------------------------------------------------------------ poster: notice
def _is_salutation(p):
    """'尊敬的各位业主：' opens a letter and sits flush left; every other paragraph is indented."""
    p = p.strip()
    return len(p) <= 20 and p.endswith(("：", ":"))


def poster_notice(ctx, fonts_css):
    """Notices: water cuts, holiday hours, meetings. A strong header, the key facts in a box, then the text."""
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    a = ctx.item.get("art") or {}
    has_art = bool(a.get("motif") or a.get("image"))
    org = c.get("org") or ctx.brand.get("name")
    kicker = c.get("kicker") or "通知"
    kick = T(ctx, "headline", " ".join(kicker) if len(kicker) <= 4 else kicker, c="on_accent", on="accent", cls="d",
             style=f"font-size:{ctx.px(7.5 if o != 'landscape' else 7)};line-height:1;white-space:nowrap;letter-spacing:.1em;")
    org_t = T(ctx, "label", org, c="on_accent", on="accent",
              style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;letter-spacing:.12em;margin-top:{ctx.px(1.2)};opacity:.92;white-space:nowrap;")
    headline = T(ctx, "headline", c.get("headline"), cls="d", fit=({"portrait": 8, "square": 7, "landscape": 7}[o] * u, max(ctx.minb * 1.4, 4 * u)),
                 style=f"max-height:{ctx.px(22)};flex:none;")
    det = c.get("details") or []
    rows = "".join(
        f'<div style="display:flex;gap:{ctx.px(2)};align-items:baseline">'
        + T(ctx, "caption", d.get("k"), c="accent_text", on="surface",
            style=f"font-size:{max(ctx.minc, 2.3 * u):.1f}px;font-weight:700;white-space:nowrap;min-width:4.2em;letter-spacing:.08em;")
        + T(ctx, "body", d.get("v"), on="surface", style=f"font-size:{max(ctx.minb, 2.9 * u):.1f}px;font-weight:700;line-height:1.4;")
        + "</div>" for d in det)
    box = (f'<div style="background:{t["surface"]};border:{ctx.px(0.25)} solid {t["line"]};border-top:{ctx.px(0.8)} solid {t["accent"]};'
           f'border-radius:{ctx.px(ctx.d["shape"]["radius"] * 0.5)};padding:{ctx.px(2.4)} {ctx.px(3)};display:flex;flex-direction:column;gap:{ctx.px(1.2)};flex:none">{rows}</div>'
           if rows else "")
    body_txt = c.get("body") or ""
    paras = [p for p in str(body_txt).split("\n\n") if p.strip()] if body_txt else []
    body = ""
    if paras:
        inner = "".join(f'<p style="text-indent:{0 if _is_salutation(p) else 2}em;margin:0 0 .6em">{rich(p)}</p>' for p in paras)
        body = (f'<div id="noticebody" class="t body" data-role="body" data-c="ink" data-on="bg" data-fit="1" '
                f'data-max="{max(ctx.minb, (3 if o == "landscape" else 3.7) * u):.1f}" data-min="{ctx.minb:.1f}" '
                f'style="color:{t["ink"]};font-size:{max(ctx.minb, 3 * u):.1f}px;line-height:1.75;flex:1 1 auto;min-height:0;overflow:hidden;text-align:justify">{inner}</div>')
    foot = (f'<div style="display:flex;align-items:flex-end;gap:{ctx.px(3)};flex:none;margin-top:{ctx.px(1.5)}">'
            f'<div style="flex:1 1 auto;min-width:0">'
            + T(ctx, "body", c.get("cta"), c="accent_text", style=f"font-size:{max(ctx.minb, 2.5 * u):.1f}px;font-weight:700;")
            + "</div>" + qr_block(ctx, c.get("qr"), 10, on="bg")
            + f'<div style="flex:none;text-align:right">'
            + T(ctx, "body", c.get("issuer") or org, style=f"font-size:{max(ctx.minb, 2.6 * u):.1f}px;font-weight:700;white-space:nowrap;")
            + T(ctx, "caption", c.get("date_line"), c="muted", style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;margin-top:{ctx.px(0.5)};white-space:nowrap;")
            + "</div></div>")
    motif = (f'<div style="width:{ctx.px(15)};height:{ctx.px(13)};flex:none;position:relative">{art_on_fill(ctx, a)}</div>' if has_art else "")

    def mid(gap):  # facts box and text grow together while the text still has room
        return (f'<div data-grow="1.25" data-keep="{2 * u:.0f}" style="display:flex;flex-direction:column;gap:{ctx.px(gap)};'
                f'flex:1 1 auto;min-height:0">{box}{body}</div>')
    if o == "landscape":
        band = (f'<div style="position:absolute;left:0;top:0;bottom:0;width:28%;background:{t["accent"]};z-index:1"></div>'
                f'<div style="position:absolute;left:{pad:.1f}px;top:{pad:.1f}px;bottom:{pad:.1f}px;width:calc(28% - {pad * 1.6:.1f}px);'
                f'display:flex;flex-direction:column;justify-content:space-between;z-index:3"><div>{kick}{org_t}</div>{motif}</div>')
        html = (band + f'<div style="position:absolute;left:calc(28% + {pad:.1f}px);right:{pad:.1f}px;top:{pad:.1f}px;bottom:{pad:.1f}px;'
                f'display:flex;flex-direction:column;gap:{ctx.px(2)};z-index:3" data-grow-box="1">{headline}{mid(2)}{foot}</div>')
    else:
        bh = 15 if o != "square" else 13
        band = (f'<div style="position:absolute;left:0;right:0;top:0;height:{bh * u + pad:.1f}px;background:{t["accent"]};z-index:1"></div>'
                f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:{pad * 0.9:.1f}px;height:{bh * u:.1f}px;'
                f'display:flex;justify-content:space-between;align-items:center;z-index:3"><div>{kick}{org_t}</div>{motif}</div>')
        html = (band + f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:{bh * u + pad * 1.8:.1f}px;bottom:{pad:.1f}px;'
                f'display:flex;flex-direction:column;gap:{ctx.px(2.2)};z-index:3" data-grow-box="1">{headline}{mid(2.2)}{foot}</div>')
    return page(ctx, fonts_css, html, ".pattern{opacity:.5}#noticebody p:last-child{margin-bottom:0}")


# ------------------------------------------------------------------ menu
def _menu_item(ctx, it, fs, on):
    t = ctx.t
    tag = it.get("tag")
    tag_html = (f'<span class="t label" data-role="label" data-c="on_accent" data-on="accent" '
                f'style="background:{t["accent"]};color:{t["on_accent"]};font-size:.72em;padding:.1em .45em;'
                f'border-radius:.4em;margin-right:.5em;vertical-align:.15em;white-space:nowrap;font-weight:700">{esc(tag)}</span>'
                if tag else "")
    price = it.get("price")
    price_html = (f'<span class="t price d" data-role="price" data-c="accent_text" data-on="{on}" '
                  f'style="color:{t["accent_text"]};white-space:nowrap;font-size:1.12em">'
                  f'<span style="font-size:.62em;margin-right:.08em">¥</span>{esc(price)}</span>' if price not in (None, "") else "")
    desc = (f'<div class="t caption" data-role="caption" data-c="muted" data-on="{on}" '
            f'style="color:{t["muted"]};font-size:.8em;line-height:1.4;margin-top:.15em">{esc(it.get("desc"))}</div>'
            if it.get("desc") else "")
    return (f'<div class="mi" style="break-inside:avoid;padding:var(--rowpad,.42em) 0">'
            f'<div style="display:flex;align-items:baseline;gap:.5em">'
            f'<div class="t body nw" data-role="body" data-c="ink" data-on="{on}" style="color:{t["ink"]};font-weight:700;flex:0 1 auto;min-width:0;white-space:nowrap;overflow:hidden" data-nw="1">'
            f'{tag_html}{esc(it.get("name"))}</div>'
            + (f'<div style="flex:1 1 auto;border-bottom:.12em dotted {t["line"]};transform:translateY(-.25em);min-width:1em"></div>'
               if price_html else "")  # no price (timetables, duty rosters): no leader dots to nowhere
            + f'{price_html}</div>{desc}</div>')


def _menu_cols(ctx, n_items, n_sections):
    o = ctx.o
    if o == "landscape":
        return 3 if n_items > 14 else 2
    if ctx.cv["ar"] < 0.6:  # phone
        return 2 if n_items > 18 else 1
    return 2 if n_items > 10 or n_sections > 2 else 1


def menu_list(ctx, fonts_css, cards=False):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    a = ctx.item.get("art") or {}
    secs = c.get("sections") or []
    n_items = sum(len(s.get("items") or []) for s in secs)
    cols = _menu_cols(ctx, n_items, len(secs))
    on = "surface" if cards else "bg"
    r = ctx.px(ctx.d["shape"]["radius"])
    sec_html = []
    for s in secs:
        items = "".join(_menu_item(ctx, it, None, on) for it in s.get("items") or [])
        head = (f'<div style="display:flex;align-items:baseline;gap:.6em;margin-bottom:.35em;break-after:avoid;break-inside:avoid;'
                f'{"" if cards else "border-bottom:.14em solid " + t["ink"] + ";padding-bottom:.25em"}">'
                f'<div class="t sub d" data-role="sub" data-c="accent_text" data-on="{on}" style="color:{t["accent_text"]};font-size:1.42em;line-height:1.2">{esc(s.get("name"))}</div>'
                + (f'<div class="t caption" data-role="caption" data-c="muted" data-on="{on}" style="color:{t["muted"]};font-size:.8em">{esc(s.get("note"))}</div>' if s.get("note") else "")
                + "</div>")
        box = (f"background:{t['surface']};border-radius:{r};padding:.9em 1.1em .7em;border:{ctx.px(0.2)} solid {t['line']};"
               if cards else "")
        # short sections stay in one column so every dish sits under its heading; long ones may continue
        brk = "avoid" if cards or len(s.get("items") or []) <= 6 else "auto"
        sec_html.append(f'<section style="break-inside:{brk};margin-bottom:1.1em;{box}">{head}{items}</section>')
    base = (4.4 if ctx.cv["kind"] == "screen" else 4.6) * u  # start big, shrink until it fits: fills the page
    floor = max(ctx.minb, ctx.minc / 0.72)  # smallest child is a .72em tag
    alt = f' data-cols-try="{"1,2,3" if o == "landscape" else "1,2"}"'
    body_box = (f'<div id="menubody" data-fit="1" data-max="{base:.1f}" data-min="{floor:.1f}"{alt} '
                f'style="font-size:{base:.1f}px;flex:1 1 auto;min-height:0;overflow:hidden;column-count:{cols};'
                f'column-gap:{ctx.px(4)};line-height:1.4">{"".join(sec_html)}</div>')
    has_art = bool(a.get("motif") or a.get("image"))
    title = T(ctx, "headline", c.get("title") or "菜单", cls="d",
              style=f"font-size:{ctx.px(9 if o != 'landscape' else 7.5)};line-height:1.05;white-space:nowrap;")
    subtitle = T(ctx, "sub", c.get("subtitle"), c="muted", style=f"font-size:{max(ctx.minb, 2.5 * u):.1f}px;")
    det = c.get("details") or []
    note = T(ctx, "caption", c.get("note"), c="muted", style=f"font-size:{max(ctx.minc, 1.9 * u):.1f}px;")
    if o == "landscape":
        side = (f'<div style="display:flex;flex-direction:column;gap:{ctx.px(1.4)};min-height:0;'
                f'border-right:{ctx.px(0.3)} solid {t["ink"]};padding-right:{ctx.px(4)}">'
                + brand_mark(ctx, 3.0) + title + subtitle
                + (f'<div style="flex:1 1 auto;min-height:{ctx.px(10)};position:relative;margin:{ctx.px(1)} 0">'
                   f'<div style="position:absolute;inset:0">{art_block(ctx, a)}</div></div>' if has_art else '<div style="flex:1 1 auto"></div>')
                + details_block(ctx, det, on="bg", size=max(ctx.minb, 2.2 * u)) + note
                + f'<div style="display:flex;justify-content:flex-start;margin-top:{ctx.px(1)}">{qr_block(ctx, c.get("qr"), 10, on="bg")}</div>'
                + "</div>")
        body = (f'<div style="position:absolute;inset:{pad:.1f}px;display:grid;grid-template-columns:30% minmax(0,1fr);gap:{ctx.px(4)}">'
                f'{side}<div style="display:flex;flex-direction:column;min-height:0;min-width:0">{body_box}</div></div>')
        return page(ctx, fonts_css, body, "")
    motif_s = 16
    header = (f'<div style="display:flex;align-items:flex-end;justify-content:space-between;gap:{ctx.px(3)}">'
              f'<div style="display:flex;flex-direction:column;gap:{ctx.px(1)};min-width:0">'
              + brand_mark(ctx, 3.0) + title + subtitle + "</div>"
              + (f'<div style="width:{ctx.px(motif_s * 0.85)};height:{ctx.px(motif_s)};flex:none;position:relative">{art_block(ctx, a)}</div>'
                 if has_art else "")
              + "</div>"
              + f'<div style="height:{ctx.px(0.4)};background:{t["ink"]};margin:{ctx.px(1.6)} 0 {ctx.px(2.4)}"></div>')
    foot = ""
    if det or c.get("note") or c.get("qr"):
        foot = (f'<div style="display:flex;gap:{ctx.px(3)};align-items:center;border-top:{ctx.px(0.2)} solid {t["line"]};padding-top:{ctx.px(1.8)};margin-top:{ctx.px(1)}">'
                f'<div style="flex:1 1 auto;display:flex;flex-direction:column;gap:{ctx.px(0.8)}">'
                + details_block(ctx, det, on="bg", size=max(ctx.minb, 2.2 * u)) + note
                + "</div>" + qr_block(ctx, c.get("qr"), 10, on="bg") + "</div>")
    body = (f'<div style="position:absolute;inset:{pad:.1f}px;display:flex;flex-direction:column">{header}{body_box}{foot}</div>')
    return page(ctx, fonts_css, body, "")


def menu_cards(ctx, fonts_css):
    return menu_list(ctx, fonts_css, cards=True)


BUILDERS = {
    ("poster", "product-hero"): poster_product_hero,
    ("poster", "type-hero"): poster_type_hero,
    ("poster", "editorial"): poster_editorial,
    ("poster", "photo-full"): poster_photo_full,
    ("poster", "notice"): poster_notice,
    ("menu", "list"): menu_list,
    ("menu", "cards"): menu_cards,
}


def build(item, brand, direction, cv, facts, fonts_css):
    key = (item["type"], item.get("layout") or LAYOUTS[item["type"]][0])
    if key not in BUILDERS:
        raise SystemExit(f"no layout {key}. Known: {sorted(BUILDERS)}")
    ctx = Ctx(item, brand, direction, cv, facts)
    return BUILDERS[key](ctx, fonts_css)


import layouts_more  # noqa: E402  (invitations, certificates, business cards)
layouts_more.register(BUILDERS, LAYOUTS)
layouts_more.register_tables(BUILDERS, LAYOUTS)
import brandkit  # noqa: E402  (logo options + brand board)
brandkit.register(BUILDERS, LAYOUTS)
import layouts_art  # noqa: E402  (art-led posters)
layouts_art.register(BUILDERS, LAYOUTS)
import layouts_trend  # noqa: E402  (type-sandwich, type-stack, collage)
layouts_trend.register(BUILDERS, LAYOUTS)
import layouts_h5  # noqa: E402  (phone pages)
layouts_h5.register(BUILDERS, LAYOUTS)
import layouts_xhs  # noqa: E402  (Xiaohongshu note covers)
layouts_xhs.register(BUILDERS, LAYOUTS)
