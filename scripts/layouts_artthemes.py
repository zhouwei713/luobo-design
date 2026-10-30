"""Each art style dresses the whole poster, not only its picture.

art-hero on a portrait canvas hands off to the theme of its art.style: page colour, title font and
treatment, composition and the little graphic devices all change, while the brand name and the
copy stay the same. Square and landscape sizes keep the shared art-hero layout.

  watercolor  paper page, washes everywhere, the title sits in a wash, left aligned
  papercut    layered paper hills, the cup stands on them, the title is a paper strip
  riso        huge spot-ink title with misregistration, the cup overprints it, halftone
  clay        pastel page, the cup on a clay pedestal, the title in a puffy clay pill
  pop         comic panel, tilted cup, burst, the title in a speech bubble with a black stroke
  lineart     white page, outlined giant number, small line drawing, thin serif title, centred
  crayon      kraft paper, the title handwritten with a crayon highlight, doodles
  diffuse     soft light blobs, the copy on a frosted glass card
  ink         rice paper, vertical calligraphy title on the right, red name block, mountains
  neon        dark wall, glowing tube title, neon pills
"""
import art
import artstyle
from common import contrast, mix, rgba
from fonts import stack
from layouts import T, art_block, page

FONTS = {"watercolor": "xiaowei", "papercut": "kuaile", "riso": "sans", "clay": "kuaile", "pop": "sans",
         "lineart": "serif", "crayon": "wenkai", "diffuse": "sans", "ink": "mashan", "neon": "kuaile"}

# where the little ingredients go, as fractions of the page, per theme (x, y, size, rotation)
SPOTS = {
    "watercolor": [(.16, .14, .1, -14), (.86, .2, .09, 18), (.82, .5, .1, -6), (.12, .48, .08, 12)],
    "papercut": [(.14, .36, .1, -10), (.86, .34, .09, 14), (.9, .62, .08, -8)],
    "riso": [(.88, .14, .09, -12), (.46, .93, .06, 20)],
    "clay": [(.16, .3, .08, 0), (.84, .26, .07, 0), (.86, .5, .06, 0)],
    "pop": [(.14, .16, .1, -16), (.84, .62, .1, 14), (.12, .58, .08, 8)],
    "lineart": [(.2, .2, .08, -10), (.8, .42, .08, 12)],
    "crayon": [(.14, .3, .09, -12), (.86, .28, .09, 16), (.84, .56, .08, -6)],
    "diffuse": [(.18, .22, .08, -10), (.82, .18, .07, 14), (.84, .5, .08, 0)],
    "ink": [(.2, .2, .08, -8), (.14, .52, .07, 10)],
    "neon": [(.2, .24, .08, -12), (.8, .48, .08, 10)],
}


def _f(fid, weight=400):
    return f"font-family:{stack(fid)};font-weight:{weight};"


def _hero(ctx, style, uid, x, y, w, h, rot=0, dress=True):
    """The drawing (or the AI cut-out) centred at x, y (px), w x h box."""
    a = ctx.item.get("art") or {}
    if a.get("image"):
        inner = art_block(ctx, a)
        if style == "papercut":
            inner = f'<div style="position:absolute;inset:0;filter:drop-shadow(0 {ctx.px(1.2)} {ctx.px(1.2)} rgba(58,42,32,.3))">{inner}</div>'
        elif style == "riso":  # overprint: the title shows through the picture like a second ink
            inner = f'<div style="position:absolute;inset:0;mix-blend-mode:multiply">{inner}</div>'
        elif style == "diffuse":
            inner = f'<div style="position:absolute;inset:0;filter:drop-shadow(0 {ctx.px(3)} {ctx.px(4)} {rgba(ctx.t["accent"], .35)})">{inner}</div>'
    else:
        draw = art.motif(a.get("motif") or "drink", ctx.t, f"{uid}h", a.get("drink"))
        inner = artstyle.dress(style, draw, ctx.t, uid, "hero") if dress else draw
    return (f'<div style="position:absolute;left:{x - w / 2:.0f}px;top:{y - h / 2:.0f}px;width:{w:.0f}px;height:{h:.0f}px;'
            f'transform:rotate({rot}deg);z-index:3">{inner}</div>')


def _bits(ctx, style, uid):
    a = ctx.item.get("art") or {}
    if a.get("image"):
        return ""  # the AI picture already carries its ingredients
    out = []
    W, H = ctx.W, ctx.H
    for i, (name, (x, y, s, rot)) in enumerate(zip(a.get("ingredients") or [], SPOTS.get(style, []))):
        size = s * W * 1.5
        draw = art.motif(name, ctx.t, f"{uid}b{i}")
        out.append(f'<div style="position:absolute;left:{x * W - size / 2:.0f}px;top:{y * H - size / 2:.0f}px;width:{size:.0f}px;height:{size:.0f}px;'
                   f'transform:rotate({rot}deg);z-index:2">{artstyle.dress(style, draw, ctx.t, uid, "bit")}</div>')
    return "".join(out)


def _brand(ctx, pc, x, y, color=None, on=None, extra=""):
    c = ctx.item["content"]
    u = ctx.u
    color, on = color or pc["ink"], on or pc["bg"]
    return (f'<div style="position:absolute;left:{x:.0f}px;top:{y:.0f}px;z-index:6;{extra}">'
            + T(ctx, "label", ctx.brand.get("name"), c=color, on=on, cls="d", style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;white-space:nowrap;")
            + (T(ctx, "caption", c.get("art_label"), c=mix(color, on, .3), on=on,
                 style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;letter-spacing:.24em;margin-top:{ctx.px(.8)};white-space:nowrap;") if c.get("art_label") else "")
            + "</div>")


def _tag_text(ctx, tags, color, on, size, sep="　·　"):
    if not tags:
        return ""
    return T(ctx, "label", sep.join(tags[:4]), c=color, on=on, style=f"font-size:{size:.1f}px;letter-spacing:.12em;white-space:nowrap;")


def _wrap(ctx, style, uid, pc, body, css=""):
    t = ctx.t
    return page(ctx, ctx._fonts_css, artstyle.defs(style, t, uid) + body,
                artstyle.css(style, t, uid) + f".pattern{{display:none}}.canvas,html,body{{background:{pc['bg']}}}" + css)


# ------------------------------------------------------------------ themes
def th_watercolor(ctx, uid, pc, bg):
    c, u, W, H, pad = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe
    wash = (f'<svg viewBox="0 0 {W:.0f} {H:.0f}" style="position:absolute;inset:0;z-index:1;mix-blend-mode:multiply" width="100%" height="100%">'
            f'<g filter="url(#wash{uid})"><path d="{artstyle._blob(__import__("random").Random(7), W * .3, H * .8, W * .34)}" fill="{pc["a2"]}" opacity=".28"/></g></svg>')
    text = (f'<div style="position:absolute;left:{pad * 1.2:.0f}px;right:{pad * 1.2:.0f}px;bottom:{pad * 1.4:.0f}px;z-index:5">'
            + T(ctx, "label", c.get("kicker"), c="accent_text", on=pc["bg"], style=f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;letter-spacing:.3em;")
            + T(ctx, "headline", c.get("headline"), c=pc["ink"], on=pc["bg"], fit=(14 * u, 7 * u),
                style=_f("xiaowei") + f"max-height:{ctx.px(19)};margin-top:{ctx.px(1.6)};letter-spacing:.06em;")
            + T(ctx, "sub", c.get("sub"), c=pc["muted"], on=pc["bg"], style=f"font-size:{max(ctx.minb, 3.4 * u):.1f}px;margin-top:{ctx.px(2)};max-width:{ctx.px(70)};")
            + f'<div style="margin-top:{ctx.px(2.6)}">' + _tag_text(ctx, c.get("tags"), "accent_text", pc["bg"], max(ctx.minc, 2.6 * u)) + "</div></div>")
    return bg + wash + _bits(ctx, "watercolor", uid) + _hero(ctx, "watercolor", uid, W * .55, H * .36, 64 * u, 84 * u) + _brand(ctx, pc, pad, pad) + text


def th_papercut(ctx, uid, pc, bg):
    c, u, W, H, pad, t = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe, ctx.t
    strip = lambda inner, rot, bgc, extra="": (f'<div style="display:inline-block;background:{bgc};padding:{ctx.px(2)} {ctx.px(4)};transform:rotate({rot}deg);'
                                               f'box-shadow:0 {ctx.px(.8)} {ctx.px(1.6)} rgba(58,42,32,.28);{extra}">{inner}</div>')
    head = T(ctx, "headline", c.get("headline"), c=t["ink"], on="#FFFFFF", fit=(12 * u, 6 * u), style=_f("kuaile") + f"max-height:{ctx.px(15)};white-space:nowrap;")
    sub = T(ctx, "sub", c.get("sub"), c=t["ink"], on=mix(t["accent2"], "#FFFFFF", .55), style=f"font-size:{max(ctx.minb, 3.1 * u):.1f}px;")
    top = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{pad * 2.4:.0f}px;z-index:5;display:flex;flex-direction:column;align-items:flex-start;gap:{ctx.px(2.6)}">'
           + strip(T(ctx, "label", c.get("kicker"), c=t["accent_text"], on="#FFFFFF", style=f"font-size:{max(ctx.minc, 2.5 * u):.1f}px;letter-spacing:.3em;"), 2, "#FFFFFF")
           + strip(head, -2.5, "#FFFFFF", "max-width:100%")
           + strip(sub, 1.2, mix(t["accent2"], "#FFFFFF", .55), f"margin-left:{ctx.px(6)};max-width:86%")
           + "</div>")
    hill = mix(pc["a1"], "#FFFFFF", .16)
    tags = "".join(f'<div style="background:#FFFFFF;padding:{ctx.px(1)} {ctx.px(2.6)} {ctx.px(1)} {ctx.px(4)};border-radius:{ctx.px(1)};position:relative;'
                   f'box-shadow:0 {ctx.px(.5)} {ctx.px(1)} rgba(58,42,32,.3);transform:rotate({(-3, 4, -2, 3)[i % 4]}deg)">'
                   f'<span style="position:absolute;left:{ctx.px(1.3)};top:50%;width:{ctx.px(1.1)};height:{ctx.px(1.1)};border-radius:50%;background:{hill};transform:translateY(-50%)"></span>'
                   + T(ctx, "label", tg, c=t["accent_text"], on="#FFFFFF", tag="span", style=f"font-size:{max(ctx.minc, 2.5 * u):.1f}px;font-weight:700;") + "</div>"
                   for i, tg in enumerate((c.get("tags") or [])[:3]))
    bottom = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;bottom:{pad:.0f}px;z-index:5;display:flex;justify-content:space-between;align-items:flex-end">'
              f'<div style="display:flex;gap:{ctx.px(2)}">{tags}</div>'
              + T(ctx, "label", ctx.brand.get("name"), c="#FFFFFF" if contrast("#FFFFFF", hill) >= 3 else t["ink"], on=hill, cls="d",
                  style=f"font-size:{max(ctx.minb, 3.3 * u):.1f}px;white-space:nowrap;") + "</div>")
    return bg + _bits(ctx, "papercut", uid) + _hero(ctx, "papercut", uid, W * .56, H * .62, 58 * u, 76 * u) + top + bottom


def th_riso(ctx, uid, pc, bg):
    c, u, W, H, pad = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe
    ink1 = pc["a1"]
    ink1s = mix(ink1, "#000000", .18)  # small type needs a darker pass of the same ink
    ink2 = pc["a2"] if contrast(pc["a2"], pc["bg"]) > 1.3 else "#2F6FDB"
    head = T(ctx, "headline", c.get("headline"), c=ink1, on=pc["bg"], fit=(24 * u, 11 * u),
             style=_f("sans", 900) + f"max-height:{ctx.px(56)};line-height:1.14;text-shadow:{ctx.px(.9)} {ctx.px(.7)} 0 {rgba(ink2, .8)};")
    text = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{pad * 2.6:.0f}px;z-index:2">'
            + T(ctx, "label", c.get("kicker"), c=ink1s, on=pc["bg"], style=f"font-size:{max(ctx.minc, 3 * u):.1f}px;letter-spacing:.2em;font-weight:700;")
            + f'<div style="height:{ctx.px(1)}"></div>' + head + "</div>")
    side = (f'<div style="position:absolute;left:{pad:.0f}px;bottom:{pad * 3.2:.0f}px;width:{ctx.px(38)};z-index:5">'
            + T(ctx, "sub", c.get("sub"), c=mix(ink2, "#000000", .45), on=pc["bg"], style=f"font-size:{max(ctx.minb, 3.2 * u):.1f}px;line-height:1.6;")
            + f'<div style="display:flex;gap:{ctx.px(1.6)};margin-top:{ctx.px(2.4)};flex-wrap:wrap">'
            + "".join(f'<span style="border:{ctx.px(.35)} solid {ink1};padding:{ctx.px(.6)} {ctx.px(1.8)}">'
                      + T(ctx, "label", tg, c=ink1s, on=pc["bg"], tag="span", style=f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;font-weight:700;") + "</span>"
                      for tg in (c.get("tags") or [])[:3]) + "</div></div>")
    foot = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;bottom:{pad:.0f}px;display:flex;justify-content:space-between;z-index:5">'
            + T(ctx, "label", ctx.brand.get("name"), c=ink1s, on=pc["bg"], cls="d", style=f"font-size:{max(ctx.minb, 2.8 * u):.1f}px;white-space:nowrap;")
            + T(ctx, "caption", c.get("art_label"), c=ink1s, on=pc["bg"], style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;letter-spacing:.3em;white-space:nowrap;")
            + "</div>")
    return bg + text + _bits(ctx, "riso", uid) + _hero(ctx, "riso", uid, W * .66, H * .66, 64 * u, 84 * u) + side + foot


def th_clay(ctx, uid, pc, bg):
    c, u, W, H, pad, t = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe, ctx.t
    ped_c = mix(pc["a1"], "#FFFFFF", .35)
    pedestal = (f'<div style="position:absolute;left:{W * .5 - 30 * u:.0f}px;top:{H * .55:.0f}px;width:{ctx.px(60)};height:{ctx.px(13)};border-radius:{ctx.px(6.5)};'
                f'background:{ped_c};filter:url(#cl{uid});z-index:2"></div>')
    pill_c = mix(pc["bg"], "#FFFFFF", .75)
    pill = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{H * .7:.0f}px;height:{ctx.px(19)};border-radius:{ctx.px(9.5)};'
            f'background:{pill_c};filter:url(#cl{uid});z-index:3"></div>')
    text = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{H * .7:.0f}px;height:{ctx.px(19)};display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;z-index:5;padding:0 {ctx.px(5)}">'
            + T(ctx, "headline", c.get("headline"), c=t["ink"], on=pill_c, fit=(11 * u, 6 * u), style=_f("kuaile") + f"max-height:{ctx.px(13)};white-space:nowrap;letter-spacing:.06em;")
            + "</div>")
    below = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{H * .7 + 22 * u:.0f}px;display:flex;flex-direction:column;align-items:center;gap:{ctx.px(2.4)};z-index:5">'
             + T(ctx, "sub", c.get("sub"), c=pc["muted"], on=pc["bg"], style=f"font-size:{max(ctx.minb, 3.2 * u):.1f}px;text-align:center;")
             + f'<div style="display:flex;gap:{ctx.px(2)}">'
             + "".join(f'<div style="position:relative;padding:{ctx.px(1)} {ctx.px(3)}">'
                       f'<div style="position:absolute;inset:0;border-radius:{ctx.px(4)};background:{(pc["a1"], pc["a2"], ped_c)[i % 3]};filter:url(#cl{uid})"></div>'
                       + T(ctx, "label", tg, c="#FFFFFF" if contrast("#FFFFFF", (pc["a1"], pc["a2"], ped_c)[i % 3]) > 3 else t["ink"],
                           on=(pc["a1"], pc["a2"], ped_c)[i % 3], style=f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;font-weight:700;position:relative;") + "</div>"
                       for i, tg in enumerate((c.get("tags") or [])[:3])) + "</div></div>")
    return (bg + pedestal + _bits(ctx, "clay", uid) + _hero(ctx, "clay", uid, W * .5, H * .36, 54 * u, 70 * u)
            + pill + text + below + _brand(ctx, pc, pad, pad))


def th_pop(ctx, uid, pc, bg):
    c, u, W, H, pad, t = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe, ctx.t
    frame = f'<div style="position:absolute;inset:{ctx.px(2.4)};border:{ctx.px(1.4)} solid #111111;z-index:4;pointer-events:none"></div>'
    title_c = t["accent"] if contrast(t["accent"], "#FFFFFF") >= 3 else "#E63946"
    bubble = (f'<div data-grp="bubble" style="position:absolute;left:{pad:.0f}px;right:{pad * 1.4:.0f}px;top:{H * .68:.0f}px;z-index:5;transform:rotate(-3deg);'
              f'background:#FFFFFF;border:{ctx.px(1)} solid #111111;border-radius:{ctx.px(5)};padding:{ctx.px(3)} {ctx.px(4)};box-shadow:{ctx.px(1.4)} {ctx.px(1.4)} 0 #111111">'
              + T(ctx, "headline", c.get("headline"), c=title_c, on="#FFFFFF", fit=(13 * u, 6 * u),
                  style=_f("sans", 900) + f"max-height:{ctx.px(16)};white-space:nowrap;-webkit-text-stroke:{ctx.px(.35)} #111111;text-shadow:{ctx.px(.6)} {ctx.px(.6)} 0 #111111;")
              + T(ctx, "sub", c.get("sub"), c="#111111", on="#FFFFFF", style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;font-weight:700;margin-top:{ctx.px(1.6)};")
              + f'<div style="position:absolute;left:{ctx.px(10)};top:100%;width:0;height:0;border-left:{ctx.px(3)} solid transparent;border-right:{ctx.px(3)} solid transparent;border-top:{ctx.px(4.5)} solid #111111"></div>'
              + "</div>")
    tags = (c.get("tags") or [])[:2]
    burst = ""
    if tags:
        s = 22 * u
        import math
        pts = " ".join(f"{50 + (50 if k % 2 == 0 else 36) * math.cos(math.radians(k * 18)):.1f},{50 + (50 if k % 2 == 0 else 36) * math.sin(math.radians(k * 18)):.1f}" for k in range(20))
        burst = (f'<div data-grp="burst" style="position:absolute;right:{pad * 1.1:.0f}px;top:{pad * 1.8:.0f}px;width:{s:.0f}px;height:{s:.0f}px;transform:rotate(12deg);z-index:5">'
                 f'<svg viewBox="-4 -4 108 108" style="position:absolute;inset:0" width="100%" height="100%"><polygon points="{pts}" fill="{title_c}" stroke="#111111" stroke-width="4"/></svg>'
                 f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">'
                 + T(ctx, "label", "\n".join(tags), c="#FFFFFF", on=title_c, style=f"font-size:{max(ctx.minc, 3 * u):.1f}px;font-weight:900;white-space:nowrap;text-align:center;line-height:1.25;")
                 + "</div></div>")
    return (bg + _bits(ctx, "pop", uid) + _hero(ctx, "pop", uid, W * .5, H * .4, 60 * u, 78 * u, rot=-8) + frame + burst + bubble
            + _brand(ctx, pc, pad * 1.1, pad * 1.1, color="#111111", on=pc["bg"]))


def th_lineart(ctx, uid, pc, bg):
    c, u, W, H, pad, t = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe, ctx.t
    num = "".join(ch for ch in str(c.get("kicker") or "") if ch.isdigit())[-2:] or "01"
    giant = T(ctx, "label", num, c=t["accent"], on=pc["bg"],
              style=_f("serif", 700) + f"position:absolute;left:{pad:.0f}px;top:{pad * 1.6:.0f}px;font-size:{ctx.px(30)};line-height:1;color:transparent;"
              f"-webkit-text-stroke:{max(1.5, .25 * u):.1f}px {t['accent']};z-index:1;letter-spacing:-.02em;")
    text = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{H * .68:.0f}px;display:flex;flex-direction:column;align-items:center;z-index:5;text-align:center">'
            + f'<div style="width:{ctx.px(12)};height:1px;background:{pc["ink"]};margin-bottom:{ctx.px(3.4)}"></div>'
            + T(ctx, "headline", c.get("headline"), c=pc["ink"], on=pc["bg"], fit=(9.5 * u, 5 * u), style=_f("serif", 400) + f"max-height:{ctx.px(12)};letter-spacing:.32em;white-space:nowrap;")
            + T(ctx, "sub", c.get("sub"), c=pc["muted"], on=pc["bg"], style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;margin-top:{ctx.px(2.6)};")
            + f'<div style="margin-top:{ctx.px(3)}">' + _tag_text(ctx, c.get("tags"), "accent_text", pc["bg"], max(ctx.minc, 2.4 * u), "　/　") + "</div></div>")
    foot = (f'<div style="position:absolute;left:0;right:0;bottom:{pad:.0f}px;display:flex;justify-content:center;z-index:5">'
            + T(ctx, "label", ctx.brand.get("name"), c=pc["ink"], on=pc["bg"], cls="d", style=f"font-size:{max(ctx.minb, 2.6 * u):.1f}px;letter-spacing:.4em;white-space:nowrap;")
            + "</div>")
    return bg + giant + _bits(ctx, "lineart", uid) + _hero(ctx, "lineart", uid, W * .5, H * .4, 54 * u, 70 * u) + text + foot


def th_crayon(ctx, uid, pc, bg):
    c, u, W, H, pad, t = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe, ctx.t
    y0 = H * .7
    mark = (f'<svg viewBox="0 0 {W:.0f} {H:.0f}" width="100%" height="100%" style="position:absolute;inset:0;z-index:3">'
            f'<g filter="url(#cr{uid})"><path d="M{pad:.0f} {y0 + 8.5 * u:.0f} Q{W * .3:.0f} {y0 + 6 * u:.0f} {W * .55:.0f} {y0 + 8 * u:.0f} T{W - pad * 2:.0f} {y0 + 7 * u:.0f}" '
            f'stroke="{pc["a2"]}" stroke-width="{ctx.px(5.4).replace("px", "")}" fill="none" stroke-linecap="round" opacity=".75"/></g></svg>')
    text = (f'<div style="position:absolute;left:{pad * 1.5:.0f}px;right:{pad * 1.6:.0f}px;top:{y0:.0f}px;z-index:5">'
            + T(ctx, "headline", c.get("headline"), c=pc["ink"], on=mix(pc["a2"], pc["bg"], .3), fit=(13 * u, 7 * u),
                style=_f("wenkai", 700) + f"max-height:{ctx.px(16)};white-space:nowrap;transform:rotate(-2deg);transform-origin:center;")
            + T(ctx, "sub", c.get("sub"), c=pc["ink"], on=pc["bg"], style=_f("wenkai") + f"font-size:{max(ctx.minb, 3.4 * u):.1f}px;margin-top:{ctx.px(3)};")
            + f'<div style="display:flex;gap:{ctx.px(3)};margin-top:{ctx.px(2.6)}">'
            + "".join(f'<span style="border:{ctx.px(.45)} solid {pc["a1"]};border-radius:50% 46% 52% 48%;padding:{ctx.px(.8)} {ctx.px(2.6)};filter:url(#cr{uid})">'
                      + T(ctx, "label", tg, c=mix(pc["a1"], "#000000", .2), on=pc["bg"], tag="span", style=_f("wenkai", 700) + f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;") + "</span>"
                      for tg in (c.get("tags") or [])[:3]) + "</div></div>")
    return (bg + _bits(ctx, "crayon", uid) + _hero(ctx, "crayon", uid, W * .5, H * .42, 58 * u, 76 * u) + mark + text
            + _brand(ctx, pc, pad, pad))


def th_diffuse(ctx, uid, pc, bg):
    c, u, W, H, pad, t = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe, ctx.t
    card_bg = mix(pc["bg"], "#FFFFFF", .55)
    card = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{H * .66:.0f}px;bottom:{pad:.0f}px;z-index:5;border-radius:{ctx.px(4)};'
            f'background:{rgba("#FFFFFF", .42)};border:1px solid {rgba("#FFFFFF", .7)};-webkit-backdrop-filter:blur({ctx.px(2.4)});backdrop-filter:blur({ctx.px(2.4)});'
            f'box-shadow:0 {ctx.px(2)} {ctx.px(5)} {rgba(t["ink"], .08)};padding:{ctx.px(4)} {ctx.px(5)};display:flex;flex-direction:column">'
            + T(ctx, "label", c.get("kicker"), c="accent_text", on=card_bg, style=f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;letter-spacing:.3em;font-weight:700;")
            + T(ctx, "headline", c.get("headline"), c=t["ink"], on=card_bg, fit=(11 * u, 6 * u), style=_f("sans", 700) + f"max-height:{ctx.px(14)};margin-top:{ctx.px(1.4)};white-space:nowrap;")
            + T(ctx, "sub", c.get("sub"), c=mix(t["ink"], card_bg, .25), on=card_bg, style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;margin-top:{ctx.px(1.6)};")
            + f'<div style="flex:1"></div><div style="display:flex;justify-content:space-between;align-items:center">'
            + f'<div style="display:flex;gap:{ctx.px(1.6)}">'
            + "".join(f'<span style="background:{rgba("#FFFFFF", .7)};border-radius:{ctx.px(3)};padding:{ctx.px(.7)} {ctx.px(2.2)}">'
                      + T(ctx, "label", tg, c="accent_text", on="#FFFFFF", tag="span", style=f"font-size:{max(ctx.minc, 2.3 * u):.1f}px;font-weight:700;") + "</span>"
                      for tg in (c.get("tags") or [])[:3]) + "</div>"
            + T(ctx, "label", ctx.brand.get("name"), c=t["ink"], on=card_bg, cls="d", style=f"font-size:{max(ctx.minb, 2.6 * u):.1f}px;white-space:nowrap;")
            + "</div></div>")
    lab = T(ctx, "caption", c.get("art_label"), c=pc["muted"], on=pc["bg"], style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;letter-spacing:.3em;white-space:nowrap;")
    return (bg + _bits(ctx, "diffuse", uid) + _hero(ctx, "diffuse", uid, W * .5, H * .36, 58 * u, 76 * u) + card
            + f'<div style="position:absolute;left:{pad:.0f}px;top:{pad:.0f}px;z-index:5">{lab}</div>')


def th_ink(ctx, uid, pc, bg):
    c, u, W, H, pad = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe
    ink = "#222222"
    col = (f'<div style="position:absolute;right:{pad * 1.3:.0f}px;top:{pad * 1.6:.0f}px;display:flex;flex-direction:row-reverse;gap:{ctx.px(3)};z-index:5;align-items:flex-start">'
           + T(ctx, "label", c.get("headline"), c=ink, on=pc["bg"],
               style=_f("mashan") + f"writing-mode:vertical-rl;font-size:{ctx.px(13)};line-height:1.05;letter-spacing:.12em;max-height:{H * .62:.0f}px;")
           + T(ctx, "label", c.get("sub"), c=mix(ink, pc["bg"], .25), on=pc["bg"],
               style=f"writing-mode:vertical-rl;font-size:{max(ctx.minb, 3 * u):.1f}px;line-height:1.8;letter-spacing:.2em;max-height:{H * .5:.0f}px;margin-top:{ctx.px(8)};")
           + "</div>")
    seal_c = "#B8332B"
    name = (f'<div style="position:absolute;right:{pad * 1.3:.0f}px;top:{H * .7:.0f}px;background:{seal_c};padding:{ctx.px(1.4)} {ctx.px(1)};z-index:5;border-radius:{ctx.px(.6)}">'
            + T(ctx, "label", ctx.brand.get("name"), c="#FFFFFF", on=seal_c, style=_f("mashan") + f"writing-mode:vertical-rl;font-size:{max(ctx.minb, 3.2 * u):.1f}px;letter-spacing:.1em;")
            + "</div>")
    foot = (f'<div style="position:absolute;left:{pad:.0f}px;bottom:{pad:.0f}px;z-index:5">'
            + T(ctx, "label", c.get("kicker"), c=seal_c, on=pc["bg"], style=f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;letter-spacing:.3em;")
            + f'<div style="height:{ctx.px(1.2)}"></div>' + _tag_text(ctx, c.get("tags"), mix(ink, pc["bg"], .3), pc["bg"], max(ctx.minc, 2.4 * u), "　")
            + "</div>")
    return bg + _bits(ctx, "ink", uid) + _hero(ctx, "ink", uid, W * .4, H * .5, 56 * u, 74 * u) + col + name + foot


def th_neon(ctx, uid, pc, bg):
    c, u, W, H, pad = ctx.item["content"], ctx.u, ctx.W, ctx.H, ctx.safe
    c1 = mix(pc["a1"], "#FFFFFF", .35)
    c2 = "#5CF2FF" if contrast(pc["a1"], "#5CF2FF") > 1.4 else "#FF7AD9"
    glow = lambda col: f"text-shadow:0 0 {ctx.px(.6)} #FFFFFF,0 0 {ctx.px(1.6)} {col},0 0 {ctx.px(3.6)} {col},0 0 {ctx.px(7)} {col};"
    inset = W * .11
    text = (f'<div style="position:absolute;left:{inset:.0f}px;right:{inset:.0f}px;top:{H * .66:.0f}px;display:flex;flex-direction:column;align-items:center;z-index:5;text-align:center">'
            + T(ctx, "label", c.get("kicker"), c=c2, on=pc["bg"], style=f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;letter-spacing:.4em;" + glow(c2))
            + T(ctx, "headline", c.get("headline"), c="#FFF4EC", on=pc["bg"], fit=(12 * u, 6 * u), style=_f("kuaile") + f"max-height:{ctx.px(15)};white-space:nowrap;margin-top:{ctx.px(1.6)};" + glow(c1))
            + T(ctx, "sub", c.get("sub"), c=mix("#FFFFFF", pc["bg"], .25), on=pc["bg"], style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;margin-top:{ctx.px(2)};")
            + f'<div style="display:flex;gap:{ctx.px(2.4)};margin-top:{ctx.px(3)}">'
            + "".join(f'<span style="border:{ctx.px(.35)} solid {c2};border-radius:{ctx.px(4)};padding:{ctx.px(.7)} {ctx.px(2.6)};box-shadow:0 0 {ctx.px(1.4)} {c2},inset 0 0 {ctx.px(1)} {c2}">'
                      + T(ctx, "label", tg, c="#FFFFFF", on=pc["bg"], tag="span", style=f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;font-weight:700;") + "</span>"
                      for tg in (c.get("tags") or [])[:3]) + "</div></div>")
    return (bg + _bits(ctx, "neon", uid) + _hero(ctx, "neon", uid, W * .5, H * .36, 52 * u, 68 * u) + text
            + _brand(ctx, pc, inset + 2 * u, inset * 1.05, color="#FFFFFF", on=pc["bg"]))


THEMES = {"watercolor": th_watercolor, "papercut": th_papercut, "riso": th_riso, "clay": th_clay, "pop": th_pop,
          "lineart": th_lineart, "crayon": th_crayon, "diffuse": th_diffuse, "ink": th_ink, "neon": th_neon}


def themed(ctx, fonts_css, style):
    """Full-poster theme for a portrait art-hero. Returns None when this size has no theme."""
    if style not in THEMES or ctx.o != "portrait":
        return None
    uid = ctx.nid("th")
    ctx._fonts_css = fonts_css
    seed = sum(ord(ch) for ch in ctx.item.get("id", "x"))
    bg, pc = artstyle.panel(style, ctx.t, uid, ctx.W, ctx.H, seed, full_page=True)
    body = THEMES[style](ctx, uid, pc, bg)
    return _wrap(ctx, style, uid, pc, body)
