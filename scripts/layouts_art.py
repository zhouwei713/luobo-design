"""Art-led posters: the picture is the hero and the type steps back.

art-hero   a big art panel (full bleed) in one of the art styles, the copy underneath (or beside it)
art-frame  the art hung like a print: frame, white mat, a museum-style label under it

art.style picks the look (artstyle.STYLES); art.motif is the drawing ("drink" + art.drink for a
described cup), art.ingredients scatters small drawings around it. Works with no image model;
with one, art.image replaces the drawing and the style goes into the prompts.
"""
import art
import artstyle
from common import esc, mix, rgba
from layouts import T, art_block, brand_mark, page


def _style(ctx):
    a = ctx.item.get("art") or {}
    s = a.get("style") or "flat"
    return s if s in artstyle.STYLES else "flat"


def _art_layer(ctx, style, uid, pw, ph, hero_frac=.6, place=(.5, .54)):
    """The panel background, the hero drawing and the scattered ingredients, all in one style."""
    a = ctx.item.get("art") or {}
    seed = sum(ord(ch) for ch in ctx.item.get("id", "x"))
    bg, pc = artstyle.panel(style, ctx.t, uid, pw, ph, seed)
    m = min(pw, ph)
    out = [bg]
    for i, name in enumerate((a.get("ingredients") or [])[:6]):
        x, y, s, rot = artstyle.SCATTER[i]
        size = s * m * 1.9
        draw = art.motif(name, ctx.t, f"{uid}i{i}")
        out.append(f'<div style="position:absolute;left:{x * pw - size / 2:.0f}px;top:{y * ph - size / 2:.0f}px;width:{size:.0f}px;height:{size:.0f}px;'
                   f'transform:rotate({rot}deg)">{artstyle.dress(style, draw, ctx.t, uid, "bit")}</div>')
    if a.get("image"):
        hero = art_block(ctx, a)
    else:
        hero = art.motif(a.get("motif") or "drink", ctx.t, f"{uid}h", a.get("drink"))
    hw = m * hero_frac
    hh = hw * 1.3 if (a.get("motif") or "drink") == "drink" or a.get("image") else hw  # cups and AI cut-outs are tall
    hh = min(hh, ph * .86)
    out.append(f'<div style="position:absolute;left:{place[0] * pw - hw / 2:.0f}px;top:{place[1] * ph - hh / 2:.0f}px;width:{hw:.0f}px;height:{hh:.0f}px">'
               f'{artstyle.dress(style, hero, ctx.t, uid, "hero") if not a.get("image") else hero}</div>')
    return "".join(out), pc


def _tags(ctx, tags, size):
    t = ctx.t
    if not tags:
        return ""
    chips = "".join(
        f'<span style="display:inline-flex;align-items:center;padding:{size * .3:.0f}px {size * .7:.0f}px;border:{max(1.5, size * .08):.1f}px solid {t["accent"]};'
        f'border-radius:{size:.0f}px;white-space:nowrap">'
        + T(ctx, "label", tg, c="accent_text", tag="span", style=f"font-size:{size:.1f}px;font-weight:700;letter-spacing:.06em;")
        + "</span>" for tg in tags[:4])
    return f'<div style="display:flex;flex-wrap:wrap;gap:{size * .6:.0f}px">{chips}</div>'


def poster_art_hero(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    style = _style(ctx)
    if (ctx.item.get("art") or {}).get("theme", True):  # the style dresses the whole poster where it has a theme
        import layouts_artthemes
        themed = layouts_artthemes.themed(ctx, fonts_css, style)
        if themed:
            return themed
    uid = ctx.nid("as")
    W, H, pad = ctx.W, ctx.H, ctx.safe
    if o == "portrait":
        pw, ph = W, H * (.64 if ctx.cv["ar"] > .6 else .58)
        pbox = f"left:0;top:0;width:{pw:.0f}px;height:{ph:.0f}px"
        tbox = f"left:{pad:.0f}px;right:{pad:.0f}px;top:{ph + pad * .9:.0f}px;bottom:{pad:.0f}px"
    elif o == "square":
        pw, ph = W * .56, H
        pbox = f"left:0;top:0;width:{pw:.0f}px;height:{ph:.0f}px"
        tbox = f"left:{pw + pad:.0f}px;right:{pad:.0f}px;top:{pad:.0f}px;bottom:{pad:.0f}px"
    else:
        pw, ph = W * .52, H
        pbox = f"left:0;top:0;width:{pw:.0f}px;height:{ph:.0f}px"
        tbox = f"left:{pw + pad * 1.2:.0f}px;right:{pad * 1.2:.0f}px;top:{pad * 1.2:.0f}px;bottom:{pad * 1.2:.0f}px"
    layer, pc = _art_layer(ctx, style, uid, pw, ph, hero_frac=.62 if o == "portrait" else .66)
    on_panel = (T(ctx, "label", ctx.brand.get("name"), c=pc["ink"], on=pc["bg"], cls="d",
                  style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;white-space:nowrap;")
                + (T(ctx, "caption", c.get("art_label"), c=pc["muted"], on=pc["bg"],
                     style=f"font-size:{max(ctx.minc, 2.1 * u):.1f}px;letter-spacing:.24em;margin-top:{ctx.px(.8)};white-space:nowrap;")
                   if c.get("art_label") else ""))
    panel = (f'<div style="position:absolute;{pbox};overflow:hidden;z-index:2">{layer}'
             f'<div style="position:absolute;left:{pad:.0f}px;top:{pad:.0f}px;z-index:6">{on_panel}</div></div>')
    head_max = {"portrait": 12, "square": 8.5, "landscape": 9}[o] * u
    offer = c.get("offer") or {}
    price = (f'<div style="display:flex;align-items:baseline;gap:{ctx.px(1)}">'
             + T(ctx, "price", offer.get("big"), c="accent_text", cls="d", style=f"font-size:{ctx.px(6)};line-height:1;white-space:nowrap;")
             + T(ctx, "caption", offer.get("small"), c="muted", style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;white-space:nowrap;")
             + "</div>") if offer.get("big") else ""
    text = (T(ctx, "label", c.get("kicker"), c="accent_text", style=f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;letter-spacing:.3em;font-weight:700;")
            + f'<div style="height:{ctx.px(1.4)}"></div>'
            + T(ctx, "headline", c.get("headline"), cls="d", fit=(head_max, max(ctx.minb * 1.4, 4.5 * u)),
                style=f"max-height:{ctx.px(24 if o != 'portrait' else 15)};flex:none;")
            + f'<div style="height:{ctx.px(1.8)}"></div>'
            + T(ctx, "sub", c.get("sub"), c="muted", fit=(max(ctx.minb, 3.3 * u), ctx.minb),
                style=f"max-height:{ctx.px(16 if o != 'portrait' else 10)};flex:none;")
            + f'<div style="height:{ctx.px(2.4)}"></div>'
            + _tags(ctx, c.get("tags"), max(ctx.minc, 2.5 * u))
            + f'<div style="flex:1 1 auto;min-height:{ctx.px(2)}"></div>'
            + f'<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)}">'
            + f'<div style="min-width:0">{price}'
            + T(ctx, "body", c.get("cta"), style=f"font-size:{max(ctx.minb, 2.5 * u):.1f}px;font-weight:700;margin-top:{ctx.px(.8)};")
            + "</div>"
            + T(ctx, "caption", c.get("note"), c="muted", cls="d", style=f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;text-align:right;white-space:nowrap;letter-spacing:.12em;")
            + "</div>")
    body = (artstyle.defs(style, t, uid) + panel
            + f'<div style="position:absolute;{tbox};display:flex;flex-direction:column;z-index:3">{text}</div>')
    return page(ctx, fonts_css, body, artstyle.css(style, t, uid) + ".pattern{opacity:.35}")


def poster_art_frame(ctx, fonts_css):
    c, t, u, o = ctx.item["content"], ctx.t, ctx.u, ctx.o
    style = _style(ctx)
    uid = ctx.nid("af")
    W, H, pad = ctx.W, ctx.H, ctx.safe
    mat = 3.2 * u
    border = max(3, .9 * u)
    if o == "landscape":
        fh = H - 2 * pad - 2 * u
        fw = fh * .8
        fx, fy = pad * 1.6, (H - fh) / 2
        label_box = f"left:{fx + fw + pad * 1.4:.0f}px;right:{pad * 1.4:.0f}px;top:0;bottom:0;justify-content:center;align-items:flex-start;text-align:left"
    else:
        fw = W * (.74 if o == "portrait" else .5)
        fh = fw * 1.25
        group = fh + 3.4 * u + 20 * u  # frame plus the label under it, centred as one block
        fx, fy = (W - fw) / 2, max(pad, (H - group) / 2)
        label_box = f"left:{pad:.0f}px;right:{pad:.0f}px;top:{fy + fh + 3.4 * u:.0f}px;bottom:{pad:.0f}px;align-items:center;text-align:center"
    iw, ih = fw - 2 * (mat + border), fh - 2 * (mat + border)
    layer, pc = _art_layer(ctx, style, uid, iw, ih, hero_frac=.62)
    frame = (f'<div style="position:absolute;left:{fx:.0f}px;top:{fy:.0f}px;width:{fw:.0f}px;height:{fh:.0f}px;z-index:2;'
             f'background:#FFFFFF;border:{border:.0f}px solid {mix(t["ink"], t["bg"], .1)};padding:{mat:.0f}px;'
             f'box-shadow:0 {2 * u:.0f}px {4 * u:.0f}px {rgba(t["ink"], .18)}">'
             f'<div style="position:relative;width:{iw:.0f}px;height:{ih:.0f}px;overflow:hidden;box-shadow:inset 0 0 0 1px {rgba(t["ink"], .08)}">{layer}</div></div>')
    head = {"portrait": 6.5, "square": 5.2, "landscape": 7}[o] * u
    st = artstyle.STYLES[style]
    label = (T(ctx, "headline", c.get("headline"), cls="d", fit=(head, max(ctx.minb * 1.3, 3.6 * u)),
               style=f"max-height:{ctx.px(16)};flex:none;width:100%;")
             + f'<div style="height:{ctx.px(1.2)}"></div>'
             + T(ctx, "sub", c.get("sub"), c="muted", fit=(max(ctx.minb, 2.6 * u), ctx.minb), style=f"max-height:{ctx.px(9)};flex:none;width:100%;")
             + f'<div style="height:{ctx.px(1.6)}"></div>'
             + T(ctx, "caption", c.get("art_label") or f"{st['name']} · {ctx.brand.get('name') or ''}".strip(" ·"), c="accent_text",
                 style=f"font-size:{max(ctx.minc, 2 * u):.1f}px;letter-spacing:.28em;white-space:nowrap;"))
    body = (artstyle.defs(style, t, uid) + frame
            + f'<div style="position:absolute;{label_box};display:flex;flex-direction:column;z-index:3">{label}</div>')
    return page(ctx, fonts_css, body, artstyle.css(style, t, uid))


def register(builders, layouts):
    layouts["poster"] = list(dict.fromkeys(layouts["poster"] + ["art-hero", "art-frame"]))
    builders[("poster", "art-hero")] = poster_art_hero
    builders[("poster", "art-frame")] = poster_art_frame
