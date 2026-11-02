"""Two restrained poster systems: magazine (paper, ink, serif) and swiss (grid, hairlines, light sans).

What makes them read as designed rather than templated:
- type carries the page: huge display type in a LIGHT weight (swiss 200-300, magazine serif 500),
  small type heavier, and a size gap of ten times between the two
- a quiet line of metadata on top (brand, date, issue) in tracked mono, with a hairline under it
- hairlines and whitespace separate things; no rounded cards, no shadows, no stickers, no sparkles
- exactly one accent colour, used in one or two places
- pictures are real photos in straight-edged frames, or there is no picture: nothing drawn in code
- left-aligned on a grid; the page is filled top to bottom with intent

Layouts: poster "magazine", poster "swiss"; notices in these directions use notice_refined.
"""
import re

from common import mix, rgba
from fonts import stack
from layouts import T, esc, page, plain, qr_block, rich

LATIN = re.compile(r"[A-Za-z0-9 .,:;!?'\"()\-+/%#&@]")


def text_em(s):
    """Rough width of a line in ems: CJK 1, Latin and digits about half."""
    s = plain(s)
    return sum(0.56 if LATIN.match(ch) else (0.3 if ch == " " else 1.0) for ch in s)


def lines_of(s):
    return [ln for ln in str(s or "").split("\n") if ln.strip()]


def title_px(ctx, text, system, roomy=False):
    """Display size from the longest line, capped by bands that keep a title a title (not a wall)."""
    W, pad = ctx.W, ctx.safe
    lines = lines_of(text) or [""]
    em = max(text_em(x) for x in lines) or 1
    avail = W - 2 * pad * (1.2 if ctx.o == "landscape" else 1.0)
    if ctx.o == "landscape":
        avail *= 0.56
    track = 0.06 if system == "magazine" else -0.01
    fit = avail / (em * (1 + track)) * 0.97
    n = max(len(plain(x).replace(" ", "")) for x in lines)
    short = min(ctx.W, ctx.H)
    if system == "swiss":
        cap = short * (0.215 if n <= 3 else 0.185 if n <= 4 else 0.15 if n <= 6 else 0.115 if n <= 8 else 0.09)
    else:
        cap = short * (0.17 if n <= 4 else 0.15 if n <= 6 else 0.12 if n <= 8 else 0.095)
    if len(lines) >= 3:
        cap *= 0.86
    if roomy:
        cap *= 1.2
    if ctx.H / ctx.W > 1.55:  # a phone-long page has height to spare: let the title use it
        cap *= 1.22
    return max(min(fit, cap), ctx.minb * 1.6)


def meta(ctx, text, c="muted", on="bg", upper=True, size=None):
    """Tracked mono metadata: issue line, labels, numbers."""
    fs = size or max(ctx.minc, 1.85 * ctx.u)
    return T(ctx, "label", text, c=c, on=on, tag="span",
             style=f"font-family:{stack('mono')};font-size:{fs:.1f}px;letter-spacing:.18em;font-weight:500;"
                   + ("text-transform:uppercase;" if upper else "") + "white-space:nowrap;line-height:1.2;")


def hair(ctx, strong=True, color=None):
    t = ctx.t
    c = color or (t["ink"] if strong else rgba(t["ink"], .35))
    return f'<div style="height:{1.5 if strong else 1}px;background:{c};flex:none"></div>'


def top_row(ctx, left, right, system):
    """Brand on the left, date or issue on the right, a hairline under both."""
    t = ctx.t
    lf = (T(ctx, "label", left, c="ink", tag="span",
            style=f"font-family:{stack(ctx.d['body']['font'])};font-size:{max(ctx.minc, 2.1 * ctx.u):.1f}px;font-weight:{600 if system == 'swiss' else 500};"
                  f"letter-spacing:{'.04em' if system == 'swiss' else '.22em'};white-space:nowrap;") if left else "<span></span>")
    rt = meta(ctx, right) if right else ""
    return (f'<div style="flex:none"><div style="display:flex;justify-content:space-between;align-items:baseline;gap:{ctx.px(2)}">{lf}{rt}</div>'
            f'<div style="height:{ctx.px(1.8)}"></div>{hair(ctx, system == "swiss", None if system == "swiss" else rgba(t["ink"], .4))}</div>')


def headline(ctx, text, system, roomy=False, color="ink"):
    if not text:
        return ""
    fs = title_px(ctx, text, system, roomy)
    d = ctx.d["display"]
    if system == "swiss":
        st = (f"font-family:{stack(d['font'])};font-weight:{d.get('weight', 250)};letter-spacing:{d.get('tracking', -0.01)}em;"
              f"line-height:1.04;")
    else:
        st = (f"font-family:{stack(d['font'])};font-weight:{d.get('weight', 500)};letter-spacing:{d.get('tracking', .06)}em;"
              f"line-height:1.16;")
    n = len(lines_of(text)) or 1
    # the title is the one block that gives way when the page is full: its box shrinks, the fit script
    # then brings the type down until it fits again
    st += f"max-height:{fs * (1.2 if system == 'magazine' else 1.1) * n + 4:.0f}px;flex:0 1 auto;min-height:{fs * 0.55 * n:.0f}px;"
    return T(ctx, "headline", text, c=color, fit=(fs, fs * 0.55), style=st)


def lead(ctx, text, system, size_u=3.1, color="ink"):
    if not text:
        return ""
    fam = stack(ctx.d["body"]["font"])
    st = (f"font-family:{fam};font-size:{max(ctx.minb, size_u * ctx.u):.1f}px;line-height:{1.55 if system == 'swiss' else 1.7};"
          f"font-weight:{400};max-width:{'88%' if ctx.o != 'landscape' else '100%'};flex:none;text-wrap:pretty;")
    return T(ctx, "sub", text, c=color, style=st)


def ledger(ctx, c, system, size_u=3.4):
    """Details (k/v) or tags as numbered rows between hairlines. Returns '' when there is nothing to list."""
    t, u = ctx.t, ctx.u
    rows = []
    det = c.get("details") or []
    if det:
        for d in det:
            rows.append((d.get("k") or d.get("label") or "", d.get("v") or d.get("value") or ""))
    elif c.get("tags"):
        rows = [(f"{i:02d}", tg) for i, tg in enumerate(c["tags"][:6], 1)]
    if ctx.o == "square":
        rows = rows[:3]
    if not rows:
        return ""
    line = t["ink"] if system == "swiss" else rgba(t["ink"], .4)
    w = "1.5px" if system == "swiss" else "1px"
    fam = stack(ctx.d["body"]["font"])
    fs = max(ctx.minb, size_u * u)
    out = []
    for k, v in rows:
        out.append(f'<div style="display:grid;grid-template-columns:minmax(0,{ "16%" if not det else "24%"}) minmax(0,1fr);gap:{ctx.px(2)};'
                   f'align-items:baseline;border-top:{w} solid {line};padding:{ctx.px(1.7 if ctx.o != "square" else 1.2)} 0">'
                   + meta(ctx, k, c="accent_text", upper=False)
                   + T(ctx, "body", v, style=f"font-family:{fam};font-size:{fs:.1f}px;line-height:1.35;font-weight:400;")
                   + "</div>")
    return f'<div style="flex:none;border-bottom:{w} solid {line}">{"".join(out)}</div>'


def offer_block(ctx, offer, system):
    """A square-cornered accent block (swiss) or an accent outline (magazine). Never a starburst."""
    if not offer or not offer.get("big"):
        return ""
    t, u = ctx.t, ctx.u
    big = T(ctx, "badge", offer["big"], c="on_accent" if system == "swiss" else "accent_text", on="accent" if system == "swiss" else "bg",
            style=f"font-family:{stack(ctx.d['display']['font'])};font-size:{4.4 * u:.1f}px;font-weight:{500 if system == 'swiss' else 600};"
                  "line-height:1.1;white-space:nowrap;", nowrap=True)
    small = T(ctx, "caption", offer.get("small"), c="on_accent" if system == "swiss" else "accent_text",
              on="accent" if system == "swiss" else "bg",
              style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;margin-top:{ctx.px(.6)};white-space:nowrap;font-weight:500;")
    if system == "swiss":
        box = f"background:{t['accent']};padding:{ctx.px(1.8)} {ctx.px(2.4)};"
    else:
        box = f"border:1.5px solid {t['accent']};padding:{ctx.px(1.6)} {ctx.px(2.2)};"
    return f'<div class="on-accent" style="{box}flex:none;display:flex;flex-direction:column;align-items:flex-start">{big}{small}</div>'


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
    """Ink and accent breathed onto the paper at the corners: atmosphere, never a pattern."""
    t = ctx.t
    return (f'<div style="position:absolute;inset:0;z-index:0;pointer-events:none;background:'
            f'radial-gradient(70% 45% at 92% 6%,{rgba(t["accent"], .10)} 0%,{rgba(t["accent"], 0)} 70%),'
            f'radial-gradient(65% 40% at 4% 100%,{rgba(t["ink"], .08)} 0%,{rgba(t["ink"], 0)} 70%),'
            f'radial-gradient(40% 30% at 30% 40%,{rgba(mix(t["bg"], "#FFFFFF", .6), .5)} 0%,{rgba(t["bg"], 0)} 70%)"></div>')


def foot_row(ctx, c, system):
    """CTA on the left; offer, or a QR code, on the right."""
    u = ctx.u
    cta = T(ctx, "body", c.get("cta"), c="ink",
            style=f"font-family:{stack(ctx.d['body']['font'])};font-size:{max(ctx.minb, 3.0 * u):.1f}px;"
                  f"font-weight:{600 if system == 'swiss' else 500};line-height:1.35;")
    right = offer_block(ctx, c.get("offer"), system) + qr_block(ctx, c.get("qr"), 10, on="bg")
    if not (cta or right):
        return ""
    return (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)};flex:none">'
            f'<div style="flex:1 1 auto;min-width:0">{cta}</div><div style="display:flex;gap:{ctx.px(2)};align-items:flex-end">{right}</div></div>')


# ------------------------------------------------------------------ swiss
def poster_swiss(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    a = ctx.item.get("art") or {}
    pad = ctx.safe * 1.05
    has_img = bool(a.get("image"))
    right = c.get("date_line") or c.get("kicker")
    kick = c.get("kicker") if c.get("date_line") else None
    # a square has room for the title and one more block: the offer wins over the list
    led = "" if (o == "square" and (c.get("offer") or c.get("qr") or c.get("cta"))) else ledger(ctx, c, "swiss", 3.4 if o != "square" else 3.0)
    roomy = not has_img  # no picture: the title is the picture
    big = c.get("big_title") if c.get("big_title") and plain(c.get("big_title")) != plain(c.get("headline")) else None
    head = headline(ctx, big or c.get("headline"), "swiss", roomy)
    sub = lead(ctx, c.get("sub"), "swiss", (3.1 if has_img else 3.5) if o != "square" else 2.8)
    kicker = (T(ctx, "label", kick, c="accent_text", style=f"font-size:{max(ctx.minc, 2.3 * u):.1f}px;font-weight:600;letter-spacing:.06em;flex:none;")
              if kick else "")
    num = (T(ctx, "headline", c.get("big_number"), c="accent_text", cls="d",
             style=f"font-family:{stack('inter')};font-weight:200;font-size:{min(ctx.W, ctx.H) * .2:.0f}px;line-height:.9;letter-spacing:-.03em;flex:none;")
           if c.get("big_number") else "")
    foot = foot_row(ctx, c, "swiss")
    gap = ctx.px(3.2)
    if o == "landscape":
        leftcol = (f'<div style="display:flex;flex-direction:column;gap:{gap};min-width:0;justify-content:center">'
                   f'{kicker}{head}{sub}</div>')
        rightcol = (f'<div style="display:flex;flex-direction:column;gap:{gap};min-width:0;min-height:0">'
                    + (photo(ctx, a) if has_img else num + f'<div style="flex:1 1 auto"></div>' + led) + foot + "</div>")
        body = (f'<div style="position:absolute;inset:{pad:.0f}px;display:flex;flex-direction:column;gap:{ctx.px(4)}">'
                + top_row(ctx, ctx.brand.get("name"), right, "swiss")
                + f'<div style="flex:1 1 auto;min-height:0;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:{ctx.px(6)}">'
                + leftcol + rightcol + "</div></div>")
    else:
        middle = (photo(ctx, a) if has_img else "")
        spacer = f'<div style="flex:1 1 auto;min-height:{ctx.px(2)}"></div>'
        if not has_img and ctx.H / ctx.W > 1.2 and sub:  # tall page, no photo: the lead drops to meet the list
            spacer, sub, lower = spacer, "", sub
        else:
            lower = ""
        body = (f'<div style="position:absolute;inset:{pad:.0f}px;display:flex;flex-direction:column;gap:{gap}">'
                + top_row(ctx, ctx.brand.get("name"), right, "swiss")
                + f'<div style="height:{(ctx.H * .07 if ctx.H / ctx.W > 1.55 else 4 * u) if o != "square" else 1.5 * u:.0f}px;flex:none"></div>'
                + kicker + head + sub + num
                + (middle if has_img else spacer)
                + lower + led + foot + "</div>")
    css = "em.hl{font-style:normal;color:" + t["accent_text"] + "}"
    return page(ctx, fonts_css, body, css + ".pattern{display:none}")


# ------------------------------------------------------------------ magazine
def poster_magazine(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    a = ctx.item.get("art") or {}
    pad = ctx.safe * 1.05
    has_img = bool(a.get("image"))
    right = c.get("date_line") or c.get("kicker")
    kick = c.get("kicker") if c.get("date_line") else None
    head = headline(ctx, c.get("big_title") or c.get("headline"), "magazine", roomy=not has_img)
    kicker = (T(ctx, "label", kick, c="accent_text",
                style=f"font-family:{stack('song')};font-size:{max(ctx.minc, 2.5 * u):.1f}px;letter-spacing:.32em;font-weight:500;flex:none;")
              if kick else "")
    en = (T(ctx, "sub", c.get("en"), c="muted",
            style=f"font-family:{stack('playfair')};font-style:italic;font-size:{max(ctx.minb, (4.2 if o == 'portrait' else 3.6) * u):.1f}px;line-height:1.3;flex:none;")
          if c.get("en") else "")
    quote = lead(ctx, c.get("sub"), "magazine", (3.9 if o != "square" else 3.3) if not has_img else 2.9)
    led = ledger(ctx, {"details": c.get("details")}, "magazine", 3.2) if c.get("details") else ""
    tags = c.get("tags") or []
    strip_l = " · ".join(tags[:5]) if tags else (c.get("note") or "")
    strip_r = ctx.brand.get("name") if strip_l else ""
    strip = ""
    if strip_l or strip_r:
        strip = (f'<div style="flex:none">{hair(ctx, False)}<div style="height:{ctx.px(1.6)}"></div>'
                 f'<div style="display:flex;justify-content:space-between;gap:{ctx.px(2)}">{meta(ctx, strip_l, upper=False)}{meta(ctx, strip_r)}</div></div>')
    foot = foot_row(ctx, c, "magazine")
    gap = ctx.px(2.8)
    if o == "landscape":
        leftcol = (f'<div style="display:flex;flex-direction:column;gap:{gap};min-width:0;justify-content:center">{kicker}{head}{en}</div>')
        rightcol = (f'<div style="display:flex;flex-direction:column;gap:{gap};min-width:0;min-height:0">'
                    + (photo(ctx, a) if has_img else f'<div style="flex:1 1 auto"></div>{hair(ctx, False)}{quote}')
                    + led + foot + "</div>")
        body = (wash(ctx) + f'<div style="position:absolute;inset:{pad:.0f}px;display:flex;flex-direction:column;gap:{ctx.px(4)};z-index:2">'
                + top_row(ctx, ctx.brand.get("name"), right, "magazine")
                + f'<div style="flex:1 1 auto;min-height:0;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:{ctx.px(6)}">'
                + leftcol + rightcol + "</div>" + strip + "</div>")
    else:
        if has_img:
            mid = photo(ctx, a) + quote
        else:
            # the air is split so the quote sits a little below the middle, not stuck to the bottom edge
            mid = (f'<div style="flex:3 1 0;min-height:{ctx.px(3)}"></div>{hair(ctx, False)}{quote}'
                   f'<div style="flex:2 1 0;min-height:0"></div>')
        body = (wash(ctx) + f'<div style="position:absolute;inset:{pad:.0f}px;display:flex;flex-direction:column;gap:{gap};z-index:2">'
                + top_row(ctx, ctx.brand.get("name"), right, "magazine")
                + f'<div style="height:{ctx.px(5 if o != "square" else 1.5)};flex:none"></div>'
                + kicker + head + en + mid + led + foot + strip + "</div>")
    css = "em.hl{font-style:normal;color:" + t["accent_text"] + "}"
    return page(ctx, fonts_css, body, css + ".pattern{display:none}")


# ------------------------------------------------------------------ notices in these systems
def notice_refined(ctx, fonts_css):
    """A civic notice set like a page of a well-made bulletin: no coloured header band, no clip art."""
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    system = ctx.d.get("system") or "swiss"
    pad = ctx.safe * 1.05
    org = c.get("org") or ctx.brand.get("name")
    kicker = c.get("kicker") or "通知"
    kick = T(ctx, "label", kicker, c="accent_text",
             style=f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;letter-spacing:.4em;font-weight:{600 if system == 'swiss' else 500};flex:none;")
    head = headline(ctx, c.get("headline"), system)
    led = ledger(ctx, {"details": c.get("details")}, system, 3.0)
    paras = [p for p in str(c.get("body") or "").split("\n\n") if p.strip()]
    body = ""
    if paras:
        from layouts import _is_salutation
        inner = "".join(f'<p style="text-indent:{0 if _is_salutation(p) else 2}em;margin:0 0 .6em">{rich(p)}</p>' for p in paras)
        fam = stack(ctx.d["body"]["font"])
        body = (f'<div id="noticebody" class="t body" data-role="body" data-c="ink" data-on="bg" data-fit="1" '
                f'data-max="{max(ctx.minb, (3.9 if o != "landscape" else 3.2) * u):.1f}" data-min="{ctx.minb:.1f}" '
                f'style="color:{t["ink"]};font-family:{fam};font-size:{max(ctx.minb, 3.1 * u):.1f}px;line-height:1.75;flex:1 1 auto;min-height:0;overflow:hidden;text-align:justify">{inner}</div>')
    phone = T(ctx, "body", c.get("cta"), c="accent_text",
              style=f"font-size:{max(ctx.minb, 2.6 * u):.1f}px;font-weight:500;")
    sign = (f'<div style="text-align:right;flex:none">'
            + T(ctx, "body", c.get("issuer") or org, style=f"font-size:{max(ctx.minb, 2.7 * u):.1f}px;font-weight:600;white-space:nowrap;")
            + (f'<div style="margin-top:{ctx.px(.6)}">{meta(ctx, c.get("date_line"), upper=False)}</div>' if c.get("date_line") else "")
            + "</div>")
    foot = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)};flex:none">'
            f'<div style="flex:1 1 auto;min-width:0">{phone}</div>{qr_block(ctx, c.get("qr"), 10, on="bg")}{sign}</div>')
    gap = ctx.px(2.6)
    html = ((wash(ctx) if system == "magazine" else "")
            + f'<div style="position:absolute;inset:{pad:.0f}px;display:flex;flex-direction:column;gap:{gap};z-index:2">'
            + top_row(ctx, org, c.get("date_line") if c.get("date_line") else "", system)
            + f'<div style="height:{ctx.px(2.5)};flex:none"></div>'
            + kick + head + led + body + foot + "</div>")
    return page(ctx, fonts_css, html, ".pattern{display:none}#noticebody p:last-child{margin-bottom:0}")


LAYOUT_FONTS = {"swiss": ["inter", "hei", "mono"], "magazine": ["song", "mono", "playfair"]}


def register(builders, layouts):
    layouts["poster"] += ["magazine", "swiss"]
    builders[("poster", "magazine")] = poster_magazine
    builders[("poster", "swiss")] = poster_swiss
