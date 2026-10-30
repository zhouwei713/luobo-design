"""Xiaohongshu (RedNote) note covers, item type "xhs".

Built from 80 covers that passed a thousand likes across eleven fields. What they share: real photos beat
designed graphics, and the words on top follow one look, chunky type with a thick outline ("花字"),
tilted stickers, check badges, never over the face. Covers that sell "save this" look like the content
itself: a phone memo, a ranking, a list.

photo     the user's photo full bleed, an outlined headline kept clear of the face (art.focus)
textcard  a pastel card with one sentence, like the app's own text template
memo      a phone notes screen: title, date, a checklist with yellow ticks
ranking   number headline, TOP pill, ranked rows with a value column
grid      2x2 or 3x3 photo matrix, a tag and a label on every cell, a title card in the middle
compare   two photos stacked (before / after, theirs / mine), outlined labels
doodle    cream paper, hand-lettered title with marker highlights, a cute illustration, scribbles

Covers are 3:4. Optional on any of them: content.series ("#02") and content.handle ("@name").
"""
import math
import random

import art
from common import esc, mix, rgba
from fonts import stack
from layouts import T, art_block, page

LAYOUT_FONTS = {"photo": ["sans"], "textcard": ["sans"], "memo": ["sans"], "ranking": ["sans"],
                "grid": ["sans"], "compare": ["sans"], "doodle": ["kuaile", "mashan", "sans"]}

CARD_COLORS = {  # background, accent, ink: the app's own text-card palettes are this soft
    "green": ("#DDF6D6", "#9AD48F", "#2D3A2C"), "yellow": ("#FFF4BF", "#F2C53D", "#3A3020"),
    "pink": ("#FFE4E8", "#F29AAA", "#3D292E"), "blue": ("#DCEBFF", "#8AB4EA", "#22303F"),
    "cream": ("#F6F0E4", "#D8C7A6", "#2F2920"), "gray": ("#EEEEEE", "#BBBBBB", "#222222"),
}
YELLOW, RED, GREEN, INK = "#FFE14D", "#E8402F", "#21B35A", "#141414"
RED_TEXT = "#C42D1C"  # the red that still reads as body text on white


def _f(fid, weight=400):
    return f"font-family:{stack(fid)};font-weight:{weight};"


def ring(color, r=.07, drop=None):
    """A solid outline drawn with sixteen text shadows (scales with the font, works on any text)."""
    parts = [f"{r * math.cos(2 * math.pi * i / 16):.3f}em {r * math.sin(2 * math.pi * i / 16):.3f}em 0 {color}" for i in range(16)]
    if drop:
        parts.append(f"0 {r * 1.9:.3f}em 0 {drop}")
    return "text-shadow:" + ",".join(parts) + ";"


def huazi(ctx, text, fill="#FFFFFF", stroke=INK, hl=YELLOW, width=.92, cap_px=None, rot=0, font="sans", weight=900,
          role="headline", r=.075, drop=None, align="left"):
    """One line of 花字, set to span `width` of its parent, never taller than cap_px."""
    style = _f(font, weight) + f"color:{fill};line-height:1.18;{ring(stroke, r, drop)}"
    node = T(ctx, role, text, c=fill, on=stroke, style=style, tag="span")
    cap = f' data-cap-px="{cap_px:.0f}"' if cap_px else ""
    node = node.replace('class="t', f'data-justify="{width:.3f}"{cap} class="t', 1)
    return (f'<div class="hz" style="text-align:{align};transform:rotate({rot}deg);transform-origin:{align} center;--hl:{hl}">'
            f'{node}</div>')


def title_lines(ctx, c):
    return [ln for ln in str(c.get("title") or c.get("headline") or "").split("\n") if ln.strip()]


def plain_len(s):
    return len(str(s).replace("**", ""))


def sticker(ctx, text, i=0, size_u=3.4):
    """A tilted tag: white with a black edge, or red with white type, alternating."""
    red = i % 2 == 1
    bg, fg = (RED, "#FFFFFF") if red else ("#FFFFFF", INK)
    rot = (-6, 5, -3, 7)[i % 4]
    return (f'<div style="display:inline-block;transform:rotate({rot}deg);background:{bg};border:{ctx.px(.45)} solid {INK};'
            f'border-radius:{ctx.px(1.2)};padding:{ctx.px(.5)} {ctx.px(1.6)};box-shadow:{ctx.px(.5)} {ctx.px(.6)} 0 {INK}">'
            + T(ctx, "label", text, c=fg, on=bg, tag="span", style=_f("sans", 900) + f"font-size:{max(ctx.minc, size_u * ctx.u):.1f}px;white-space:nowrap;")
            + "</div>")


def check_badge(ctx, text, size_u=3.8):
    tick = (f'<svg viewBox="0 0 20 20" style="width:1.15em;height:1.15em;flex:none"><rect x="1" y="1" width="18" height="18" rx="4" fill="{GREEN}" stroke="#fff" stroke-width="1.6"/>'
            f'<path d="M5 10.5 L8.6 14 L15 6.5" stroke="#fff" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    return (f'<div style="display:inline-flex;align-items:center;gap:.25em;font-size:{max(ctx.minb, size_u * ctx.u):.1f}px">{tick}'
            + T(ctx, "label", text, c="#FFFFFF", on=INK, tag="span", style=_f("sans", 900) + f"white-space:nowrap;{ring(INK, .09)}")
            + "</div>")


def extras(ctx, c, on_photo=True):
    """Series number at the top, handle at the bottom: the two marks an account repeats on every cover."""
    out = ""
    pad, u = ctx.safe, ctx.u
    if c.get("series"):
        col = "#FFFFFF" if on_photo else rgba(ctx.t["ink"], .55)
        out += (f'<div style="position:absolute;left:0;right:0;top:{pad:.0f}px;text-align:center;z-index:20">'
                + T(ctx, "label", c["series"], c=col, on=INK if on_photo else ctx.t["bg"], tag="span",
                    style=_f("sans", 700) + f"font-size:{max(ctx.minc, 2.6 * u):.1f}px;letter-spacing:.12em;"
                    + (ring(INK, .06) if on_photo else "")) + "</div>")
    if c.get("handle"):
        col = "#FFFFFF" if on_photo else rgba(ctx.t["ink"], .6)
        out += (f'<div style="position:absolute;left:{pad:.0f}px;bottom:{pad:.0f}px;z-index:20">'
                + T(ctx, "caption", c["handle"], c=col, on=INK if on_photo else ctx.t["bg"], tag="span",
                    style=_f("sans", 500) + f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;" + (ring(INK, .06) if on_photo else "")) + "</div>")
    return out


def photo_or_placeholder(ctx, src, label="【换成你的实拍照片】", tint=None, motif=None, seed=1, corner="bottom"):
    """A cover photo, or a soft placeholder that QA lists as missing."""
    if src:
        return f'<img src="{esc(src)}" data-role="image" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">'
    t = ctx.t
    a, b = tint or (mix(t["accent2"], "#FFFFFF", .55), mix(t["accent"], "#FFFFFF", .45))
    draw = ""
    if motif:
        draw = (f'<div style="position:absolute;left:22%;right:22%;top:30%;bottom:22%;opacity:.9">'
                f'{art.motif(motif, t, ctx.nid("pm"))}</div>')
    return (f'<div style="position:absolute;inset:0;background:linear-gradient(160deg,{a},{b})"></div>{draw}'
            f'<div style="position:absolute;right:{ctx.safe:.0f}px;{corner}:{ctx.safe:.0f}px;z-index:2">'
            + T(ctx, "caption", label, c="#FFFFFF", on=INK, tag="span", style=f"font-size:{max(ctx.minc, 2 * ctx.u):.1f}px;{ring(rgba(INK, .5), .05)}")
            + "</div>")


# ------------------------------------------------------------------ photo
def xhs_photo(ctx, fonts_css):
    c, a = ctx.item["content"], ctx.item.get("art") or {}
    W, H, pad, u = ctx.W, ctx.H, ctx.safe, ctx.u
    fx, fy, fw, fh = (a.get("focus") or [.22, .3, .56, .4])  # face or subject box, fractions of the photo
    pos = c.get("title_pos") or ("bottom" if fy + fh / 2 < .42 else "top")
    lines = title_lines(ctx, c)
    n = max(1, len(lines))
    longest = max((plain_len(x) for x in lines), default=1)
    avail = (fy * H - pad * 1.3) if pos == "top" else (H - (fy + fh) * H - pad * 1.3)
    avail = max(avail, H * .3)  # when the face leaves no room, the title may sit on the body, never on the face
    extra = (5.4 * u if c.get("sub") else 0) + (5.6 * u if c.get("badges") else 0) + (5.4 * u if c.get("stickers") else 0)
    cap = max(7 * u, min(16 * u, (avail - extra) / (n * 1.2)))
    cols = c.get("colors") or ["#FFFFFF", YELLOW]
    rows = []
    for i, ln in enumerate(lines):
        w = min(.9, .9 * plain_len(ln) / longest)  # the same type size on every line
        rows.append(huazi(ctx, ln, fill=cols[i % len(cols)], width=w, cap_px=cap, rot=(-1.5 if i % 2 == 0 else 1)))
    top_tags = "".join(sticker(ctx, s, i) for i, s in enumerate((c.get("stickers") or [])[:3]))
    sub = ""
    if c.get("sub"):
        sub = (f'<div style="margin-top:{ctx.px(1.6)};display:inline-block;background:{INK};padding:{ctx.px(.6)} {ctx.px(1.8)};transform:rotate(-1deg)">'
               + T(ctx, "sub", c["sub"], c=YELLOW, on=INK, tag="span", style=_f("sans", 900) + f"font-size:{max(ctx.minb, 3.8 * u):.1f}px;white-space:nowrap;")
               + "</div>")
    badges = "".join(check_badge(ctx, b) for b in (c.get("badges") or [])[:3])
    block = (f'<div data-grp="title" style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;{"top" if pos == "top" else "bottom"}:{pad * 1.3:.0f}px;padding:0 {ctx.px(1)};z-index:10">'
             + (f'<div style="display:flex;gap:{ctx.px(2)};margin-bottom:{ctx.px(1.6)}">{top_tags}</div>' if top_tags else "")
             + "".join(rows) + sub
             + (f'<div style="display:flex;flex-wrap:wrap;gap:{ctx.px(1)} {ctx.px(3)};margin-top:{ctx.px(1.8)}">{badges}</div>' if badges else "")
             + "</div>")
    shade = ("linear-gradient(180deg,rgba(0,0,0,.38),rgba(0,0,0,0) 46%)" if pos == "top"
             else "linear-gradient(0deg,rgba(0,0,0,.42),rgba(0,0,0,0) 50%)")
    body = (photo_or_placeholder(ctx, a.get("image"), motif=a.get("motif"))
            + f'<div style="position:absolute;inset:0;background:{shade};z-index:2"></div>' + block + extras(ctx, c))
    return page(ctx, fonts_css, body, ".pattern{display:none}.hz em.hl{color:var(--hl)}")


# ------------------------------------------------------------------ textcard
def xhs_textcard(ctx, fonts_css):
    c = ctx.item["content"]
    W, H, pad, u = ctx.W, ctx.H, ctx.safe, ctx.u
    bg, acc, ink = CARD_COLORS.get(c.get("color") or "green", CARD_COLORS["green"])
    align = c.get("align") or "left"
    quote = (f'<svg viewBox="0 0 60 44" style="position:absolute;left:{pad * 1.2:.0f}px;top:{pad * 1.6:.0f}px;width:{ctx.px(9)};z-index:2">'
             f'<path d="M4 44 V24 Q4 6 22 2 L24 8 Q14 12 14 22 H24 V44 Z M34 44 V24 Q34 6 52 2 L54 8 Q44 12 44 22 H54 V44 Z" fill="{acc}"/></svg>')
    text = T(ctx, "headline", c.get("title") or "", c=ink, on=bg, fit=(9.2 * u, 5 * u),
             style=_f("sans", 700) + f"line-height:1.55;letter-spacing:.02em;text-align:{align};width:100%;max-height:100%;white-space:pre-line;")
    box = (f'<div style="position:absolute;left:{pad * 1.25:.0f}px;right:{pad * 1.25:.0f}px;top:{H * .3:.0f}px;bottom:{H * .22:.0f}px;'
           f'display:flex;align-items:center;z-index:3"><div style="width:100%;height:100%;display:flex;align-items:center">{text}</div></div>')
    sub = (f'<div style="position:absolute;left:{pad * 1.25:.0f}px;right:{pad * 1.25:.0f}px;bottom:{H * .13:.0f}px;text-align:{align};z-index:3">'
           + T(ctx, "sub", c.get("sub"), c=rgba(ink, .6), on=bg, style=f"font-size:{max(ctx.minb, 3 * u):.1f}px;") + "</div>") if c.get("sub") else ""
    dash = f'<div style="position:absolute;right:{pad * 1.3:.0f}px;bottom:{pad * 1.4:.0f}px;width:{ctx.px(5)};height:{ctx.px(.7)};border-radius:9px;background:{acc}"></div>'
    body = f'<div style="position:absolute;inset:0;background:{bg}"></div>' + quote + box + sub + dash + extras(ctx, c, on_photo=False)
    css = (f".pattern{{display:none}}em.hl{{color:{ink};font-style:normal;background:linear-gradient(transparent 58%,{acc} 58%)}}")
    return page(ctx, fonts_css, body, css)


# ------------------------------------------------------------------ memo
def _item_text(x):
    if isinstance(x, str):
        return x, ""
    return x.get("t") or x.get("text") or "", x.get("d") or x.get("desc") or ""


def xhs_memo(ctx, fonts_css):
    c = ctx.item["content"]
    W, H, pad, u = ctx.W, ctx.H, ctx.safe, ctx.u
    gold = "#A87A00"  # the notes app's amber, darkened enough to read
    icon = lambda d: (f'<svg viewBox="0 0 24 24" style="width:{ctx.px(4.2)};height:{ctx.px(4.2)}"><circle cx="12" cy="12" r="10" fill="none" stroke="{gold}" stroke-width="1.8"/>{d}</svg>')
    bar = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{pad:.0f}px;display:flex;align-items:center;justify-content:space-between;z-index:3">'
           f'<div style="display:flex;align-items:center;gap:{ctx.px(.6)}"><svg viewBox="0 0 12 20" style="width:{ctx.px(2)};height:{ctx.px(3.4)}"><path d="M10 2 L2 10 L10 18" stroke="{gold}" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>'
           + T(ctx, "caption", c.get("app") or "备忘录", c=gold, on="#FFFFFF", tag="span", style=f"font-size:{max(ctx.minc, 3.2 * u):.1f}px;")
           + f'</div><div style="display:flex;gap:{ctx.px(2.4)}">'
           + icon(f'<path d="M8 12 A4 4 0 1 1 12 16" stroke="{gold}" stroke-width="1.8" fill="none"/>')
           + icon(f'<path d="M12 7 V15 M8 11 L12 7 L16 11" stroke="{gold}" stroke-width="1.8" fill="none"/>')
           + icon(f'<circle cx="8" cy="12" r="1.3" fill="{gold}"/><circle cx="12" cy="12" r="1.3" fill="{gold}"/><circle cx="16" cy="12" r="1.3" fill="{gold}"/>')
           + "</div></div>")
    head = (T(ctx, "headline", c.get("title") or "", c=INK, on="#FFFFFF", fit=(7.2 * u, 4.6 * u),
              style=_f("sans", 900) + "line-height:1.3;max-height:2.7em;")
            + (T(ctx, "caption", c.get("date"), c="#707070", on="#FFFFFF", style=f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;margin-top:{ctx.px(1.2)};") if c.get("date") else ""))
    rows = []
    for i, x in enumerate((c.get("items") or [])[:12]):
        t, d = _item_text(x)
        tick = (f'<svg viewBox="0 0 20 20" style="width:1.05em;height:1.05em;flex:none;margin-top:.2em"><circle cx="10" cy="10" r="9.5" fill="#F4C21B"/>'
                f'<path d="M5.5 10.4 L8.6 13.4 L14.5 7" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')
        rows.append(f'<div style="display:flex;gap:.5em;align-items:flex-start;margin:.55em 0">{tick}<div style="min-width:0">'
                    + T(ctx, "body", t, c=INK, on="#FFFFFF", style="font-size:1em;font-weight:700;line-height:1.4;")
                    + (T(ctx, "caption", d, c="#555555", on="#FFFFFF", style="font-size:.78em;line-height:1.5;margin-top:.15em;") if d else "")
                    + "</div></div>")
    lst = (f'<div data-fit="1" data-max="{4 * u:.1f}" data-min="{2.3 * u:.1f}" style="font-size:{4 * u:.1f}px;height:100%;overflow:hidden">'
           + "".join(rows) + "</div>")
    body = (f'<div style="position:absolute;inset:0;background:#FFFFFF"></div>' + bar
            + f'<div style="position:absolute;left:{pad * 1.05:.0f}px;right:{pad * 1.05:.0f}px;top:{pad * 2.3:.0f}px;z-index:3">{head}</div>'
            + f'<div style="position:absolute;left:{pad * 1.05:.0f}px;right:{pad * 1.05:.0f}px;top:{H * .26:.0f}px;bottom:{pad * .9:.0f}px;z-index:3">{lst}</div>'
            + extras(ctx, {k: v for k, v in c.items() if k == "handle"}, on_photo=False))
    css = ".pattern{display:none}em.hl{font-style:normal;background:linear-gradient(transparent 55%,#FFE77A 55%)}"
    return page(ctx, fonts_css, body, css)


# ------------------------------------------------------------------ ranking
def xhs_ranking(ctx, fonts_css):
    c, t = ctx.item["content"], ctx.t
    W, H, pad, u = ctx.W, ctx.H, ctx.safe, ctx.u
    acc = t["accent"]
    bg = f"linear-gradient(180deg,{mix(acc, '#FFFFFF', .86)},#FFFFFF 46%)"
    pill = lambda s, dark: (f'<span style="display:inline-block;border-radius:99px;padding:{ctx.px(.4)} {ctx.px(1.6)};'
                            f'border:{ctx.px(.3)} solid {INK};background:{INK if dark else "#FFFFFF"}">'
                            + T(ctx, "label", s, c="#FFFFFF" if dark else INK, on=INK if dark else "#FFFFFF", tag="span",
                                style=_f("sans", 900) + f"font-size:{max(ctx.minc, 2.4 * u):.1f}px;white-space:nowrap;") + "</span>")
    top = (f'<div style="display:flex;justify-content:space-between;align-items:center">'
           + (pill(c["kicker"], True) if c.get("kicker") else "<span></span>")
           + (pill(c["tag"], False) if c.get("tag") else "") + "</div>")
    head = T(ctx, "headline", c.get("title") or "", c=INK, on="#FFFFFF", fit=(10 * u, 6 * u),
             style=_f("sans", 900) + f"line-height:1.12;margin-top:{ctx.px(2.4)};max-height:2.4em;white-space:pre-line;")
    sub = T(ctx, "sub", c.get("sub"), c="#444444", on="#FFFFFF", style=_f("sans", 700) + f"font-size:{max(ctx.minb, 3 * u):.1f}px;margin-top:{ctx.px(1.2)};") if c.get("sub") else ""
    rows = []
    for i, x in enumerate((c.get("items") or [])[:10]):
        name, desc = _item_text(x)
        val = x.get("v", "") if isinstance(x, dict) else ""
        hot = i < 3
        num = (f'<div style="flex:none;width:1.9em;height:1.9em;border-radius:.35em;display:flex;align-items:center;justify-content:center;'
               f'background:{acc if hot else "#EEF0F3"}">'
               + T(ctx, "label", f"{i + 1:02d}", c="#FFFFFF" if hot else "#666666", on=acc if hot else "#EEF0F3", tag="span",
                   style=_f("sans", 900) + "font-size:.82em;") + "</div>")
        rows.append(f'<div style="display:flex;align-items:center;gap:.6em;padding:.38em 0;border-bottom:1px solid #EEF0F3">{num}'
                    f'<div style="flex:1;min-width:0">' + T(ctx, "body", name, c=INK, on="#FFFFFF", style="font-size:1em;font-weight:900;line-height:1.25;white-space:nowrap;overflow:hidden;")
                    + (T(ctx, "caption", desc, c="#666666", on="#FFFFFF", style="font-size:.7em;line-height:1.35;white-space:nowrap;overflow:hidden;") if desc else "")
                    + "</div>" + (T(ctx, "label", val, c=acc, on="#FFFFFF", tag="span", style="font-size:.86em;font-weight:900;white-space:nowrap;") if val else "")
                    + "</div>")
    lst = (f'<div data-fit="1" data-max="{3.9 * u:.1f}" data-min="{2.3 * u:.1f}" style="font-size:{3.9 * u:.1f}px;height:100%;overflow:hidden">'
           + "".join(rows) + "</div>")
    card = (f'<div style="position:absolute;left:{pad * .8:.0f}px;right:{pad * .8:.0f}px;top:{H * .34:.0f}px;bottom:{pad * .9:.0f}px;background:#FFFFFF;'
            f'border-radius:{ctx.px(2.4)};box-shadow:0 {ctx.px(.8)} {ctx.px(3)} rgba(0,0,0,.08);padding:{ctx.px(2)} {ctx.px(3)};z-index:3">{lst}</div>')
    body = (f'<div style="position:absolute;inset:0;background:{bg}"></div>'
            + f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{pad * .9:.0f}px;height:{H * .34 - pad * 1.1:.0f}px;z-index:3;display:flex;flex-direction:column">{top}{head}{sub}</div>'
            + card + extras(ctx, {k: v for k, v in c.items() if k == "handle"}, on_photo=False))
    css = f".pattern{{display:none}}em.hl{{font-style:normal;color:{acc}}}"
    return page(ctx, fonts_css, body, css)


# ------------------------------------------------------------------ grid
def xhs_grid(ctx, fonts_css):
    c = ctx.item["content"]
    W, H, pad, u = ctx.W, ctx.H, ctx.safe, ctx.u
    cells = c.get("photos") or [{} for _ in range(int(c.get("cells") or 4))]
    cells = [x if isinstance(x, dict) else {"src": x} for x in cells][:9]
    cols = 2 if len(cells) <= 4 else 3
    rows_n = math.ceil(len(cells) / cols)
    gap = ctx.px(.5)
    tiles = []
    tints = ["#E8C39E", "#9CC5A1", "#F2A7A0", "#A9C4E8", "#F5D97A", "#C9A9E0", "#8FD3C1", "#F0B37E", "#D6D0C4"]
    for i, x in enumerate(cells):
        inner = (f'<img src="{esc(x["src"])}" data-role="image" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">' if x.get("src")
                 else f'<div style="position:absolute;inset:0;background:{tints[i % 9]}"></div>')
        col, row = i % cols, i // cols  # cells on the outer edge keep the canvas safe margin
        lx = f"{pad:.0f}px" if col == 0 else "6%"
        tx = f"{pad:.0f}px" if row == 0 else "6%"
        bx = f"{pad:.0f}px" if row == rows_n - 1 else "6%"
        tag = (f'<div style="position:absolute;left:{lx};top:{tx};background:{YELLOW};border-radius:{ctx.px(.8)};padding:{ctx.px(.2)} {ctx.px(1)}">'
               + T(ctx, "label", x["tag"], c=INK, on=YELLOW, tag="span", style=_f("sans", 900) + f"font-size:{max(ctx.minc, 2.2 * u):.1f}px;white-space:nowrap;") + "</div>") if x.get("tag") else ""
        lab = (f'<div style="position:absolute;left:{lx};right:4%;bottom:{bx}">'
               + T(ctx, "label", x["label"], c="#FFFFFF", on=INK, tag="span", style=_f("sans", 900) + f"font-size:{max(ctx.minb, (3.4 if cols == 2 else 2.8) * u):.1f}px;white-space:nowrap;{ring(INK, .08)}")
               + "</div>") if x.get("label") else ""
        tiles.append(f'<div style="position:relative;overflow:hidden">{inner}{tag}{lab}</div>')
    grid = (f'<div style="position:absolute;inset:0;display:grid;grid-template-columns:repeat({cols},1fr);grid-template-rows:repeat({rows_n},1fr);gap:{gap};background:#fff">'
            + "".join(tiles) + "</div>")
    lines = title_lines(ctx, c)
    longest = max((plain_len(x) for x in lines), default=1)
    if (c.get("title_pos") or "center") == "top":
        title = (f'<div data-grp="title" style="position:absolute;left:0;right:0;top:0;background:#FFFFFF;padding:{ctx.px(2)} {pad:.0f}px;z-index:5;text-align:center">'
                 + "".join(huazi(ctx, ln, fill=INK if i == 0 else RED, stroke="#FFFFFF", r=.02, width=min(.9, .9 * plain_len(ln) / longest), cap_px=10 * u, align="center")
                           for i, ln in enumerate(lines)) + "</div>")
    else:
        title = (f'<div data-grp="title" style="position:absolute;left:18%;right:18%;top:50%;transform:translate(0,-50%) rotate(-2deg);background:#FFFFFF;'
                 f'border-radius:{ctx.px(1.6)};padding:{ctx.px(2.2)} {ctx.px(2.6)};box-shadow:0 {ctx.px(1)} {ctx.px(3)} rgba(0,0,0,.25);z-index:5;text-align:center">'
                 + "".join(huazi(ctx, ln, fill=INK, stroke="#FFFFFF", r=.02, width=min(.96, .96 * plain_len(ln) / longest), cap_px=11 * u, align="center")
                           for ln in lines)
                 + (T(ctx, "sub", c.get("sub"), c=RED_TEXT, on="#FFFFFF", style=_f("sans", 900) + f"font-size:{max(ctx.minb, 2.8 * u):.1f}px;margin-top:{ctx.px(.8)};") if c.get("sub") else "")
                 + "</div>")
    body = grid + title + extras(ctx, c)
    return page(ctx, fonts_css, body, f".pattern{{display:none}}.hz em.hl{{color:{RED}}}")


# ------------------------------------------------------------------ compare
def xhs_compare(ctx, fonts_css):
    c = ctx.item["content"]
    W, H, pad, u = ctx.W, ctx.H, ctx.safe, ctx.u
    ph = list(c.get("photos") or [])[:2] + [None, None]
    labels = list(c.get("labels") or ["之前", "之后"])[:2] + ["", ""]
    lr = c.get("split") == "lr"
    halves = []
    for i in range(2):
        src = ph[i]["src"] if isinstance(ph[i], dict) else ph[i]
        box = (f"left:{i * 50}%;top:0;width:50%;height:100%" if lr else f"left:0;top:{i * 50}%;width:100%;height:50%")
        tint = (("#B9B4AC", "#8F8A83") if i == 0 else ("#FFF3E3", "#F2D7B5"))
        edge = "top" if (i == 0 or lr) else "bottom"  # labels sit away from the title strip in the middle
        lab = (f'<div style="position:absolute;left:{pad * 1.1:.0f}px;{edge}:{pad * 1.2:.0f}px;right:{pad:.0f}px;z-index:4">'
               + huazi(ctx, labels[i], fill="#FFFFFF" if i == 0 else YELLOW, width=.5 if not lr else .9, cap_px=9 * u, rot=-2)
               + "</div>") if labels[i] else ""
        halves.append(f'<div style="position:absolute;{box};overflow:hidden">'
                      + photo_or_placeholder(ctx, src, label="【换成照片】", tint=tint, corner="top" if i == 0 else "bottom") + lab + "</div>")
    line = (f'<div style="position:absolute;{"left:50%;top:0;bottom:0;width" if lr else "top:50%;left:0;right:0;height"}:{ctx.px(.8)};'
            f'background:#FFFFFF;z-index:5;{"transform:translateX(-50%)" if lr else "transform:translateY(-50%)"}"></div>')
    title = ""
    if c.get("title"):
        title = (f'<div data-grp="title" style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;{"bottom" if lr else "top"}:{(pad * 1.2) if lr else (H / 2 - 7 * u):.0f}px;z-index:6;text-align:center">'
                 f'<span style="display:inline-block;background:#FFFFFF;padding:{ctx.px(1)} {ctx.px(2.4)};box-shadow:0 {ctx.px(.6)} {ctx.px(2)} rgba(0,0,0,.2)">'
                 + T(ctx, "headline", c["title"].replace("\n", " "), c=INK, on="#FFFFFF", tag="span", style=_f("sans", 900) + f"font-size:{8 * u:.1f}px;white-space:nowrap;")
                 + "</span></div>")
    body = "".join(halves) + line + title + extras(ctx, c)
    return page(ctx, fonts_css, body, f".pattern{{display:none}}.hz em.hl{{color:var(--hl)}}em.hl{{color:{RED};font-style:normal}}")


# ------------------------------------------------------------------ doodle
def _scribbles(ctx, seed, colors):
    rng = random.Random(seed)
    out = []
    shapes = [
        lambda c: f'<path d="M10 2 L12.4 7.6 L18.5 8 L13.8 12 L15.3 18 L10 14.8 L4.7 18 L6.2 12 L1.5 8 L7.6 7.6 Z" fill="none" stroke="{c}" stroke-width="1.6" stroke-linejoin="round"/>',
        lambda c: f'<path d="M10 17 C2 11 3 4 7.5 4 C9 4 10 5.5 10 6.5 C10 5.5 11 4 12.5 4 C17 4 18 11 10 17 Z" fill="{c}"/>',
        lambda c: f'<path d="M2 12 Q5 4 8 12 T14 12 T19 10" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round"/>',
        lambda c: f'<path d="M10 1 V19 M1 10 H19 M4 4 L16 16 M16 4 L4 16" stroke="{c}" stroke-width="1.5" stroke-linecap="round"/>',
        lambda c: f'<circle cx="10" cy="10" r="6" fill="none" stroke="{c}" stroke-width="1.8"/>',
    ]
    spots = [(5, 7), (88, 6), (4, 44), (90, 40), (8, 88), (86, 86), (50, 3), (93, 63)]
    for i, (x, y) in enumerate(spots):
        s = rng.uniform(3.2, 5.4)
        out.append(f'<svg viewBox="0 0 20 20" style="position:absolute;left:{x}%;top:{y}%;width:{ctx.px(s)};height:{ctx.px(s)};'
                   f'transform:rotate({rng.randint(-20, 20)}deg);z-index:2">{shapes[i % len(shapes)](colors[i % len(colors)])}</svg>')
    return "".join(out)


def xhs_doodle(ctx, fonts_css):
    c, a = ctx.item["content"], ctx.item.get("art") or {}
    W, H, pad, u = ctx.W, ctx.H, ctx.safe, ctx.u
    bg = CARD_COLORS.get(c.get("color") or "cream", CARD_COLORS["cream"])[0]
    palette = c.get("colors") or ["#2F6B4F", "#C4561A", "#2B2B2B"]
    font = "mashan" if c.get("font") == "brush" else "kuaile"
    lines = title_lines(ctx, c)
    longest = max((plain_len(x) for x in lines), default=1)
    rows = []
    for i, ln in enumerate(lines):
        node = T(ctx, "headline", ln, c=palette[i % len(palette)], on=bg, tag="span",
                 style=_f(font, 400) + "line-height:1.25;letter-spacing:.02em;")
        node = node.replace('class="t', f'data-justify="{min(.9, .9 * plain_len(ln) / longest):.3f}" data-cap-px="{12 * u:.0f}" class="t', 1)
        rows.append(f'<div style="text-align:center;transform:rotate({(-2, 1.5, -1)[i % 3]}deg)">{node}</div>')
    title = (f'<div data-grp="title" style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;top:{H * .12:.0f}px;z-index:5">'
             + "".join(rows) + "</div>")
    pic = (f'<div style="position:absolute;left:18%;right:18%;top:{H * .47:.0f}px;bottom:{H * .13:.0f}px;z-index:3">'
           + art_block(ctx, {**a, "image_fit": "contain", "style": a.get("style") or "crayon"}) + "</div>")
    sub = (f'<div style="position:absolute;left:{pad:.0f}px;right:{pad:.0f}px;bottom:{pad * 1.1:.0f}px;text-align:center;z-index:5">'
           + T(ctx, "sub", c.get("sub"), c=palette[-1], on=bg, style=_f(font, 400) + f"font-size:{max(ctx.minb, 3.6 * u):.1f}px;") + "</div>") if c.get("sub") else ""
    body = (f'<div style="position:absolute;inset:0;background:{bg}"></div>' + _scribbles(ctx, len(c.get("title") or ""), palette + [YELLOW])
            + title + pic + sub + extras(ctx, c, on_photo=False))
    css = f".pattern{{display:none}}em.hl{{font-style:normal;background:linear-gradient(transparent 52%,{YELLOW} 52%)}}"
    return page(ctx, fonts_css, body, css)


def register(builders, layouts):
    layouts["xhs"] = ["photo", "textcard", "memo", "ranking", "grid", "compare", "doodle"]
    for name, fn in (("photo", xhs_photo), ("textcard", xhs_textcard), ("memo", xhs_memo), ("ranking", xhs_ranking),
                     ("grid", xhs_grid), ("compare", xhs_compare), ("doodle", xhs_doodle)):
        builders[("xhs", name)] = fn
