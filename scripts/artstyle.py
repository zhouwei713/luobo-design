"""Art styles without an image model: the same vector drawings rendered as watercolour, paper cut,
risograph print, clay, line art, crayon, pop art, neon, soft gradient light or ink wash.

Everything is SVG filters, CSS and generated shapes, so it renders the same on every machine.
When an image model is configured, STYLES[...]["prompt_en" / "prompt_zh"] goes into the prompts
instead, so the generated picture and the procedural fallback ask for the same look.

  panel(style, t, uid, w, h) -> (html for the background, {"bg", "ink", "muted"} colours to put text on it)
  dress(style, inner_html, t, uid, role) -> the drawing wearing the style (role "hero" or "bit")
  defs(style, t, uid) -> hidden <svg> with the filters, once per page
"""
import math
import random

from common import contrast, mix, rgba

STYLES = {
    "flat": {"name": "扁平插画", "name_en": "flat illustration",
             "prompt_en": "clean flat vector illustration, simple shapes, solid colours",
             "prompt_zh": "干净的扁平矢量插画，简单的形状，纯色块"},
    "watercolor": {"name": "水彩", "name_en": "watercolour",
                   "prompt_en": "loose watercolour painting on cold-press paper, soft wet edges, pigment blooms and granulation, gentle washes, white paper showing through",
                   "prompt_zh": "水彩画，冷压水彩纸，湿润柔和的边缘，颜料晕染和沉淀的颗粒，淡淡的铺色，留出纸的白"},
    "papercut": {"name": "剪纸", "name_en": "layered paper cut",
                 "prompt_en": "layered paper-cut art, stacked coloured card stock with soft drop shadows between layers, crisp cut edges, handmade diorama feel",
                 "prompt_zh": "多层剪纸艺术，彩色卡纸层层叠起，层与层之间有柔和的投影，利落的刀口，手工立体感"},
    "riso": {"name": "孔版印刷", "name_en": "risograph print",
             "prompt_en": "risograph print, two spot inks with slight misregistration, visible halftone dots and paper grain, overprint colours",
             "prompt_zh": "孔版印刷（Risograph）效果，两种专色轻微错版，看得见网点和纸张颗粒，颜色叠印"},
    "clay": {"name": "3D 黏土", "name_en": "3D clay",
             "prompt_en": "cute 3D clay render, soft plasticine material, rounded puffy shapes, studio soft lighting, pastel background, subtle fingerprints",
             "prompt_zh": "可爱的 3D 黏土质感，软软的橡皮泥材质，圆鼓鼓的造型，柔和的棚拍光，浅色背景，隐约的手捏痕迹"},
    "lineart": {"name": "线描", "name_en": "line art",
                "prompt_en": "minimal single-weight line drawing with one offset block of colour, lots of white space, editorial illustration",
                "prompt_zh": "极简的等粗线描，配一块错开的色块，大量留白，杂志插画感"},
    "crayon": {"name": "蜡笔手绘", "name_en": "crayon drawing",
               "prompt_en": "childlike crayon and oil-pastel drawing on kraft paper, waxy texture, rough strokes, playful scribbles",
               "prompt_zh": "蜡笔和油画棒手绘，牛皮纸底，蜡质的颗粒感，粗糙的笔触，童趣的涂鸦"},
    "pop": {"name": "波普", "name_en": "pop art",
            "prompt_en": "bold pop art comic style, thick black outlines, Ben-Day halftone dots, starburst, saturated primary colours, hard offset shadow",
            "prompt_zh": "大胆的波普漫画风，粗黑描边，本戴网点，爆炸星形，高饱和原色，硬投影"},
    "neon": {"name": "霓虹", "name_en": "neon sign",
             "prompt_en": "glowing neon sign on a dark brick wall at night, bright tube lines with bloom, reflections, moody",
             "prompt_zh": "夜晚深色砖墙上发光的霓虹灯牌，明亮的灯管线条和光晕，有反光，氛围感"},
    "diffuse": {"name": "弥散光", "name_en": "soft gradient light",
                "prompt_en": "dreamy diffuse gradient background with soft blurred colour blobs, frosted glass, gentle glow, fine grain, modern minimal",
                "prompt_zh": "梦幻的弥散渐变背景，柔和模糊的色块，磨砂玻璃，温柔的光晕，细腻的颗粒，现代极简"},
    "ink": {"name": "水墨", "name_en": "Chinese ink wash",
            "prompt_en": "Chinese ink wash painting on rice paper, expressive brush strokes, ink bleeding, misty mountains, generous empty space, one red accent",
            "prompt_zh": "中国水墨画，宣纸，写意的笔触，墨色晕开，远山云雾，大面积留白，一点朱红"},
}


def _light(c, k):
    return mix(c, "#FFFFFF", k)


def _readable(bg, *cands):
    best = max(cands, key=lambda c: contrast(c, bg))
    return best


def colours(style, t):
    """The colours of the art panel. Text placed on the panel uses ink / muted from here."""
    a1, a2, bg = t["accent"], t["accent2"], t["bg"]
    if contrast(a1, a2) < 1.3:
        a2 = mix(a1, "#FFFFFF", .55)
    p = {"bg": _light(bg, .5), "a1": a1, "a2": a2}
    if style == "watercolor":
        p["bg"] = mix(bg, "#FFFDF8", .7)
    elif style == "papercut":
        p["bg"] = _light(a1, .8)
    elif style == "riso":
        p["bg"] = "#F4EFE6"
    elif style == "clay":
        p["bg"] = _light(a2 if contrast(a2, "#FFFFFF") > 1.4 else a1, .78)
    elif style == "crayon":
        p["bg"] = "#EADBC2"
    elif style == "pop":
        p["bg"] = "#FFD93B" if contrast(a1, "#FFD93B") > 1.6 else _light(a2, .3)
    elif style == "neon":
        p["bg"] = "#17121F"
    elif style == "diffuse":
        p["bg"] = mix(bg, "#FFFFFF", .6)
    elif style == "ink":
        p["bg"] = "#F3EEE3"
    elif style == "lineart":
        p["bg"] = mix(bg, "#FFFFFF", .3)
    p["ink"] = _readable(p["bg"], t["ink"], "#1B1B1B", "#FFFFFF", "#F6F1E8")
    p["muted"] = mix(p["ink"], p["bg"], .3)
    return p


# ------------------------------------------------------------------ filters
def defs(style, t, uid):
    u = uid
    p = colours(style, t)
    f = ""
    if style == "watercolor":
        f = f"""
<filter id="wc{u}" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB">
 <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" seed="4" result="n"/>
 <feDisplacementMap in="SourceGraphic" in2="n" scale="16" xChannelSelector="R" yChannelSelector="G" result="d"/>
 <feGaussianBlur in="d" stdDeviation="1.4" result="db"/>
 <feMorphology in="db" operator="erode" radius="2.5" result="er"/>
 <feComposite in="db" in2="er" operator="out" result="edge"/>
 <feColorMatrix in="edge" type="matrix" values="0.62 0 0 0 0  0 0.62 0 0 0  0 0 0.62 0 0  0 0 0 0.85 0" result="edgeDark"/>
 <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="9" result="g"/>
 <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.6 1.45" result="gm"/>
 <feComposite in="db" in2="gm" operator="in" result="gran"/>
 <feComponentTransfer in="gran" result="soft"><feFuncA type="linear" slope="1"/></feComponentTransfer>
 <feMerge><feMergeNode in="soft"/><feMergeNode in="edgeDark"/></feMerge>
</filter>
<filter id="wash{u}" x="-30%" y="-30%" width="160%" height="160%">
 <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="3" seed="2" result="n"/>
 <feDisplacementMap in="SourceGraphic" in2="n" scale="70" xChannelSelector="R" yChannelSelector="G" result="d"/>
 <feGaussianBlur in="d" stdDeviation="5"/>
</filter>"""
    elif style == "papercut":
        f = f"""
<filter id="pc{u}" x="-12%" y="-12%" width="124%" height="130%">
 <feMorphology in="SourceAlpha" operator="dilate" radius="6" result="dil"/>
 <feFlood flood-color="#FFFFFF"/><feComposite in2="dil" operator="in" result="border"/>
 <feMerge result="m"><feMergeNode in="border"/><feMergeNode in="SourceGraphic"/></feMerge>
 <feGaussianBlur in="dil" stdDeviation="7" result="sh"/><feOffset in="sh" dx="0" dy="10" result="sho"/>
 <feFlood flood-color="#3A2A20" flood-opacity=".32"/><feComposite in2="sho" operator="in" result="shadow"/>
 <feMerge><feMergeNode in="shadow"/><feMergeNode in="m"/></feMerge>
</filter>
<filter id="pcs{u}" x="-5%" y="-20%" width="110%" height="140%"><feDropShadow dx="0" dy="-6" stdDeviation="7" flood-color="#3A2A20" flood-opacity=".28"/></filter>"""
    elif style == "riso":
        def duo(i, c):
            r, g, b = (int(c[k:k + 2], 16) / 255 for k in (1, 3, 5))
            return (f'<filter id="ri{i}{u}" color-interpolation-filters="sRGB">'
                    f'<feColorMatrix type="matrix" values="0 0 0 0 {r:.3f}  0 0 0 0 {g:.3f}  0 0 0 0 {b:.3f}  -0.17 -0.17 -0.17 1 0" result="ink"/>'
                    f'<feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="1" seed="{3 + i}" result="g"/>'
                    f'<feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2 1.7" result="gm"/>'
                    f'<feComposite in="ink" in2="gm" operator="in"/></filter>')
        f = duo(1, p["a1"]) + duo(2, p["a2"] if contrast(p["a2"], p["bg"]) > 1.3 else "#2F6FDB")
    elif style == "clay":
        f = f"""
<filter id="cl{u}" x="-15%" y="-15%" width="130%" height="135%" color-interpolation-filters="sRGB">
 <feGaussianBlur in="SourceAlpha" stdDeviation="7" result="b"/>
 <feDiffuseLighting in="b" surfaceScale="7" diffuseConstant="1.05" lighting-color="#FFFFFF" result="diff"><feDistantLight azimuth="235" elevation="52"/></feDiffuseLighting>
 <feComposite in="diff" in2="SourceAlpha" operator="in" result="diffIn"/>
 <feBlend in="SourceGraphic" in2="diffIn" mode="multiply" result="shaded"/>
 <feSpecularLighting in="b" surfaceScale="7" specularConstant=".75" specularExponent="22" lighting-color="#FFFFFF" result="spec"><feDistantLight azimuth="235" elevation="58"/></feSpecularLighting>
 <feComposite in="spec" in2="SourceAlpha" operator="in" result="specIn"/>
 <feComposite in="shaded" in2="specIn" operator="arithmetic" k1="0" k2="1.12" k3=".55" k4="0" result="lit"/>
 <feGaussianBlur in="SourceAlpha" stdDeviation="12" result="sb"/><feOffset in="sb" dx="0" dy="16" result="so"/>
 <feFlood flood-color="#3A2A20" flood-opacity=".22"/><feComposite in2="so" operator="in" result="sh"/>
 <feMerge><feMergeNode in="sh"/><feMergeNode in="lit"/></feMerge>
</filter>"""
    elif style == "crayon":
        f = f"""
<filter id="cr{u}" x="-10%" y="-10%" width="120%" height="120%">
 <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="5" result="n"/>
 <feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G" result="d"/>
 <feTurbulence type="fractalNoise" baseFrequency="0.7 0.08" numOctaves="2" seed="11" result="g"/>
 <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.4 1.95" result="gm"/>
 <feComposite in="d" in2="gm" operator="in" result="wax"/>
 <feMorphology in="d" operator="erode" radius="1.5" result="er"/><feComposite in="d" in2="er" operator="out" result="edge"/>
 <feColorMatrix in="edge" type="matrix" values="0.55 0 0 0 0  0 0.55 0 0 0  0 0 0.55 0 0  0 0 0 1 0" result="edgeD"/>
 <feMerge><feMergeNode in="wax"/><feMergeNode in="edgeD"/></feMerge>
</filter>"""
    elif style == "pop":
        f = f"""
<filter id="po{u}" x="-15%" y="-15%" width="135%" height="135%">
 <feMorphology in="SourceAlpha" operator="dilate" radius="7" result="dil"/>
 <feFlood flood-color="#111111"/><feComposite in2="dil" operator="in" result="outline"/>
 <feOffset in="outline" dx="14" dy="14" result="hard"/>
 <feMerge><feMergeNode in="hard"/><feMergeNode in="outline"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>"""
    elif style == "neon":
        f = f"""
<filter id="ne{u}" x="-40%" y="-40%" width="180%" height="180%">
 <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="b1"/>
 <feGaussianBlur in="SourceGraphic" stdDeviation="9" result="b2"/>
 <feGaussianBlur in="SourceGraphic" stdDeviation="24" result="b3"/>
 <feMerge><feMergeNode in="b3"/><feMergeNode in="b2"/><feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>"""
    elif style == "ink":
        f = f"""
<filter id="ik{u}" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB">
 <feColorMatrix type="matrix" values="0.510 0.385 0.105 0 -0.1  0.210 0.685 0.105 0 -0.1  0.210 0.385 0.405 0 -0.1  0 0 0 1 0" result="gray"/>
 <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" seed="7" result="n"/>
 <feDisplacementMap in="gray" in2="n" scale="9" xChannelSelector="R" yChannelSelector="G" result="d"/>
 <feGaussianBlur in="d" stdDeviation="4" result="bleed"/>
 <feComponentTransfer in="bleed" result="bleedSoft"><feFuncA type="linear" slope=".45"/></feComponentTransfer>
 <feMerge><feMergeNode in="bleedSoft"/><feMergeNode in="d"/></feMerge>
</filter>
<filter id="mt{u}" x="-20%" y="-40%" width="140%" height="180%">
 <feTurbulence type="fractalNoise" baseFrequency="0.02 0.06" numOctaves="4" seed="3" result="n"/>
 <feDisplacementMap in="SourceGraphic" in2="n" scale="40" xChannelSelector="R" yChannelSelector="G" result="d"/>
 <feGaussianBlur in="d" stdDeviation="6"/>
</filter>"""
    return f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{f}</defs></svg>' if f else ""


# ------------------------------------------------------------------ dressing a drawing
def dress(style, inner, t, uid, role="hero"):
    """inner: html that draws the motif and fills its box. Returns html filling the same box."""
    u = uid
    p = colours(style, t)
    box = "position:absolute;inset:0"
    if style == "watercolor":
        blend = ";mix-blend-mode:multiply" if role == "bit" else ""
        return f'<div style="{box};filter:url(#wc{u}){blend}">{inner}</div>'
    if style == "papercut":
        return f'<div style="{box};filter:url(#pc{u})">{inner}</div>'
    if style == "riso":
        off = 1.6 if role == "hero" else 0.8
        return (f'<div style="{box};filter:url(#ri2{u});mix-blend-mode:multiply;transform:translate({off}%, -{off * .6}%)">{inner}</div>'
                f'<div style="{box};filter:url(#ri1{u});mix-blend-mode:multiply">{inner}</div>')
    if style == "clay":
        return f'<div style="{box};filter:url(#cl{u})">{inner}</div>'
    if style == "crayon":
        return f'<div style="{box};filter:url(#cr{u})">{inner}</div>'
    if style == "pop":
        return f'<div style="{box};filter:url(#po{u})">{inner}</div>'
    if style in ("lineart", "neon"):
        cls = f"ln{u}" if style == "lineart" else f"nl{u}"
        blob = ""
        if style == "lineart" and role == "hero":
            blob = (f'<div style="position:absolute;left:24%;top:30%;width:58%;height:58%;border-radius:46% 54% 50% 50%;'
                    f'background:{rgba(p["a1"], .28)};transform:translate(6%,4%)"></div>')
        glow = f";filter:url(#ne{u})" if style == "neon" else ""
        return f'{blob}<div class="{cls}" style="{box}{glow}">{inner}</div>'
    if style == "diffuse":
        return f'<div style="{box};filter:drop-shadow(0 30px 40px {rgba(p["a1"], .35)})">{inner}</div>'
    if style == "ink":
        return f'<div style="{box};filter:url(#ik{u})">{inner}</div>'
    return f'<div style="{box}">{inner}</div>'


def css(style, t, uid):
    u = uid
    p = colours(style, t)
    if style == "lineart":
        return (f".ln{u} svg *{{fill:none!important;stroke:{p['ink']}!important;stroke-width:1.7px!important;stroke-linejoin:round;stroke-linecap:round}}"
                f".ln{u} svg>ellipse:first-of-type{{display:none}}")
    if style == "neon":
        c1 = mix(p["a1"], "#FFFFFF", .15)
        c2 = "#5CF2FF" if contrast(p["a1"], "#5CF2FF") > 1.4 else "#FF5CC8"
        return (f".nl{u} svg *{{fill:none!important;stroke:{c1}!important;stroke-width:2.2px!important;stroke-linejoin:round;stroke-linecap:round}}"
                f".nl{u} svg circle,.nl{u} svg rect{{stroke:{c2}!important}}"
                f".nl{u} svg>ellipse:first-of-type{{display:none}}")
    return ""


# ------------------------------------------------------------------ backgrounds
def _blob(rng, cx, cy, r, n=9, wob=.22):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1 + rng.uniform(-wob, wob))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = f"M{(pts[0][0] + pts[-1][0]) / 2:.1f} {(pts[0][1] + pts[-1][1]) / 2:.1f} "
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        d += f"Q{p0[0]:.1f} {p0[1]:.1f} {(p0[0] + p1[0]) / 2:.1f} {(p0[1] + p1[1]) / 2:.1f} "
    return d + "Z"


def panel(style, t, uid, w, h, seed=1, full_page=False):
    """Background art for a w x h panel. Returns (html, colours)."""
    u = uid
    p = colours(style, t)
    rng = random.Random(seed)
    W, H = w, h
    m = min(W, H)
    svg = lambda body, extra="": (f'<svg viewBox="0 0 {W:.0f} {H:.0f}" preserveAspectRatio="none" width="100%" height="100%" '
                                  f'style="position:absolute;inset:0{extra}">{body}</svg>')
    layers = [f'<div style="position:absolute;inset:0;background:{p["bg"]}"></div>']
    if style == "watercolor":
        washes = ""
        for c, x, y, r, o in ((p["a2"], .25, .3, .42, .32), (p["a1"], .78, .72, .38, .22), (mix(p["a1"], p["a2"], .5), .7, .18, .26, .2)):
            washes += f'<path d="{_blob(rng, W * x, H * y, m * r)}" fill="{c}" opacity="{o}"/>'
        layers.append(svg(f'<g filter="url(#wash{u})">{washes}</g>', ";mix-blend-mode:multiply"))
        for i in range(14):  # paint spatters
            x, y, r = rng.uniform(.05, .95) * W, rng.uniform(.05, .95) * H, rng.uniform(.002, .008) * m
            layers.append(svg(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{rgba(p["a1"], .35)}"/>'))
    elif style == "papercut":
        hills = ""
        for i, k in enumerate((.62, .48, .32, .16)):
            y0 = H * (0.56 + i * .11)
            amp = H * .05
            d = f"M0 {y0:.0f} "
            for j in range(5):
                x1, x2 = W * (j + .5) / 5, W * (j + 1) / 5
                d += f"Q{x1:.0f} {y0 + (amp if j % 2 else -amp) * rng.uniform(.6, 1.2):.0f} {x2:.0f} {y0:.0f} "
            d += f"L{W:.0f} {H:.0f} L0 {H:.0f} Z"
            hills += f'<path d="{d}" fill="{mix(p["a1"], "#FFFFFF", k)}" filter="url(#pcs{u})"/>'
        sun = f'<circle cx="{W * .78:.0f}" cy="{H * .2:.0f}" r="{m * .12:.0f}" fill="{mix(p["a2"], "#FFFFFF", .2)}" filter="url(#pcs{u})"/>'
        layers.append(svg(sun + hills))
    elif style == "riso":
        c2 = p["a2"] if contrast(p["a2"], p["bg"]) > 1.3 else "#2F6FDB"
        shapes = (f'<circle cx="{W * .74:.0f}" cy="{H * .4:.0f}" r="{m * .3:.0f}" fill="{rgba(c2, .38)}"/>'
                  + ("" if full_page else "".join(f'<rect x="0" y="{H * (.62 + i * .06):.0f}" width="{W * .42:.0f}" height="{H * .025:.0f}" fill="{rgba(p["a1"], .5)}"/>' for i in range(5))))
        layers.append(svg(shapes, ";mix-blend-mode:multiply"))
        layers.append(f'<div style="position:absolute;inset:0;mix-blend-mode:multiply;opacity:.35;'
                      f'background-image:radial-gradient({p["a1"]} 28%, transparent 30%);background-size:{m * .018:.1f}px {m * .018:.1f}px;'
                      f'-webkit-mask-image:linear-gradient(160deg, transparent 40%, #000 100%);mask-image:linear-gradient(160deg, transparent 40%, #000 100%)"></div>')
    elif style == "clay":
        pebbles = ""
        for x, y, r, c in ((.14, .82, .07, p["a1"]), (.86, .26, .05, p["a2"]), (.9, .86, .045, mix(p["a1"], "#FFFFFF", .4)), (.1, .2, .035, p["a2"])):
            pebbles += (f'<div style="position:absolute;left:{(x - r) * 100:.1f}%;top:calc({y * 100:.1f}% - {r * m:.0f}px);width:{2 * r * m:.0f}px;height:{2 * r * m:.0f}px;'
                        f'border-radius:50%;background:{c};filter:url(#cl{u})"></div>')
        layers.append(f'<div style="position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 30%, {mix(p["bg"], "#FFFFFF", .5)}, {p["bg"]})"></div>')
        layers.append(f'<div style="position:absolute;left:18%;right:18%;bottom:8%;height:9%;border-radius:50%;background:{rgba("#3A2A20", .1)};filter:blur({m * .02:.0f}px)"></div>')
        layers.append(pebbles)
    elif style == "lineart":
        doodles = ""
        for i in range(6):
            x, y, s = rng.uniform(.08, .92) * W, rng.uniform(.08, .58 if full_page else .92) * H, m * rng.uniform(.018, .03)  # keep doodles off the copy
            if i % 2:
                doodles += f'<path d="M{x - s:.0f} {y:.0f} L{x + s:.0f} {y:.0f} M{x:.0f} {y - s:.0f} L{x:.0f} {y + s:.0f}" stroke="{p["ink"]}" stroke-width="{m * .004:.1f}" stroke-linecap="round"/>'
            else:
                doodles += f'<path d="M{x - 2 * s:.0f} {y:.0f} q{s:.0f} {-s:.0f} {2 * s:.0f} 0 t{2 * s:.0f} 0" stroke="{p["a1"]}" stroke-width="{m * .004:.1f}" fill="none" stroke-linecap="round"/>'
        layers.append(svg(doodles))
    elif style == "crayon":
        scr = ""
        for c, y0 in (((p["a2"], .2),) if full_page else ((p["a1"], .9), (p["a2"], .2))):
            d = f"M{W * .05:.0f} {H * y0:.0f} "
            for i in range(26):
                d += f"L{W * (.05 + .9 * (i + 1) / 26):.0f} {H * (y0 + (.03 if i % 2 else -.03)):.0f} "
            scr += f'<path d="{d}" stroke="{c}" stroke-width="{m * .02:.0f}" fill="none" stroke-linejoin="round" stroke-linecap="round" opacity=".8"/>'
        for x, y in ((.12, .3), (.88, .55), (.2, .66)):
            cx, cy, s = W * x, H * y, m * .03
            pts = " ".join(f"{cx + s * (1 if k % 2 == 0 else .45) * math.cos(math.radians(-90 + k * 36)):.0f},{cy + s * (1 if k % 2 == 0 else .45) * math.sin(math.radians(-90 + k * 36)):.0f}" for k in range(10))
            scr += f'<polygon points="{pts}" fill="#F6C443"/>'
        layers.append(svg(f'<g filter="url(#cr{u})">{scr}</g>'))
    elif style == "pop":
        rays = "".join(f'<path d="M{W / 2:.0f} {H * .5:.0f} L{W / 2 + 2 * m * math.cos(math.radians(a)):.0f} {H * .5 + 2 * m * math.sin(math.radians(a)):.0f} '
                       f'L{W / 2 + 2 * m * math.cos(math.radians(a + 9)):.0f} {H * .5 + 2 * m * math.sin(math.radians(a + 9)):.0f} Z" fill="{rgba("#FFFFFF", .32)}"/>' for a in range(0, 360, 18))
        star = " ".join(f"{W / 2 + m * (.44 if k % 2 == 0 else .33) * math.cos(math.radians(k * 15)):.0f},{H * .5 + m * (.44 if k % 2 == 0 else .33) * math.sin(math.radians(k * 15)):.0f}" for k in range(24))
        layers.append(svg(rays + f'<polygon points="{star}" fill="#FFFFFF" stroke="#111111" stroke-width="{m * .008:.1f}"/>'))
        layers.append(f'<div style="position:absolute;inset:0;opacity:.5;background-image:radial-gradient({p["a1"]} 30%, transparent 32%);'
                      f'background-size:{m * .03:.0f}px {m * .03:.0f}px;-webkit-mask-image:radial-gradient(circle at 50% 50%, transparent 38%, #000 70%);'
                      f'mask-image:radial-gradient(circle at 50% 50%, transparent 38%, #000 70%)"></div>')
    elif style == "neon":
        layers.append(f'<div style="position:absolute;inset:0;background:radial-gradient(90% 70% at 50% 45%, #2A1F3A, {p["bg"]} 70%)"></div>')
        bricks = "".join(f'<path d="M0 {y:.0f} H{W:.0f}" stroke="{rgba("#FFFFFF", .04)}" stroke-width="2"/>' for y in [H * i / 22 for i in range(1, 22)])
        layers.append(svg(bricks))
        layers.append(f'<div style="position:absolute;inset:8%;border:{m * .006:.0f}px solid {mix(p["a1"], "#FFFFFF", .2)};border-radius:{m * .04:.0f}px;'
                      f'box-shadow:0 0 {m * .02:.0f}px {mix(p["a1"], "#FFFFFF", .2)}, inset 0 0 {m * .02:.0f}px {mix(p["a1"], "#FFFFFF", .2)};opacity:.85"></div>')
    elif style == "diffuse":
        for c, x, y, r in ((p["a1"], 20, 25, .55), (p["a2"], 80, 30, .5), (mix(p["a1"], "#FFFFFF", .5), 60, 85, .6)):
            layers.append(f'<div style="position:absolute;left:{x}%;top:{y}%;width:{r * m:.0f}px;height:{r * m:.0f}px;transform:translate(-50%,-50%);'
                          f'border-radius:50%;background:{c};opacity:.55;filter:blur({m * .09:.0f}px)"></div>')
    elif style == "ink":
        ridges = ""
        for i, (y0, g, o) in enumerate(((.6, "#9A968E", .45), (.72, "#5E5B55", .5), (.86, "#2B2A28", .6))):
            d = f"M0 {H:.0f} L0 {H * y0:.0f} "
            for j in range(6):
                x1, x2 = W * (j + .5) / 6, W * (j + 1) / 6
                d += f"Q{x1:.0f} {H * (y0 - rng.uniform(.04, .12)):.0f} {x2:.0f} {H * (y0 + rng.uniform(-.02, .03)):.0f} "
            d += f"L{W:.0f} {H:.0f} Z"
            ridges += f'<path d="{d}" fill="{g}" opacity="{o}"/>'
        layers.append(svg(f'<g filter="url(#mt{u})">{ridges}</g>', ";mix-blend-mode:multiply;opacity:.45"))
        layers.append(f'<div style="position:absolute;left:0;right:0;top:35%;height:30%;background:linear-gradient(transparent,{rgba(p["bg"], .9)},transparent)"></div>')
        layers.append(svg(f'<circle cx="{W * .8:.0f}" cy="{H * .16:.0f}" r="{m * .05:.0f}" fill="#C8322A" opacity=".85"/>'))
    # paper or grain on top for the hand-made styles
    if style in ("watercolor", "crayon", "riso", "ink", "papercut", "diffuse"):
        from art import noise_uri
        layers.append(f'<div style="position:absolute;inset:0;pointer-events:none;background-image:url(\'{noise_uri(True, .5)}\');'
                      f'background-size:300px 300px;mix-blend-mode:multiply;opacity:{.28 if style != "diffuse" else .18}"></div>')
    return "".join(layers), p


# how each style rewrites the subject, and what it must keep the model away from
SUBJECT = {
    "watercolor": ("{s}, painted in loose transparent watercolour", "{s}，用水彩画出来，颜色透明、边缘晕开",
                   "photorealism, sharp digital rendering, glossy 3D, hard outlines", "写实照片、数码硬边、3D 光泽、硬描边"),
    "papercut": ("{s}, built entirely from layered cut paper and coloured card stock, visible cut edges and paper thickness, flat paper shapes",
                 "{s}，整个用彩色卡纸一层层剪出来，看得见纸的切口和厚度，都是平面纸片",
                 "photorealism, glossy plastic, transparent glass, real liquid, 3D render", "写实照片、塑料反光、透明玻璃质感、真实液体、3D 渲染"),
    "riso": ("{s}, printed as a two-colour risograph in flat spot inks", "{s}，用两种专色孔版印刷出来，平涂色块",
             "photorealism, smooth gradients, glossy highlights", "写实照片、平滑渐变、高光反光"),
    "clay": ("{s}, sculpted from soft matte plasticine clay, rounded chunky shapes", "{s}，用哑光橡皮泥捏出来，圆鼓鼓的造型",
             "photorealism, transparent glass, real liquid, sharp edges", "写实照片、透明玻璃、真实液体、锋利边缘"),
    "lineart": ("{s}, drawn with one continuous single-weight dark line, one flat block of colour behind", "{s}，用等粗的单线画出来，背后一块平涂色块",
                "shading, photorealism, many colours, textures", "明暗阴影、写实、很多颜色、纹理"),
    "crayon": ("{s}, drawn by hand with wax crayons and oil pastels, childlike and scribbly", "{s}，用蜡笔和油画棒手绘，带点童趣的涂鸦感",
               "photorealism, clean vector, smooth gradients", "写实照片、干净的矢量、平滑渐变"),
    "pop": ("{s}, bold comic pop-art illustration with thick black outlines and Ben-Day dots", "{s}，粗黑描边的波普漫画插画，带网点",
            "photorealism, soft gradients, muted colours", "写实照片、柔和渐变、灰暗的颜色"),
    "neon": ("{s}, drawn only as glowing neon tube outlines", "{s}，只用发光的霓虹灯管线条勾出来",
             "solid fills, daylight, photorealism", "实心填色、白天、写实照片"),
    "diffuse": ("{s}, soft minimal illustration with smooth matte forms floating in diffuse coloured light", "{s}，柔和极简的插画，哑光的形体浮在弥散的彩色光里",
                "harsh shadows, clutter, photorealism", "生硬阴影、杂乱、写实照片"),
    "ink": ("{s}, painted with Chinese ink and light colour washes on rice paper, expressive brushwork", "{s}，用水墨加淡彩画在宣纸上，写意的笔触",
            "photorealism, plastic shine, saturated colours, hard outlines", "写实照片、塑料反光、高饱和颜色、硬描边"),
}


def styled_subject(style, en, zh):
    """(subject_en, subject_zh, avoid_en, avoid_zh) with the subject told in the style's own words."""
    if style not in SUBJECT:
        return en, zh, "", ""
    a, b, c, d = SUBJECT[style]
    return a.format(s=en), b.format(s=zh), c, d


def styled_direction(d, style):
    """A copy of the direction whose picture style is the art style, for prompts and image generation."""
    if not style or style == "flat" or style not in STYLES:
        return d
    s = STYLES[style]
    d = dict(d)
    d["image_style"], d["image_style_zh"], d["_art_style"] = s["prompt_en"], s["prompt_zh"], style
    return d


SCATTER = [(.13, .36, .12, -18), (.84, .14, .1, 22), (.88, .62, .13, -8), (.1, .7, .11, 14), (.2, .9, .08, 30), (.76, .88, .09, -24)]
