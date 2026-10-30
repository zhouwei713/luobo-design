"""Brand kit: three logo options as real vector files, plus a one-page brand board.

Item type "brandkit", layout "board". Content: name, tagline, monogram (optional, default the first
character of the name), name_en (optional). art.motif gives option C its icon.

Logos are built from outlined glyphs (outline.py), so the SVGs need no fonts. Files written by
render.py: logos/<A|B|C>-<kind>.svg, -reversed.svg, B-icon.svg, and PNG copies.
"""
import art
from common import esc, mix, rgba
from layouts import T, page, plain
from outline import outline_text


def _text_svg(text, fid, weight, size, tracking, color):
    """(svg fragment, width, height). Falls back to live text when outlining is impossible."""
    from layouts import BAD_GLYPHS
    if any(ch in text for ch in BAD_GLYPHS.get(fid, "")):  # a logo people misread is worse than a plainer font
        fid, weight = "sans", 900
    r = outline_text(text, fid, weight, size, tracking)
    if r:
        d, w, h, asc = r
        return f'<path d="{d}" fill="{color}"/>', w, h, True
    from fonts import stack
    w = size * len(text) * (1 + tracking)
    return (f'<text x="0" y="{size * 0.88:.1f}" font-size="{size}" font-family="{stack(fid)}" font-weight="{weight}" '
            f'letter-spacing="{tracking}em" fill="{color}">{esc(text)}</text>'), w, size * 1.12, False


def _svg(w, h, body, pad=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad:.1f} {-pad:.1f} {w + 2 * pad:.1f} {h + 2 * pad:.1f}" '
            f'width="{w + 2 * pad:.0f}" height="{h + 2 * pad:.0f}">{body}</svg>')


def wordmark(name, tagline, d, ink, accent, sub):
    disp, body = d["display"], d["body"]
    frag, w, h, ok = _text_svg(name, disp["font"], disp.get("weight", 700), 100, max(0.04, disp.get("tracking", 0)), ink)
    out = [frag]
    y = h + 10
    deco = d["shape"].get("deco")
    if deco in ("sticker", "soft"):
        out.append(f'<circle cx="{w + 26:.1f}" cy="{h * 0.72:.1f}" r="13" fill="{accent}"/>')
        w += 40
    else:
        out.append(f'<rect x="0" y="{y:.1f}" width="{w * 0.32:.1f}" height="7" fill="{accent}"/>')
        y += 18
    if tagline:
        tf, tw, th, _ = _text_svg(tagline, body["font"], 400, 30, 0.2, sub)
        out.append(f'<g transform="translate(0 {y + 6:.1f})">{tf}</g>')
        y += th + 6
        w = max(w, tw)
    return _svg(w, y, "".join(out), pad=8), ok


def emblem_shape(d, s, fill, line):
    deco = d["shape"].get("deco")
    if deco == "seal":
        return (f'<rect x="0" y="0" width="{s}" height="{s}" rx="{s * 0.06:.1f}" fill="{fill}"/>'
                f'<rect x="{s * 0.07:.1f}" y="{s * 0.07:.1f}" width="{s * 0.86:.1f}" height="{s * 0.86:.1f}" rx="{s * 0.03:.1f}" '
                f'fill="none" stroke="{line}" stroke-width="{s * 0.025:.1f}"/>')
    if deco == "sticker":
        return f'<rect x="0" y="0" width="{s}" height="{s}" rx="{s * 0.28:.1f}" fill="{fill}"/>'
    if deco == "line":
        return f'<circle cx="{s / 2}" cy="{s / 2}" r="{s / 2 - s * 0.03:.1f}" fill="none" stroke="{fill}" stroke-width="{s * 0.05:.1f}"/>'
    return f'<circle cx="{s / 2}" cy="{s / 2}" r="{s / 2}" fill="{fill}"/>'


def emblem_icon(mono, d, fill, glyph_c):
    """The mark alone, square: avatar, app icon, favicon."""
    s = 240
    deco = d["shape"].get("deco")
    gc = fill if deco == "line" else glyph_c
    disp = d["display"]
    frag, w, h, ok = _text_svg(mono, disp["font"], disp.get("weight", 700), 150, 0, gc)
    gx, gy = (s - w) / 2, (s - h) / 2 + 4
    return _svg(s, s, emblem_shape(d, s, fill, glyph_c) + f'<g transform="translate({gx:.1f} {gy:.1f})">{frag}</g>'), ok


def emblem(name, mono, d, ink, fill, glyph_c):
    icon, ok = emblem_icon(mono, d, fill, glyph_c)
    inner = icon[icon.index(">") + 1:icon.rindex("</svg>")]
    disp = d["display"]
    nf, nw, nh, _ = _text_svg(name, disp["font"], disp.get("weight", 700), 56, max(0.06, disp.get("tracking", 0)), ink)
    W = max(240, nw)
    body = (f'<g transform="translate({(W - 240) / 2:.1f} 0)">{inner}</g>'
            f'<g transform="translate({(W - nw) / 2:.1f} 262)">{nf}</g>')
    return _svg(W, 262 + nh, body, pad=8), ok


def combination(name, tagline, motif, d, t, ink, sub, on_dark=False):
    s = 150
    tt = dict(t)
    if on_dark:
        tt.update({"ink": t["on_accent"], "surface": mix(t["accent"], "#FFFFFF", .85)})
    icon = art.motif(motif, tt, "lg" + motif.replace("-", "")) if motif else ""
    if icon:
        icon = icon.replace('width="100%" height="100%"', f'width="{s}" height="{s}"')
    disp, body = d["display"], d["body"]
    nf, nw, nh, ok = _text_svg(name, disp["font"], disp.get("weight", 700), 84, max(0.04, disp.get("tracking", 0)), ink)
    x = s + 28 if icon else 0
    parts = [f'<g transform="translate(0 0)">{icon}</g>' if icon else "",
             f'<g transform="translate({x} {(s - nh) / 2 - (18 if tagline else 0):.1f})">{nf}</g>']
    w = x + nw
    if tagline:
        tf, tw, th, _ = _text_svg(tagline, body["font"], 400, 26, 0.18, sub)
        parts.append(f'<g transform="translate({x + 3} {(s - nh) / 2 + nh - 6:.1f})">{tf}</g>')
        w = max(w, x + tw)
    return _svg(w, s, "".join(parts), pad=8), ok


def make_logos(item, brand, d):
    c = item.get("content") or {}
    t = d["tokens"]
    name = plain(c.get("name") or brand.get("name") or "品牌")
    mono = plain(c.get("monogram") or name[0])
    tagline = plain(c.get("tagline") or brand.get("tagline") or "")
    motif = (item.get("art") or {}).get("motif")
    light_on_accent = t["on_accent"]
    logos = {}
    svg, ok1 = wordmark(name, tagline, d, t["ink"], t["accent"], t["muted"])
    rev, _ = wordmark(name, tagline, d, light_on_accent, t["accent2"] if t["accent2"] != t["accent"] else light_on_accent, light_on_accent)
    logos["A"] = {"kind": "wordmark", "label": "文字标", "svg": svg, "reversed": rev}
    svg, ok2 = emblem(name, mono, d, t["ink"], t["accent"], t["on_accent"])
    rev, _ = emblem(name, mono, d, light_on_accent, light_on_accent if d["shape"].get("deco") != "line" else light_on_accent, t["accent"])
    icon, _ = emblem_icon(mono, d, t["accent"], t["on_accent"])
    logos["B"] = {"kind": "emblem", "label": "图形标", "svg": svg, "reversed": rev, "icon": icon}
    svg, ok3 = combination(name, tagline, motif, d, t, t["ink"], t["muted"])
    rev, _ = combination(name, tagline, motif, d, t, light_on_accent, light_on_accent, on_dark=True)
    logos["C"] = {"kind": "combination", "label": "组合标", "svg": svg, "reversed": rev}
    logos["_outlined"] = ok1 and ok2 and ok3
    return logos


def _fit_svg(svg, max_w, max_h):
    """Inline an SVG scaled into a box."""
    return svg.replace("<svg ", f'<svg style="max-width:{max_w};max-height:{max_h};width:100%;height:100%" preserveAspectRatio="xMidYMid meet" ', 1)


def board(ctx, fonts_css):
    from fonts import stack
    c, t, u, d = ctx.item.get("content") or {}, ctx.t, ctx.u, ctx.d
    logos = make_logos(ctx.item, ctx.brand, d)
    ctx.item["_logos"] = logos
    pad = ctx.safe
    name = plain(c.get("name") or ctx.brand.get("name") or "品牌")
    r = ctx.px(d["shape"]["radius"])
    head = (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;flex:none">'
            f'<div>' + T(ctx, "label", "BRAND KIT", c="accent_text", style=f"font-size:{max(ctx.minc, 1.9 * u):.1f}px;letter-spacing:.4em;font-weight:700;")
            + T(ctx, "headline", f"{name} 品牌小卡", cls="d", style=f"font-size:{ctx.px(5.4)};line-height:1.2;margin-top:{ctx.px(0.8)};white-space:nowrap;")
            + "</div>"
            + T(ctx, "body", f"视觉方向 {d['name']} · {d['mood']}", c="muted", style=f"font-size:{max(ctx.minb, 2 * u):.1f}px;")
            + "</div>")
    cards = []
    for k in ("A", "B", "C"):
        lg = logos[k]
        cards.append(
            f'<div style="flex:1 1 0;min-width:0;display:flex;flex-direction:column;border-radius:{r};overflow:hidden;'
            f'border:{ctx.px(0.2)} solid {t["line"]}">'
            f'<div style="flex:7 1 0;min-height:0;background:{t["surface"]};display:flex;align-items:center;justify-content:center;padding:{ctx.px(3)};position:relative">'
            + T(ctx, "label", f"{k}  {lg['label']}", c="muted", on="surface",
                style=f"position:absolute;left:{ctx.px(1.6)};top:{ctx.px(1.2)};font-size:{max(ctx.minc, 1.7 * u):.1f}px;letter-spacing:.1em;")
            + f'<div style="width:78%;height:62%;display:flex;align-items:center;justify-content:center">{_fit_svg(lg["svg"], "100%", "100%")}</div></div>'
            f'<div style="flex:3 1 0;min-height:0;background:{t["accent"]};display:flex;align-items:center;justify-content:center;padding:{ctx.px(1.6)}">'
            f'<div style="width:56%;height:70%;display:flex;align-items:center;justify-content:center">{_fit_svg(lg["reversed"], "100%", "100%")}</div></div></div>')
    row1 = f'<div style="flex:1.25 1 0;min-height:0;display:flex;gap:{ctx.px(2.4)}">{"".join(cards)}</div>'
    sw = []
    for key, zh in (("bg", "底色"), ("surface", "卡片"), ("ink", "主文字"), ("muted", "次文字"), ("accent", "强调"), ("accent2", "辅助")):
        on = "ink" if key not in ("ink",) else "on_ink"
        sw.append(f'<div style="display:flex;flex-direction:column;gap:{ctx.px(0.5)}">'
                  f'<div style="height:{ctx.px(4.6)};border-radius:{ctx.px(0.8)};background:{t[key]};border:{ctx.px(0.15)} solid {t["line"]}"></div>'
                  + T(ctx, "caption", f"{zh}", c="muted", style=f"font-size:{max(ctx.minc, 1.6 * u):.1f}px;")
                  + T(ctx, "caption", t[key].upper(), style=f"font-size:{max(ctx.minc, 1.6 * u):.1f}px;font-family:monospace;")
                  + "</div>")
    palette = (f'<div style="flex:1 1 0;min-width:0;display:flex;flex-direction:column;gap:{ctx.px(1.2)}">'
               + T(ctx, "label", "颜色", c="accent_text", style=f"font-size:{max(ctx.minc, 1.8 * u):.1f}px;letter-spacing:.3em;font-weight:700;")
               + f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:{ctx.px(1.2)}">{"".join(sw)}</div></div>')
    from common import load_ref
    fonts = load_ref("fonts.json")
    df, bf = fonts.get(d["display"]["font"], {}), fonts.get(d["body"]["font"], {})
    typo = (f'<div style="flex:1 1 0;min-width:0;display:flex;flex-direction:column;gap:{ctx.px(1)}">'
            + T(ctx, "label", "字体", c="accent_text", style=f"font-size:{max(ctx.minc, 1.8 * u):.1f}px;letter-spacing:.3em;font-weight:700;")
            + T(ctx, "headline", f"{name} Aa 123", cls="d", style=f"font-size:{ctx.px(5)};line-height:1.2;white-space:nowrap;overflow:hidden;")
            + T(ctx, "caption", f"标题 {df.get('family', '')}", c="muted", style=f"font-size:{max(ctx.minc, 1.6 * u):.1f}px;")
            + T(ctx, "body", "正文用这款字，清楚好读，适合价目、地址和说明文字。", style=f"font-size:{max(ctx.minb, 2.2 * u):.1f}px;margin-top:{ctx.px(1)};")
            + T(ctx, "caption", f"正文 {bf.get('family', '')}", c="muted", style=f"font-size:{max(ctx.minc, 1.6 * u):.1f}px;")
            + "</div>")
    icon = logos["B"]["icon"]
    apps = (f'<div style="flex:1 1 0;min-width:0;display:flex;flex-direction:column;gap:{ctx.px(1.2)}">'
            + T(ctx, "label", "用起来", c="accent_text", style=f"font-size:{max(ctx.minc, 1.8 * u):.1f}px;letter-spacing:.3em;font-weight:700;")
            + f'<div style="display:flex;gap:{ctx.px(2)};align-items:center;flex:1 1 auto">'
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:{ctx.px(0.6)}">'
            f'<div style="width:{ctx.px(11)};height:{ctx.px(11)};border-radius:50%;overflow:hidden;background:{t["surface"]};display:flex;align-items:center;justify-content:center">{_fit_svg(icon, "100%", "100%")}</div>'
            + T(ctx, "caption", "头像", c="muted", style=f"font-size:{max(ctx.minc, 1.5 * u):.1f}px;") + "</div>"
            f'<div style="flex:1 1 auto;aspect-ratio:90/54;max-height:{ctx.px(15)};background:{t["surface"]};border-radius:{ctx.px(0.6)};'
            f'box-shadow:0 {ctx.px(0.4)} {ctx.px(1.6)} {rgba(t["ink"], .18)};display:flex;flex-direction:column;justify-content:space-between;padding:{ctx.px(1.4)}">'
            f'<div style="height:{ctx.px(4)};display:flex">{_fit_svg(logos["A"]["svg"], "60%", "100%")}</div>'
            f'<div style="display:flex;flex-direction:column;gap:{ctx.px(0.5)}">'
            + "".join(f'<div style="height:{ctx.px(0.6)};width:{w}%;background:{rgba(t["ink"], .2)};border-radius:2px"></div>' for w in (60, 45, 52))
            + "</div></div></div></div>")
    row2 = (f'<div style="flex:1 1 0;min-height:0;display:flex;gap:{ctx.px(4)};padding-top:{ctx.px(2.2)};'
            f'border-top:{ctx.px(0.2)} solid {t["line"]}">{palette}{typo}{apps}</div>')
    html = (f'<div style="position:absolute;inset:{pad:.1f}px;display:flex;flex-direction:column;gap:{ctx.px(2.4)}">'
            f'{head}{row1}{row2}</div>')
    return page(ctx, fonts_css, html, "")


def register(builders, layouts):
    layouts["brandkit"] = ["board"]
    builders[("brandkit", "board")] = board
