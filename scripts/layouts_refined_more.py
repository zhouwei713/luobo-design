"""Invitations, certificates, business cards, table cards and menus in the jing (素净) system.

Same rules as layouts_refined.py: a real display face, the brand line down the right edge, facts in one
flat tinted block, one accent, no frames with corner ornaments, no gradients, no drawn motifs. A real photo (art.image) is used in a
straight-edged frame; a motif (art.motif) is ignored here because these systems never draw clip art.

build() in layouts.py sends these five item types here whenever the direction has a "system".
The old layout name is kept as a hint: tablecard number/tent and card classic/band still differ.
"""
from common import rgba
from fonts import stack
from layouts import T, page, plain, qr_block, rich
from layouts_more import CERT_CSS, seal_spot
from layouts_refined import box, fact_block, hair, meta, photo, side_strip, title_px


def sysof(ctx):
    return "jing"


def dfont(ctx, weight=None, track=None):
    """The direction's display face."""
    d = ctx.d["display"]
    w = weight or d.get("weight", 600)
    tr = d.get("tracking", .02) if track is None else track
    return f"font-family:{stack(d['font'])};font-weight:{w};letter-spacing:{tr}em;"


def nfont(ctx):
    """Numerals in the display face, tabular."""
    d = ctx.d["display"]
    return f"font-family:{stack(d['font'])};font-weight:{d.get('weight', 600)};letter-spacing:0;font-variant-numeric:tabular-nums;"


def bfont(ctx):
    return f"font-family:{stack(ctx.d['body']['font'])};"


def line_c(ctx, strong=False):
    t = ctx.t
    return rgba(t["ink"], .35 if strong else .16)


def lw(ctx):
    return "1px"


def meta_row(ctx, left, right, center=False):
    """Brand and date: one vertical line down the right edge (see layouts_refined.side_strip)."""
    return side_strip(ctx, left, right)


def hairframe(ctx, inset):
    """No frames in this system."""
    return ""


def bg_wash(ctx):
    return ""


def spacer(ctx, grow=1, minu=1):
    return f'<div style="flex:{grow} 1 0;min-height:{ctx.px(minu)}"></div>'


def gap(ctx, n):
    return f'<div style="height:{ctx.px(n)};flex:none"></div>'


def kv_rows(ctx, rows, fs, center=False, kw="24%"):
    """Facts as one flat tinted block, label above value."""
    return fact_block(ctx, rows, fs / ctx.u)


def _details(c):
    return [((d.get("k") or d.get("label") or ""), (d.get("v") or d.get("value") or "")) for d in (c.get("details") or [])]


# ------------------------------------------------------------------ invitation
def invitation(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    s = sysof(ctx)
    a = ctx.item.get("art") or {}
    has_img = bool(a.get("image"))
    pad = ctx.safe * 1.15
    tall = ctx.cv["ar"] < 0.6
    k = 1.2 if tall else 1.0
    center = s in ("magazine", "jing")
    host = c.get("host") or ctx.brand.get("name")
    top = meta_row(ctx, c.get("kicker") or "邀请", c.get("date_line") or (host if s == "swiss" else ""), center=center)
    title_size = min(title_px(ctx, c.get("title"), s, roomy=not has_img), (13 if s == "swiss" else 11) * u * k)
    title = (T(ctx, "headline", c.get("title"), fit=(title_size, title_size * .55),
               style=f"{dfont(ctx)}line-height:{1.08 if s == 'swiss' else 1.2};flex:none;max-height:{title_size * 2.5:.0f}px;"
                     f"{'text-align:center;width:100%;' if center else ''}")
             if c.get("title") else "")
    big = c.get("big_number")
    num = (T(ctx, "headline", big, c="accent_text",
             style=f"{nfont(ctx)}font-size:{(17 if s == 'swiss' else 9) * u * k:.0f}px;line-height:.95;white-space:nowrap;flex:none;"
                   f"{'text-align:center;width:100%;' if center else ''}")
           if big else "")
    en = (T(ctx, "sub", c.get("en"), c="muted",
            style=f"font-family:{stack('playfair')};font-style:italic;font-size:{max(ctx.minb, 3.2 * u * k):.1f}px;line-height:1.3;flex:none;"
                  f"{'text-align:center;width:100%;' if center else ''}")
          if c.get("en") and s == "magazine" else "")  # no italic Latin line in jing
    fs = max(ctx.minb, 2.7 * u * k)
    sal = c.get("salutation") or (f"尊敬的 {c.get('guest')}：" if c.get("guest") else "")
    sal_html = T(ctx, "body", sal, style=f"{bfont(ctx)}font-size:{fs * 1.08:.1f}px;font-weight:{600 if s == 'swiss' else 500};flex:none;")
    body = (T(ctx, "body", c.get("body"), fit=(fs * 1.05, ctx.minb),
              style=f"{bfont(ctx)}text-indent:2em;line-height:1.85;text-align:justify;max-height:{ctx.px(24 * k)};flex:none;")
            if c.get("body") else "")
    rows = kv_rows(ctx, _details(c), max(ctx.minb, 2.5 * u * k), kw="20%")
    closing = T(ctx, "body", c.get("closing"), c="accent_text",
                style=f"{dfont(ctx, weight=400 if s == 'swiss' else 500, track=.12)}font-size:{max(ctx.minb, 3.4 * u * k):.1f}px;")
    rsvp = (f'<div style="margin-top:{ctx.px(.8)}">{meta(ctx, c.get("rsvp"), upper=False)}</div>' if c.get("rsvp") else "")
    sign = T(ctx, "body", host, style=f"{bfont(ctx)}font-size:{max(ctx.minb, 2.6 * u * k):.1f}px;font-weight:{600 if s == 'swiss' else 500};"
                                      "text-align:right;white-space:nowrap;letter-spacing:.06em;")
    foot = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)};flex:none">'
            f'<div style="min-width:0">{closing}{rsvp}</div>{qr_block(ctx, c.get("qr"), 10, on="bg")}<div style="flex:none">{sign}</div></div>')
    reading = f'<div style="display:flex;flex-direction:column;gap:{ctx.px(1.4)};flex:none">{sal_html}{body}</div>'
    if o == "landscape":
        left = (f'<div style="display:flex;flex-direction:column;justify-content:center;gap:{ctx.px(2.4)};min-width:0">'
                + (photo(ctx, a) if has_img else "") + num + title + en + "</div>")
        right = (f'<div style="display:flex;flex-direction:column;gap:{ctx.px(2.2)};min-width:0;justify-content:center">'
                 + reading + rows + gap(ctx, 1) + foot + "</div>")
        inner = (top + f'<div style="flex:1 1 auto;min-height:0;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:{ctx.px(6)}">'
                 + left + right + "</div>")
    elif s == "swiss":
        inner = (top + spacer(ctx, 1, 2)
                 + num + gap(ctx, 1.5) + title
                 + (gap(ctx, 2) + photo(ctx, a) if has_img else "")
                 + spacer(ctx, 1.4, 3) + reading + gap(ctx, 2.4) + rows + spacer(ctx, 1, 2) + foot)
    else:
        inner = (top + spacer(ctx, 1, 2)
                 + (photo(ctx, a) + gap(ctx, 3) if has_img else "")
                 + title + gap(ctx, 1.6) + en + (gap(ctx, 2.4) + num if num else "")
                 + spacer(ctx, 1.2, 3)
                 + f'<div style="width:{ctx.px(8)};margin:0 auto;flex:none">{hair(ctx, False, line_c(ctx, True))}</div>'
                 + spacer(ctx, .8, 2) + reading + gap(ctx, 2.4) + rows + spacer(ctx, 1, 2) + foot)
    html = (bg_wash(ctx) + hairframe(ctx, ctx.safe * .5)
            + f'<div style="{box(ctx, pad)}display:flex;flex-direction:column;gap:{ctx.px(.8)};z-index:2">{inner}</div>')
    css = "em.hl{font-style:normal;color:" + t["accent_text"] + "}.pattern{display:none}"
    return page(ctx, fonts_css, html, css)


# ------------------------------------------------------------------ certificate
def _cert_text(c):
    award = c.get("award")
    body = c.get("body") or ""
    if award:
        if "{award}" in body:
            body = body.replace("{award}", f"**{award}**")
        else:
            body = f"{body}**{award}**。" if body else f"荣获**{award}**。"
    return body


def certificate(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    s = sysof(ctx)
    center = s in ("magazine", "jing")
    pad = ctx.safe * 1.3
    title_txt = c.get("title") or "荣誉证书"
    top = meta_row(ctx, c.get("subtitle") or "证书", c.get("number") or "", center=False)
    title = T(ctx, "headline", plain(title_txt), c="ink",
              style=f"{dfont(ctx)}font-size:{(8.4 if s == 'magazine' else 7) * u:.0f}px;line-height:1.1;white-space:nowrap;flex:none;"
                    f"{'text-align:center;letter-spacing:.42em;padding-left:.42em;' if center else ''}")
    name = c.get("recipient") or "【姓名】"
    suffix = c.get("recipient_suffix", "")
    port = o == "portrait"
    nsize = (14 if s == "swiss" else 9) * u * (1.2 if port else 1)
    name_line = (f'<div style="display:flex;align-items:baseline;gap:{ctx.px(1.2)};flex:none;{"justify-content:center;" if center else ""}">'
                 + T(ctx, "headline", name, style=f"{dfont(ctx, weight=300 if s == 'swiss' else 500, track=.08)}font-size:{nsize:.0f}px;line-height:1.15;"
                                                   f"white-space:nowrap;border-bottom:1px solid {line_c(ctx, True)};padding:0 {ctx.px(1)} {ctx.px(.4)};")
                 + T(ctx, "body", (suffix + "：") if suffix else "：", style=f"{bfont(ctx)}font-size:{max(ctx.minb, 3 * u):.1f}px;")
                 + "</div>")
    fs = max(ctx.minb, 3 * u * (1.18 if port else 1))
    para = T(ctx, "body", _cert_text(c), cls="cert-body", fit=(fs * 1.1, ctx.minb),
             style=f"{bfont(ctx)}text-indent:2em;line-height:1.9;max-height:{ctx.px(22)};flex:none;"
                   f"{'max-width:82%;margin:0 auto;' if center and o == 'landscape' else ''}")
    after = T(ctx, "body", c.get("body_after"), style=f"{bfont(ctx)}font-size:{fs:.1f}px;text-indent:2em;line-height:1.9;flex:none;")
    signers = "".join(
        f'<div style="display:flex;flex-direction:column;gap:{ctx.px(.6)};min-width:{ctx.px(16)}">'
        f'<div style="height:{ctx.px(4)};border-bottom:1px solid {line_c(ctx, True)}">'
        + (T(ctx, "body", sg.get("name"), style=f"{bfont(ctx)}font-size:{max(ctx.minb, 2.4 * u):.1f}px;white-space:nowrap;") if sg.get("name") else "")
        + "</div>" + meta(ctx, sg.get("role"), upper=False) + "</div>"
        for sg in (c.get("signers") or []))
    issuer = (f'<div style="position:relative;display:flex;flex-direction:column;align-items:{"flex-end" if s == "swiss" else "center"};'
              f'justify-content:center;min-width:{ctx.px(17)};min-height:{ctx.px(15)};padding:{ctx.px(1.2)} {ctx.px(1.6)}" data-grp="seal">'
              + (seal_spot(ctx, 14).replace("align-items:flex-end", "align-items:flex-start").replace("padding-bottom", "padding-top") if c.get("seal", True) else "")
              + T(ctx, "body", c.get("issuer"), style=f"{bfont(ctx)}font-size:{max(ctx.minb, 2.7 * u):.1f}px;font-weight:{600 if s == 'swiss' else 500};"
                                                     "white-space:nowrap;letter-spacing:.06em;position:relative;z-index:2;")
              + (f'<div style="margin-top:{ctx.px(.8)};position:relative;z-index:2">{meta(ctx, c.get("date"), upper=False)}</div>' if c.get("date") else "")
              + "</div>")
    sign = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(4)};flex:none;'
            '">'
            f'<div style="display:flex;gap:{ctx.px(4)}">{signers}</div>{issuer}</div>')
    if s == "swiss":
        inner = (top + spacer(ctx, .8, 2) + title + spacer(ctx, 1, 2) + name_line + gap(ctx, 2.4) + para + after
                 + spacer(ctx, 1.2, 2) + sign)
    else:
        inner = (top + spacer(ctx, .9, 2) + title + spacer(ctx, 1, 2) + name_line + gap(ctx, 2.6) + para + after
                 + spacer(ctx, 1.2, 2) + sign)
    html = (bg_wash(ctx) + hairframe(ctx, ctx.safe * .55)
            + ""
            + f'<div style="{box(ctx, pad)}display:flex;flex-direction:column;gap:{ctx.px(.6)};z-index:2">{inner}</div>')
    css = CERT_CSS + ".cert-body em.hl{font-style:normal;color:" + t["accent_text"] + "}.pattern{display:none}"
    return page(ctx, fonts_css, html, css)


# ------------------------------------------------------------------ business card
def card(ctx, fonts_css):
    if ctx.item.get("_side") == "back":
        return card_back(ctx, fonts_css)
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    s = sysof(ctx)
    band = (ctx.item.get("layout") == "band") and s == "swiss"
    pad = ctx.safe
    fs = max(ctx.minb, 2.3 * u)
    brand = ctx.brand.get("name") or c.get("org")
    if ctx.brand.get("logo"):
        top_l = f'<img class="logo" src="{ctx.brand["logo"]}" style="height:{ctx.px(4.4)};width:auto" data-role="logo">'
    else:
        top_l = T(ctx, "label", brand, tag="span",
                  style=f"{bfont(ctx)}font-size:{max(ctx.minc, 2.2 * u):.1f}px;font-weight:{600 if s == 'swiss' else 500};"
                        f"letter-spacing:{'.04em' if s == 'swiss' else '.2em'};white-space:nowrap;")
    org = c.get("org") if plain(c.get("org")) != plain(brand) else ""
    top_r = meta(ctx, org) if org else ""
    name = T(ctx, "headline", c.get("name"),
             style=f"{dfont(ctx, weight=300 if s == 'swiss' else 500, track=.04 if s == 'swiss' else .14)}"
                   f"font-size:{ctx.px(8.6 if o == 'landscape' else 9)};line-height:1.1;white-space:nowrap;")
    en = (T(ctx, "caption", c.get("name_en"), c="muted",
            style=f"{bfont(ctx)}font-size:{max(ctx.minc, 2 * u):.1f}px;letter-spacing:.04em;"
                  + f"margin-top:{ctx.px(.6)};white-space:nowrap;")
          if c.get("name_en") else "")
    title = T(ctx, "body", c.get("title"), c="accent_text",
              style=f"{bfont(ctx)}font-size:{fs:.1f}px;font-weight:500;margin-top:{ctx.px(1.2)};white-space:nowrap;")
    rows = "".join(
        f'<div style="display:grid;grid-template-columns:{ctx.px(9)} minmax(0,1fr);gap:{ctx.px(1.4)};align-items:baseline">'
        + meta(ctx, d.get("k"), upper=False, size=max(ctx.minc, fs * .78))
        + T(ctx, "body", d.get("v"), style=f"{bfont(ctx)}font-size:{fs:.1f}px;white-space:nowrap;line-height:1.35;")
        + "</div>" for d in (c.get("contacts") or []))
    contacts = f'<div style="display:flex;flex-direction:column;gap:{ctx.px(.5)};min-width:0">{rows}</div>'
    qr = qr_block(ctx, c.get("qr"), 24, on="bg") if c.get("qr") else ""
    lc = line_c(ctx, True)
    head = (f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:{ctx.px(2)};flex:none">{top_l}{top_r}</div>')
    who = f'<div style="flex:none">{name}{en}{title}</div>'
    bottom = (f'<div style="flex:none;border-top:{lw(ctx)} solid {lc};padding-top:{ctx.px(1.6)};display:flex;justify-content:space-between;'
              f'align-items:flex-end;gap:{ctx.px(2)}">{contacts}{qr}</div>')
    off = 0
    band_html = ""
    if band:
        bw = ctx.cv["bleed_px"] + 2.2 * u
        band_html = f'<div style="position:absolute;left:0;top:0;bottom:0;width:{bw:.1f}px;background:{t["accent"]};z-index:1"></div>'
        off = 2.2 * u + 1.6 * u
    html = (band_html + bg_wash(ctx)
            + f'<div style="position:absolute;left:{pad + off:.1f}px;right:{pad:.1f}px;top:{pad:.1f}px;bottom:{pad:.1f}px;'
              f'display:flex;flex-direction:column;z-index:3">{head}{spacer(ctx, 1, 1)}{who}{spacer(ctx, 1, 1.2)}{bottom}</div>')
    return page(ctx, fonts_css, html, ".pattern{display:none}")


def card_back(ctx, fonts_css):
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    s = sysof(ctx)
    pad = ctx.safe
    brand = ctx.brand.get("name") or c.get("org") or ""
    if s in ("swiss", "jing"):  # the one place the accent fills a whole face
        mark = (f'<img class="logo" src="{ctx.brand["logo"]}" style="height:{ctx.px(9)};width:auto" data-role="logo">' if ctx.brand.get("logo") else
                T(ctx, "headline", brand, c="on_accent", on="accent",
                  style=f"{dfont(ctx, weight=300, track=0)}font-size:{ctx.px(8)};line-height:1.05;"))
        html = (f'<div style="position:absolute;inset:0;background:{t["accent"]};z-index:1"></div>'
                f'<div style="{box(ctx, pad)}display:flex;flex-direction:column;justify-content:space-between;z-index:3">'
                + meta(ctx, c.get("slogan") or "", c="on_accent", on="accent", upper=False)
                + f'<div>{mark}</div></div>')
        return page(ctx, fonts_css, html, ".pattern{display:none}")
    mark = (f'<img class="logo" src="{ctx.brand["logo"]}" style="height:{ctx.px(9)};width:auto" data-role="logo">' if ctx.brand.get("logo") else
            T(ctx, "headline", brand, style=f"{dfont(ctx, track=.2)}font-size:{ctx.px(6.4)};line-height:1.1;text-align:center;white-space:nowrap;"))
    slogan = (f'<div style="margin-top:{ctx.px(2)}">{meta(ctx, c.get("slogan"), upper=False)}</div>' if c.get("slogan") else "")
    html = (hairframe(ctx, ctx.safe * .6)
            + f'<div style="{box(ctx, pad)}display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:3">'
            f'{mark}<div style="width:{ctx.px(6)};margin-top:{ctx.px(2)}">{hair(ctx, False, line_c(ctx, True))}</div>{slogan}</div>')
    return page(ctx, fonts_css, html, ".pattern{display:none}")


# ------------------------------------------------------------------ table cards
def tablecard(ctx, fonts_css):
    if ctx.item.get("layout") == "tent":
        return tent(ctx, fonts_css)
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    s = sysof(ctx)
    center = s in ("magazine", "jing")
    pad = ctx.safe * 1.3
    num = str(c.get("number") or "1")
    big = T(ctx, "headline", num, c="accent_text" if s == "swiss" else "ink",
            style=f"{nfont(ctx)}font-size:{ctx.px((44 if s == 'swiss' else 36) if len(num) <= 2 else 28)};line-height:.9;white-space:nowrap;flex:none;"
                  f"{'text-align:center;' if center else ''}")
    label = c.get("label", "号桌")
    lab = (f'<div style="display:flex;{"justify-content:center;" if center else ""}flex:none;margin-top:{ctx.px(1.2)}">'
           + T(ctx, "label", plain(label).replace(" ", ""), c="accent_text" if s == "magazine" else "ink",
               style=f"{dfont(ctx, weight=400 if s == 'swiss' else 500, track=.5)}font-size:{max(ctx.minc, 4.2 * u):.1f}px;white-space:nowrap;")
           + "</div>")
    guests = c.get("guests") or []
    cols = 2 if len(guests) > 4 else 1
    gfs = max(ctx.minb, (3.6 if s == "swiss" else 3.2) * u)
    cells = "".join(
        f'<div style="border-top:1px solid {line_c(ctx)};padding:{ctx.px(1)} 0;{"text-align:center;" if center else ""}">'
        + T(ctx, "body", g, style=f"{bfont(ctx)}font-size:{gfs:.1f}px;white-space:nowrap;letter-spacing:.08em;") + "</div>"
        for g in guests)
    glist = (f'<div style="display:grid;grid-template-columns:repeat({cols},minmax(0,1fr));column-gap:{ctx.px(4)};flex:none;'
             f'border-bottom:1px solid {line_c(ctx)}">{cells}</div>') if guests else ""
    top = meta_row(ctx, c.get("event") or ctx.brand.get("name"), "" if center else c.get("date"), center=center)
    foot = (f'<div style="display:flex;{"justify-content:center;" if center else ""}flex:none">{meta(ctx, c.get("date"))}</div>'
            if center and c.get("date") else "")
    inner = top + spacer(ctx, .7, 2) + big + lab + spacer(ctx, .7, 2.4) + glist + spacer(ctx, .6, 1.6) + foot
    html = (bg_wash(ctx) + hairframe(ctx, ctx.safe * .7)
            + f'<div style="{box(ctx, pad)}display:flex;flex-direction:column;z-index:2">{inner}</div>')
    return page(ctx, fonts_css, html, ".pattern{display:none}")


def tent(ctx, fonts_css):
    """Folded name card: the top face upside down so both faces read once folded."""
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    s = sysof(ctx)
    pad, H = ctx.safe, ctx.H

    def face(sfx):
        n = len(plain(c.get("name")))
        return (f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%">'
                + T(ctx, "headline", c.get("name"), eid=ctx.nid("tn" + sfx),
                    fit=((15 if n <= 4 else 11) * u, max(ctx.minb * 1.4, 5 * u)),
                    style=f"{dfont(ctx, weight=300 if s == 'swiss' else 500, track=.16)}line-height:1.15;white-space:nowrap;"
                          f"width:100%;text-align:center;max-height:{ctx.px(22)};flex:none;")
                + f'<div style="width:{ctx.px(7)};margin:{ctx.px(2.2)} 0 {ctx.px(1.6)}">{hair(ctx, s == "swiss", t["accent"] if s == "swiss" else line_c(ctx, True))}</div>'
                + T(ctx, "label", c.get("role"), c="accent_text", eid=ctx.nid("tr" + sfx),
                    style=f"{bfont(ctx)}font-size:{max(ctx.minc, 3 * u):.1f}px;letter-spacing:.3em;")
                + (f'<div style="margin-top:{ctx.px(1)}">{meta(ctx, c.get("event"), upper=False)}</div>' if c.get("event") else "")
                + "</div>")
    half = H / 2
    html = (bg_wash(ctx)
            + f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:{pad:.1f}px;height:{half - pad * 1.6:.1f}px;'
              f'transform:rotate(180deg);z-index:3">{face("a")}</div>'
            + f'<div style="position:absolute;left:0;right:0;top:{half:.1f}px;border-top:1px dashed {rgba(t["muted"], .45)};z-index:2"></div>'
            + f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:{half + pad * 0.6:.1f}px;bottom:{pad:.1f}px;z-index:3">{face("b")}</div>')
    return page(ctx, fonts_css, html, ".pattern{display:none}")


# ------------------------------------------------------------------ menu
def _menu_item(ctx, it, on="bg"):
    t, s = ctx.t, sysof(ctx)
    tag = (f'<span class="t label" data-role="label" data-c="accent_text" data-on="{on}" '
           f'style="color:{t["accent_text"]};font-family:{stack(ctx.d["body"]["font"])};font-size:.62em;letter-spacing:.1em;margin-right:.7em;'
           f'vertical-align:.18em;white-space:nowrap;font-weight:500">{rich(it.get("tag"))}</span>' if it.get("tag") else "")
    price = it.get("price")
    pfam = stack(ctx.d["display"]["font"])
    price_html = (f'<span class="t price" data-role="price" data-c="ink" data-on="{on}" '
                  f'style="color:{t["ink"]};font-family:{pfam};font-variant-numeric:tabular-nums;white-space:nowrap;font-size:1.02em;'
                  f'font-weight:{400 if s == "swiss" else 500}"><span style="font-size:.66em;margin-right:.12em;color:{t["muted"]}">¥</span>{rich(price)}</span>' if price not in (None, "") else "")
    desc = (f'<div class="t caption" data-role="caption" data-c="muted" data-on="{on}" '
            f'style="color:{t["muted"]};font-size:.76em;line-height:1.45;margin-top:.2em">{rich(it.get("desc"))}</div>'
            if it.get("desc") else "")
    return (f'<div class="mi" style="break-inside:avoid;padding:var(--rowpad,.5em) 0;border-top:1px solid {line_c(ctx)}">'
            f'<div style="display:flex;align-items:baseline;justify-content:space-between;gap:1em">'
            f'<div class="t body nw" data-role="body" data-c="ink" data-on="{on}" data-nw="1" '
            f'style="color:{t["ink"]};font-weight:{500 if s == "swiss" else 500};flex:0 1 auto;min-width:0;white-space:nowrap;overflow:hidden">'
            f'{tag}{rich(it.get("name"))}</div>{price_html}</div>{desc}</div>')


def menu(ctx, fonts_css):
    from layouts import _menu_cols
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    s = sysof(ctx)
    pad = ctx.safe * 1.1
    a = ctx.item.get("art") or {}
    secs = c.get("sections") or []
    n_items = sum(len(x.get("items") or []) for x in secs)
    cols = _menu_cols(ctx, n_items, len(secs))
    sec_html = []
    for i, x in enumerate(secs, 1):
        items = "".join(_menu_item(ctx, it) for it in x.get("items") or [])
        head = (f'<div style="display:flex;align-items:baseline;justify-content:space-between;gap:.8em;padding-bottom:.45em;'
                f'border-bottom:{lw(ctx)} solid {line_c(ctx, True)};break-after:avoid;break-inside:avoid">'
                f'<div style="display:flex;align-items:baseline;gap:.7em">'
                f'<span class="t label" data-role="label" data-c="accent_text" data-on="bg" style="color:{t["accent_text"]};font-family:{stack(ctx.d["body"]["font"])};font-weight:600;'
                f'font-size:.62em;letter-spacing:.16em">{i:02d}</span>'
                f'<span class="t sub" data-role="sub" data-c="ink" data-on="bg" style="color:{t["ink"]};{dfont(ctx, weight=400 if s == "swiss" else 500, track=.1)}'
                f'font-size:1.3em;line-height:1.2">{rich(x.get("name"))}</span></div>'
                + (f'<span class="t caption" data-role="caption" data-c="muted" data-on="bg" style="color:{t["muted"]};font-size:.74em">{rich(x.get("note"))}</span>'
                   if x.get("note") else "")
                + "</div>")
        brk = "avoid" if len(x.get("items") or []) <= 6 else "auto"
        # the first row's top rule would double the section rule: the next sibling of the head starts flush
        sec_html.append(f'<section class="ms" style="break-inside:{brk};margin-bottom:1.5em">{head}{items}</section>')
    base = (4.2 if ctx.cv["kind"] == "screen" else 4.4) * u
    floor = max(ctx.minb, ctx.minc / 0.62)
    alt = f' data-cols-try="{"1,2,3" if o == "landscape" else "1,2"}"'
    body_box = (f'<div id="menubody" data-fit="1" data-max="{base:.1f}" data-min="{floor:.1f}"{alt} '
                f'style="{bfont(ctx)}font-size:{base:.1f}px;flex:1 1 auto;min-height:0;overflow:hidden;column-count:{cols};'
                f'column-gap:{ctx.px(5)};line-height:1.4">{"".join(sec_html)}</div>')
    tt = c.get("title") or "菜单"
    tsize = min(title_px(ctx, tt, s), (12 if o != "landscape" else 9) * u)
    title = T(ctx, "headline", tt, style=f"{dfont(ctx)}font-size:{tsize:.0f}px;line-height:1.08;flex:none;")
    sub = T(ctx, "sub", c.get("subtitle"), c="muted",
            style=f"{bfont(ctx)}font-size:{max(ctx.minb, 2.6 * u):.1f}px;line-height:1.5;flex:none;")
    det = _details(c)
    note = (meta(ctx, c.get("note"), upper=False) if c.get("note") else "")
    info = ""
    if det or note or c.get("qr"):
        drows = "".join(f'<div style="display:flex;gap:{ctx.px(1.2)};align-items:baseline">{meta(ctx, k, c="accent_text", upper=False)}'
                        + T(ctx, "body", v, style=f"{bfont(ctx)}font-size:{max(ctx.minb, 2.2 * u):.1f}px;") + "</div>" for k, v in det)
        info = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)};flex:none;'
                f'border-top:{lw(ctx)} solid {line_c(ctx, True)};padding-top:{ctx.px(1.8)}">'
                f'<div style="display:flex;flex-direction:column;gap:{ctx.px(.7)};min-width:0">{drows}{note}</div>'
                f'{qr_block(ctx, c.get("qr"), 10, on="bg")}</div>')
    top = meta_row(ctx, ctx.brand.get("name") or "", c.get("date_line") or c.get("kicker") or "菜单")
    img = photo(ctx, a, grow=True) if a.get("image") else ""
    if o == "landscape":
        side = (f'<div style="display:flex;flex-direction:column;gap:{ctx.px(1.6)};min-height:0;min-width:0">'
                + title + sub + (img if img else spacer(ctx, 1, 2)) + info + "</div>")
        body = (f'<div style="flex:1 1 auto;min-height:0;display:grid;grid-template-columns:minmax(0,30%) minmax(0,1fr);gap:{ctx.px(5)}">'
                f'{side}<div style="display:flex;flex-direction:column;min-height:0;min-width:0">{body_box}</div></div>')
        inner = top + gap(ctx, 1.4) + body
    else:
        head = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(4)};flex:none">'
                f'<div style="min-width:0;display:flex;flex-direction:column;gap:{ctx.px(1)}">{title}{sub}</div>'
                + (f'<div style="width:28%;aspect-ratio:4/5;display:flex;flex:none">{img}</div>' if img else "")
                + "</div>")
        inner = top + gap(ctx, 3) + head + gap(ctx, 3.4) + body_box + gap(ctx, 1.4) + info
    html = (bg_wash(ctx) + f'<div style="{box(ctx, pad)}display:flex;flex-direction:column;gap:{ctx.px(.6)};z-index:2">{inner}</div>')
    css = (".pattern{display:none}#menubody section.ms > .mi:nth-child(2){border-top:0}"
           "em.hl{font-style:normal;color:" + t["accent_text"] + "}")
    return page(ctx, fonts_css, html, css)


BUILD = {"invitation": invitation, "certificate": certificate, "card": card, "tablecard": tablecard, "menu": menu}
