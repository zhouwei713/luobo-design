"""Trend poster layouts: what current poster design does that templates rarely do.

type-sandwich  a giant title with the subject standing in it: most of the title sits behind the
               subject, the first character of the last line comes back in front of it
type-stack     every line of copy set so it spans the full width, lines of different sizes stacked
               like a wall of type, one line reversed out of a colour bar
collage        torn paper, tape, a sticker-edged cut-out, a ransom-note title in mixed faces,
               hand-drawn arrows and stars, halftone dots

Any of them takes an optional "tech" decoration layer (barcode, serial numbers, crosshairs,
edge micro-type) with art.deco = "tech". Portrait first; other sizes fall back to sensible
proportions of the same composition.
"""
import math
import random

import art
from common import contrast, esc, mix, rgba
from fonts import stack
from layouts import T, art_block, page, plain

LAYOUT_FONTS = {"type-sandwich": ["sans"], "type-stack": ["sans", "serif"],
                "collage": ["sans", "xiaowei", "mashan", "kuaile", "serif"]}


def _f(fid, weight=400):
    return f"font-family:{stack(fid)};font-weight:{weight};"


def _subject(ctx, uid, filt=""):
    """The cut-out (AI or user photo) or the procedural drawing, filling its box."""
    a = ctx.item.get("art") or {}
    if a.get("image"):
        inner = art_block(ctx, {**a, "image_fit": "contain"})
    else:
        inner = f'<div class="art motif" style="width:100%;height:100%">{art.motif(a.get("motif") or "drink", ctx.t, uid + "s", a.get("drink"))}</div>'
    return f'<div style="position:absolute;inset:0;{filt}">{inner}</div>'


def _grain(opacity=.22):
    return (f'<div style="position:absolute;inset:0;pointer-events:none;z-index:40;background-image:url(\'{art.noise_uri(True, .5)}\');'
            f'background-size:300px 300px;mix-blend-mode:multiply;opacity:{opacity}"></div>')


def tech_deco(ctx, color, seed=1, barcode=True):
    """Barcode, serial numbers, crosshairs and edge micro-type: detail that reads as 'designed'."""
    rng = random.Random(seed)
    u, W, H, pad = ctx.u, ctx.W, ctx.H, ctx.safe
    bars, x = "", 0
    while x < 150:
        w = rng.choice((1, 1, 2, 3))
        bars += f'<rect x="{x}" y="0" width="{w}" height="40" fill="{color}"/>'
        x += w + rng.choice((1, 2, 2, 3))
    small = f"font-size:{max(ctx.minc, 1.5 * u):.1f}px;letter-spacing:.18em;white-space:nowrap;"
    cross = lambda x, y: (f'<svg style="position:absolute;left:{x - 1.4 * u:.0f}px;top:{y - 1.4 * u:.0f}px;width:{ctx.px(2.8)};height:{ctx.px(2.8)};z-index:30" viewBox="0 0 20 20">'
                          f'<path d="M10 0V20M0 10H20" stroke="{color}" stroke-width="1"/><circle cx="10" cy="10" r="4" fill="none" stroke="{color}" stroke-width="1"/></svg>')
    brand = (ctx.brand.get("name") or "").upper()
    serial = f"NO.{rng.randint(100, 999)}-{rng.randint(10, 99)}"
    return (cross(pad * .55, pad * .55) + cross(W - pad * .55, pad * .55) + cross(pad * .55, H - pad * .55) + cross(W - pad * .55, H - pad * .55)
            + f'<div aria-hidden="true" style="position:absolute;right:{pad * .35:.0f}px;top:50%;transform:translate(0,-50%) rotate(90deg);transform-origin:right center;'
              f'color:{color};opacity:.7;z-index:30;{small}font-family:monospace">{esc(serial)} · DAILY SERIES · {esc(brand)}</div>'
            + (f'<svg aria-hidden="true" style="position:absolute;right:{pad:.0f}px;bottom:{pad * .9:.0f}px;width:{ctx.px(14)};height:{ctx.px(3.6)};z-index:30" '
               f'viewBox="0 0 150 40" preserveAspectRatio="none">{bars}</svg>' if barcode else ""))


# ------------------------------------------------------------------ type-sandwich
def poster_type_sandwich(ctx, fonts_css):
    c, t, u, W, H, pad = ctx.item["content"], ctx.t, ctx.u, ctx.W, ctx.H, ctx.safe
    a = ctx.item.get("art") or {}
    uid = ctx.nid("sw")
    title = plain(c.get("big_title") or c.get("headline") or "")
    lines = [ln for ln in title.split("\n") if ln.strip()] or [title]
    n = max(len(ln) for ln in lines)
    ar = ctx.cv["ar"]
    bg = mix(t["accent2"], "#FFFFFF", .72) if contrast(t["accent"], mix(t["accent2"], "#FFFFFF", .72)) >= 3 else mix(t["bg"], "#FFFFFF", .3)
    ink = t["accent"] if contrast(t["accent"], bg) >= 3 else t["ink"]
    tall = (a.get("motif", "drink") == "drink") or bool(a.get("image"))
    last = lines[-1]
    shadow = f'filter:drop-shadow(0 {ctx.px(2)} {ctx.px(2.4)} {rgba(t["ink"], .22)})'
    if ctx.o == "portrait":
        # title across the top, centred; the subject rises into the last line; its first character comes forward
        fs = min((W - 2 * pad * 1.05) / max(n, 1) * .97, H * .24)
        lh, top = fs, pad * 1.2
        tstyle = (_f("sans", 900) + f"position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;text-align:center;font-size:{fs:.1f}px;line-height:1;"
                  f"letter-spacing:-.02em;white-space:nowrap;color:{ink};")
        first_right = (W - len(last) * fs * .98) / 2 + fs * .99
        clip = f"inset(-20% {max(0, W - pad - first_right):.0f}px -20% -20%)"
        # the subject only reaches the lower part of the last line, so no character is hidden (poster-craft.md)
        sub_top = top + (len(lines) - 1) * lh + lh * (.4 if tall else .7)  # wide subjects cover more of a character
        sh = H - sub_top - pad * 4.6
        sw = sh * (.75 if tall else 1)
        sx = W * .56 - sw / 2
        info_box = f"left:{pad:.0f}px;right:{pad:.0f}px;bottom:{pad:.0f}px"
    else:
        # square and landscape: title stacked on the left, the subject stands on the right through the title;
        # the last character of the last line comes forward
        box_w = W * (.55 if ctx.o == "landscape" else .62)
        fs = min((box_w - pad) / max(n, 1) * .97, (H - pad * 5.5) / len(lines))
        lh, top = fs, pad * 1.1
        tstyle = (_f("sans", 900) + f"position:absolute;left:{pad:.0f}px;width:{box_w:.0f}px;text-align:left;font-size:{fs:.1f}px;line-height:1;"
                  f"letter-spacing:-.02em;white-space:nowrap;color:{ink};")
        last_left = pad + (len(last) - 1) * fs * .98
        clip = f"inset(-20% -20% -20% {max(0, last_left - pad - fs * .02):.0f}px)"
        if tall:
            sh = H * .84
            sw = sh * .75
            sx = min(W - pad - sw, pad + len(last) * fs * .98 - sw * .3)  # the subject's left edge reaches into the last character
            sub_top = (H - sh) / 2 - pad * .4
        else:
            # a wide subject would bury the title: it sits to the right and only clips the last character's corner
            sub_top = top + (len(lines) - 1) * lh + lh * .25
            sw = sh = min(H * .6, W * .46, H - pad - u * 22 - sub_top)  # stays clear of the copy at the bottom
            right = pad + len(last) * fs * .98  # right edge of the last character
            sx = min(right - fs * .3 - sw * .36, W - pad - sw * .95)  # the ears land on that character's lower corner
        if not tall:
            info_box = f"left:{pad:.0f}px;right:{pad:.0f}px;bottom:{pad:.0f}px"
        elif ctx.o == "landscape" and W - (sx + sw) > W * .2:  # spare room on the right: the copy goes there
            info_box = f"left:{sx + sw + pad * .6:.0f}px;right:{pad:.0f}px;bottom:{pad:.0f}px"
        else:
            info_box = f"left:{pad:.0f}px;width:{max(sx - pad * 1.4, W * .4):.0f}px;bottom:{pad:.0f}px"
    back = "".join(T(ctx, "headline", ln, c=ink, on=bg, style=tstyle + f"top:{top + i * lh:.0f}px;z-index:2;") for i, ln in enumerate(lines))
    front = (f'<div aria-hidden="true" style="{tstyle}top:{top + (len(lines) - 1) * lh:.0f}px;z-index:5;clip-path:{clip}">{esc(last)}</div>')
    subject = (f'<div style="position:absolute;left:{sx:.0f}px;top:{sub_top:.0f}px;width:{sw:.0f}px;height:{sh:.0f}px;z-index:4;{shadow}">{_subject(ctx, uid)}</div>')
    info = (f'<div style="position:absolute;{info_box};z-index:6;display:flex;justify-content:space-between;align-items:flex-end;gap:{ctx.px(3)}">'
            f'<div style="min-width:0">'
            + T(ctx, "label", c.get("kicker"), c=mix(ink, "#000000", .25), on=bg, style=f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;letter-spacing:.3em;font-weight:700;")
            + T(ctx, "sub", c.get("sub"), c=t["ink"], on=bg, style=f"font-size:{max(ctx.minb, 3.4 * u):.1f}px;margin-top:{ctx.px(1)};font-weight:700;")
            + T(ctx, "caption", "　".join(c.get("tags") or []), c=mix(t["ink"], bg, .25), on=bg, style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;margin-top:{ctx.px(.8)};letter-spacing:.1em;")
            + T(ctx, "body", "　".join(f"{d.get('k', '')} {d.get('v', '')}".strip() for d in c.get("details") or []), c=t["ink"], on=bg,
                style=f"font-size:{max(ctx.minb, 2.6 * u):.1f}px;margin-top:{ctx.px(1)};")
            + "</div>"
            + T(ctx, "label", ctx.brand.get("name"), c=t["ink"], on=bg, cls="d", style=f"font-size:{max(ctx.minb, 2.8 * u):.1f}px;white-space:nowrap;margin-bottom:{ctx.px(5) if a.get('deco') == 'tech' else 0};")
            + "</div>")
    deco = tech_deco(ctx, mix(t["ink"], bg, .2), seed=len(title)) if a.get("deco") == "tech" else ""
    body = back + subject + front + info + deco + _grain(.18)
    return page(ctx, fonts_css, body, f".pattern{{display:none}}.canvas,html,body{{background:{bg}}}")


# ------------------------------------------------------------------ type-stack
def poster_type_stack(ctx, fonts_css):
    c, t, u, W, H, pad = ctx.item["content"], ctx.t, ctx.u, ctx.W, ctx.H, ctx.safe
    a = ctx.item.get("art") or {}
    uid = ctx.nid("ts")
    lines = c.get("lines")
    if not lines:
        lines = [x for x in [c.get("kicker")] + plain(c.get("headline") or "").split("\n") + str(c.get("sub") or "").replace("，", "\n").split("\n") if x]
    bg = mix(t["bg"], "#FFFFFF", .35)
    ink = t["ink"]
    rows = []
    looks = c.get("looks") or ["ink", "accent", "bar", "ink", "outline", "accent", "ink", "bar"]
    for i, ln in enumerate(lines[:9]):
        look = looks[i % len(looks)]
        wt = 900 if look != "serif" else 700
        fam = "serif" if look == "serif" else "sans"
        if look == "bar":
            rows.append(f'<div style="background:{t["accent"]};padding:{ctx.px(.6)} {ctx.px(1.6)} {ctx.px(1)};margin:{ctx.px(.6)} 0">'
                        + T(ctx, "headline", ln, c=t["on_accent"], on=t["accent"], style=_f(fam, wt) + "line-height:1.06;", tag="span").replace('class="t', 'data-justify="1" class="t', 1)
                        + "</div>")
            continue
        col = t["accent_text"] if look == "accent" else ink
        extra = ""
        if look == "outline":
            extra = f"color:transparent;-webkit-text-stroke:{max(1.5, .22 * u):.1f}px {ink};"
        rows.append(f'<div style="margin:{ctx.px(.5)} 0">'
                    + T(ctx, "headline", ln, c=col if look != "outline" else ink, on=bg, style=_f(fam, wt) + "line-height:1.06;" + extra, tag="span").replace('class="t', 'data-justify="1" class="t', 1)
                    + "</div>")
    # small picture: a round sticker bottom right
    s = 30 * u
    s = 20 * u
    pic = (f'<div style="position:absolute;right:{pad * .7:.0f}px;bottom:{pad * .5:.0f}px;width:{s:.0f}px;height:{s:.0f}px;border-radius:50%;background:{t["accent2"]};'
           f'border:{ctx.px(.8)} solid {bg};box-shadow:0 0 0 {ctx.px(.3)} {ink};z-index:6;overflow:hidden;transform:rotate(-8deg)">'
           f'<div style="position:absolute;left:12%;top:8%;width:76%;height:92%">{_subject(ctx, uid)}</div></div>') if (a.get("motif") or a.get("image")) else ""
    foot = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad + 24 * u:.0f}px;bottom:{pad:.0f}px;display:flex;justify-content:space-between;align-items:flex-end;z-index:7">'
            + T(ctx, "label", ctx.brand.get("name"), c=ink, on=bg, cls="d", style=f"font-size:{max(ctx.minb, 2.8 * u):.1f}px;white-space:nowrap;")
            + T(ctx, "caption", c.get("note"), c=mix(ink, bg, .3), on=bg, style=f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;letter-spacing:.2em;white-space:nowrap;")
            + "</div>")
    wide = ctx.o == "landscape"
    if wide and (a.get("motif") or a.get("image")):  # landscape: the wall on the left, the picture large on the right
        ph_ = H - pad * 2
        pw_ = ph_ * .75
        pic = (f'<div style="position:absolute;right:{pad:.0f}px;top:{pad:.0f}px;width:{pw_:.0f}px;height:{ph_:.0f}px;z-index:4;'
               f'filter:drop-shadow(0 {ctx.px(2)} {ctx.px(2.4)} {rgba(t["ink"], .2)})">{_subject(ctx, uid)}</div>')
        foot = foot.replace(f"right:{pad + 24 * u:.0f}px", f"right:{pw_ + pad * 2:.0f}px")
    wall_right = (pw_ + pad * 2) if wide and (a.get("motif") or a.get("image")) else pad
    budget = H - pad * 2 - (10 if wide else 22) * u
    wall = (f'<div data-wall="{budget:.0f}" style="position:absolute;left:{pad:.0f}px;right:{wall_right:.0f}px;top:{pad:.0f}px;height:{budget:.0f}px;z-index:3;'
            f'display:flex;flex-direction:column;justify-content:space-between">'
            + "".join(rows) + "</div>")
    deco = tech_deco(ctx, mix(ink, bg, .3), seed=len(lines), barcode=not pic) if a.get("deco") == "tech" else ""
    return page(ctx, fonts_css, wall + pic + foot + deco + _grain(.15), f".pattern{{display:none}}.canvas,html,body{{background:{bg}}}")


# ------------------------------------------------------------------ collage
def _torn(rng, x, y, w, h, jag=10):
    """A polygon like a piece of torn paper: straight-ish sides with small rips."""
    pts = []
    for (x0, y0, x1, y1) in ((x, y, x + w, y), (x + w, y, x + w, y + h), (x + w, y + h, x, y + h), (x, y + h, x, y)):
        steps = max(6, int(math.hypot(x1 - x0, y1 - y0) / 18))
        for i in range(steps):
            k = i / steps
            px, py = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
            nx, ny = (y1 - y0), -(x1 - x0)
            nl = math.hypot(nx, ny) or 1
            j = rng.uniform(-jag, jag) * (1 if i % 2 else .5)
            pts.append(f"{px + nx / nl * j:.1f},{py + ny / nl * j:.1f}")
    return " ".join(pts)


def poster_collage(ctx, fonts_css):
    c, t, u, W, H, pad = ctx.item["content"], ctx.t, ctx.u, ctx.W, ctx.H, ctx.safe
    a = ctx.item.get("art") or {}
    uid = ctx.nid("cg")
    rng = random.Random(sum(ord(ch) for ch in ctx.item.get("id", "x")))
    paper = "#EFE8DA"
    kraft = "#D8C3A0"
    a1, a2, ink = t["accent"], t["accent2"], t["ink"]
    pieces = [(a2, W * .05, H * .1, W * .62, H * .42, -6), (a1, W * .42, H * .3, W * .55, H * .36, 5),
              (kraft, W * .02, H * .55, W * .7, H * .26, -3), ("#FFFFFF", W * .55, H * .06, W * .38, H * .22, 8)]
    torn = "".join(f'<polygon points="{_torn(rng, x, y, w, h, u * .9)}" fill="{col}" transform="rotate({r} {x + w / 2:.0f} {y + h / 2:.0f})"/>' for col, x, y, w, h, r in pieces)
    shadow = f'<filter id="tsh{uid}"><feDropShadow dx="0" dy="{u * .5:.1f}" stdDeviation="{u * .6:.1f}" flood-color="#3A2A20" flood-opacity=".28"/></filter>'
    paper_layer = (f'<svg aria-hidden="true" viewBox="0 0 {W:.0f} {H:.0f}" width="100%" height="100%" style="position:absolute;inset:0;z-index:1">'
                   f'<defs>{shadow}</defs><g filter="url(#tsh{uid})">{torn}</g></svg>')
    dots = (f'<div style="position:absolute;left:{W * .48:.0f}px;top:{H * .02:.0f}px;width:{W * .5:.0f}px;height:{W * .5:.0f}px;border-radius:50%;z-index:2;opacity:.55;'
            f'background-image:radial-gradient({ink} 30%, transparent 33%);background-size:{u * 1.6:.1f}px {u * 1.6:.1f}px;'
            f'-webkit-mask-image:radial-gradient(circle, #000 35%, transparent 70%);mask-image:radial-gradient(circle, #000 35%, transparent 70%)"></div>')
    # subject: a white sticker edge and a hard shadow, slightly turned
    sticker = (f'<svg width="0" height="0" style="position:absolute"><filter id="stk{uid}" x="-10%" y="-10%" width="120%" height="125%">'
               f'<feMorphology in="SourceAlpha" operator="dilate" radius="{u * .9:.1f}" result="d"/><feFlood flood-color="#FFFFFF"/><feComposite in2="d" operator="in" result="edge"/>'
               f'<feGaussianBlur in="d" stdDeviation="{u * .5:.1f}" result="b"/><feOffset in="b" dx="{u * .4:.1f}" dy="{u * .8:.1f}" result="o"/>'
               f'<feFlood flood-color="#2A1E16" flood-opacity=".35"/><feComposite in2="o" operator="in" result="sh"/>'
               f'<feMerge><feMergeNode in="sh"/><feMergeNode in="edge"/><feMergeNode in="SourceGraphic"/></feMerge></filter></svg>')
    sh_, sw_ = H * .5, H * .5 * .75
    subj = (f'<div style="position:absolute;left:{W * .5 - sw_ / 2 + W * .06:.0f}px;top:{H * .14:.0f}px;width:{sw_:.0f}px;height:{sh_:.0f}px;z-index:5;transform:rotate(-4deg)">'
            f'{_subject(ctx, uid, f"filter:url(#stk{uid})")}</div>')
    tape = lambda x, y, r, w=16: (f'<div style="position:absolute;left:{x:.0f}px;top:{y:.0f}px;width:{ctx.px(w)};height:{ctx.px(4)};background:{rgba("#F6EBC8", .78)};'
                                  f'transform:rotate({r}deg);z-index:7;box-shadow:0 1px 2px rgba(0,0,0,.12)"></div>')
    # ransom-note title: every character cut from a different scrap
    faces = [("sans", 900), ("xiaowei", 400), ("mashan", 400), ("kuaile", 400), ("serif", 700)]
    scraps = [("#FFFFFF", ink), (ink, "#FFFFFF"), (a1, t["on_accent"]), (kraft, ink), (a2, ink if contrast(ink, a2) >= 4.5 else "#FFFFFF"), ("#FFF3A6", ink)]
    head = plain(c.get("headline") or "")
    fs = min(13 * u, (W - 2 * pad) / max(len(max(head.split("\n"), key=len)), 1) * .82)
    letters = ""
    for li, line in enumerate(head.split("\n")):
        row = ""
        for ci, ch in enumerate(line):
            bgc, fg = scraps[(ci + li * 2 + rng.randint(0, 5)) % len(scraps)]
            fid, wt = faces[(ci * 3 + li + rng.randint(0, 4)) % len(faces)]
            rot = rng.uniform(-7, 7)
            row += (f'<span style="display:inline-block;background:{bgc};padding:{fs * .06:.0f}px {fs * .1:.0f}px;margin:0 {fs * .03:.0f}px;transform:rotate({rot:.1f}deg);'
                    f'box-shadow:0 {u * .3:.1f}px {u * .5:.1f}px rgba(42,30,22,.28)">'
                    + T(ctx, "label", ch, c=fg, on=bgc, tag="span", style=_f(fid, wt) + f"font-size:{fs * rng.uniform(.86, 1.08):.0f}px;line-height:1.05;")
                    + "</span>")
        letters += f'<div style="white-space:nowrap">{row}</div>'
    title = f'<div data-grp="ransom" style="position:absolute;left:{pad:.0f}px;top:{H * .65:.0f}px;z-index:8;transform:rotate(-2deg)">{letters}</div>'
    label = (f'<div style="position:absolute;left:{pad * 1.4:.0f}px;right:{pad * 2:.0f}px;bottom:{pad * 1.3:.0f}px;z-index:8;background:#FFFFFF;'
             f'padding:{ctx.px(1.6)} {ctx.px(2.4)};transform:rotate(1.5deg);box-shadow:0 {u * .3:.1f}px {u * .6:.1f}px rgba(42,30,22,.22)">'
             + T(ctx, "sub", c.get("sub"), c=ink, on="#FFFFFF", style=_f("serif", 400) + f"font-size:{max(ctx.minb, 3.2 * u):.1f}px;line-height:1.5;")
             + "</div>")
    stickers = ""
    for i, tg in enumerate((c.get("tags") or [])[:2]):
        s = 15 * u
        col = (a1, ink)[i % 2]
        stickers += (f'<div style="position:absolute;right:{pad * (.9 + i * .4):.0f}px;top:{H * (.2 + i * .17):.0f}px;width:{s:.0f}px;height:{s:.0f}px;border-radius:50%;background:{col};'
                     f'border:{ctx.px(.6)} solid #FFFFFF;box-shadow:0 {u * .4:.1f}px {u * .6:.1f}px rgba(42,30,22,.3);transform:rotate({(-12, 10)[i % 2]}deg);z-index:9;'
                     f'display:flex;align-items:center;justify-content:center">'
                     + T(ctx, "label", tg, c="#FFFFFF", on=col, style=_f("kuaile") + f"font-size:{max(ctx.minc, 3 * u):.1f}px;white-space:nowrap;") + "</div>")
    # hand-drawn bits: an arrow to the subject, a scribble ring, stars
    hand = (f'<svg aria-hidden="true" viewBox="0 0 {W:.0f} {H:.0f}" width="100%" height="100%" style="position:absolute;inset:0;z-index:9;pointer-events:none">'
            f'<path d="M{W * .16:.0f} {H * .5:.0f} C {W * .12:.0f} {H * .4:.0f}, {W * .2:.0f} {H * .33:.0f}, {W * .3:.0f} {H * .34:.0f}" stroke="{ink}" stroke-width="{u * .45:.1f}" fill="none" stroke-linecap="round"/>'
            f'<path d="M{W * .27:.0f} {H * .31:.0f} L{W * .305:.0f} {H * .34:.0f} L{W * .27:.0f} {H * .365:.0f}" stroke="{ink}" stroke-width="{u * .45:.1f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            + "".join(f'<path d="M{x} {y - 3 * u} L{x + .9 * u} {y - .9 * u} L{x + 3 * u} {y} L{x + .9 * u} {y + .9 * u} L{x} {y + 3 * u} L{x - .9 * u} {y + .9 * u} L{x - 3 * u} {y} L{x - .9 * u} {y - .9 * u} Z" fill="{col}"/>'
                      for x, y, col in ((W * .9, H * .5, a1), (W * .1, H * .08, ink), (W * .86, H * .9, a2)))
            + "</svg>")
    brand = (f'<div style="position:absolute;left:{pad:.0f}px;top:{pad:.0f}px;z-index:10;background:{rgba("#F6EBC8", .9)};padding:{ctx.px(.8)} {ctx.px(2)};transform:rotate(-3deg)">'
             + T(ctx, "label", ctx.brand.get("name"), c=ink, on="#F6EBC8", cls="d", style=f"font-size:{max(ctx.minb, 2.8 * u):.1f}px;white-space:nowrap;") + "</div>")
    kicker = (f'<div style="position:absolute;right:{pad:.0f}px;top:{pad:.0f}px;z-index:10;background:{ink};padding:{ctx.px(.6)} {ctx.px(1.6)};transform:rotate(4deg)">'
              + T(ctx, "label", c.get("kicker"), c="#FFFFFF", on=ink, style=_f("sans", 900) + f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;letter-spacing:.2em;white-space:nowrap;")
              + "</div>") if c.get("kicker") else ""
    deco = tech_deco(ctx, mix(ink, paper, .3), seed=7) if a.get("deco") == "tech" else ""
    body = (paper_layer + dots + sticker + subj + tape(W * .5 - sw_ / 2 + W * .02, H * .13, -24) + tape(W * .5 + sw_ / 2 - W * .02, H * .58, 30, 14)
            + title + label + stickers + hand + brand + kicker + deco + _grain(.3))
    return page(ctx, fonts_css, body, f".pattern{{display:none}}.canvas,html,body{{background:{paper}}}")


def register(builders, layouts):
    layouts["poster"] = list(dict.fromkeys(layouts["poster"] + ["type-sandwich", "type-stack", "collage"]))
    builders[("poster", "type-sandwich")] = poster_type_sandwich
    builders[("poster", "type-stack")] = poster_type_stack
    builders[("poster", "collage")] = poster_collage
