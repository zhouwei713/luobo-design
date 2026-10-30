"""Procedural art: product motifs, sparkles, patterns and textures as SVG / CSS.

Used when no image model is configured, and as decoration around AI images.
Food colours are fixed natural tones (appetite first); packaging parts take brand tokens.
"""
import base64
import math

from common import mix, rgba

# natural food tones
TEA = ("#E2B98A", "#C88D5B")
COFFEE = ("#8A5A3B", "#5B3A25")
CREMA = "#D9A877"
PEARL = "#3B2416"
CRUST = ("#E0A15A", "#B86E2E")
CREAM = "#FFF6E6"
BROTH = ("#F2C46D", "#E3A548")
GREEN = "#6FAE4E"


def _svg(vb, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" preserveAspectRatio="xMidYMid meet" '
            f'width="100%" height="100%"><defs>{defs}</defs>{body}</svg>')


def _grad(gid, c1, c2, vertical=True):
    x2, y2 = ("0", "1") if vertical else ("1", "0")
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>')


def milk_tea(t, uid="mt"):
    pearls = []
    rows = [(212, [80, 96, 112, 128]), (198, [72, 88, 104, 120, 136]), (185, [84, 102, 120])]
    for y, xs in rows:
        for i, x in enumerate(xs):
            jx = (i * 7) % 5 - 2
            pearls.append(f'<circle cx="{x + jx}" cy="{y}" r="8.5" fill="{PEARL}"/>'
                          f'<circle cx="{x + jx - 3}" cy="{y - 3}" r="2.4" fill="#FFFFFF" opacity=".35"/>')
    body = f"""
    <ellipse cx="100" cy="232" rx="58" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="108" y="4" width="14" height="120" rx="7" fill="{t['accent2']}" transform="rotate(10 115 64)"/>
    <path d="M48 74 L152 74 L140 222 Q139 230 130 230 L70 230 Q61 230 60 222 Z" fill="url(#{uid}l)"/>
    <path d="M51 92 L149 92 L148 104 L52 104 Z" fill="{rgba('#FFFFFF', .28)}"/>
    {''.join(pearls)}
    <path d="M60 118 L140 118 L137 160 L63 160 Z" fill="{t['accent']}"/>
    <circle cx="100" cy="139" r="11" fill="{t['on_accent']}" opacity=".9"/>
    <path d="M95 139 q5 -9 10 0 q-5 9 -10 0" fill="{t['accent']}"/>
    <path d="M58 80 L66 80 L74 222 L68 222 Z" fill="#FFFFFF" opacity=".35"/>
    <path d="M44 74 Q100 22 156 74 Z" fill="{rgba('#FFFFFF', .55)}" stroke="{rgba(t['ink'], .35)}" stroke-width="2"/>
    <rect x="40" y="68" width="120" height="11" rx="5.5" fill="{t['accent2']}"/>
    <path d="M70 50 Q84 38 100 36" stroke="#FFFFFF" stroke-width="4" fill="none" stroke-linecap="round" opacity=".9"/>
    """
    return _svg("0 0 200 240", body, _grad(f"{uid}l", TEA[0], TEA[1]))


def iced_coffee(t, uid="ic"):
    cubes = "".join(f'<rect x="{x}" y="{y}" width="24" height="22" rx="4" fill="#FFFFFF" opacity=".35" '
                    f'transform="rotate({r} {x + 12} {y + 11})"/>' for x, y, r in
                    [(70, 100, 12), (102, 92, -8), (86, 124, 20)])
    body = f"""
    <ellipse cx="100" cy="232" rx="56" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="104" y="6" width="12" height="118" rx="6" fill="{t['ink']}" transform="rotate(8 110 64)"/>
    <path d="M50 70 L150 70 L139 222 Q138 230 129 230 L71 230 Q62 230 61 222 Z" fill="{rgba('#FFFFFF', .55)}"
          stroke="{rgba(t['ink'], .15)}" stroke-width="1.5"/>
    <path d="M55 96 L145 96 L139 222 Q138 228 129 228 L71 228 Q62 228 61 222 Z" fill="url(#{uid}c)"/>
    <path d="M55 96 L145 96 L144 112 Q100 120 56 112 Z" fill="{CREAM}" opacity=".9"/>
    {cubes}
    <path d="M62 150 L138 150 L135 190 L65 190 Z" fill="{t['accent']}"/>
    <rect x="86" y="164" width="28" height="12" rx="6" fill="{t['on_accent']}" opacity=".85"/>
    <path d="M60 76 L68 76 L76 222 L70 222 Z" fill="#FFFFFF" opacity=".4"/>
    """
    return _svg("0 0 200 240", body, _grad(f"{uid}c", "#A5714C", COFFEE[1]))


def hot_coffee(t, uid="hc"):
    steam = "".join(f'<path d="M{x} 58 q-10 -14 0 -26 q10 -12 0 -26" stroke="{rgba(t["ink"], .28)}" stroke-width="5" '
                    f'fill="none" stroke-linecap="round"/>' for x in (82, 100, 118))
    body = f"""
    {steam}
    <ellipse cx="100" cy="232" rx="56" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M56 84 L144 84 L134 222 Q133 230 124 230 L76 230 Q67 230 66 222 Z" fill="{t['surface']}"
          stroke="{rgba(t['ink'], .12)}" stroke-width="1.5"/>
    <path d="M60 132 L140 132 L136 182 L64 182 Z" fill="{t['accent']}"/>
    <path d="M90 146 q10 -12 20 0 q-10 14 -20 0" fill="{t['on_accent']}" opacity=".9"/>
    <rect x="50" y="70" width="100" height="18" rx="6" fill="{t['ink']}"/>
    <path d="M60 70 L64 60 L136 60 L140 70 Z" fill="{mix(t['ink'], '#FFFFFF', .2)}"/>
    <path d="M64 92 L72 92 L78 222 L72 222 Z" fill="#FFFFFF" opacity=".5"/>
    """
    return _svg("0 0 200 240", body)


def latte(t, uid="la"):
    body = f"""
    <circle cx="100" cy="100" r="96" fill="{rgba(t['ink'], .08)}"/>
    <circle cx="100" cy="100" r="88" fill="{t['surface']}" stroke="{rgba(t['ink'], .1)}" stroke-width="2"/>
    <circle cx="100" cy="100" r="64" fill="{mix(t['surface'], t['ink'], .06)}"/>
    <circle cx="100" cy="100" r="56" fill="url(#{uid}g)"/>
    <path d="M100 136 C70 112 66 84 86 78 C95 75 100 84 100 90 C100 84 105 75 114 78 C134 84 130 112 100 136 Z"
          fill="{CREAM}"/>
    <path d="M100 126 C82 110 80 92 92 88" stroke="{CREMA}" stroke-width="3" fill="none" opacity=".7"/>
    <rect x="158" y="92" width="34" height="16" rx="8" fill="{t['surface']}" stroke="{rgba(t['ink'], .1)}" stroke-width="2"/>
    """
    defs = (f'<radialGradient id="{uid}g"><stop offset="0" stop-color="{CREMA}"/>'
            f'<stop offset="1" stop-color="{COFFEE[0]}"/></radialGradient>')
    return _svg("0 0 200 200", body, defs)


def bread(t, uid="br"):
    cuts = "".join(f'<path d="M{x} 92 q14 -10 26 4" stroke="{CREAM}" stroke-width="7" fill="none" '
                   f'stroke-linecap="round" opacity=".75"/>' for x in (52, 86, 120))
    body = f"""
    <ellipse cx="100" cy="164" rx="86" ry="10" fill="{rgba(t['ink'], .14)}"/>
    <path d="M18 150 Q14 80 70 70 Q100 62 130 70 Q186 80 182 150 Q182 160 170 160 L30 160 Q18 160 18 150 Z"
          fill="url(#{uid}g)"/>
    {cuts}
    <path d="M36 104 Q44 84 64 78" stroke="#FFFFFF" stroke-width="5" fill="none" opacity=".35" stroke-linecap="round"/>
    """
    return _svg("0 0 200 180", body, _grad(f"{uid}g", CRUST[0], CRUST[1]))


def noodle_bowl(t, uid="nb"):
    noodles = "".join(f'<path d="M{48 + i * 12} 92 q6 10 0 20 q-6 10 0 20" stroke="#F7E3B5" stroke-width="5" '
                      f'fill="none" stroke-linecap="round"/>' for i in range(9))
    steam = "".join(f'<path d="M{x} 50 q-8 -12 0 -22 q8 -10 0 -22" stroke="{rgba(t["ink"], .25)}" stroke-width="4.5" '
                    f'fill="none" stroke-linecap="round"/>' for x in (78, 100, 122))
    body = f"""
    {steam}
    <rect x="128" y="20" width="7" height="110" rx="3" fill="{t['ink']}" transform="rotate(24 131 75)"/>
    <rect x="142" y="20" width="7" height="110" rx="3" fill="{t['ink']}" transform="rotate(30 145 75)"/>
    <ellipse cx="100" cy="88" rx="80" ry="20" fill="url(#{uid}b)"/>
    {noodles}
    <circle cx="70" cy="86" r="13" fill="#FFFFFF"/><circle cx="70" cy="86" r="6.5" fill="#F4A62A"/>
    <circle cx="112" cy="80" r="3.5" fill="{GREEN}"/><circle cx="124" cy="90" r="3" fill="{GREEN}"/>
    <circle cx="96" cy="94" r="3" fill="{GREEN}"/><circle cx="138" cy="84" r="3.5" fill="{GREEN}"/>
    <path d="M18 88 Q22 170 100 172 Q178 170 182 88 Z" fill="{t['accent']}"/>
    <path d="M30 112 Q100 128 170 112" stroke="{t['on_accent']}" stroke-width="4" fill="none" opacity=".5"/>
    <ellipse cx="100" cy="176" rx="44" ry="7" fill="{mix(t['accent'], '#000000', .25)}"/>
    """
    return _svg("0 0 200 190", body, _grad(f"{uid}b", BROTH[0], BROTH[1]))


def gift(t, uid="gf"):
    body = f"""
    <ellipse cx="100" cy="186" rx="70" ry="8" fill="{rgba(t['ink'], .14)}"/>
    <rect x="34" y="82" width="132" height="100" rx="8" fill="{t['accent']}"/>
    <rect x="26" y="62" width="148" height="30" rx="8" fill="{mix(t['accent'], '#FFFFFF', .12)}"/>
    <rect x="90" y="62" width="20" height="120" fill="{t['accent2']}"/>
    <path d="M100 62 C70 30 50 50 66 62 Z M100 62 C130 30 150 50 134 62 Z" fill="{t['accent2']}"/>
    """
    return _svg("0 0 200 200", body)


def gaiwan(t, uid="gw"):
    """Lidded tea bowl on a saucer, for tea houses and new-Chinese tea brands."""
    steam = "".join(f'<path d="M{x} 46 q-8 -12 0 -22 q8 -10 0 -22" stroke="{rgba(t["ink"], .22)}" stroke-width="4" '
                    f'fill="none" stroke-linecap="round"/>' for x in (86, 112))
    body = f"""
    {steam}
    <ellipse cx="100" cy="176" rx="84" ry="14" fill="{rgba(t['ink'], .12)}"/>
    <ellipse cx="100" cy="166" rx="80" ry="15" fill="{t['surface']}" stroke="{rgba(t['ink'], .2)}" stroke-width="2"/>
    <path d="M42 98 Q46 156 100 160 Q154 156 158 98 Z" fill="{t['surface']}" stroke="{rgba(t['ink'], .2)}" stroke-width="2"/>
    <path d="M50 120 Q100 134 150 120" stroke="{t['accent']}" stroke-width="5" fill="none"/>
    <path d="M58 132 Q100 144 142 132" stroke="{t['accent2']}" stroke-width="2.5" fill="none" opacity=".7"/>
    <path d="M36 98 Q100 60 164 98 Z" fill="{t['surface']}" stroke="{rgba(t['ink'], .22)}" stroke-width="2"/>
    <ellipse cx="100" cy="98" rx="64" ry="7" fill="{mix(t['surface'], t['ink'], .08)}"/>
    <ellipse cx="100" cy="66" rx="12" ry="6" fill="{t['accent']}"/>
    <path d="M60 86 Q80 76 100 74" stroke="#FFFFFF" stroke-width="4" fill="none" opacity=".7" stroke-linecap="round"/>
    """
    return _svg("0 0 200 190", body)



GOLD = ("#F4CF5A", "#D29E1E")
SILVER = ("#E4E8EE", "#AEB6C2")


def dumbbell(t, uid="db"):
    plates = ""
    for x, w, h in ((14, 18, 96), (34, 16, 76), (150, 16, 76), (168, 18, 96)):
        plates += f'<rect x="{x}" y="{70 - h / 2}" width="{w}" height="{h}" rx="5" fill="{t["ink"]}"/>'
    body = f"""
    <ellipse cx="100" cy="128" rx="84" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="8" y="62" width="184" height="16" rx="8" fill="url(#{uid}s)"/>
    {plates}
    <rect x="70" y="58" width="60" height="24" rx="10" fill="{t['accent']}"/>
    <path d="M78 64 L122 64" stroke="{t['on_accent']}" stroke-width="3" opacity=".5" stroke-linecap="round"/>
    """
    return _svg("0 0 200 140", body, _grad(f"{uid}s", SILVER[0], SILVER[1]))


def nail_polish(t, uid="np"):
    body = f"""
    <ellipse cx="100" cy="230" rx="52" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="80" y="20" width="40" height="78" rx="8" fill="{t['ink']}"/>
    <rect x="86" y="26" width="6" height="64" rx="3" fill="#FFFFFF" opacity=".25"/>
    <rect x="72" y="94" width="56" height="14" rx="4" fill="{mix(t['ink'], '#FFFFFF', .2)}"/>
    <path d="M52 132 Q52 106 78 106 L122 106 Q148 106 148 132 L148 206 Q148 226 128 226 L72 226 Q52 226 52 206 Z" fill="url(#{uid}g)"/>
    <path d="M62 128 Q62 116 74 116 L80 116 L80 212 L70 212 Q62 212 62 204 Z" fill="#FFFFFF" opacity=".35"/>
    <circle cx="164" cy="190" r="9" fill="{t['accent']}"/><path d="M164 170 Q172 182 164 190 Q156 182 164 170" fill="{t['accent']}"/>
    """
    return _svg("0 0 200 240", body, _grad(f"{uid}g", mix(t['accent'], '#FFFFFF', .15), mix(t['accent'], '#000000', .15)))


def scissors_comb(t, uid="sc"):
    teeth = "".join(f'<rect x="{126 + i * 7}" y="96" width="4" height="40" rx="2" fill="{t["accent2"]}"/>' for i in range(9))
    body = f"""
    <ellipse cx="100" cy="188" rx="82" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="120" y="70" width="70" height="30" rx="8" fill="{t['accent2']}"/>{teeth}
    <path d="M40 30 L104 120" stroke="url(#{uid}s)" stroke-width="12" stroke-linecap="round"/>
    <path d="M104 30 L40 120" stroke="url(#{uid}s)" stroke-width="12" stroke-linecap="round"/>
    <circle cx="72" cy="75" r="5" fill="{t['ink']}"/>
    <circle cx="30" cy="146" r="22" fill="none" stroke="{t['accent']}" stroke-width="12"/>
    <circle cx="112" cy="146" r="22" fill="none" stroke="{t['accent']}" stroke-width="12"/>
    <path d="M40 120 L34 126 M104 120 L108 126" stroke="{t['accent']}" stroke-width="12" stroke-linecap="round"/>
    """
    return _svg("0 0 200 200", body, _grad(f"{uid}s", SILVER[0], SILVER[1], vertical=False))


def lotus(t, uid="lo"):
    petal = lambda r, c, o: (f'<path d="M100 120 C82 96 84 64 100 40 C116 64 118 96 100 120 Z" fill="{c}" opacity="{o}" '
                             f'transform="rotate({r} 100 120)"/>')
    body = (f'<ellipse cx="100" cy="136" rx="76" ry="8" fill="{rgba(t["ink"], .12)}"/>'
            + petal(-62, t["accent2"], .8) + petal(62, t["accent2"], .8) + petal(-32, t["accent"], .75)
            + petal(32, t["accent"], .75) + petal(0, t["accent"], 1)
            + f'<path d="M40 124 Q100 140 160 124" stroke="{t["accent2"]}" stroke-width="5" fill="none" stroke-linecap="round"/>')
    return _svg("0 0 200 150", body)


def open_book(t, uid="ob"):
    lines = "".join(f'<path d="M{x0} {y} L{x1} {y}" stroke="{rgba(t["ink"], .18)}" stroke-width="3" stroke-linecap="round"/>'
                    for y in (62, 78, 94, 110) for x0, x1 in ((34, 86), (114, 166)))
    body = f"""
    <ellipse cx="100" cy="160" rx="88" ry="8" fill="{rgba(t['ink'], .14)}"/>
    <path d="M14 46 Q58 30 100 46 L100 150 Q58 134 14 150 Z" fill="{t['accent']}"/>
    <path d="M186 46 Q142 30 100 46 L100 150 Q142 134 186 150 Z" fill="{mix(t['accent'], '#000000', .15)}"/>
    <path d="M22 40 Q60 26 98 42 L98 140 Q60 126 22 140 Z" fill="{t['surface']}"/>
    <path d="M178 40 Q140 26 102 42 L102 140 Q140 126 178 140 Z" fill="{mix(t['surface'], t['ink'], .05)}"/>
    {lines}
    <path d="M140 30 L140 70 L148 62 L156 70 L156 30 Z" fill="{t['accent2']}"/>
    """
    return _svg("0 0 200 170", body)


def grad_cap(t, uid="gc"):
    body = f"""
    <ellipse cx="100" cy="164" rx="70" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M52 86 L52 130 Q100 158 148 130 L148 86 Z" fill="{mix(t['ink'], '#FFFFFF', .12)}"/>
    <path d="M100 30 L190 70 L100 110 L10 70 Z" fill="{t['ink']}"/>
    <path d="M100 38 L172 70 L100 102 L28 70 Z" fill="{mix(t['ink'], '#FFFFFF', .08)}"/>
    <circle cx="100" cy="70" r="6" fill="{t['accent2']}"/>
    <path d="M100 70 L160 92 L160 128" stroke="{t['accent2']}" stroke-width="4" fill="none"/>
    <path d="M152 126 L168 126 L172 150 L148 150 Z" fill="{t['accent2']}"/>
    """
    return _svg("0 0 200 175", body)


def microphone(t, uid="mc"):
    grille = "".join(f'<path d="M74 {y} L126 {y}" stroke="{rgba("#FFFFFF", .3)}" stroke-width="3"/>' for y in range(46, 118, 12))
    body = f"""
    <ellipse cx="100" cy="230" rx="50" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="70" y="20" width="60" height="112" rx="30" fill="{t['ink']}"/>{grille}
    <rect x="70" y="92" width="60" height="16" fill="{t['accent']}"/>
    <path d="M52 100 Q52 156 100 156 Q148 156 148 100" stroke="{mix(t['ink'], '#FFFFFF', .3)}" stroke-width="8" fill="none" stroke-linecap="round"/>
    <rect x="95" y="156" width="10" height="56" fill="{mix(t['ink'], '#FFFFFF', .3)}"/>
    <rect x="62" y="210" width="76" height="14" rx="7" fill="{t['ink']}"/>
    <circle cx="160" cy="44" r="6" fill="{t['accent2']}"/><circle cx="40" cy="70" r="4" fill="{t['accent2']}"/>
    """
    return _svg("0 0 200 240", body)


def camera(t, uid="cm"):
    body = f"""
    <ellipse cx="100" cy="160" rx="86" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M70 36 L84 20 L120 20 L134 36 Z" fill="{mix(t['ink'], '#FFFFFF', .15)}"/>
    <rect x="14" y="34" width="172" height="116" rx="18" fill="{t['ink']}"/>
    <rect x="14" y="60" width="172" height="10" fill="{t['accent']}"/>
    <circle cx="100" cy="94" r="44" fill="{mix(t['ink'], '#FFFFFF', .2)}"/>
    <circle cx="100" cy="94" r="34" fill="{t['ink']}" stroke="{t['accent2']}" stroke-width="5"/>
    <circle cx="100" cy="94" r="18" fill="url(#{uid}l)"/><circle cx="92" cy="86" r="6" fill="#FFFFFF" opacity=".6"/>
    <rect x="150" y="44" width="22" height="10" rx="3" fill="{t['accent2']}"/>
    """
    defs = f'<radialGradient id="{uid}l"><stop offset="0" stop-color="#5A7BA8"/><stop offset="1" stop-color="#1A2433"/></radialGradient>'
    return _svg("0 0 200 170", body, defs)


def trophy(t, uid="tr"):
    body = f"""
    <ellipse cx="100" cy="212" rx="64" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M52 40 Q20 40 22 70 Q26 104 64 110" stroke="url(#{uid}g)" stroke-width="10" fill="none"/>
    <path d="M148 40 Q180 40 178 70 Q174 104 136 110" stroke="url(#{uid}g)" stroke-width="10" fill="none"/>
    <path d="M50 26 L150 26 L146 72 Q140 128 100 132 Q60 128 54 72 Z" fill="url(#{uid}g)"/>
    <path d="M64 34 L74 34 L76 96 Q66 82 64 60 Z" fill="#FFFFFF" opacity=".35"/>
    <path d="M100 52 L107 68 L124 69 L111 80 L115 97 L100 88 L85 97 L89 80 L76 69 L93 68 Z" fill="{GOLD[1]}" opacity=".7"/>
    <rect x="90" y="130" width="20" height="34" fill="{GOLD[1]}"/>
    <rect x="62" y="162" width="76" height="16" rx="4" fill="{GOLD[1]}"/>
    <rect x="52" y="178" width="96" height="28" rx="5" fill="{t['ink']}"/>
    <rect x="76" y="186" width="48" height="12" rx="2" fill="{t['accent2'] if t['accent2'] != t['ink'] else t['accent']}" opacity=".8"/>
    """
    return _svg("0 0 200 220", body, _grad(f"{uid}g", GOLD[0], GOLD[1]))


def medal(t, uid="md"):
    body = f"""
    <path d="M62 10 L94 10 L118 96 L86 96 Z" fill="{t['accent']}"/>
    <path d="M138 10 L106 10 L82 96 L114 96 Z" fill="{mix(t['accent'], '#000000', .18)}"/>
    <circle cx="100" cy="148" r="62" fill="url(#{uid}g)"/>
    <circle cx="100" cy="148" r="48" fill="none" stroke="#FFFFFF" stroke-width="3" opacity=".6"/>
    <path d="M100 116 L109 136 L131 138 L114 152 L119 174 L100 162 L81 174 L86 152 L69 138 L91 136 Z" fill="#FFFFFF" opacity=".85"/>
    """
    return _svg("0 0 200 215", body, _grad(f"{uid}g", GOLD[0], GOLD[1]))


def laurel(t, uid="la", color=None):
    """Open wreath: the right branch is drawn, the left one is its mirror image."""
    c = color or t["accent2"]
    leaves, R, cx0, cy0 = [], 82, 120, 104
    for i in range(9):
        deg = -72 + i * 15
        rad = math.radians(deg)
        x, y = cx0 + R * math.cos(rad), cy0 - R * math.sin(rad)
        rot = 90 - (deg + 90) + 28
        for off in (-1, 1):
            ox, oy = x + off * 9 * math.cos(rad), y - off * 9 * math.sin(rad)
            leaves.append(f'<ellipse cx="{ox:.1f}" cy="{oy:.1f}" rx="5.5" ry="13" fill="{c}" '
                          f'transform="rotate({rot + off * 22:.1f} {ox:.1f} {oy:.1f})" opacity="{.95 - i * .04:.2f}"/>')
    branch = (f'<path d="M{cx0 + 24} {cy0 + 80} A{R} {R} 0 0 0 {cx0 + R * math.cos(math.radians(30)):.1f} {cy0 - R * .5:.1f}" '
              f'stroke="{c}" stroke-width="3" fill="none"/>' + "".join(leaves))
    return _svg("0 0 240 200", f'<g>{branch}</g><g transform="translate(240 0) scale(-1 1)">{branch}</g>')


def briefcase(t, uid="bc"):
    body = f"""
    <ellipse cx="100" cy="170" rx="84" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M74 44 L74 30 Q74 22 82 22 L118 22 Q126 22 126 30 L126 44" stroke="{t['ink']}" stroke-width="8" fill="none"/>
    <rect x="16" y="44" width="168" height="118" rx="14" fill="{t['accent']}"/>
    <rect x="16" y="44" width="168" height="46" rx="14" fill="{mix(t['accent'], '#FFFFFF', .1)}"/>
    <rect x="86" y="80" width="28" height="22" rx="4" fill="url(#{uid}g)"/>
    <path d="M24 92 L176 92" stroke="{mix(t['accent'], '#000000', .25)}" stroke-width="3"/>
    """
    return _svg("0 0 200 180", body, _grad(f"{uid}g", GOLD[0], GOLD[1]))


def scales(t, uid="sl"):
    pan = lambda x: (f'<path d="M{x} 70 L{x - 30} 132 M{x} 70 L{x + 30} 132" stroke="{rgba(t["ink"], .5)}" stroke-width="2.5"/>'
                     f'<path d="M{x - 38} 132 Q{x} 160 {x + 38} 132 Z" fill="url(#{uid}g)"/>')
    body = f"""
    <ellipse cx="100" cy="206" rx="60" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="94" y="40" width="12" height="150" fill="{t['ink']}"/>
    <rect x="60" y="186" width="80" height="14" rx="4" fill="{t['ink']}"/>
    <rect x="24" y="64" width="152" height="8" rx="4" fill="{t['ink']}"/>
    <circle cx="100" cy="36" r="12" fill="url(#{uid}g)"/>
    {pan(44)}{pan(156)}
    """
    return _svg("0 0 200 215", body, _grad(f"{uid}g", GOLD[0], GOLD[1]))


def calendar(t, uid="cl"):
    dots = "".join(f'<rect x="{38 + c * 26}" y="{96 + r * 22}" width="16" height="12" rx="3" '
                   f'fill="{t["accent"] if (r, c) == (1, 3) else rgba(t["ink"], .14)}"/>' for r in range(3) for c in range(5))
    body = f"""
    <ellipse cx="100" cy="186" rx="78" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="22" y="30" width="156" height="150" rx="16" fill="{t['surface']}" stroke="{rgba(t['ink'], .15)}" stroke-width="2"/>
    <path d="M22 46 Q22 30 38 30 L162 30 Q178 30 178 46 L178 80 L22 80 Z" fill="{t['accent']}"/>
    <rect x="56" y="16" width="10" height="30" rx="5" fill="{t['ink']}"/><rect x="134" y="16" width="10" height="30" rx="5" fill="{t['ink']}"/>
    {dots}
    """
    return _svg("0 0 200 195", body)


def envelope(t, uid="ev"):
    body = f"""
    <ellipse cx="100" cy="166" rx="84" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="16" y="40" width="168" height="118" rx="10" fill="{t['surface']}" stroke="{rgba(t['ink'], .15)}" stroke-width="2"/>
    <path d="M16 54 L100 112 L184 54" fill="none" stroke="{rgba(t['ink'], .18)}" stroke-width="3"/>
    <path d="M16 50 Q16 40 26 40 L174 40 Q184 40 184 50 L100 106 Z" fill="{mix(t['surface'], t['ink'], .06)}"/>
    <circle cx="100" cy="104" r="20" fill="{t['accent']}"/>
    <path d="M100 116 C88 106 88 96 95 94 C98 93 100 96 100 98 C100 96 102 93 105 94 C112 96 112 106 100 116 Z" fill="{t['on_accent']}"/>
    """
    return _svg("0 0 200 175", body)



def lantern(t, uid="ln"):
    red = t["accent"] if t["accent"] not in (t["bg"],) else "#D62828"
    if luminance_hex(red) > 0.45:  # gold accent on a red festival palette: the lantern itself is red
        red = "#D62828"
    body = f"""
    <path d="M100 6 L100 30" stroke="{GOLD[1]}" stroke-width="4"/>
    <rect x="76" y="28" width="48" height="14" rx="4" fill="{GOLD[1]}"/>
    <ellipse cx="100" cy="104" rx="70" ry="64" fill="{red}" stroke="{GOLD[0]}" stroke-width="3"/>
    <path d="M100 40 Q60 104 100 168 M100 40 Q140 104 100 168 M100 40 Q78 104 100 168 M100 40 Q122 104 100 168"
          stroke="{mix(red, '#000000', .25)}" stroke-width="2.5" fill="none" opacity=".6"/>
    <ellipse cx="74" cy="80" rx="12" ry="24" fill="#FFFFFF" opacity=".18"/>
    <rect x="76" y="166" width="48" height="14" rx="4" fill="{GOLD[1]}"/>
    <path d="M86 180 L84 220 M93 180 L92 226 M100 180 L100 230 M107 180 L108 226 M114 180 L116 220" stroke="{GOLD[0]}" stroke-width="3"/>
    """
    return _svg("0 0 200 235", body)


def red_envelope(t, uid="re"):
    body = f"""
    <ellipse cx="100" cy="222" rx="60" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="40" y="20" width="120" height="196" rx="12" fill="#E03131" stroke="{GOLD[0]}" stroke-width="3"/>
    <path d="M40 32 Q40 20 52 20 L148 20 Q160 20 160 32 L160 72 Q100 112 40 72 Z" fill="#B71C1C"/>
    <circle cx="100" cy="88" r="24" fill="url(#{uid}g)"/>
    <rect x="92" y="80" width="16" height="16" fill="#B71C1C" transform="rotate(45 100 88)"/>
    <path d="M62 140 L138 140 M62 158 L138 158" stroke="{GOLD[0]}" stroke-width="3" opacity=".7"/>
    """
    return _svg("0 0 200 235", body, _grad(f"{uid}g", GOLD[0], GOLD[1]))


def mooncake(t, uid="mk"):
    petals = "".join(f'<circle cx="{100 + 66 * math.cos(math.radians(a)):.1f}" cy="{100 + 66 * math.sin(math.radians(a)):.1f}" r="22" fill="url(#{uid}g)"/>'
                     for a in range(0, 360, 30))
    body = f"""
    <ellipse cx="100" cy="186" rx="80" ry="8" fill="{rgba(t['ink'], .18)}"/>
    {petals}
    <circle cx="100" cy="100" r="70" fill="url(#{uid}g)"/>
    <circle cx="100" cy="100" r="54" fill="none" stroke="#A8642A" stroke-width="3" opacity=".6"/>
    <path d="M100 66 C118 82 118 118 100 134 C82 118 82 82 100 66 Z M66 100 C82 82 118 82 134 100 C118 118 82 118 66 100 Z"
          fill="none" stroke="#A8642A" stroke-width="3" opacity=".55"/>
    <circle cx="100" cy="100" r="7" fill="#A8642A" opacity=".55"/>
    """
    return _svg("0 0 200 200", body, _grad(f"{uid}g", "#E9B871", "#C98A45"))


def zongzi(t, uid="zz"):
    body = f"""
    <ellipse cx="100" cy="190" rx="70" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M100 24 L176 176 L24 176 Z" fill="url(#{uid}g)" stroke="#2F5D2A" stroke-width="3" stroke-linejoin="round"/>
    <path d="M100 24 L120 176 M100 24 L66 176 M100 24 L150 176" stroke="#2F5D2A" stroke-width="2" opacity=".5"/>
    <path d="M44 132 L156 132" stroke="#C9A36B" stroke-width="7"/>
    <path d="M60 100 L140 100" stroke="#C9A36B" stroke-width="6" opacity=".9"/>
    <path d="M100 24 Q112 10 128 14" stroke="#4E8A3E" stroke-width="5" fill="none" stroke-linecap="round"/>
    """
    return _svg("0 0 200 200", body, _grad(f"{uid}g", "#7CB15A", "#3F7A34"))


def xmas_tree(t, uid="xt"):
    balls = "".join(f'<circle cx="{x}" cy="{y}" r="7" fill="{c}"/>' for x, y, c in
                    [(88, 86, t["accent"]), (116, 112, GOLD[0]), (78, 140, GOLD[0]), (124, 156, t["accent"]), (100, 128, "#FFFFFF")])
    body = f"""
    <ellipse cx="100" cy="226" rx="62" ry="7" fill="{rgba(t['ink'], .18)}"/>
    <rect x="88" y="192" width="24" height="30" fill="#7A4A2A"/>
    <path d="M100 30 L150 108 L126 108 L164 166 L136 166 L176 198 L24 198 L64 166 L36 166 L74 108 L50 108 Z" fill="url(#{uid}g)"/>
    {balls}
    <path d="M100 8 L106 24 L122 24 L109 33 L114 48 L100 39 L86 48 L91 33 L78 24 L94 24 Z" fill="{GOLD[0]}"/>
    """
    return _svg("0 0 200 235", body, _grad(f"{uid}g", "#3E8E5A", "#1F5B3A"))


def heart(t, uid="ht"):
    body = f"""
    <ellipse cx="100" cy="188" rx="64" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M100 176 C40 132 14 96 30 62 C44 32 84 30 100 60 C116 30 156 32 170 62 C186 96 160 132 100 176 Z" fill="url(#{uid}g)"/>
    <path d="M52 66 Q60 50 78 50" stroke="#FFFFFF" stroke-width="7" fill="none" stroke-linecap="round" opacity=".5"/>
    """
    return _svg("0 0 200 200", body, _grad(f"{uid}g", mix(t['accent'], '#FFFFFF', .2), mix(t['accent'], '#000000', .12)))


def bouquet(t, uid="bq"):
    flowers = ""
    for x, y, c in [(74, 64, t["accent"]), (112, 52, t["accent2"]), (136, 84, t["accent"]), (96, 92, mix(t["accent"], "#FFFFFF", .3)), (60, 100, t["accent2"])]:
        petals = "".join(f'<circle cx="{x + 13 * math.cos(math.radians(a)):.1f}" cy="{y + 13 * math.sin(math.radians(a)):.1f}" r="11" fill="{c}"/>'
                         for a in range(0, 360, 60))
        flowers += petals + f'<circle cx="{x}" cy="{y}" r="8" fill="{GOLD[0]}"/>'
    body = f"""
    <ellipse cx="100" cy="226" rx="50" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M100 210 L70 110 M100 210 L100 100 M100 210 L130 110 M100 210 L58 120 M100 210 L142 116" stroke="#4E8A3E" stroke-width="4"/>
    <path d="M64 120 Q48 100 60 90 Q70 110 64 120 Z M140 118 Q158 100 146 88 Q134 108 140 118 Z" fill="#6FAE4E"/>
    {flowers}
    <path d="M62 140 L138 140 L112 214 L88 214 Z" fill="{t['surface']}" stroke="{rgba(t['ink'], .15)}" stroke-width="2"/>
    <path d="M86 168 Q100 158 114 168 Q100 180 86 168 Z" fill="{t['accent']}"/>
    """
    return _svg("0 0 200 235", body)


def shopping_bag(t, uid="sb"):
    body = f"""
    <ellipse cx="100" cy="214" rx="68" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M70 70 Q70 30 100 30 Q130 30 130 70" stroke="{t['ink']}" stroke-width="8" fill="none"/>
    <path d="M36 66 L164 66 L154 208 L46 208 Z" fill="{t['accent']}"/>
    <path d="M36 66 L164 66 L162 90 L38 90 Z" fill="{mix(t['accent'], '#000000', .15)}"/>
    <circle cx="70" cy="78" r="5" fill="{t['ink']}"/><circle cx="130" cy="78" r="5" fill="{t['ink']}"/>
    <path d="M100 120 L108 140 L130 140 L112 152 L118 174 L100 162 L82 174 L88 152 L70 140 L92 140 Z" fill="{t['accent2']}"/>
    """
    return _svg("0 0 200 225", body)


def fireworks(t, uid="fw"):
    out = []
    for cx, cy, r, c in [(70, 70, 50, t["accent"]), (140, 110, 42, t["accent2"]), (86, 150, 30, GOLD[0])]:
        for i in range(12):
            a = math.radians(i * 30)
            out.append(f'<path d="M{cx + r * .35 * math.cos(a):.1f} {cy + r * .35 * math.sin(a):.1f} L{cx + r * math.cos(a):.1f} {cy + r * math.sin(a):.1f}" '
                       f'stroke="{c}" stroke-width="4" stroke-linecap="round"/>')
            out.append(f'<circle cx="{cx + r * 1.12 * math.cos(a):.1f}" cy="{cy + r * 1.12 * math.sin(a):.1f}" r="3" fill="{c}"/>')
    return _svg("0 0 200 200", "".join(out))


def megaphone(t, uid="mg"):
    body = f"""
    <ellipse cx="100" cy="180" rx="76" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M40 80 L120 40 L120 150 L40 112 Z" fill="{t['accent']}"/>
    <rect x="22" y="78" width="26" height="36" rx="6" fill="{t['ink']}"/>
    <path d="M56 112 L64 160 L84 160 L76 120 Z" fill="{t['ink']}"/>
    <ellipse cx="120" cy="95" rx="12" ry="55" fill="{mix(t['accent'], '#000000', .2)}"/>
    <path d="M146 70 Q160 95 146 120 M160 56 Q182 95 160 134" stroke="{t['accent2']}" stroke-width="6" fill="none" stroke-linecap="round"/>
    """
    return _svg("0 0 200 190", body)


def building(t, uid="bd"):
    wins = "".join(f'<rect x="{x}" y="{y}" width="14" height="16" rx="2" fill="{t["accent2"] if (x + y) % 3 == 0 else rgba("#FFFFFF", .75)}"/>'
                   for x in (40, 62, 84) for y in (60, 88, 116, 144))
    wins2 = "".join(f'<rect x="{x}" y="{y}" width="14" height="16" rx="2" fill="{rgba("#FFFFFF", .75)}"/>' for x in (124, 146) for y in (96, 124, 152))
    body = f"""
    <ellipse cx="100" cy="196" rx="86" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <rect x="28" y="40" width="82" height="152" rx="4" fill="{t['accent']}"/>
    <rect x="112" y="80" width="60" height="112" rx="4" fill="{mix(t['accent'], '#FFFFFF', .25)}"/>
    {wins}{wins2}
    <rect x="58" y="168" width="22" height="24" fill="{t['ink']}"/>
    <circle cx="24" cy="172" r="16" fill="#6FAE4E"/><rect x="22" y="176" width="4" height="18" fill="#7A4A2A"/>
    """
    return _svg("0 0 200 205", body)


def rings(t, uid="rg"):
    body = f"""
    <ellipse cx="100" cy="168" rx="76" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <circle cx="78" cy="104" r="44" fill="none" stroke="url(#{uid}g)" stroke-width="12"/>
    <circle cx="124" cy="104" r="44" fill="none" stroke="url(#{uid}s)" stroke-width="12"/>
    <path d="M78 52 L68 38 L78 24 L88 38 Z" fill="#FFFFFF" stroke="{rgba(t['ink'], .25)}" stroke-width="2"/>
    <path d="M150 30 l4 10 10 4 -10 4 -4 10 -4 -10 -10 -4 10 -4 Z" fill="{t['accent']}"/>
    """
    return _svg("0 0 200 180", body, _grad(f"{uid}g", GOLD[0], GOLD[1]) + _grad(f"{uid}s", SILVER[0], SILVER[1]))


def birthday_cake(t, uid="bk"):
    candles = "".join(f'<rect x="{x}" y="30" width="8" height="34" rx="3" fill="{c}"/><path d="M{x + 4} 14 Q{x + 11} 24 {x + 4} 30 Q{x - 3} 24 {x + 4} 14" fill="{GOLD[0]}"/>'
                      for x, c in ((70, t["accent"]), (96, t["accent2"]), (122, t["accent"])))
    body = f"""
    <ellipse cx="100" cy="206" rx="86" ry="8" fill="{rgba(t['ink'], .14)}"/>
    {candles}
    <rect x="44" y="64" width="112" height="56" rx="10" fill="{t['surface']}" stroke="{rgba(t['ink'], .12)}" stroke-width="2"/>
    <path d="M44 84 Q58 98 72 84 Q86 98 100 84 Q114 98 128 84 Q142 98 156 84 L156 74 Q156 64 146 64 L54 64 Q44 64 44 74 Z" fill="{t['accent']}"/>
    <rect x="24" y="118" width="152" height="74" rx="10" fill="{mix(t['surface'], t['accent2'], .25)}" stroke="{rgba(t['ink'], .12)}" stroke-width="2"/>
    <path d="M24 140 Q44 156 64 140 Q84 156 104 140 Q124 156 144 140 Q164 156 176 142" stroke="{t['accent']}" stroke-width="6" fill="none"/>
    <rect x="14" y="190" width="172" height="10" rx="5" fill="{t['ink']}" opacity=".8"/>
    """
    return _svg("0 0 200 215", body)


def peach(t, uid="pc"):
    body = f"""
    <ellipse cx="100" cy="190" rx="66" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M100 182 C50 182 26 140 34 106 C42 72 76 58 100 74 C124 58 158 72 166 106 C174 140 150 182 100 182 Z" fill="url(#{uid}g)"/>
    <path d="M100 76 Q92 128 100 180" stroke="#D9667A" stroke-width="3" fill="none" opacity=".6"/>
    <path d="M100 74 Q70 40 44 50 Q66 76 100 74 Z" fill="#6FAE4E"/>
    <path d="M100 74 Q128 36 156 44 Q136 74 100 74 Z" fill="#4E8A3E"/>
    <ellipse cx="66" cy="120" rx="10" ry="20" fill="#FFFFFF" opacity=".3"/>
    """
    return _svg("0 0 200 200", body, _grad(f"{uid}g", "#FFD1C1", "#F27C8D"))


def double_happiness(t, uid="xi"):
    """囍 as a paper cut: two 喜 side by side sharing their long strokes. Pure geometry, no font needed."""
    c = t["accent"]
    r = lambda x, y, w, h: f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>'
    box = lambda x, y, w, h, k=9: r(x, y, w, k) + r(x, y + h - k, w, k) + r(x, y, k, h) + r(x + w - k, y, k, h)
    parts = [r(26, 18, 148, 9), r(36, 42, 128, 9)]           # 士: top stroke, second stroke (shared)
    for cx in (60, 140):
        parts += [r(cx - 4.5, 18, 9, 33)]                     # 士: the upright
        parts += [box(cx - 28, 60, 56, 30)]                  # first 口
        parts += [f'<polygon points="{cx - 20},98 {cx - 12},98 {cx - 6},112 {cx - 14},112"/>',
                  f'<polygon points="{cx + 12},98 {cx + 20},98 {cx + 14},112 {cx + 6},112"/>']  # 丷
        parts += [box(cx - 28, 134, 56, 46)]                 # second 口
    parts += [r(16, 118, 168, 9)]                             # long stroke across both
    body = f'<g fill="{c}">{"".join(parts)}</g>'
    return _svg("0 0 200 200", body)


def carrot(t, uid="cr"):
    body = f"""
    <ellipse cx="100" cy="190" rx="40" ry="6" fill="{rgba(t['ink'], .14)}"/>
    <path d="M100 62 Q86 34 70 26 Q84 50 92 64 Z" fill="#4E9A3E"/>
    <path d="M100 62 Q100 28 112 14 Q110 44 106 64 Z" fill="#6DBB4F"/>
    <path d="M102 64 Q122 36 140 32 Q124 54 110 68 Z" fill="#4E9A3E"/>
    <path d="M66 70 Q100 54 134 70 Q140 80 133 98 L107 176 Q100 190 93 176 L67 98 Q60 80 66 70 Z" fill="url(#{uid}g)"/>
    <path d="M78 96 L92 98 M118 118 L106 120 M84 134 L96 136 M112 152 L103 153" stroke="#D45A12" stroke-width="4" stroke-linecap="round" opacity=".55"/>
    <path d="M76 82 Q74 100 82 124" stroke="#FFFFFF" stroke-width="6" fill="none" stroke-linecap="round" opacity=".45"/>
    """
    return _svg("0 0 200 200", body, _grad(f"{uid}g", "#FFA24A", "#F06A1A"))


def pet_box(t, uid="pb"):
    """A kitten peeking out of an opened delivery box, paws on the rim: online pet shops, pet supplies."""
    fur, fur2 = "#F4A85C", "#E0873A"
    body = f"""
    <ellipse cx="100" cy="188" rx="70" ry="7" fill="{rgba(t['ink'], .14)}"/>
    <path d="M44 104 L156 104 L160 112 L40 112 Z" fill="#8A5A2B"/>
    <path d="M70 70 L74 38 L94 60 Z" fill="{fur}"/><path d="M76 62 L78 46 L88 58 Z" fill="#F7C6B5"/>
    <path d="M130 70 L126 38 L106 60 Z" fill="{fur}"/><path d="M124 62 L122 46 L112 58 Z" fill="#F7C6B5"/>
    <ellipse cx="100" cy="88" rx="38" ry="33" fill="{fur}"/>
    <path d="M86 58 Q90 66 88 74 M100 55 L100 70 M114 58 Q110 66 112 74" stroke="{fur2}" stroke-width="4" stroke-linecap="round" fill="none"/>
    <ellipse cx="100" cy="99" rx="18" ry="13" fill="#FFF3E6"/>
    <ellipse cx="86" cy="86" rx="5" ry="6.5" fill="#2A211C"/><ellipse cx="114" cy="86" rx="5" ry="6.5" fill="#2A211C"/>
    <circle cx="87.6" cy="83.6" r="1.8" fill="#FFFFFF"/><circle cx="115.6" cy="83.6" r="1.8" fill="#FFFFFF"/>
    <path d="M96 95 L104 95 L100 100 Z" fill="#E77C8E"/>
    <path d="M100 100 Q96 105 92 103 M100 100 Q104 105 108 103" stroke="#2A211C" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M78 98 L58 95 M78 102 L58 104 M122 98 L142 95 M122 102 L142 104" stroke="#2A211C" stroke-width="1.6" stroke-linecap="round" opacity=".55"/>
    <path d="M40 112 L160 112 L160 184 L40 184 Z" fill="url(#{uid}g)"/>
    <path d="M92 112 L108 112 L108 184 L92 184 Z" fill="#E8C99A" opacity=".7"/>
    <path d="M40 112 L14 98 L28 84 L58 106 Z" fill="#B97D43"/>
    <path d="M160 112 L186 98 L172 84 L142 106 Z" fill="#B97D43"/>
    <rect x="70" y="104" width="22" height="14" rx="7" fill="{fur}"/><rect x="108" y="104" width="22" height="14" rx="7" fill="{fur}"/>
    <path d="M77 110 L77 117 M84 110 L84 117 M115 110 L115 117 M122 110 L122 117" stroke="{fur2}" stroke-width="2" stroke-linecap="round"/>
    <path d="M56 160 L80 160 M56 168 L72 168" stroke="#8A5A2B" stroke-width="3" stroke-linecap="round" opacity=".5"/>
    """
    return _svg("0 0 200 200", body, _grad(f"{uid}g", "#D9A469", "#C08447"))


def paw(t, uid="pw"):
    c = t.get("accent", "#E07A3F")
    body = f"""
    <ellipse cx="100" cy="128" rx="38" ry="32" fill="{c}"/>
    <ellipse cx="58" cy="86" rx="15" ry="19" fill="{c}" transform="rotate(-18 58 86)"/>
    <ellipse cx="86" cy="64" rx="15" ry="19" fill="{c}" transform="rotate(-6 86 64)"/>
    <ellipse cx="114" cy="64" rx="15" ry="19" fill="{c}" transform="rotate(6 114 64)"/>
    <ellipse cx="142" cy="86" rx="15" ry="19" fill="{c}" transform="rotate(18 142 86)"/>
    """
    return _svg("0 0 200 200", body)


def bone(t, uid="bn"):
    body = """
    <g transform="rotate(-30 100 100)">
    <rect x="52" y="88" width="96" height="24" rx="12" fill="#FFF4E2" stroke="#E2C9A2" stroke-width="3"/>
    <circle cx="50" cy="86" r="17" fill="#FFF4E2" stroke="#E2C9A2" stroke-width="3"/><circle cx="50" cy="114" r="17" fill="#FFF4E2" stroke="#E2C9A2" stroke-width="3"/>
    <circle cx="150" cy="86" r="17" fill="#FFF4E2" stroke="#E2C9A2" stroke-width="3"/><circle cx="150" cy="114" r="17" fill="#FFF4E2" stroke="#E2C9A2" stroke-width="3"/>
    <rect x="50" y="90" width="100" height="20" fill="#FFF4E2"/>
    </g>"""
    return _svg("0 0 200 200", body)


def _beach(uid, sky=True):
    """Sun, sea, sand and a small sail, drawn on a 200 x 200 square; callers clip it to a shape."""
    return (
        (f'<rect x="0" y="0" width="200" height="200" fill="url(#{uid}k)"/>' if sky else "")
        + f"""
    <circle cx="128" cy="86" r="30" fill="url(#{uid}s)"/>
    <path d="M0 116 Q55 108 100 114 T200 112 L200 160 L0 160 Z" fill="#2BB3C0"/>
    <path d="M0 128 Q40 122 70 128 T130 127 T200 126 L200 170 L0 170 Z" fill="#1597A8"/>
    <path d="M22 122 Q32 118 42 122 M120 121 Q132 117 144 121 M160 133 Q170 129 180 133" stroke="#FFFFFF" stroke-width="2.4" fill="none" stroke-linecap="round" opacity=".75"/>
    <path d="M152 110 L152 90 L166 108 Z" fill="#FFFFFF"/><path d="M149 110 L170 110 L166 114 L152 114 Z" fill="#FF7A59"/>
    <path d="M0 168 Q60 140 120 150 Q170 158 200 172 L200 200 L0 200 Z" fill="url(#{uid}d)"/>""")


def _palm(t):
    return f"""
    <ellipse cx="70" cy="176" rx="28" ry="4" fill="{rgba(t['ink'], .14)}"/>
    <path d="M62 174 Q58 132 72 96 Q78 80 84 70" stroke="#8E5B32" stroke-width="9" fill="none" stroke-linecap="round"/>
    <path d="M62 160 L70 158 M61 146 L69 144 M62 132 L70 131 M65 118 L73 118 M69 104 L77 105 M74 91 L81 93" stroke="#6E4425" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M84 68 Q62 52 30 60 Q58 58 80 74 Z" fill="#2E9E58"/>
    <path d="M84 68 Q70 40 40 32 Q66 46 80 70 Z" fill="#45B86A"/>
    <path d="M84 68 Q96 40 128 34 Q102 50 88 70 Z" fill="#2E9E58"/>
    <path d="M84 68 Q114 56 142 68 Q112 64 88 74 Z" fill="#45B86A"/>
    <path d="M84 68 Q92 84 86 104 Q84 86 80 74 Z" fill="#2E9E58"/>
    <path d="M84 68 Q66 76 56 96 Q70 80 82 72 Z" fill="#45B86A"/>
    <circle cx="80" cy="76" r="5.5" fill="#6B4A2B"/><circle cx="89" cy="77" r="5" fill="#7C5733"/>"""


def _beach_defs(uid):
    return (_grad(f"{uid}s", "#FFD27A", "#FF9F4A") + _grad(f"{uid}d", "#F8E2B8", "#EBC98E")
            + _grad(f"{uid}k", "#9FD8F0", "#E6F6FB"))


def palm_beach(t, uid="pm"):
    """A round island scene with the palm leaning out of the circle: seaside travel."""
    body = (f'<clipPath id="{uid}c"><circle cx="100" cy="108" r="84"/></clipPath>'
            f'<g clip-path="url(#{uid}c)">{_beach(uid)}</g>' + _palm(t))
    return _svg("0 0 200 200", body, _beach_defs(uid))


def plane_window(t, uid="pw2"):
    """An aeroplane window looking out on a beach: arrivals, flights, 'you are almost there'."""
    body = f"""
    <rect x="34" y="8" width="132" height="184" rx="62" fill="#E9EEF2"/>
    <rect x="44" y="18" width="112" height="164" rx="54" fill="#C9D3DA"/>
    <clipPath id="{uid}c"><rect x="52" y="26" width="96" height="148" rx="47"/></clipPath>
    <g clip-path="url(#{uid}c)"><g transform="translate(-4 4) scale(1.04)">{_beach(uid)}{_palm(t)}</g></g>
    <path d="M60 60 Q66 40 84 34" stroke="#FFFFFF" stroke-width="5" fill="none" stroke-linecap="round" opacity=".55"/>
    """
    return _svg("0 0 200 200", body, _beach_defs(uid))


def sailboat(t, uid="sbt"):
    body = f"""
    <path d="M30 150 Q65 142 100 150 T170 150" stroke="#2BB3C0" stroke-width="6" fill="none" stroke-linecap="round"/>
    <path d="M104 30 L104 128 L44 128 Z" fill="#FFFFFF" stroke="{rgba(t['ink'], .18)}" stroke-width="2"/>
    <path d="M110 46 L110 128 L156 128 Z" fill="#FF7A59"/>
    <rect x="102" y="26" width="4" height="106" fill="#6E4425"/>
    <path d="M40 132 L164 132 L148 156 L56 156 Z" fill="#123B4A"/>
    <path d="M58 142 L146 142" stroke="#FFFFFF" stroke-width="3" opacity=".6"/>
    """
    return _svg("0 0 200 200", body)


def suitcase(t, uid="sc2"):
    c = t.get("accent", "#0FA3B1")
    body = f"""
    <ellipse cx="100" cy="186" rx="56" ry="6" fill="{rgba(t['ink'], .14)}"/>
    <path d="M78 40 Q78 28 90 28 L110 28 Q122 28 122 40 L122 52 L112 52 L112 40 L88 40 L88 52 L78 52 Z" fill="#123B4A"/>
    <rect x="46" y="50" width="108" height="128" rx="16" fill="{c}"/>
    <path d="M72 50 L72 178 M128 50 L128 178" stroke="#FFFFFF" stroke-width="6" opacity=".35"/>
    <rect x="60" y="78" width="30" height="20" rx="4" fill="#FFD27A" transform="rotate(-8 75 88)"/>
    <circle cx="124" cy="132" r="14" fill="#FF7A59"/><path d="M124 140 C112 131 116 122 124 127 C132 122 136 131 124 140 Z" fill="#FFFFFF"/>
    <circle cx="66" cy="182" r="6" fill="#123B4A"/><circle cx="134" cy="182" r="6" fill="#123B4A"/>
    """
    return _svg("0 0 200 200", body)


def luminance_hex(h):
    from common import luminance
    return luminance(h)


MOTIFS = {
    "lantern": lantern, "red-envelope": red_envelope, "mooncake": mooncake, "zongzi": zongzi, "xmas-tree": xmas_tree,
    "heart": heart, "bouquet": bouquet, "shopping-bag": shopping_bag, "fireworks": fireworks, "megaphone": megaphone,
    "building": building, "rings": rings, "double-happiness": double_happiness, "carrot": carrot, "birthday-cake": birthday_cake, "peach": peach,
    "dumbbell": dumbbell, "nail-polish": nail_polish, "scissors-comb": scissors_comb, "lotus": lotus,
    "open-book": open_book, "grad-cap": grad_cap, "microphone": microphone, "camera": camera, "trophy": trophy,
    "medal": medal, "laurel": laurel, "briefcase": briefcase, "scales": scales, "calendar": calendar, "envelope": envelope,
    "gaiwan": gaiwan,
    "milk-tea": milk_tea, "iced-coffee": iced_coffee, "hot-coffee": hot_coffee, "latte": latte,
    "bread": bread, "noodle-bowl": noodle_bowl, "gift": gift,
    "pet-box": pet_box, "paw": paw, "bone": bone,
    "palm-beach": palm_beach, "plane-window": plane_window, "sailboat": sailboat, "suitcase": suitcase,
}
MOTIF_ASPECT = {"gaiwan": 200 / 190, "milk-tea": 200 / 240, "iced-coffee": 200 / 240, "hot-coffee": 200 / 240, "latte": 1,
                "bread": 200 / 180, "noodle-bowl": 200 / 190, "gift": 1}


def motif(name, t, uid=None, opts=None):
    if name == "drink":  # a cup described by art.drink (colours, topping, bits)
        from art_drinks import drink_cup
        return drink_cup(t, uid or "dk", opts)
    fn = MOTIFS.get(name) or gift
    return fn(t, uid or name.replace("-", ""))


def _register_drinks():
    from art_drinks import INGREDIENTS, drink_cup
    MOTIFS.update(INGREDIENTS)
    MOTIFS["drink"] = lambda t, uid="dk": drink_cup(t, uid, None)


_register_drinks()


# ------------------------------------------------------------------ small decorations
def sparkle(color, size=40):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="{size}" height="{size}">'
            f'<path d="M20 0 C22 14 26 18 40 20 C26 22 22 26 20 40 C18 26 14 22 0 20 C14 18 18 14 20 0 Z" '
            f'fill="{color}"/></svg>')


def data_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def noise_uri(fine=True, opacity=0.5):
    freq = "0.9" if fine else "0.55"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">'
           f'<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="3" stitchTiles="stitch"/>'
           f'<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 {opacity} 0"/></filter>'
           f'<rect width="100%" height="100%" filter="url(#n)"/></svg>')
    return data_uri(svg)


def cloud_tile(color):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="110" viewBox="0 0 160 110">'
           f'<g fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round">'
           f'<path d="M20 60 q0 -18 18 -18 q4 -16 22 -12 q10 -12 24 0 q18 -2 18 16 q14 2 12 14 H22 q-8 0 -2 0"/>'
           f'<path d="M50 60 q2 -10 12 -10 q8 0 10 8"/>'
           f'<path d="M100 100 q0 -12 12 -12 q4 -10 16 -6 q12 0 10 12 H102"/></g></svg>')
    return data_uri(svg)


def luminance_dark(h):
    from common import is_dark
    return is_dark(h)


def pattern_css(kind, t, u):
    """CSS background for the canvas pattern layer."""
    ink = t["ink"]
    if kind == "dots":
        s = 3.4 * u
        return (f"background-image: radial-gradient({rgba(ink, .10)} {0.32 * u:.1f}px, transparent {0.36 * u:.1f}px);"
                f"background-size: {s:.1f}px {s:.1f}px;")
    if kind == "grid":
        s = 4 * u
        return (f"background-image: linear-gradient({rgba(ink, .06)} 1px, transparent 1px),"
                f"linear-gradient(90deg, {rgba(ink, .06)} 1px, transparent 1px);"
                f"background-size: {s:.1f}px {s:.1f}px;")
    if kind == "stripes":
        s = 1.6 * u
        return (f"background-image: repeating-linear-gradient(-45deg, {rgba(t['muted'], .08)} 0 {s:.1f}px,"
                f" transparent {s:.1f}px {2 * s:.1f}px);")
    if kind == "rays":
        return (f"background-image: repeating-conic-gradient(from 0deg at 50% 42%, {rgba('#FFFFFF', .07)} 0deg 6deg,"
                f" transparent 6deg 12deg);")
    if kind == "waves":
        s = 5 * u
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="20"><path d="M0 10 q10 -8 20 0 t20 0 t20 0 t20 0" '
               f'stroke="{rgba(ink, .08)}" stroke-width="2" fill="none"/></svg>')
        return f"background-image: url('{data_uri(svg)}'); background-size: {s * 4:.0f}px {s:.0f}px;"
    if kind == "snow":
        flakes = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" opacity="{o}"/>' for x, y, r, o in
                         [(12, 18, 2.2, .5), (48, 8, 1.5, .4), (70, 40, 2.6, .45), (30, 56, 1.4, .35), (88, 70, 1.8, .4), (8, 84, 2.4, .45)])
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96">{flakes}</svg>'
        op = 1 if luminance_dark(t["bg"]) else 0
        if not op:
            svg = svg.replace("#FFFFFF", t["accent2"])
        return f"background-image: url('{data_uri(svg)}'); background-size: {12 * u:.0f}px {12 * u:.0f}px;"
    if kind == "hearts":
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80"><path d="M20 30 C14 25 11 21 13 17 C15 13 19 13 20 16 '
               f'C21 13 25 13 27 17 C29 21 26 25 20 30 Z" fill="{rgba(t["accent"], .12)}"/><path d="M60 70 C55 66 53 63 54 60 '
               f'C56 57 59 57 60 59 C61 57 64 57 66 60 C67 63 65 66 60 70 Z" fill="{rgba(t["accent"], .09)}"/></svg>')
        return f"background-image: url('{data_uri(svg)}'); background-size: {11 * u:.0f}px {11 * u:.0f}px;"
    if kind == "confetti":
        bits = "".join(f'<rect x="{x}" y="{y}" width="{w}" height="3" rx="1.5" fill="{c}" transform="rotate({r} {x} {y})" opacity=".35"/>'
                       for x, y, w, c, r in [(10, 14, 10, t["accent"], 30), (54, 22, 8, t["accent2"], -20), (30, 60, 9, t["accent2"], 60),
                                             (78, 74, 10, t["accent"], -45), (66, 44, 6, t["ink"], 15)])
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96">{bits}</svg>'
        return f"background-image: url('{data_uri(svg)}'); background-size: {13 * u:.0f}px {13 * u:.0f}px;"
    if kind == "stars":
        st = "".join(f'<path d="M{x} {y - s} L{x + s * .3} {y - s * .3} L{x + s} {y} L{x + s * .3} {y + s * .3} L{x} {y + s} '
                     f'L{x - s * .3} {y + s * .3} L{x - s} {y} L{x - s * .3} {y - s * .3} Z" fill="{t["accent2"]}" opacity="{o}"/>'
                     for x, y, s, o in [(16, 20, 4, .5), (70, 14, 2.5, .4), (44, 52, 3, .35), (86, 78, 4, .45), (20, 86, 2, .35)])
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">{st}</svg>'
        return f"background-image: url('{data_uri(svg)}'); background-size: {14 * u:.0f}px {14 * u:.0f}px;"
    if kind == "clouds":
        return (f"background-image: url('{cloud_tile(rgba(t['accent'], .10))}');"
                f"background-size: {16 * u:.0f}px {11 * u:.0f}px;")
    return ""


def starburst_polygon(points=20, inner=0.86):
    pts = []
    for i in range(points * 2):
        r = 50 if i % 2 == 0 else 50 * inner
        a = math.pi * i / points - math.pi / 2
        pts.append(f"{50 + r * math.cos(a):.2f}% {50 + r * math.sin(a):.2f}%")
    return "polygon(" + ", ".join(pts) + ")"
