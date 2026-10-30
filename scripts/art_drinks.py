"""A drink cup you can describe, plus small ingredient drawings to scatter around it.

art.motif = "drink" with art.drink = {
    "liquid": ["#F7B267", "#F4845F"],   # top and bottom colour of the drink (one colour is fine)
    "layers": 1 | 2,                     # 2 = a layered drink (the bottom colour sits as its own band)
    "top": "foam" | "cheese" | "cream" | "none",
    "bits": "pearls" | "fruit" | "taro" | "ice" | "jelly" | "none",
    "bit_color": "#F7A43A",              # fruit pieces / jelly colour
    "cup": "dome" | "flat" | "hot",
    "label": true                        # a band in the brand accent with a little carrot mark
}
Ingredient names: orange-slice, coconut, mango, jasmine, taro, osmanthus, coffee-bean, ice-cube,
tea-leaf, pearl, carrot-mini, strawberry, lemon-slice, leaf.
"""
import math

from common import mix, rgba


def _svg(vb, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" preserveAspectRatio="xMidYMid meet" '
            f'width="100%" height="100%"><defs>{defs}</defs>{body}</svg>')


def drink_cup(t, uid="dk", o=None):
    o = o or {}
    liq = o.get("liquid") or ["#E2B98A", "#C88D5B"]
    if isinstance(liq, str):
        liq = [liq, mix(liq, "#000000", .12)]
    top_c, bot_c = liq[0], liq[-1]
    cup = o.get("cup", "dome")
    top = o.get("top", "none")
    bits = o.get("bits", "none")
    bit_c = o.get("bit_color", "#F4A340")
    # cup: 200 x 250, straight-ish tumbler
    L0, R0, L1, R1, ytop, ybot = 50, 150, 62, 138, 78, 232
    xl = lambda y: L0 + (L1 - L0) * (y - ytop) / (ybot - ytop)
    xr = lambda y: R0 + (R1 - R0) * (y - ytop) / (ybot - ytop)
    liquid_top = 98 if top == "none" else 112
    defs = (f'<linearGradient id="{uid}l" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top_c}"/>'
            f'<stop offset="1" stop-color="{bot_c}"/></linearGradient>'
            f'<clipPath id="{uid}c"><path d="M{xl(liquid_top):.1f} {liquid_top} L{xr(liquid_top):.1f} {liquid_top} L{R1} {ybot - 8} '
            f'Q{R1 - 1} {ybot} {R1 - 10} {ybot} L{L1 + 10} {ybot} Q{L1 + 1} {ybot} {L1} {ybot - 8} Z"/></clipPath>')
    parts = [f'<ellipse cx="100" cy="{ybot + 8}" rx="58" ry="7" fill="{rgba(t["ink"], .14)}"/>']
    # straw first so it sits behind the lid line
    if cup != "hot":
        parts.append(f'<rect x="112" y="6" width="13" height="{ytop + 40}" rx="6.5" fill="{t["accent2"]}" transform="rotate(10 118 60)"/>')
    # glass
    parts.append(f'<path d="M{L0} {ytop} L{R0} {ytop} L{R1} {ybot - 8} Q{R1 - 1} {ybot} {R1 - 10} {ybot} L{L1 + 10} {ybot} Q{L1 + 1} {ybot} {L1} {ybot - 8} Z" '
                 f'fill="{rgba("#FFFFFF", .5)}" stroke="{rgba(t["ink"], .18)}" stroke-width="1.5"/>')
    inner = [f'<rect x="0" y="{liquid_top}" width="200" height="{ybot - liquid_top}" fill="url(#{uid}l)"/>']
    if o.get("layers") == 2:
        mid = (liquid_top + ybot) / 2 + 12
        inner.append(f'<path d="M0 {mid} Q50 {mid - 8} 100 {mid} T200 {mid} L200 260 L0 260 Z" fill="{bot_c}"/>')
    if bits == "pearls":
        for row, (y, xs) in enumerate([(220, [78, 94, 110, 126]), (206, [70, 86, 102, 118, 134]), (193, [82, 100, 118])]):
            for i, x in enumerate(xs):
                jx = (i * 7 + row * 3) % 5 - 2
                inner.append(f'<circle cx="{x + jx}" cy="{y}" r="8" fill="#3B2416"/><circle cx="{x + jx - 3}" cy="{y - 3}" r="2.2" fill="#FFFFFF" opacity=".35"/>')
    elif bits == "taro":
        for i, (x, y) in enumerate([(80, 214), (100, 220), (120, 212), (90, 198), (112, 196), (130, 222)]):
            inner.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{"#B9A2D6" if i % 2 else "#F2E2C4"}"/>')
    elif bits == "fruit":
        for i, (x, y, r) in enumerate([(78, 200, 14), (104, 214, -10), (124, 196, 24), (92, 178, 6), (120, 170, -18), (76, 160, 30)]):
            inner.append(f'<rect x="{x - 8}" y="{y - 7}" width="16" height="14" rx="3" fill="{bit_c if i % 3 else mix(bit_c, "#FFFFFF", .25)}" transform="rotate({r} {x} {y})"/>')
    elif bits == "jelly":
        for i, (x, y) in enumerate([(80, 206), (104, 214), (126, 204), (92, 186), (116, 184)]):
            inner.append(f'<rect x="{x - 9}" y="{y - 9}" width="18" height="18" rx="4" fill="{rgba(bit_c, .75)}"/>')
    if bits == "ice" or cup == "flat" and bits == "none":
        for x, y, r in [(70, liquid_top + 16, 12), (102, liquid_top + 8, -8), (88, liquid_top + 40, 20), (118, liquid_top + 32, 6)]:
            inner.append(f'<rect x="{x}" y="{y}" width="24" height="22" rx="4" fill="#FFFFFF" opacity=".4" transform="rotate({r} {x + 12} {y + 11})"/>')
    parts.append(f'<g clip-path="url(#{uid}c)">{"".join(inner)}</g>')
    # topping band
    if top in ("foam", "cheese", "cream"):
        c = {"foam": "#FFF4E2", "cheese": "#FFE7A3", "cream": "#FFFFFF"}[top]
        y0 = liquid_top - 16
        wave = " ".join(f"Q{xl(y0) + (i + .5) * (xr(y0) - xl(y0)) / 6:.1f} {y0 - 7} {xl(y0) + (i + 1) * (xr(y0) - xl(y0)) / 6:.1f} {y0}" for i in range(6))
        parts.append(f'<path d="M{xl(y0):.1f} {y0} {wave} L{xr(liquid_top + 2):.1f} {liquid_top + 2} L{xl(liquid_top + 2):.1f} {liquid_top + 2} Z" fill="{c}"/>')
        if top == "cheese":
            parts.append(f'<path d="M{xl(liquid_top + 2):.1f} {liquid_top + 2} L{xr(liquid_top + 2):.1f} {liquid_top + 2}" stroke="{mix(c, "#C98A2E", .35)}" stroke-width="2" opacity=".6"/>')
    # label band
    if o.get("label", True):
        y1, y2 = 150, 186
        parts.append(f'<path d="M{xl(y1):.1f} {y1} L{xr(y1):.1f} {y1} L{xr(y2):.1f} {y2} L{xl(y2):.1f} {y2} Z" fill="{t["accent"]}"/>')
        cx, cy = 100, (y1 + y2) / 2
        parts.append(f'<path d="M{cx - 7} {cy - 7} Q{cx} {cy - 11} {cx + 7} {cy - 7} L{cx + 1.5} {cy + 11} Q{cx} {cy + 14} {cx - 1.5} {cy + 11} Z" fill="{t["on_accent"]}"/>'
                     f'<path d="M{cx} {cy - 9} Q{cx - 4} {cy - 17} {cx - 9} {cy - 18} M{cx} {cy - 9} Q{cx + 3} {cy - 18} {cx + 8} {cy - 19}" stroke="{t["on_accent"]}" stroke-width="2.4" fill="none" stroke-linecap="round"/>')
    # shine
    parts.append(f'<path d="M{L0 + 8} {ytop + 6} L{L0 + 16} {ytop + 6} L{L1 + 12} {ybot - 10} L{L1 + 6} {ybot - 10} Z" fill="#FFFFFF" opacity=".35"/>')
    # lid
    if cup == "dome":
        parts.append(f'<path d="M44 {ytop} Q100 {ytop - 54} 156 {ytop} Z" fill="{rgba("#FFFFFF", .55)}" stroke="{rgba(t["ink"], .3)}" stroke-width="2"/>'
                     f'<path d="M70 {ytop - 26} Q84 {ytop - 40} 100 {ytop - 42}" stroke="#FFFFFF" stroke-width="4" fill="none" stroke-linecap="round" opacity=".9"/>')
    elif cup == "hot":
        parts.append(f'<path d="M44 {ytop} L156 {ytop} L150 {ytop - 16} L50 {ytop - 16} Z" fill="{mix(t["accent2"], "#FFFFFF", .2)}"/>'
                     f'<rect x="58" y="{ytop - 24}" width="84" height="10" rx="5" fill="{t["accent2"]}"/>')
        for i, x in enumerate((84, 100, 116)):
            parts.append(f'<path d="M{x} {ytop - 34} q-8 -12 0 -24 q8 -12 0 -24" stroke="{rgba(t["ink"], .25)}" stroke-width="4" fill="none" stroke-linecap="round"/>')
    parts.append(f'<rect x="40" y="{ytop - 6}" width="120" height="11" rx="5.5" fill="{t["accent2"]}"/>')
    return _svg("0 -30 200 280", "".join(parts), defs)


# ------------------------------------------------------------------ ingredients (100 x 100)
def _orange(t, uid, flesh="#FFA53B", rind="#F0801A", pith="#FFE2B3"):
    segs = "".join(
        f'<path d="M50 50 L{50 + 34 * math.cos(math.radians(a)):.1f} {50 + 34 * math.sin(math.radians(a)):.1f} '
        f'A34 34 0 0 1 {50 + 34 * math.cos(math.radians(a + 40)):.1f} {50 + 34 * math.sin(math.radians(a + 40)):.1f} Z" fill="{flesh}" '
        f'stroke="{pith}" stroke-width="3"/>' for a in range(0, 360, 45))
    return _svg("0 0 100 100", f'<circle cx="50" cy="50" r="44" fill="{rind}"/><circle cx="50" cy="50" r="38" fill="{pith}"/>{segs}'
                f'<circle cx="50" cy="50" r="4" fill="{pith}"/>')


def orange_slice(t, uid="os"):
    return _orange(t, uid)


def lemon_slice(t, uid="ls"):
    return _orange(t, uid, "#FFE36B", "#F5C518", "#FFF7CC")


def coconut(t, uid="cn"):
    return _svg("0 0 100 100", '<circle cx="50" cy="52" r="42" fill="#7A4A2A"/><path d="M14 52 A36 36 0 0 0 86 52 Z" fill="#7A4A2A"/>'
                '<ellipse cx="50" cy="48" rx="36" ry="30" fill="#FFFDF7"/><ellipse cx="50" cy="48" rx="36" ry="30" fill="none" stroke="#5E3720" stroke-width="5"/>'
                '<path d="M26 40 Q40 28 58 30" stroke="#FFFFFF" stroke-width="4" fill="none" opacity=".8" stroke-linecap="round"/>')


def mango(t, uid="mg"):
    return _svg("0 0 100 100", f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFD24A"/>'
                f'<stop offset="1" stop-color="#FF9F1C"/></linearGradient></defs>'
                f'<path d="M30 20 Q78 6 86 52 Q90 88 52 90 Q14 92 14 58 Q14 30 30 20 Z" fill="url(#{uid})"/>'
                '<path d="M30 20 Q24 10 34 6" stroke="#5B8F3A" stroke-width="4" fill="none" stroke-linecap="round"/>'
                '<path d="M34 8 Q50 2 56 12 Q44 16 34 8 Z" fill="#6DBB4F"/>'
                '<path d="M28 36 Q30 28 38 26" stroke="#FFFFFF" stroke-width="5" fill="none" opacity=".5" stroke-linecap="round"/>')


def jasmine(t, uid="js"):
    petals = "".join(f'<ellipse cx="50" cy="28" rx="10" ry="22" fill="#FFFFFF" stroke="#E7E1D3" stroke-width="1.5" transform="rotate({a} 50 50)"/>'
                     for a in range(0, 360, 72))
    return _svg("0 0 100 100", petals + '<circle cx="50" cy="50" r="8" fill="#F6D86B"/>')


def osmanthus(t, uid="om"):
    out = ""
    for cx, cy, s in ((34, 40, 1), (64, 34, .8), (58, 66, .9), (30, 70, .7)):
        out += "".join(f'<circle cx="{cx + 7 * s * math.cos(math.radians(a)):.1f}" cy="{cy + 7 * s * math.sin(math.radians(a)):.1f}" r="{6 * s:.1f}" fill="#F7B32B"/>'
                       for a in range(45, 405, 90)) + f'<circle cx="{cx}" cy="{cy}" r="{3 * s:.1f}" fill="#E07B12"/>'
    return _svg("0 0 100 100", out)


def taro(t, uid="tr"):
    return _svg("0 0 100 100", '<path d="M50 12 Q84 20 86 56 Q86 90 50 90 Q14 90 14 56 Q16 20 50 12 Z" fill="#8E6E8E"/>'
                '<path d="M24 46 Q50 40 78 46 M20 62 Q50 56 82 62 M26 78 Q50 72 74 78" stroke="#6B4E6B" stroke-width="3" fill="none"/>'
                '<path d="M50 12 Q46 2 52 0" stroke="#6DAE4E" stroke-width="4" fill="none" stroke-linecap="round"/>')


def coffee_bean(t, uid="cb"):
    return _svg("0 0 100 100", '<ellipse cx="50" cy="50" rx="30" ry="40" fill="#6B3E26" transform="rotate(25 50 50)"/>'
                '<path d="M40 16 Q60 50 44 84" stroke="#3E2214" stroke-width="5" fill="none" transform="rotate(25 50 50)" stroke-linecap="round"/>'
                '<ellipse cx="38" cy="36" rx="6" ry="12" fill="#FFFFFF" opacity=".25" transform="rotate(25 50 50)"/>')


def ice_cube(t, uid="ic"):
    return _svg("0 0 100 100", '<rect x="16" y="16" width="68" height="68" rx="12" fill="#DDF3FF" stroke="#A9D8F0" stroke-width="3" transform="rotate(12 50 50)"/>'
                '<path d="M30 34 L46 30" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round" transform="rotate(12 50 50)"/>')


def tea_leaf(t, uid="tl"):
    return _svg("0 0 100 100", '<path d="M14 86 Q10 30 70 12 Q92 8 88 30 Q76 86 14 86 Z" fill="#5FA34A"/>'
                '<path d="M14 86 Q46 54 78 22" stroke="#3F7D33" stroke-width="3.5" fill="none" stroke-linecap="round"/>')


def leaf(t, uid="lf"):
    return tea_leaf(t, uid)


def pearl(t, uid="pl"):
    return _svg("0 0 100 100", '<circle cx="50" cy="50" r="34" fill="#3B2416"/><circle cx="38" cy="38" r="9" fill="#FFFFFF" opacity=".35"/>')


def strawberry(t, uid="sb"):
    seeds = "".join(f'<ellipse cx="{x}" cy="{y}" rx="2" ry="3" fill="#FFE9A8"/>' for x, y in
                    ((38, 42), (52, 40), (64, 46), (44, 56), (58, 58), (50, 72), (36, 64), (66, 62)))
    return _svg("0 0 100 100", '<path d="M50 92 Q16 70 18 40 Q22 24 50 28 Q78 24 82 40 Q84 70 50 92 Z" fill="#E8344A"/>' + seeds
                + '<path d="M50 30 L36 18 L48 22 L50 8 L54 22 L66 16 L58 30 Z" fill="#4E9A3E"/>')


def carrot_mini(t, uid="cm"):
    return _svg("0 0 100 100", '<path d="M50 30 Q44 16 36 12 Q44 24 46 32 Z" fill="#4E9A3E"/><path d="M50 30 Q52 14 60 8 Q58 22 54 32 Z" fill="#6DBB4F"/>'
                '<path d="M34 34 Q50 26 66 34 Q70 40 66 48 L53 88 Q50 94 47 88 L34 48 Q30 40 34 34 Z" fill="#F57C22"/>'
                '<path d="M40 46 L47 47 M58 58 L52 59" stroke="#D45A12" stroke-width="2.5" stroke-linecap="round"/>')


INGREDIENTS = {"orange-slice": orange_slice, "lemon-slice": lemon_slice, "coconut": coconut, "mango": mango, "jasmine": jasmine,
               "osmanthus": osmanthus, "taro": taro, "coffee-bean": coffee_bean, "ice-cube": ice_cube, "tea-leaf": tea_leaf,
               "leaf": leaf, "pearl": pearl, "strawberry": strawberry, "carrot-mini": carrot_mini}
