"""H5 pages: a phone page people swipe through, built from the same tokens, fonts and checks.

An h5 item expands (render.expand) into one h5page per screen. Every screen is laid out on a
390 px wide stage. For QA and previews each screen renders as a fixed 390x844 picture; h5.py
then stitches the same markup into one self-contained HTML file where the stage scales with the
phone's width and grows with its height.

Interactive bits are plain markup: <a class="btn" data-action="..."> buttons, data-tpl lines that
take the guest's name from ?to=, and a data-countdown block. h5.py adds the script.
"""
import datetime as dt
import html as _html

from common import esc, rgba
from layouts import T, art_block, page

WEEK = "一二三四五六日"
PAGES = {"invite": ["cover", "letter", "info", "schedule", "rsvp"]}


def when_of(c):
    """content.when = {"start": "2027-05-22T17:30", "end": ..., "tz": "Asia/Shanghai"} -> datetimes."""
    w = c.get("when") or {}
    try:
        start = dt.datetime.fromisoformat(w["start"])
    except Exception:  # noqa: BLE001
        return None, None, w.get("tz") or "Asia/Shanghai"
    try:
        end = dt.datetime.fromisoformat(w["end"]) if w.get("end") else start + dt.timedelta(hours=3)
    except Exception:  # noqa: BLE001
        end = start + dt.timedelta(hours=3)
    return start, end, w.get("tz") or "Asia/Shanghai"


def pages_for(item):
    c = item.get("content") or {}
    out = []
    for p in PAGES.get(item.get("layout") or "invite", PAGES["invite"]):
        if p == "schedule" and not c.get("schedule"):
            continue
        out.append(p)
    return out


# ------------------------------------------------------------------ shared parts
def _frame(ctx):
    from layouts_more import ornate_frame
    t = ctx.t
    if ctx.d["shape"].get("deco") not in ("line", "seal"):
        return ""
    return ornate_frame(ctx, t["accent"], rgba(t["accent"], .55), 2.6 * ctx.u)


def _col(ctx, inner, pad=(12, 8, 9, 8), align="center", gap=0):
    """The screen's content column. Fixed 844 high in previews, at least one screen high on phones."""
    top, side, bottom, side2 = pad
    return (f'<div class="h5col" data-grow-box="1" style="position:relative;z-index:3;display:flex;flex-direction:column;align-items:{align};'
            f'padding:{ctx.px(top)} {ctx.px(side)} {ctx.px(bottom)} {ctx.px(side2)};gap:{ctx.px(gap)};text-align:{align if align != "stretch" else "left"}">{inner}</div>')


def _sp(ctx, n=None, grow=False):
    if grow:
        return f'<div style="flex:1 1 0;min-height:{ctx.px(n or 2)}"></div>'
    return f'<div style="height:{ctx.px(n)};flex:none"></div>'


def _label(ctx, s):
    u = ctx.u
    return (T(ctx, "label", s, c="accent_text", style=f"font-size:{max(ctx.minc, 3.3 * u):.1f}px;letter-spacing:.4em;font-weight:700;")
            + f'<div style="width:{ctx.px(8)};height:{ctx.px(0.5)};background:{ctx.t["accent"]};margin:{ctx.px(2.4)} auto 0"></div>')


def _guest_line(ctx, tpl, guest, role="body", style="", c="ink"):
    """A line that carries the guest's name; h5.py swaps in ?to=NAME."""
    return f'<div data-tpl="{esc(tpl)}" style="width:100%">' + T(ctx, role, tpl.replace("{guest}", guest), c=c, style=style) + "</div>"


def _btn(ctx, label, action, href="#", primary=True, extra=""):
    t, u = ctx.t, ctx.u
    r = max(ctx.d["shape"]["radius"] * 0.6, 0.6) * u if ctx.d["shape"]["radius"] else 0
    if primary:
        st = f"background:{t['accent']};border:{ctx.px(0.3)} solid {t['accent']};"
        txt = T(ctx, "label", label, c="on_accent", on="accent", style=f"font-size:{max(ctx.minb, 4.1 * u):.1f}px;font-weight:700;letter-spacing:.12em;white-space:nowrap;")
    else:
        st = f"background:transparent;border:{ctx.px(0.3)} solid {t['accent']};"
        txt = T(ctx, "label", label, c="accent_text", style=f"font-size:{max(ctx.minb, 3.8 * u):.1f}px;font-weight:700;letter-spacing:.08em;white-space:nowrap;")
    return (f'<a class="btn rv" data-action="{action}" href="{_html.escape(href, quote=True)}" {extra} '
            f'style="{st}display:flex;align-items:center;justify-content:center;min-height:{ctx.px(13)};padding:0 {ctx.px(4)};'
            f'border-radius:{r:.1f}px;text-decoration:none;flex:1 1 0;min-width:0;-webkit-tap-highlight-color:transparent">{txt}</a>')


def _date_big(ctx, c):
    start, _, _ = when_of(c)
    if c.get("big_number"):
        return c["big_number"]
    return f"{start:%Y.%m.%d}" if start else "【日期】"


def _date_line(ctx, c):
    start, _, _ = when_of(c)
    if c.get("date_text"):
        return c["date_text"]
    if not start:
        return "【日期】"
    return f"{start.year} 年 {start.month} 月 {start.day} 日 星期{WEEK[start.weekday()]}"


def countdown_days(c, today=None):
    start, _, _ = when_of(c)
    if not start:
        return None
    today = today or dt.date.today()
    return (start.date() - today).days


def _screen(ctx, fonts_css, inner, css=""):
    return page(ctx, fonts_css, inner, ".h5col{height:100%}" + css)


# ------------------------------------------------------------------ screens
def h5_cover(ctx, fonts_css):
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    a = ctx.item.get("art") or {}
    guest = c.get("guest") or c.get("default_guest") or "亲朋好友"
    if a.get("image"):  # a photo of the couple / the birthday star: a framed picture instead of the motif
        motif = (f'<div class="rv" style="width:{ctx.px(58)};height:{ctx.px(72)};position:relative;flex:none;padding:{ctx.px(1.2)};'
                 f'border:{ctx.px(0.3)} solid {t["accent"]}">{art_block(ctx, {**a, "image_fit": "cover"})}</div>')
    else:
        motif = (f'<div class="rv" style="width:{ctx.px(30)};height:{ctx.px(30)};position:relative;flex:none">{art_block(ctx, a)}</div>'
                 if a.get("motif") else "")
    host = c.get("host") or ctx.brand.get("name")
    inner = (_sp(ctx, 2)
             + T(ctx, "label", c.get("kicker") or "INVITATION", c="accent_text", cls="rv",
                 style=f"font-size:{max(ctx.minc, 3 * u):.1f}px;letter-spacing:.42em;font-weight:700;")
             + _sp(ctx, 4, grow=True) + motif + _sp(ctx, 5)
             + T(ctx, "headline", c.get("title") or "邀请函", cls="d rv", fit=(14 * u, 8 * u),
                 style=f"max-height:{ctx.px(34)};width:100%;text-align:center;flex:none;")
             + _sp(ctx, 3)
             + T(ctx, "sub", host, cls="d rv", style=f"font-size:{ctx.px(5.4)};letter-spacing:.1em;white-space:nowrap;")
             + f'<div class="rv" style="width:{ctx.px(10)};height:{ctx.px(0.5)};background:{t["accent"]};margin:{ctx.px(4)} 0;flex:none"></div>'
             + T(ctx, "headline", _date_big(ctx, c), c="accent_text", cls="d rv",
                 style=f"font-size:{ctx.px(10)};line-height:1;letter-spacing:.06em;white-space:nowrap;")
             + _sp(ctx, 2)
             + T(ctx, "caption", _date_line(ctx, c), c="muted", cls="rv", style=f"font-size:{max(ctx.minc, 3.4 * u):.1f}px;letter-spacing:.12em;")
             + _sp(ctx, 4, grow=True)
             + f'<div class="rv">' + _guest_line(ctx, c.get("invite_line") or "诚邀 {guest}", guest, role="body",
                                                 style=f"font-size:{max(ctx.minb, 4.6 * u):.1f}px;letter-spacing:.12em;font-weight:700;") + "</div>"
             + _sp(ctx, 7)
             + f'<div class="hint" style="display:flex;flex-direction:column;align-items:center;gap:{ctx.px(1)}">'
             + f'<svg width="{ctx.px(6)}" height="{ctx.px(4)}" viewBox="0 0 24 16"><path d="M2 2 L12 12 L22 2" fill="none" stroke="{t["accent"]}" stroke-width="2.5" stroke-linecap="round"/></svg>'
             + T(ctx, "caption", "向上滑动", c="muted", style=f"font-size:{max(ctx.minc, 3 * u):.1f}px;letter-spacing:.3em;")
             + "</div>")
    return _screen(ctx, fonts_css, _frame(ctx) + _col(ctx, inner, pad=(10, 9, 8, 9)))


def h5_letter(ctx, fonts_css):
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    guest = c.get("guest") or c.get("default_guest") or "亲朋好友"
    paras = [p for p in str(c.get("body") or "").split("\n\n") if p.strip()]
    body = (f'<div id="letterbody" class="t body rv" data-role="body" data-c="ink" data-on="bg" data-fit="1" '
            f'data-max="{max(ctx.minb, 4.4 * u):.1f}" data-min="{ctx.minb:.1f}" '
            f'style="color:{t["ink"]};font-size:{max(ctx.minb, 4.4 * u):.1f}px;line-height:1.95;text-align:justify;width:100%;'
            f'flex:0 1 auto;max-height:{ctx.px(120)};overflow:hidden">'
            + "".join(f'<p style="text-indent:2em;margin:0 0 .7em">{esc(p)}</p>' for p in paras) + "</div>")
    sal = c.get("salutation") or "尊敬的 {guest}："
    inner = (_sp(ctx, 4) + _label(ctx, c.get("letter_label") or "邀 请 函") + _sp(ctx, 4, grow=True)
             + f'<div data-grow="1.3" data-keep="{14 * u:.0f}" style="width:100%;display:flex;flex-direction:column">'
             + f'<div class="rv" style="width:100%">' + _guest_line(ctx, sal, guest, style=f"font-size:{max(ctx.minb, 4.8 * u):.1f}px;font-weight:700;text-align:left;") + "</div>"
             + _sp(ctx, 4) + body + _sp(ctx, 5)
             + f'<div class="rv" style="width:100%;text-align:right">'
             + T(ctx, "body", c.get("closing") or "恭候光临", c="accent_text", cls="d", style=f"font-size:{max(ctx.minb, 4.6 * u):.1f}px;letter-spacing:.2em;")
             + _sp(ctx, 2)
             + T(ctx, "body", c.get("host") or ctx.brand.get("name"), style=f"font-size:{max(ctx.minb, 4.2 * u):.1f}px;font-weight:700;")
             + "</div></div>" + _sp(ctx, 6, grow=True))
    return _screen(ctx, fonts_css, _frame(ctx) + _col(ctx, inner, pad=(10, 11, 10, 11)))


def h5_info(ctx, fonts_css):
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    start, _, _ = when_of(c)
    days = countdown_days(c)
    big = f"{start.month} 月 {start.day} 日" if start else "【日期】"
    rows = "".join(
        f'<div class="rv" style="display:flex;gap:{ctx.px(3)};align-items:baseline;justify-content:center">'
        + T(ctx, "caption", d.get("k"), c="accent_text", style=f"font-size:{max(ctx.minc, 3.4 * u):.1f}px;font-weight:700;letter-spacing:.2em;white-space:nowrap;")
        + T(ctx, "body", d.get("v"), style=f"font-size:{max(ctx.minb, 4.2 * u):.1f}px;white-space:nowrap;")
        + "</div>" for d in (c.get("details") or []))
    count = ""
    if days is not None:
        label = c.get("countdown_label") or "距离婚礼还有"
        count = (f'<div class="rv" data-countdown="1" data-label="{esc(label)}" style="background:{t["surface"]};border:{ctx.px(0.25)} solid {t["line"]};'
                 f'padding:{ctx.px(3.4)} {ctx.px(5)};display:flex;align-items:baseline;gap:{ctx.px(2)};justify-content:center;width:100%">'
                 + T(ctx, "caption", label, c="muted", on="surface", eid="cd-label", style=f"font-size:{max(ctx.minc, 3.6 * u):.1f}px;letter-spacing:.12em;white-space:nowrap;")
                 + T(ctx, "headline", str(max(days, 0)), c="accent_text", on="surface", cls="d", eid="cd-days",
                     style=f"font-size:{ctx.px(10)};line-height:1;white-space:nowrap;")
                 + T(ctx, "caption", "天", c="muted", on="surface", eid="cd-unit", style=f"font-size:{max(ctx.minc, 3.6 * u):.1f}px;")
                 + "</div>")
    venue = c.get("venue") or "【地点】"
    addr = c.get("address")
    btns = (f'<div style="display:flex;flex-direction:column;gap:{ctx.px(2.6)};width:100%">'
            + _btn(ctx, c.get("nav_label") or "一键导航", "nav", "#")
            + f'<div style="display:flex;gap:{ctx.px(2.6)};width:100%">'
            + _btn(ctx, "加入日历", "ics", "#", primary=False)
            + _btn(ctx, "复制地址", "copy", "#", primary=False)
            + "</div></div>")
    inner = (_sp(ctx, 4) + _label(ctx, c.get("info_label") or "时 间 地 点") + _sp(ctx, 3, grow=True)
             + T(ctx, "headline", big, cls="d rv", style=f"font-size:{ctx.px(11)};line-height:1.1;white-space:nowrap;")
             + _sp(ctx, 2)
             + T(ctx, "caption", _date_line(ctx, c), c="muted", cls="rv", style=f"font-size:{max(ctx.minc, 3.5 * u):.1f}px;letter-spacing:.1em;")
             + _sp(ctx, 4)
             + f'<div style="display:flex;flex-direction:column;gap:{ctx.px(1.6)}">{rows}</div>'
             + _sp(ctx, 5) + count + _sp(ctx, 3, grow=True)
             + T(ctx, "sub", venue, cls="d rv", style=f"font-size:{ctx.px(6)};letter-spacing:.06em;text-align:center;")
             + _sp(ctx, 1.6)
             + (T(ctx, "caption", addr, c="muted", cls="rv", style=f"font-size:{max(ctx.minc, 3.5 * u):.1f}px;text-align:center;") if addr else "")
             + _sp(ctx, 5) + btns + _sp(ctx, 3, grow=True))
    return _screen(ctx, fonts_css, _frame(ctx) + _col(ctx, inner, pad=(10, 10, 10, 10)))


def h5_schedule(ctx, fonts_css):
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    items = c.get("schedule") or []
    dot = ctx.px(3)
    rows = ""
    for i, s in enumerate(items):
        rows += (f'<div class="rv" style="text-align:left;display:grid;grid-template-columns:{ctx.px(20)} {ctx.px(6)} 1fr;align-items:start;min-height:{ctx.px(17)}">'
                 + T(ctx, "headline", s.get("time"), c="accent_text", cls="d", style=f"font-size:{ctx.px(5.6)};line-height:1.1;text-align:right;white-space:nowrap;")
                 + f'<div style="position:relative;height:100%;display:flex;justify-content:center">'
                 + (f'<div style="position:absolute;top:{ctx.px(2)};bottom:{ctx.px(-2)};width:{ctx.px(0.3)};background:{rgba(t["accent"], .5)}"></div>' if i < len(items) - 1 else "")
                 + f'<div style="width:{dot};height:{dot};border-radius:50%;background:{t["accent"]};margin-top:{ctx.px(1.2)};position:relative"></div></div>'
                 + "<div>" + T(ctx, "body", s.get("what"), style=f"font-size:{max(ctx.minb, 4.6 * u):.1f}px;font-weight:700;line-height:1.3;")
                 + (T(ctx, "caption", s.get("note"), c="muted", style=f"font-size:{max(ctx.minc, 3.4 * u):.1f}px;margin-top:{ctx.px(1)};") if s.get("note") else "")
                 + "</div></div>")
    inner = (_sp(ctx, 4) + _label(ctx, c.get("schedule_label") or "当 日 流 程") + _sp(ctx, 6, grow=True)
             + f'<div style="width:100%;display:flex;flex-direction:column">{rows}</div>' + _sp(ctx, 8, grow=True))
    return _screen(ctx, fonts_css, _frame(ctx) + _col(ctx, inner, pad=(10, 9, 10, 9)))


def h5_rsvp(ctx, fonts_css):
    c, t, u = ctx.item["content"], ctx.t, ctx.u
    a = ctx.item.get("art") or {}
    motif = (f'<div class="rv" style="width:{ctx.px(20)};height:{ctx.px(20)};position:relative;flex:none">{art_block(ctx, a)}</div>'
             if (a.get("motif") or a.get("image")) else "")
    url = c.get("rsvp_url")
    rsvp_btn = _btn(ctx, c.get("rsvp_label") or "回复是否出席", "rsvp", url or "#")
    missing = (T(ctx, "caption", "【回执链接】", c="muted", style=f"font-size:{max(ctx.minc, 3 * u):.1f}px;margin-top:{ctx.px(1.4)};")
               if not url else "")
    contacts = c.get("contacts") or []
    cbtns = ""
    if contacts:
        cbtns = (f'<div style="display:flex;gap:{ctx.px(2.6)};width:100%">'
                 + "".join(_btn(ctx, k.get("label") or f"联系{k.get('name', '')}", "tel", f"tel:{k.get('phone', '')}", primary=False)
                           for k in contacts[:2]) + "</div>")
    inner = (_sp(ctx, 4, grow=True) + motif + _sp(ctx, 5)
             + T(ctx, "headline", c.get("closing") or "恭候光临", cls="d rv", fit=(11 * u, 7 * u),
                 style=f"max-height:{ctx.px(26)};width:100%;text-align:center;flex:none;")
             + _sp(ctx, 3)
             + T(ctx, "body", c.get("rsvp"), c="muted", cls="rv", style=f"font-size:{max(ctx.minb, 3.9 * u):.1f}px;text-align:center;")
             + _sp(ctx, 7)
             + f'<div style="display:flex;flex-direction:column;align-items:center;gap:{ctx.px(2.6)};width:100%">'
             + f'<div style="display:flex;width:100%">{rsvp_btn}</div>{missing}{cbtns}</div>'
             + _sp(ctx, 4, grow=True)
             + T(ctx, "body", c.get("host") or ctx.brand.get("name"), cls="d rv", style=f"font-size:{max(ctx.minb, 4.4 * u):.1f}px;letter-spacing:.1em;")
             + _sp(ctx, 1.4)
             + T(ctx, "caption", c.get("date_line"), c="muted", cls="rv", style=f"font-size:{max(ctx.minc, 3.2 * u):.1f}px;")
             + _sp(ctx, 3))
    return _screen(ctx, fonts_css, _frame(ctx) + _col(ctx, inner, pad=(10, 10, 10, 10)))


SCREENS = {"cover": h5_cover, "letter": h5_letter, "info": h5_info, "schedule": h5_schedule, "rsvp": h5_rsvp}


def register(builders, layouts):
    layouts["h5"] = list(PAGES)
    layouts["h5page"] = list(SCREENS)
    for k, fn in SCREENS.items():
        builders[("h5page", k)] = fn
