"""The restrained system, 素净 (jing): quiet pages that still read as Chinese design, not as a Western magazine.

What it keeps and what it refuses:
- the title carries the page: a real display face (宋 600 or 黑 700), set by meaning, line-height about 1.2,
  never an ultra-light Latin face stretched over Chinese
- brand and date run down the right edge as one small vertical line (竖排), not as a tracked mono strip with a rule
- facts sit in one flat tinted block (surface colour): labels above values, grouped, no hairline ledger
- the offer is one solid block of the accent colour; the accent appears in one or two places only
- flat colour and paper texture; no gradient washes, no glass, no rounded cards, no shadows, no stickers
- a real photo goes in a straight-edged frame; without one the title and the blocks hold the page

Layouts: poster "jing" (old names "magazine" and "swiss" point here); notices in this system use notice_refined.
"""
import re

from common import contrast, is_dark, mix, rgba
from fonts import stack
from layouts import T, esc, page, plain, qr_block, rich

CJK = re.compile(r"[㐀-鿿]")
LATIN = re.compile(r"[A-Za-z0-9 .,:;!?'\"()\-+/%#&@]")


def text_em(s):
    """Rough width of a line in ems: CJK 1, Latin and digits about half."""
    s = plain(s)
    return sum(0.56 if LATIN.match(ch) else (0.3 if ch == " " else 1.0) for ch in s)


def lines_of(s):
    return [ln for ln in str(s or "").split("\n") if ln.strip()]


def strip_w(ctx):
    """Room the vertical brand line takes on the right of the content box."""
    return max(ctx.minc, 2.0 * ctx.u) * 1.25 + 2.6 * ctx.u


def box(ctx, pad):
    """Content box style: inset by the margin, with room on the right when the vertical line is there."""
    pr = f"padding-right:{strip_w(ctx):.1f}px;" if getattr(ctx, "_strip", False) else ""
    return f"position:absolute;inset:{pad:.1f}px;{pr}"


def title_px(ctx, text, system=None, roomy=False):
    """Display size from the longest line, capped so a title stays a title (not a wall)."""
    W, pad = ctx.W, ctx.safe
    lines = lines_of(text) or [""]
    em = max(text_em(x) for x in lines) or 1
    avail = W - 2 * pad * (1.2 if ctx.o == "landscape" else 1.0) - (strip_w(ctx) if getattr(ctx, "_strip", False) else 0)
    if ctx.o == "landscape":
        avail *= 0.56
    fit = avail / (em * 1.02) * 0.97
    n = max(len(plain(x).replace(" ", "")) for x in lines)
    short = min(ctx.W, ctx.H)
    cap = short * (0.2 if n <= 3 else 0.17 if n <= 4 else 0.14 if n <= 6 else 0.11 if n <= 8 else 0.09)
    if len(lines) >= 3:
        cap *= 0.86
    if roomy:
        cap *= 1.15
    if ctx.H / ctx.W > 1.55:  # a phone-long page has height to spare: let the title use it
        cap *= 1.2
    return max(min(fit, cap), ctx.minb * 1.6)


def meta(ctx, text, c="muted", on="bg", upper=False, size=None):
    """Small secondary text: labels, dates, numbers. The body face, lightly tracked; never a mono strip."""
    fs = size or max(ctx.minc, 1.9 * ctx.u)
    return T(ctx, "label", text, c=c, on=on, tag="span",
             style=f"font-family:{stack(ctx.d['body']['font'])};font-size:{fs:.1f}px;letter-spacing:.08em;font-weight:500;"
                   "white-space:nowrap;line-height:1.3;")


def hair(ctx, strong=True, color=None):
    """A short separator. Used sparingly: blocks and air do the separating in this system."""
    t = ctx.t
    c = color or (rgba(t["ink"], .5) if strong else rgba(t["ink"], .2))
    return f'<div style="height:1px;background:{c};flex:none"></div>'


def side_strip(ctx, left, right):
    """Brand and date as one vertical line down the right edge of the content box."""
    if not (left or right):
        return ""
    ctx._strip = True
    fs = max(ctx.minc, 2.0 * ctx.u)
    parts = []
    if left:
        parts.append(T(ctx, "label", plain(left), c="ink", tag="span",
                       style=f"font-family:{stack(ctx.d['body']['font'])};font-size:{fs:.1f}px;font-weight:600;letter-spacing:.2em;"))
    if right:
        parts.append(T(ctx, "label", plain(right), c="muted", tag="span",
                       style=f"font-family:{stack(ctx.d['body']['font'])};font-size:{fs:.1f}px;font-weight:400;letter-spacing:.16em;"))
    dot = f'<span style="display:block;width:{fs * .32:.1f}px;height:{fs * .32:.1f}px;background:{ctx.t["accent"]};margin:{fs * .7:.1f}px auto"></span>'
    return (f'<div style="position:absolute;right:0;top:0;writing-mode:vertical-rl;display:flex;align-items:center;'
            f'white-space:nowrap;z-index:3">{dot.join(parts)}</div>')


def top_row(ctx, left, right, system=None):
    """Kept for callers of the old systems: the brand line now runs down the right edge."""
    return side_strip(ctx, left, right)


def headline(ctx, text, system=None, roomy=False, color="ink"):
    if not text:
        return ""
    fs = title_px(ctx, text, roomy=roomy)
    d = ctx.d["display"]
    st = (f"font-family:{stack(d['font'])};font-weight:{d.get('weight', 600)};letter-spacing:{d.get('tracking', .02)}em;"
          "line-height:1.2;")
    n = len(lines_of(text)) or 1
    # the title is the one block that gives way when the page is full: its box shrinks, the fit script
    # then brings the type down until it fits again
    st += f"max-height:{fs * 1.26 * n + 4:.0f}px;flex:0 1 auto;min-height:{fs * 0.55 * n:.0f}px;"
    return T(ctx, "headline", text, c=color, fit=(fs, fs * 0.55), style=st)


def lead(ctx, text, system=None, size_u=3.1, color="ink"):
    if not text:
        return ""
    fam = stack(ctx.d["body"]["font"])
    st = (f"font-family:{fam};font-size:{max(ctx.minb, size_u * ctx.u):.1f}px;line-height:1.6;"
          f"font-weight:400;max-width:{'86%' if ctx.o != 'landscape' else '100%'};flex:none;text-wrap:pretty;")
    return T(ctx, "sub", text, c=color, style=st)


def kicker_tag(ctx, text):
    """The kicker as a small solid block of the accent colour."""
    if not text:
        return ""
    t = ctx.t
    return (f'<div class="on-accent" style="align-self:flex-start;background:{t["accent"]};padding:{ctx.px(.7)} {ctx.px(1.4)};flex:none">'
            + T(ctx, "label", text, c="on_accent", on="accent", tag="span",
                style=f"font-size:{max(ctx.minc, 2.3 * ctx.u):.1f}px;font-weight:600;letter-spacing:.12em;white-space:nowrap;")
            + "</div>")


def on_surface_accent(ctx):
    """The accent, deepened until small text in it reads on the surface tint."""
    t = ctx.t
    c, step = t["accent_text"], 0
    target = "#FFFFFF" if is_dark(t["surface"]) else "#000000"
    while contrast(c, t["surface"]) < 4.6 and step < 20:
        c, step = mix(c, target, .06), step + 1
    return c


def fact_block(ctx, rows, size_u=3.2, cols=None):
    """Facts in one flat tinted block: label above value, two columns when there is room."""
    if not rows:
        return ""
    t, u = ctx.t, ctx.u
    fam = stack(ctx.d["body"]["font"])
    fs = max(ctx.minb, size_u * u)
    if cols is None:
        longest = max(len(plain(v)) for _, v in rows)
        cols = 1 if (ctx.o == "portrait" and ctx.W < 700) or longest > 14 or len(rows) == 1 else 2
    cells = "".join(
        f'<div style="min-width:0;display:flex;flex-direction:column;gap:{ctx.px(.5)}">'
        + (T(ctx, "label", k, c=on_surface_accent(ctx), on="surface", tag="span",
             style=f"font-family:{fam};font-size:{max(ctx.minc, fs * .62):.1f}px;font-weight:600;letter-spacing:.12em;white-space:nowrap;")
           if k else "")
        + T(ctx, "body", v, on="surface", style=f"font-family:{fam};font-size:{fs:.1f}px;line-height:1.4;font-weight:500;")
        + "</div>" for k, v in rows)
    return (f'<div style="flex:none;background:{t["surface"]};padding:{ctx.px(2.4)} {ctx.px(2.8)};display:grid;'
            f'grid-template-columns:repeat({cols},minmax(0,1fr));gap:{ctx.px(2.2)} {ctx.px(3.2)}">{cells}</div>')


def ledger(ctx, c, system=None, size_u=3.4):
    """Details (k/v) or tags as one fact block. Returns '' when there is nothing to list."""
    rows = []
    det = c.get("details") or []
    if det:
        rows = [(d.get("k") or d.get("label") or "", d.get("v") or d.get("value") or "") for d in det]
    elif c.get("tags"):
        rows = [(f"{i:02d}", tg) for i, tg in enumerate(c["tags"][:6], 1)]
    if ctx.o == "square":
        rows = rows[:4]
    return fact_block(ctx, rows, size_u * .94)


def offer_block(ctx, offer, system=None):
    """One solid block of the accent colour. Never a starburst."""
    if not offer or not offer.get("big"):
        return ""
    t, u = ctx.t, ctx.u
    big = T(ctx, "badge", offer["big"], c="on_accent", on="accent",
            style=f"font-family:{stack(ctx.d['display']['font'])};font-size:{4.6 * u:.1f}px;font-weight:{ctx.d['display'].get('weight', 600)};"
                  "line-height:1.1;white-space:nowrap;", nowrap=True)
    small = T(ctx, "caption", offer.get("small"), c="on_accent", on="accent",
              style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;margin-top:{ctx.px(.6)};white-space:nowrap;font-weight:500;")
    return (f'<div class="on-accent" style="background:{t["accent"]};padding:{ctx.px(1.8)} {ctx.px(2.6)};flex:none;'
            f'display:flex;flex-direction:column;align-items:flex-start">{big}{small}</div>')


def photo(ctx, a, ratio=None, grow=True):
    """A real photo in a straight-edged frame; the crop follows art.focus when given."""
    fx, fy, fw, fh = (a.get("focus") or [.25, .25, .5, .5])
    pos = f"{(fx + fw / 2) * 100:.0f}% {(fy + fh / 2) * 100:.0f}%"
    fit = "contain" if a.get("_shot") else "cover"
    size = f"aspect-ratio:{ratio};" if ratio else ""
    img = (f'<img class="art" src="{esc(a["image"])}" data-role="image" '
           f'style="width:100%;height:100%;object-fit:{fit};object-position:{pos}">')
    # basis 0: the photo takes what is left after the type, it never squeezes the title
    return (f'<div style="position:relative;{size}{"flex:1 1 0;min-height:0;" if grow else "flex:none;"}overflow:hidden">{img}</div>')


def wash(ctx):
    """The old systems breathed gradients onto the paper. This one stays flat."""
    return ""


def foot_row(ctx, c, system=None):
    """CTA on the left; offer, or a QR code, on the right."""
    u = ctx.u
    cta = T(ctx, "body", c.get("cta"), c="ink",
            style=f"font-family:{stack(ctx.d['body']['font'])};font-size:{max(ctx.minb, 3.0 * u):.1f}px;font-weight:600;line-height:1.35;")
    right = offer_block(ctx, c.get("offer")) + qr_block(ctx, c.get("qr"), 10, on="bg")
    if not (cta or right):
        return ""
    return (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)};flex:none">'
            f'<div style="flex:1 1 auto;min-width:0">{cta}</div><div style="display:flex;gap:{ctx.px(2)};align-items:flex-end">{right}</div></div>')


# ------------------------------------------------------------------ poster
def poster_jing(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    a = ctx.item.get("art") or {}
    pad = ctx.safe * 1.05
    has_img = bool(a.get("image"))
    strip = side_strip(ctx, ctx.brand.get("name"), c.get("date_line"))
    kicker = kicker_tag(ctx, c.get("kicker"))
    # a square has room for the title and one more block: the offer wins over the facts
    led = "" if (o == "square" and (c.get("offer") or c.get("qr") or c.get("cta"))) else ledger(ctx, c, size_u=3.4 if o != "square" else 3.0)
    big = c.get("big_title") if c.get("big_title") and plain(c.get("big_title")) != plain(c.get("headline")) else None
    head = headline(ctx, big or c.get("headline"), roomy=not has_img)
    sub = lead(ctx, c.get("sub"), size_u=(3.1 if has_img else 3.5) if o != "square" else 2.8)
    num = (T(ctx, "headline", c.get("big_number"), c="accent_text", cls="d",
             style=f"font-weight:{ctx.d['display'].get('weight', 600)};font-size:{min(ctx.W, ctx.H) * .19:.0f}px;line-height:.95;flex:none;")
           if c.get("big_number") else "")
    foot = foot_row(ctx, c)
    gap = ctx.px(3)
    if o == "landscape":
        leftcol = (f'<div style="display:flex;flex-direction:column;gap:{gap};min-width:0;justify-content:center">'
                   f'{kicker}{head}{sub}</div>')
        rightcol = (f'<div style="display:flex;flex-direction:column;gap:{gap};min-width:0;min-height:0">'
                    + (photo(ctx, a) if has_img else num + '<div style="flex:1 1 auto"></div>' + led) + foot + "</div>")
        body = (f'<div style="{box(ctx, pad)}display:flex;flex-direction:column">{strip}'
                f'<div style="flex:1 1 auto;min-height:0;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:{ctx.px(6)}">'
                + leftcol + rightcol + "</div></div>")
    else:
        middle = photo(ctx, a) if has_img else f'<div style="flex:1 1 auto;min-height:{ctx.px(2)}"></div>'
        lower = ""
        if not has_img and ctx.H / ctx.W > 1.2 and sub:
            # tall page, no photo: the lead sits in the air a little below the middle, so the page has no single hole
            middle = (f'<div style="flex:3 1 0;min-height:{ctx.px(2)}"></div>{sub}'
                      f'<div style="flex:2 1 0;min-height:{ctx.px(1)}"></div>')
            sub = ""
        body = (f'<div style="{box(ctx, pad)}display:flex;flex-direction:column;gap:{gap}">{strip}'
                + f'<div style="height:{(ctx.H * .05 if ctx.H / ctx.W > 1.55 else 2 * u) if o != "square" else .5 * u:.0f}px;flex:none"></div>'
                + kicker + head + sub + num + middle + lower + led + foot + "</div>")
    css = "em.hl{font-style:normal;color:" + t["accent_text"] + "}"
    return page(ctx, fonts_css, body, css + ".pattern{display:none}")


# ------------------------------------------------------------------ notices in this system
def notice_refined(ctx, fonts_css):
    """A civic notice set like a page of a well-made bulletin: no coloured header band, no clip art."""
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe * 1.05
    org = c.get("org") or ctx.brand.get("name")
    strip = side_strip(ctx, org, c.get("date_line"))
    kick = kicker_tag(ctx, c.get("kicker") or "通知")
    head = headline(ctx, c.get("headline"))
    led = ledger(ctx, {"details": c.get("details")}, size_u=3.0)
    paras = [p for p in str(c.get("body") or "").split("\n\n") if p.strip()]
    body = ""
    if paras:
        from layouts import _is_salutation
        inner = "".join(f'<p style="text-indent:{0 if _is_salutation(p) else 2}em;margin:0 0 .6em">{rich(p)}</p>' for p in paras)
        fam = stack(ctx.d["body"]["font"])
        body = (f'<div id="noticebody" class="t body" data-role="body" data-c="ink" data-on="bg" data-fit="1" '
                f'data-max="{max(ctx.minb, (3.9 if o != "landscape" else 3.2) * u):.1f}" data-min="{ctx.minb:.1f}" '
                f'style="color:{t["ink"]};font-family:{fam};font-size:{max(ctx.minb, 3.1 * u):.1f}px;line-height:1.75;flex:1 1 auto;min-height:0;overflow:hidden;text-align:justify">{inner}</div>')
    phone = T(ctx, "body", c.get("cta"), c="accent_text", style=f"font-size:{max(ctx.minb, 2.6 * u):.1f}px;font-weight:600;")
    sign = ('<div style="text-align:right;flex:none">'
            + T(ctx, "body", c.get("issuer") or org, style=f"font-size:{max(ctx.minb, 2.7 * u):.1f}px;font-weight:600;white-space:nowrap;")
            + (f'<div style="margin-top:{ctx.px(.6)}">{meta(ctx, c.get("date_line"))}</div>' if c.get("date_line") else "")
            + "</div>")
    foot = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)};flex:none">'
            f'<div style="flex:1 1 auto;min-width:0">{phone}</div>{qr_block(ctx, c.get("qr"), 10, on="bg")}{sign}</div>')
    html = (f'<div style="{box(ctx, pad)}display:flex;flex-direction:column;gap:{ctx.px(2.6)};z-index:2">{strip}'
            + f'<div style="height:{ctx.px(1)};flex:none"></div>'
            + kick + head + led + body + foot + "</div>")
    return page(ctx, fonts_css, html, ".pattern{display:none}#noticebody p:last-child{margin-bottom:0}")


LAYOUT_FONTS = {"jing": ["song", "hei"], "magazine": ["song", "hei"], "swiss": ["song", "hei"]}


def register(builders, layouts):
    layouts["poster"] += ["jing", "magazine", "swiss"]  # the old names stay valid and point at jing
    for name in ("jing", "magazine", "swiss"):
        builders[("poster", name)] = poster_jing
