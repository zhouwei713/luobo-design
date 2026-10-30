"""Invitations, certificates and business cards. Registered into layouts.BUILDERS on import.

Same conventions as layouts.py: every text node goes through T() so check.py can measure it.
"""
import art
from common import esc, mix, rgba
from layouts import T, art_block, art_on_fill, brand_mark, details_block, page, qr_block, rich, plain


# ------------------------------------------------------------------ shared ornaments
def corner_svg(color, size):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="{size}" height="{size}">'
            f'<path d="M2 38 L2 2 L38 2" fill="none" stroke="{color}" stroke-width="2.2"/>'
            f'<path d="M8 38 L8 8 L38 8" fill="none" stroke="{color}" stroke-width="1"/>'
            f'<rect x="10" y="10" width="7" height="7" transform="rotate(45 13.5 13.5)" fill="{color}"/></svg>')


def ornate_frame(ctx, outer_c, inner_c, inset):
    u = ctx.u
    s = 6 * u
    corners = "".join(
        f'<div style="position:absolute;{v}:{inset + 1.6 * u:.1f}px;{h}:{inset + 1.6 * u:.1f}px;width:{s:.0f}px;height:{s:.0f}px;'
        f'transform:scale({sx},{sy});z-index:2">{corner_svg(inner_c, s)}</div>'
        for v, h, sx, sy in (("top", "left", 1, 1), ("top", "right", -1, 1), ("bottom", "left", 1, -1), ("bottom", "right", -1, -1)))
    return (f'<div style="position:absolute;inset:{inset:.1f}px;border:{ctx.px(1.1)} solid {outer_c};z-index:1"></div>'
            f'<div style="position:absolute;inset:{inset + 1.6 * u:.1f}px;border:{ctx.px(0.22)} solid {inner_c};z-index:1"></div>'
            + corners)


def seal_spot(ctx, size_u, on="bg"):
    """Where the real stamp goes. A drawn imitation of an official seal is never produced."""
    s = ctx.px(size_u)
    return (f'<div class="t caption" data-role="caption" data-c="muted" data-on="{on}" '
            f'style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:{s};height:{s};border-radius:50%;border:{ctx.px(0.25)} dashed {rgba(ctx.t["muted"], .7)};'
            f'display:flex;align-items:flex-end;justify-content:center;padding-bottom:{size_u * 0.1 * ctx.u:.1f}px;color:{rgba(ctx.t["muted"], .9)};'
            f'font-size:{max(ctx.minc, 1.5 * ctx.u):.1f}px;letter-spacing:.2em;z-index:1">盖章处</div>')


def spaced(title):
    """荣誉证书 -> 荣 誉 证 书 for short CJK titles (4 characters or fewer)."""
    t = plain(title)
    return " ".join(t) if 1 < len(t) <= 4 and all("一" <= ch <= "鿿" for ch in t) else t


# ------------------------------------------------------------------ invitation
def _invite_text(ctx, c, align="left", on="bg", ink="ink", muted="muted"):
    u = ctx.u * (1.22 if ctx.cv["ar"] < 0.6 else 1)  # phone-height cards have room for larger reading text
    parts = []
    if c.get("guest") or c.get("salutation"):
        sal = c.get("salutation") or f"尊敬的 {c.get('guest')}："
        parts.append(T(ctx, "body", sal, c=ink, on=on, style=f"font-size:{max(ctx.minb, 2.8 * u):.1f}px;font-weight:700;margin-bottom:{ctx.px(1)};"))
    if c.get("body"):
        parts.append(T(ctx, "body", c["body"], c=ink, on=on, fit=(max(ctx.minb, 2.6 * u), ctx.minb),
                       style=f"text-indent:2em;line-height:1.75;max-height:{ctx.px(26)};text-align:justify;"))
    det = c.get("details") or []
    if det:
        rows = "".join(
            f'<div style="display:flex;gap:{ctx.px(1.6)};align-items:baseline">'
            + T(ctx, "caption", d.get("k"), c="accent_text" if on != "accent" else "on_accent", on=on,
                style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;font-weight:700;letter-spacing:.2em;white-space:nowrap;min-width:3.6em;")
            + T(ctx, "body", d.get("v"), c=ink, on=on, style=f"font-size:{max(ctx.minb, 2.5 * u):.1f}px;line-height:1.45;")
            + "</div>" for d in det)
        parts.append(f'<div style="display:flex;flex-direction:column;gap:{ctx.px(1)};margin-top:{ctx.px(2.2)};'
                     f'padding-top:{ctx.px(2)};border-top:{ctx.px(0.15)} solid {ctx.t["line"]}">{rows}</div>')
    return "".join(parts)


def _invite_foot(ctx, c, on="bg", ink="ink"):
    u = ctx.u
    sign = (T(ctx, "body", c.get("host"), c=ink, on=on, style=f"font-size:{max(ctx.minb, 2.5 * u):.1f}px;text-align:right;font-weight:700;")
            + T(ctx, "caption", c.get("date_line"), c="muted", on=on, style=f"font-size:{max(ctx.minc, 2 * u):.1f}px;text-align:right;margin-top:{ctx.px(0.5)};"))
    left = (T(ctx, "body", c.get("closing"), c="accent_text", on=on, cls="d", style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;")
            + T(ctx, "caption", c.get("rsvp"), c="muted", on=on, style=f"font-size:{max(ctx.minc, 2 * u):.1f}px;margin-top:{ctx.px(0.8)};"))
    return (f'<div style="display:flex;align-items:flex-end;gap:{ctx.px(3)};margin-top:{ctx.px(2.4)};flex:none">'
            f'<div style="flex:1 1 auto;min-width:0">{left}</div>{qr_block(ctx, c.get("qr"), 10, on=on)}'
            f'<div style="flex:none;max-width:42%">{sign}</div></div>')


FLAT_MOTIFS = {"double-happiness"}  # one colour, the accent: vanishes on an accent panel


def _panel_art(ctx, a):
    return art_on_fill(ctx, a) if (a or {}).get("motif") in FLAT_MOTIFS and not (a or {}).get("image") else art_block(ctx, a)


def _calm(ctx):
    """Sun rays sell an opening sale; on an invitation or a table card they look cheap, so drop them."""
    return ".pattern{display:none}" if ctx.d.get("pattern") == "rays" else ""


def invitation_formal(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    a = ctx.item.get("art") or {}
    inset = pad * 0.5
    frame = ornate_frame(ctx, t["accent"], mix(t["accent2"], t["ink"], .1) if t["accent2"] != t["ink"] else t["muted"], inset)
    head_max = {"portrait": 9.5, "square": 8, "landscape": 8}[o] * u + (2 * u if ctx.cv["ar"] < 0.6 else 0)
    title = T(ctx, "headline", c.get("title"), cls="d", fit=(head_max, max(ctx.minb * 1.4, 4 * u)),
              style=f"max-height:{ctx.px(26)};text-align:center;width:100%;flex:none;")
    kicker = T(ctx, "label", c.get("kicker") or "INVITATION", c="accent_text",
               style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;letter-spacing:.4em;font-weight:700;text-align:center;")
    ms = 1.5 if ctx.cv["ar"] < 0.6 else 1
    motif = (f'<div style="width:{ctx.px(18 * ms)};height:{ctx.px(14 * ms)};margin:{ctx.px(1.5)} auto 0;position:relative;flex:none">{art_block(ctx, a)}</div>'
             if (a.get("motif") or a.get("image")) else "")
    big = c.get("big_number")
    bignum = (T(ctx, "headline", big, c="accent_text", cls="d", style=f"font-size:{ctx.px(7)};line-height:1;text-align:center;margin-top:{ctx.px(1.6)};letter-spacing:.06em;")
              if big else "")
    rule = f'<div style="width:{ctx.px(10)};height:{ctx.px(0.3)};background:{t["accent"]};margin:{ctx.px(1.8)} auto;flex:none"></div>'
    head = (f'<div style="display:flex;flex-direction:column;align-items:center">{brand_mark(ctx, 2.6)}'
            f'<div style="height:{ctx.px(1.2)}"></div>{kicker}{motif}<div style="height:{ctx.px(1.2)}"></div>{title}{rule}{bignum}</div>')
    body = _invite_text(ctx, c)
    foot = _invite_foot(ctx, c)
    ins = inset + 5 * u
    if o == "landscape":
        html = (f'{frame}<div style="position:absolute;inset:{ins:.1f}px;display:grid;grid-template-columns:1fr 1.25fr;gap:{ctx.px(5)};align-items:center">'
                f'<div style="border-right:{ctx.px(0.15)} solid {t["line"]};padding-right:{ctx.px(4)}">{head}</div>'
                f'<div style="display:flex;flex-direction:column;justify-content:center;min-width:0">{body}{foot}</div></div>')
    else:
        html = (f'{frame}<div data-grow-box="1" style="position:absolute;inset:{ins:.1f}px;display:flex;flex-direction:column">'
                f'{head}<div style="flex:1 1 auto;min-height:{ctx.px(4)}"></div>'
                f'<div data-grow="1.4" data-keep="{10 * u:.0f}" style="display:flex;flex-direction:column">{body}</div>'
                f'<div style="flex:1 1 auto;min-height:{ctx.px(1)}"></div>{foot}</div>')
    return page(ctx, fonts_css, html, _calm(ctx))


def invitation_split(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    a = ctx.item.get("art") or {}
    panel_c = t["accent"]
    head_max = {"portrait": 10, "square": 8.5, "landscape": 9}[o] * u + (2 * u if ctx.cv["ar"] < 0.6 else 0)
    panel_in = (T(ctx, "label", c.get("kicker") or "INVITATION", c="on_accent", on="accent",
                  style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;letter-spacing:.4em;font-weight:700;")
                + f'<div style="height:{ctx.px(1.6)}"></div>'
                + T(ctx, "headline", c.get("title"), c="on_accent", on="accent", cls="d", fit=(head_max, max(ctx.minb * 1.4, 4 * u)),
                    style=f"max-height:{ctx.px(28)};")
                + (T(ctx, "headline", c.get("big_number"), c="on_accent", on="accent", cls="d",
                     style=f"font-size:{ctx.px(6.5)};line-height:1;margin-top:{ctx.px(2)};opacity:.9;letter-spacing:.05em;")
                   if c.get("big_number") else ""))
    motif = (f'<div style="position:absolute;right:{ctx.px(3)};bottom:{ctx.px(-7)};width:{ctx.px(22)};height:{ctx.px(19)};z-index:4">{_panel_art(ctx, a)}</div>'
             if (a.get("motif") or a.get("image")) else "")
    body = _invite_text(ctx, c)
    foot = _invite_foot(ctx, c)
    if o == "landscape":
        html = (f'<div style="position:absolute;left:0;top:0;bottom:0;width:40%;background:{panel_c};z-index:1"></div>'
                f'<div style="position:absolute;left:{pad:.1f}px;top:{pad:.1f}px;bottom:{pad:.1f}px;width:calc(40% - {pad * 1.6:.1f}px);'
                f'display:flex;flex-direction:column;justify-content:center;z-index:3">{brand_mark(ctx, 2.6, on="accent")}<div style="height:{ctx.px(3)}"></div>{panel_in}</div>'
                f'<div style="position:absolute;left:40%;bottom:{ctx.px(10)};width:0;height:0;z-index:4"><div style="position:absolute;left:{ctx.px(-11)};bottom:0;width:{ctx.px(22)};height:{ctx.px(19)}">{_panel_art(ctx, a) if (a.get("motif") or a.get("image")) else ""}</div></div>'
                f'<div style="position:absolute;left:calc(40% + {pad:.1f}px);right:{pad:.1f}px;top:{pad:.1f}px;bottom:{pad:.1f}px;'
                f'display:flex;flex-direction:column;justify-content:center;z-index:3">{body}{foot}</div>')
    else:
        ph = 44 if ctx.cv["ar"] > 0.6 else 40
        html = (f'<div style="position:absolute;left:0;right:0;top:0;height:{ph}%;background:{panel_c};z-index:1">{motif}</div>'
                f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:{pad:.1f}px;height:calc({ph}% - {pad * 1.4:.1f}px);'
                f'display:flex;flex-direction:column;justify-content:flex-end;z-index:3;padding-right:{ctx.px(18)}">'
                f'<div style="position:absolute;top:0;left:0">{brand_mark(ctx, 2.6, on="accent")}</div>{panel_in}</div>'
                f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:calc({ph}% + {ctx.px(5)});bottom:{pad:.1f}px;'
                f'display:flex;flex-direction:column;z-index:3" data-grow-box="1"><div data-grow="1.4" data-keep="{8 * u:.0f}">{body}</div>'
                f'<div style="flex:1 1 auto"></div>{foot}</div>')
    return page(ctx, fonts_css, html, _calm(ctx))


# ------------------------------------------------------------------ certificate
def _cert_body(ctx, c, align_center=False, name_scale=1.0):
    u = ctx.u
    name = c.get("recipient") or "【姓名】"
    suffix = c.get("recipient_suffix", "")
    award = c.get("award")
    body = c.get("body") or ""
    if award:
        if "{award}" in body:
            body = body.replace("{award}", f"**{award}**")
        else:
            body = f"{body}**{award}**。" if body else f"荣获**{award}**。"
    fs = max(ctx.minb, 3 * u)
    name_line = (f'<div style="display:flex;align-items:baseline;gap:{ctx.px(1)};{"justify-content:center;" if align_center else ""}flex:none">'
                 + T(ctx, "headline", name, cls="d", style=f"font-size:{ctx.px(6.4 * name_scale)};line-height:1.2;"
                     f"border-bottom:{ctx.px(0.25)} solid {ctx.t['ink']};padding:0 {ctx.px(1.2)};white-space:nowrap;")
                 + T(ctx, "body", (suffix + "：") if suffix else "：", style=f"font-size:{fs * 1.1:.1f}px;")
                 + "</div>")
    para = T(ctx, "body", body, cls="cert-body", fit=(fs * 1.15, ctx.minb),
             style=f"text-indent:2em;line-height:1.9;max-height:{ctx.px(22)};margin-top:{ctx.px(2)};")
    after = T(ctx, "body", c.get("body_after"), style=f"font-size:{fs:.1f}px;text-indent:2em;line-height:1.9;")
    return name_line + para + after


def _cert_sign(ctx, c, on="bg"):
    u = ctx.u
    signers = "".join(
        f'<div style="display:flex;align-items:flex-end;gap:{ctx.px(1)}">'
        + T(ctx, "caption", s.get("role"), c="muted", on=on, style=f"font-size:{max(ctx.minc, 2 * u):.1f}px;white-space:nowrap;")
        + (T(ctx, "body", s.get("name"), on=on, style=f"font-size:{max(ctx.minb, 2.4 * u):.1f}px;white-space:nowrap;") if s.get("name") else "")
        + f'<div style="width:{ctx.px(13)};border-bottom:{ctx.px(0.15)} solid {ctx.t["ink"]};margin-bottom:{ctx.px(0.6)}"></div></div>'
        for s in (c.get("signers") or []))
    issuer = (f'<div style="position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:{ctx.px(17)};min-height:{ctx.px(16)};padding:{ctx.px(1.5)} {ctx.px(2)}" data-grp="seal">'
              + (seal_spot(ctx, 15, on) if c.get("seal", True) else "")
              + T(ctx, "body", c.get("issuer"), on=on, style=f"font-size:{max(ctx.minb, 2.8 * u):.1f}px;font-weight:700;white-space:nowrap;letter-spacing:.08em;")
              + T(ctx, "body", c.get("date"), on=on, style=f"font-size:{max(ctx.minb, 2.4 * u):.1f}px;margin-top:{ctx.px(0.8)};white-space:nowrap;")
              + "</div>")
    no = T(ctx, "caption", c.get("number"), c="muted", on=on, style=f"font-size:{max(ctx.minc, 1.7 * u):.1f}px;")
    return (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(4)};flex:none">'
            f'<div style="display:flex;flex-direction:column;gap:{ctx.px(1.6)}">{signers}{no}</div>{issuer}</div>')


CERT_CSS = ".cert-body em.hl{white-space:nowrap;font-weight:700}"  # an award name never breaks across lines


def certificate_classic(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    a = ctx.item.get("art") or {}
    inset = pad * 0.45
    gold = mix(t["accent2"], "#B8892B", .5) if t["accent2"].upper() not in ("#FFFFFF", t["ink"].upper()) else "#C9A45C"
    frame = ornate_frame(ctx, t["accent"], gold, inset)
    emblem = ""
    if a.get("motif") or a.get("image"):
        emblem = (f'<div style="width:{ctx.px(13)};height:{ctx.px(11)};margin:0 auto {ctx.px(0.6)};position:relative;flex:none">'
                  f'{art_block(ctx, a)}</div>')
    title = T(ctx, "headline", spaced(c.get("title") or "荣誉证书"), c="accent_text", cls="d",
              style=f"font-size:{ctx.px(9.5 if o == 'landscape' else 9)};line-height:1.1;text-align:center;white-space:nowrap;")
    sub = T(ctx, "label", c.get("subtitle"), c="muted",
            style=f"font-size:{max(ctx.minc, 1.9 * u):.1f}px;letter-spacing:.42em;text-align:center;margin-top:{ctx.px(1)};")
    ins = inset + 6.5 * u
    html = (f'{frame}<div style="position:absolute;inset:{ins:.1f}px;display:flex;flex-direction:column">'
            f'{emblem}{title}{sub}<div style="flex:1 1 auto;min-height:{ctx.px(2)}"></div>'
            f'<div style="padding:0 {ctx.px(4 if o == "landscape" else 1)}">{_cert_body(ctx, c)}</div>'
            f'<div style="flex:1 1 auto;min-height:{ctx.px(2)}"></div>{_cert_sign(ctx, c)}</div>')
    return page(ctx, fonts_css, html, CERT_CSS)


def certificate_modern(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    pad = ctx.safe
    a = ctx.item.get("art") or {"motif": "medal"}
    band_w = 34 if o == "landscape" else 100
    title = T(ctx, "headline", c.get("title") or "荣誉证书", c="on_accent", on="accent", cls="d",
              style=f"font-size:{ctx.px(8)};line-height:1.15;white-space:nowrap;")
    sub = T(ctx, "label", c.get("subtitle"), c="on_accent", on="accent",
            style=f"font-size:{max(ctx.minc, 1.8 * u):.1f}px;letter-spacing:.3em;margin-top:{ctx.px(1.2)};opacity:.9;")
    motif = f'<div style="width:{ctx.px(22)};height:{ctx.px(22)};position:relative">{art_on_fill(ctx, a)}</div>'
    if o == "landscape":
        band = (f'<div style="position:absolute;left:0;top:0;bottom:0;width:{band_w}%;background:{t["accent"]};z-index:1;'
                f'display:flex;flex-direction:column;justify-content:space-between;padding:{pad * 1.2:.1f}px {pad:.1f}px">'
                f'<div>{brand_mark(ctx, 2.6, on="accent")}</div>{motif}<div>{title}{sub}</div></div>'
                f'<div style="position:absolute;left:{band_w}%;top:0;bottom:0;width:{ctx.px(1)};background:{t["accent2"]};z-index:2"></div>')
        html = (band + f'<div style="position:absolute;left:calc({band_w}% + {pad * 1.3:.1f}px);right:{pad * 1.2:.1f}px;top:{pad * 1.2:.1f}px;bottom:{pad:.1f}px;'
                f'display:flex;flex-direction:column;z-index:3"><div style="flex:1 1 auto"></div>'
                f'{_cert_body(ctx, c, name_scale=1.25)}<div style="flex:1.3 1 auto"></div>{_cert_sign(ctx, c)}</div>')
    else:
        band = (f'<div style="position:absolute;left:0;right:0;top:0;height:30%;background:{t["accent"]};z-index:1;'
                f'display:flex;align-items:flex-end;justify-content:space-between;padding:{pad:.1f}px">'
                f'<div>{brand_mark(ctx, 2.6, on="accent")}<div style="height:{ctx.px(3)}"></div>{title}{sub}</div>{motif}</div>')
        html = (band + f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:calc(30% + {pad:.1f}px);bottom:{pad:.1f}px;'
                f'display:flex;flex-direction:column;z-index:3">{_cert_body(ctx, c, name_scale=1.2)}<div style="flex:1 1 auto"></div>{_cert_sign(ctx, c)}</div>')
    return page(ctx, fonts_css, html, CERT_CSS)


# ------------------------------------------------------------------ business card
def _contacts(ctx, c, on, ink, fs):
    rows = "".join(
        f'<div style="display:flex;gap:{fs * 0.6:.1f}px;align-items:baseline">'
        + T(ctx, "caption", d.get("k"), c="accent_text" if on != "accent" else "on_accent", on=on,
            style=f"font-size:{fs * 0.82:.1f}px;font-weight:700;white-space:nowrap;min-width:2.4em;")
        + T(ctx, "body", d.get("v"), c=ink, on=on, style=f"font-size:{fs:.1f}px;white-space:nowrap;")
        + "</div>" for d in (c.get("contacts") or []))
    return f'<div style="display:flex;flex-direction:column;gap:{fs * 0.32:.1f}px">{rows}</div>'


def card_front(ctx, fonts_css, band=False):
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    pad = ctx.safe
    fs = max(ctx.minb, 2.5 * u)
    name = T(ctx, "headline", c.get("name"), cls="d", style=f"font-size:{ctx.px(8.2)};line-height:1.15;white-space:nowrap;letter-spacing:.06em;")
    en = T(ctx, "caption", c.get("name_en"), c="muted", style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;letter-spacing:.14em;margin-top:{ctx.px(0.6)};")
    title = T(ctx, "body", c.get("title"), c="accent_text", style=f"font-size:{fs * 1.05:.1f}px;font-weight:700;margin-top:{ctx.px(1.4)};")
    org = ("" if plain(c.get("org")) == plain(ctx.brand.get("name")) and not ctx.brand.get("logo") else
           T(ctx, "body", c.get("org"), style=f"font-size:{fs:.1f}px;margin-top:{ctx.px(0.4)};"))
    left = f'<div>{name}{en}{title}{org}</div>'
    top = f'<div style="display:flex;justify-content:space-between;align-items:flex-start">{brand_mark(ctx, 5.2)}</div>'
    bottom = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)}">'
              f'{_contacts(ctx, c, "bg", "ink", fs)}{qr_block(ctx, c.get("qr"), 27, on="bg") if c.get("qr") else ""}</div>')  # 27u is about 15mm, the smallest QR that scans reliably
    band_html = ""
    if band:
        band_html = (f'<div style="position:absolute;left:0;top:0;bottom:0;width:{ctx.cv["bleed_px"] + 3.2 * u:.1f}px;'
                     f'background:{t["accent"]};z-index:1"></div>')
    off = (3.2 * u + 2 * u) if band else 0
    html = (band_html + f'<div style="position:absolute;left:{pad + off:.1f}px;right:{pad:.1f}px;top:{pad:.1f}px;bottom:{pad:.1f}px;'
            f'display:flex;flex-direction:column;justify-content:space-between;z-index:3">'
            f'<div style="display:flex;justify-content:space-between;gap:{ctx.px(3)}">{left}{top}</div>{bottom}</div>')
    return page(ctx, fonts_css, html, ".pattern{display:none}")


def card_back(ctx, fonts_css):
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    pad = ctx.safe
    mark = brand_mark(ctx, 11, on="accent")
    slogan = T(ctx, "body", c.get("slogan"), c="on_accent", on="accent",
               style=f"font-size:{max(ctx.minb, 2.8 * u):.1f}px;letter-spacing:.2em;margin-top:{ctx.px(2.4)};text-align:center;")
    html = (f'<div style="position:absolute;inset:0;background:{t["accent"]};z-index:1"></div>'
            f'<div style="position:absolute;inset:{pad:.1f}px;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:3">'
            f'{mark.replace("color:" + t["ink"], "color:" + t["on_accent"])}{slogan}</div>')
    return page(ctx, fonts_css, html, "")


def card_classic(ctx, fonts_css):
    return card_back(ctx, fonts_css) if ctx.item.get("_side") == "back" else card_front(ctx, fonts_css)


def card_band(ctx, fonts_css):
    return card_back(ctx, fonts_css) if ctx.item.get("_side") == "back" else card_front(ctx, fonts_css, band=True)


def register(builders, layouts):
    layouts.update({"invitation": ["formal", "split"], "certificate": ["classic", "modern"], "card": ["classic", "band"]})
    builders.update({
        ("invitation", "formal"): invitation_formal, ("invitation", "split"): invitation_split,
        ("certificate", "classic"): certificate_classic, ("certificate", "modern"): certificate_modern,
        ("card", "classic"): card_classic, ("card", "band"): card_band,
    })


# ------------------------------------------------------------------ table cards
def tablecard_number(ctx, fonts_css):
    """Table number card for banquets: big number, the guests at that table, the occasion."""
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    pad = ctx.safe
    a = ctx.item.get("art") or {}
    frame = (f'<div style="position:absolute;inset:{pad * 0.55:.1f}px;border:{ctx.px(0.5)} solid {t["accent"]};z-index:1"></div>'
             f'<div style="position:absolute;inset:{pad * 0.55 + 1.4 * u:.1f}px;border:{ctx.px(0.18)} solid {t["line"]};z-index:1"></div>')
    num = str(c.get("number") or "1")
    big = T(ctx, "headline", num, c="accent_text", cls="d", style=f"font-size:{ctx.px(34 if len(num) <= 2 else 24)};line-height:1;white-space:nowrap;")
    label = T(ctx, "label", c.get("label", "号桌"), c="muted", style=f"font-size:{max(ctx.minc, 3.4 * u):.1f}px;letter-spacing:.3em;margin-top:{ctx.px(1)};")
    guests = c.get("guests") or []
    cols = 2 if len(guests) > 5 else 1
    glist = ("" if not guests else
             f'<div style="display:grid;grid-template-columns:repeat({cols},auto);justify-content:center;gap:{ctx.px(0.6)} {ctx.px(5)};margin-top:{ctx.px(3)}">'
             + "".join(T(ctx, "body", g, style=f"font-size:{max(ctx.minb, 3.2 * u):.1f}px;text-align:center;white-space:nowrap;") for g in guests)
             + "</div>")
    motif = (f'<div style="width:{ctx.px(16)};height:{ctx.px(12)};position:relative;margin-bottom:{ctx.px(1)}">{art_block(ctx, a)}</div>'
             if (a.get("motif") or a.get("image")) else "")
    ev = T(ctx, "label", c.get("event"), c="accent_text", style=f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;letter-spacing:.2em;text-align:center;")
    date = T(ctx, "caption", c.get("date"), c="muted", style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;letter-spacing:.12em;margin-top:{ctx.px(0.8)};")
    html = (f'{frame}<div style="position:absolute;inset:{pad + 2.5 * u:.1f}px;display:flex;flex-direction:column;align-items:center;z-index:3">'
            f'{motif}{ev}<div style="flex:1 1 auto"></div>'
            f'<div style="display:flex;flex-direction:column;align-items:center">{big}{label}</div>'
            f'<div style="width:{ctx.px(12)};height:{ctx.px(0.3)};background:{t["accent"]};margin-top:{ctx.px(3)}"></div>{glist}'
            f'<div style="flex:1.2 1 auto"></div>{date}</div>')
    return page(ctx, fonts_css, html, _calm(ctx))


def tablecard_tent(ctx, fonts_css):
    """Folded name card: two faces on one sheet, the top face upside down so both read once folded."""
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    pad = ctx.safe
    W, H = ctx.W, ctx.H

    def face(eid_sfx):
        return (f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%">'
                + T(ctx, "headline", c.get("name"), cls="d", eid=ctx.nid("tn" + eid_sfx),
                    fit=((15 if len(plain(c.get('name'))) <= 4 else 11) * u, max(ctx.minb * 1.4, 5 * u)),
                    style=f"line-height:1.15;white-space:nowrap;letter-spacing:.12em;width:100%;text-align:center;max-height:{ctx.px(22)};flex:none;")
                + T(ctx, "label", c.get("role"), c="accent_text", eid=ctx.nid("tr" + eid_sfx),
                    style=f"font-size:{max(ctx.minc, 3.4 * u):.1f}px;letter-spacing:.3em;margin-top:{ctx.px(2)};")
                + T(ctx, "caption", c.get("event"), c="muted", eid=ctx.nid("te" + eid_sfx),
                    style=f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;letter-spacing:.15em;margin-top:{ctx.px(1.2)};")
                + "</div>")
    half = H / 2
    stripe = f'<div style="position:absolute;left:0;right:0;height:{ctx.px(2)};background:{t["accent"]};'
    html = (f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:{pad:.1f}px;height:{half - pad * 1.6:.1f}px;'
            f'transform:rotate(180deg);z-index:3">{face("a")}</div>'
            f'<div style="position:absolute;left:0;right:0;top:{half:.1f}px;border-top:1px dashed {rgba(t["muted"], .5)};z-index:2"></div>'
            f'<div style="position:absolute;left:{pad:.1f}px;right:{pad:.1f}px;top:{half + pad * 0.6:.1f}px;bottom:{pad:.1f}px;z-index:3">{face("b")}</div>'
            f'{stripe}top:0"></div>{stripe}bottom:0"></div>')
    return page(ctx, fonts_css, html, ".pattern{display:none}")


def register_tables(builders, layouts):
    layouts["tablecard"] = ["number", "tent"]
    builders[("tablecard", "number")] = tablecard_number
    builders[("tablecard", "tent")] = tablecard_tent
