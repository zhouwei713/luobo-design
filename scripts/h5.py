"""Stitch the rendered H5 screens into one phone page people can open, swipe and tap.

  python h5.py spec.json [--out DIR]          (pipeline.py runs this after render.py)

For every item of type h5 it writes DIR/h5/<id>.html: one self-contained file with the screens
render.py already fitted (src/*.frozen.html), the fonts cut down to the characters on the page and
embedded, the buttons wired up (navigation, add to calendar, copy address, RSVP, call), the guest's
name taken from ?to=NAME, a live countdown, and a long preview picture for checking by eye.
It then opens the file on several phone sizes, taps the buttons and writes DIR/h5/h5_qa.json,
which check.py folds into qa.json.
"""
import argparse
import base64
import hashlib
import datetime as dt
import html as _html
import io
import json
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

import render
from common import esc, load_json, load_ref, resolve_tokens, save_json, spec_brand, canvas
from layouts import Ctx, base_css
from layouts_h5 import countdown_days, pages_for, when_of

UI_TEXT = ("地址已复制 复制失败请长按地址手动复制 微信里没法直接加日历点右上角选在浏览器打开再试 已打开日历文件 "
           "婚礼已经举行感谢您的祝福 天 0123456789 亲朋好友 音乐 开 关 ：，。、！？（）《》·&-—")


# ------------------------------------------------------------------ fonts
def _ranges(cps):
    cps = sorted(cps)
    out, lo = [], None
    for i, c in enumerate(cps):
        if lo is None:
            lo = prev = c
            continue
        if c == prev + 1:
            prev = c
            continue
        out.append((lo, prev))
        lo = prev = c
    if lo is not None:
        out.append((lo, prev))
    return ",".join(f"U+{a:X}" if a == b else f"U+{a:X}-{b:X}" for a, b in out)


def _subset(path, cps, index=0):
    from fontTools import subset
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.desubroutinize = True
    opts.layout_features = ["*"]
    from fontTools.ttLib import TTFont
    font = TTFont(path, fontNumber=index, lazy=False)
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=cps)
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    return buf.getvalue()


def embed_fonts(uses, text):
    """uses: {font_id: {weights}}. Returns (@font-face css, total bytes, notes)."""
    import outline
    fonts = load_ref("fonts.json")
    cps = {ord(ch) for ch in text if not ch.isspace()} | {0x20}
    css, total, notes = [], 0, []
    for fid, weights in uses.items():
        spec = fonts.get(fid) or fonts["sans"]
        fam = spec["family"]
        try:
            if spec["source"] == "npm":
                for w, ranges, path in outline._css_blocks(fid):
                    hit = {c for c in cps if any(lo <= c <= hi for lo, hi in ranges)}
                    if not hit:
                        continue
                    data = _subset(path, hit)
                    total += len(data)
                    css.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:swap;"
                               f"src:url(data:font/woff2;base64,{base64.b64encode(data).decode()}) format('woff2');"
                               f"unicode-range:{_ranges(hit)}}}")
            else:
                for w in sorted(weights):
                    path, idx = outline._system_file(fam, w)
                    if not path:
                        notes.append(f"{fam} {w} not found; phones use their own font")
                        continue
                    data = _subset(path, cps, idx)
                    total += len(data)
                    css.append(f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:swap;"
                               f"src:url(data:font/woff2;base64,{base64.b64encode(data).decode()}) format('woff2')}}")
        except Exception as e:  # noqa: BLE001  (no brotli, broken file: the page still works with phone fonts)
            notes.append(f"{fam}: could not embed ({e})")
    return "\n".join(css), total, notes


# ------------------------------------------------------------------ links and files
def _real(s):
    """Drop 【placeholders】: a navigation search or a calendar entry should never carry them."""
    return re.sub(r"【[^】]*】", "", str(s or "")).strip()


def nav_url(c):
    venue, addr = _real(c.get("venue")), _real(c.get("address"))
    m = c.get("map") or {}
    if m.get("lng") and m.get("lat"):
        q = urllib.parse.urlencode({"position": f"{m['lng']},{m['lat']}", "name": venue or addr, "coordinate": "gaode", "callnative": 1})
        return f"https://uri.amap.com/marker?{q}"
    q = urllib.parse.urlencode({"keyword": f"{venue} {addr}".strip(), "callnative": 1})
    return f"https://uri.amap.com/search?{q}"


def ics_text(c, title):
    start, end, tz = when_of(c)
    if not start:
        return None
    try:
        from zoneinfo import ZoneInfo
        zs, ze = start.replace(tzinfo=ZoneInfo(tz)), end.replace(tzinfo=ZoneInfo(tz))
    except Exception:  # noqa: BLE001
        zs, ze = start.replace(tzinfo=dt.timezone(dt.timedelta(hours=8))), end.replace(tzinfo=dt.timezone(dt.timedelta(hours=8)))
    f = lambda d: d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    clean = lambda s: str(s or "").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    loc = " ".join(x for x in (_real(c.get("venue")), _real(c.get("address"))) if x)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//luobo-design//h5//ZH", "BEGIN:VEVENT",
                        f"UID:{f(zs)}-{hashlib.md5(title.encode('utf-8')).hexdigest()[:10]}@luobo-design", f"DTSTAMP:{stamp}",
                        f"DTSTART:{f(zs)}", f"DTEND:{f(ze)}", f"SUMMARY:{clean(title)}", f"LOCATION:{clean(loc)}",
                        "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", f"DESCRIPTION:{clean(title)}", "END:VALARM",
                        "END:VEVENT", "END:VCALENDAR", ""])


def _inline_images(fragment):
    """Local pictures (file:// in the previews) go inside the file so it works wherever it is uploaded."""
    import mimetypes
    from urllib.request import url2pathname

    def rep(m):
        p = Path(url2pathname(urllib.parse.urlparse(m.group(1)).path))
        if not p.exists():
            return m.group(0)
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        return f'src="data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"'
    return re.sub(r'src="(file://[^"]+)"', rep, fragment)


def _text_of(fragment):
    return _html.unescape(re.sub(r"<[^>]+>", " ", fragment))


def _neutral_guest(fragment, default):
    """The previews carry the first guest's name; the shared file shows a neutral greeting until ?to= says who."""
    def rep(m):
        tpl = _html.unescape(m.group(1))
        inner = m.group(2)
        return m.group(0).replace(inner, esc(tpl.replace("{guest}", default)), 1) if inner else m.group(0)
    return re.sub(r'<div data-tpl="([^"]*)"[^>]*><div [^>]*>(.*?)</div></div>', rep, fragment, flags=re.S)


JS = r"""
(function(){
  var root = document.documentElement, main = document.querySelector('main.h5');
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var useZoom = window.CSS && CSS.supports && CSS.supports('zoom', '2');
  function size(){
    var k = Math.min(window.innerWidth, 480) / 390, sh = Math.max(window.innerHeight / k, 560);
    root.style.setProperty('--sh', sh + 'px');
    document.querySelectorAll('.stage').forEach(function(s){
      if (useZoom) { s.style.zoom = k; }
      else { s.style.transform = 'scale(' + k + ')'; s.style.transformOrigin = 'top center';
             s.parentNode.style.height = (s.offsetHeight * k) + 'px'; }
    });
  }
  size(); window.addEventListener('resize', size);
  if (!reduce) root.classList.add('anim');
  document.querySelectorAll('.scr').forEach(function(sec){
    sec.querySelectorAll('.rv').forEach(function(el, i){ el.style.transitionDelay = (i * 90) + 'ms'; });
  });
  var dots = document.querySelectorAll('.dots button');
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){ if (e.isIntersecting) {
      e.target.classList.add('in');
      var i = +e.target.dataset.i; dots.forEach(function(d, j){ d.classList.toggle('on', j === i); });
    }});
  }, {root: main, threshold: 0.35});
  document.querySelectorAll('.scr').forEach(function(s){ io.observe(s); });
  dots.forEach(function(d, j){ d.addEventListener('click', function(){
    document.querySelectorAll('.scr')[j].scrollIntoView({behavior: reduce ? 'auto' : 'smooth'}); }); });

  var toastEl = document.querySelector('.toast'), tt;
  function toast(msg){ toastEl.textContent = msg; toastEl.classList.add('show'); clearTimeout(tt);
    tt = setTimeout(function(){ toastEl.classList.remove('show'); }, 2600); }
  window.__toast = toast;

  // the guest's name from ?to=NAME (shown as text, never as markup)
  try {
    var to = new URLSearchParams(location.search).get('to');
    if (to) { to = to.trim().slice(0, 24);
      document.querySelectorAll('[data-tpl]').forEach(function(w){
        var t = w.querySelector('.t'); if (t) t.textContent = w.dataset.tpl.replace('{guest}', to); }); }
  } catch (e) {}

  // countdown, counted on the phone so it is right on the day it is opened
  var cd = document.querySelector('[data-countdown]');
  if (cd && window.__START) {
    var days = Math.ceil((window.__START - Date.now()) / 86400000);
    var n = cd.querySelector('#cd-days');
    if (days > 0) { if (n) n.textContent = days; }
    else if (days === 0) { cd.querySelector('#cd-label').textContent = '就是今天'; if (n) n.textContent = ''; cd.querySelector('#cd-unit').textContent = ''; }
    else { cd.querySelector('#cd-label').textContent = window.__AFTER || '已经举行，感谢您的祝福'; if (n) n.textContent = ''; cd.querySelector('#cd-unit').textContent = ''; }
  }

  function copy(text){
    function fallback(){ var ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); var ok = false; try { ok = document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(ta); toast(ok ? '地址已复制' : '复制失败，请长按地址手动复制'); }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(function(){ toast('地址已复制'); }, fallback);
    else fallback();
  }
  var wx = /MicroMessenger/i.test(navigator.userAgent);
  document.querySelectorAll('.btn').forEach(function(b){
    b.addEventListener('click', function(ev){
      var a = b.dataset.action;
      if (a === 'copy') { ev.preventDefault(); copy(b.dataset.copy || ''); }
      else if (a === 'ics') {
        if (wx) { ev.preventDefault(); toast('微信里没法直接加日历，点右上角选在浏览器打开再试'); }
        else toast('已打开日历文件');
      }
      else if (b.getAttribute('href') === '#') { ev.preventDefault(); }
    });
  });

  var m = document.querySelector('audio');
  if (m) { var mb = document.querySelector('.music');
    function play(){ m.play().then(function(){ mb.classList.add('on'); }, function(){}); }
    mb.addEventListener('click', function(e){ e.stopPropagation(); if (m.paused) play(); else { m.pause(); mb.classList.remove('on'); } });
    document.addEventListener('WeixinJSBridgeReady', play, false);
    document.addEventListener('touchstart', function once(){ play(); document.removeEventListener('touchstart', once); }, {passive: true});
  }
})();
"""


def assemble(spec, item, out, direction, base):
    c = item.get("content") or {}
    pages = pages_for(item)
    frags = []
    for n, pg in enumerate(pages, 1):
        f = out / "src" / f"{item['id']}-{n}-{pg}-h5.frozen.html"
        if not f.exists():
            raise SystemExit(f"{f.name} missing: run render.py first")
        frags.append((pg, f.read_text(encoding="utf-8")))
    default = c.get("default_guest") or "亲朋好友"
    frags = [(pg, _inline_images(_neutral_guest(fr, default))) for pg, fr in frags]
    title = c.get("share_title") or f"{c.get('host') or (spec.get('brand') or {}).get('name') or ''} {c.get('title') or '邀请函'}"
    title = re.sub(r"\s+", " ", title.replace("**", "")).strip()

    # wire the buttons: real hrefs work even with scripts off
    ics = ics_text(c, title)
    hrefs = {"nav": nav_url(c), "ics": ("data:text/calendar;charset=utf-8," + urllib.parse.quote(ics)) if ics else "#"}
    copy_text = " ".join(x for x in (_real(c.get("venue")), _real(c.get("address"))) if x)

    def wire(fr):
        def rep(m):
            tag, action = m.group(0), m.group(1)
            if action in hrefs:
                tag = re.sub(r'href="[^"]*"', f'href="{_html.escape(hrefs[action], quote=True)}"', tag)
            if action == "ics":
                tag = tag.replace("<a ", '<a download="invitation.ics" ', 1)
            if action == "copy":
                tag = tag.replace("<a ", f'<a data-copy="{_html.escape(copy_text, quote=True)}" ', 1)
            if action == "nav":
                tag = tag.replace("<a ", '<a rel="noopener" ', 1)
            return tag
        return re.sub(r'<a class="btn[^"]*" data-action="([a-z]+)"[^>]*>', rep, fr)
    frags = [(pg, wire(fr)) for pg, fr in frags]

    # fonts: only the characters on the page, the guest names and the script's messages
    guests = [g if isinstance(g, str) else (g or {}).get("guest", "") for g in (item.get("batch") or [])]
    text = "".join(_text_of(fr) for _, fr in frags) + "".join(guests) + UI_TEXT + title
    dfont, bfont = direction["display"], direction["body"]
    uses = {}
    uses.setdefault(dfont["font"], set()).update({dfont.get("weight", 700)})
    uses.setdefault(bfont["font"], set()).update({bfont.get("weight", 400), 700})
    font_css, font_bytes, notes = embed_fonts(uses, text)

    ctx = Ctx({"type": "h5page", "content": c, "art": item.get("art") or {}}, spec.get("brand") or {}, direction, canvas("h5"), {})
    css = base_css(ctx, font_css)
    t = direction["tokens"]
    css += f"""
html,body{{width:100%;height:100%;overflow:hidden;background:{t['bg']}}}
main.h5{{height:100vh;height:100svh;overflow-y:auto;overflow-x:hidden;scroll-snap-type:y proximity;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}}
.scr{{position:relative;min-height:100vh;min-height:100svh;display:flex;justify-content:center;scroll-snap-align:start;background:{t['bg']};overflow:hidden}}
.stage{{width:390px;flex:none}}
.canvas{{width:390px;height:auto;min-height:var(--sh,844px)}}
.h5col{{min-height:var(--sh,844px)}}
[data-fit]{{overflow:visible}}
.btn{{cursor:pointer;transition:transform .15s ease, filter .15s ease}}
.btn:active{{transform:scale(.97);filter:brightness(.95)}}
html.anim .rv{{opacity:0;transform:translateY(14px);transition:opacity .7s ease,transform .7s ease}}
html.anim .scr.in .rv{{opacity:1;transform:none}}
.hint svg{{animation:bob 1.6s ease-in-out infinite}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(6px)}}}}
.dots{{position:fixed;right:max(4px,calc(50% - 240px - 34px));top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:2px;z-index:60}}
.dots button{{width:22px;height:22px;border:0;background:transparent;display:flex;align-items:center;justify-content:center;padding:0;cursor:pointer}}
.dots button::after{{content:"";width:6px;height:6px;border-radius:50%;background:{t['accent']};opacity:.35;transition:all .3s}}
.dots button.on::after{{opacity:1;height:14px;border-radius:3px}}
.toast{{position:fixed;left:50%;bottom:calc(28px + env(safe-area-inset-bottom));transform:translate(-50%,20px);max-width:84vw;padding:10px 16px;border-radius:10px;
  background:rgba(0,0,0,.78);color:#fff;font-size:14px;line-height:1.5;opacity:0;pointer-events:none;transition:all .3s;z-index:70;text-align:center}}
.toast.show{{opacity:1;transform:translate(-50%,0)}}
.music{{position:fixed;right:12px;top:calc(12px + env(safe-area-inset-top));width:44px;height:44px;border-radius:50%;border:1px solid {t['accent']};
  background:{t['surface']};color:{t['accent']};display:flex;align-items:center;justify-content:center;z-index:60;cursor:pointer}}
.music svg{{width:20px;height:20px}}
.music.on svg{{animation:spin 4s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@media (prefers-reduced-motion: reduce){{.hint svg,.music.on svg{{animation:none}}}}
"""
    music = ""
    mpath = c.get("music")
    if mpath:
        src = Path(mpath) if Path(mpath).is_absolute() else (base / mpath)
        if src.exists():
            (out / "h5").mkdir(parents=True, exist_ok=True)
            shutil.copy(src, out / "h5" / f"{item['id']}-music{src.suffix}")
            music = (f'<audio src="{item["id"]}-music{src.suffix}" loop preload="auto"></audio>'
                     f'<button class="music" aria-label="音乐"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                     f'<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg></button>')
    start, _, tz = when_of(c)
    start_ms = "null"
    if start:
        try:
            from zoneinfo import ZoneInfo
            start_ms = str(int(start.replace(tzinfo=ZoneInfo(tz)).timestamp() * 1000))
        except Exception:  # noqa: BLE001
            start_ms = str(int(start.replace(tzinfo=dt.timezone(dt.timedelta(hours=8))).timestamp() * 1000))
    secs = "".join(f'<section class="scr" data-i="{i}" data-page="{pg}"><div class="stage"><div class="canvas">{fr}</div></div></section>'
                   for i, (pg, fr) in enumerate(frags))
    dots = "".join(f'<button aria-label="第 {i + 1} 屏"></button>' for i in range(len(frags)))
    desc = c.get("share_desc") or " ".join(x for x in (c.get("rsvp"), c.get("venue")) if x)
    doc = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta name="generator" content="luobo-design h5">
<style>{css}</style></head>
<body><main class="h5">{secs}</main>
<nav class="dots" aria-label="翻页">{dots}</nav>{music}<div class="toast" role="status" aria-live="polite"></div>
<script>window.__START={start_ms};window.__AFTER={json.dumps(c.get("after_label") or "已经举行，感谢您的祝福", ensure_ascii=False)};</script>
<script>{JS}</script></body></html>"""
    (out / "h5").mkdir(parents=True, exist_ok=True)
    path = out / "h5" / f"{item['id']}.html"
    path.write_text(doc, encoding="utf-8")

    # one link per guest
    links = []
    if guests:
        url = (item.get("publish_url") or "").strip()
        basename = url if url else f"{item['id']}.html"
        md = [f"# {title} 专属链接\n",
              ("把下面的链接分别发给每位宾客，打开后会写上对方的称呼。\n" if url else
               f"还没有填网址（item.publish_url），下面先用文件名代替。把 {item['id']}.html 放到网上以后，把文件名换成真正的网址。\n")]
        for g in guests:
            link = f"{basename}?to={urllib.parse.quote(g)}"
            links.append({"guest": g, "url": link})
            md.append(f"- {g}：{link}")
        (out / "h5" / f"{item['id']}-links.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return path, {"bytes": path.stat().st_size, "font_bytes": font_bytes, "font_notes": notes, "links": links,
                  "nav": hrefs["nav"], "has_ics": bool(ics)}


# ------------------------------------------------------------------ QA on real phone sizes
QA_JS = """() => {
  const out = {overflowX: document.documentElement.scrollWidth > innerWidth + 1 || document.querySelector('main').scrollWidth > innerWidth + 1,
               btns: [], tpl: Array.from(document.querySelectorAll('[data-tpl] .t')).map(e => e.textContent)};
  document.querySelectorAll('.btn').forEach(b => { const r = b.getBoundingClientRect();
    out.btns.push({text: b.innerText.trim(), action: b.dataset.action, href: b.getAttribute('href'), w: r.width, h: r.height}); });
  const cd = document.querySelector('[data-countdown]'); out.countdown = cd ? cd.innerText.replace(/\\s+/g, ' ') : null;
  return out;
}"""


def qa(path, item_id):
    from playwright.sync_api import sync_playwright
    errs, warns, shots = [], [], []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--allow-file-access-from-files"])
        for vw, vh, name in ((390, 844, "iPhone 14"), (375, 667, "iPhone SE"), (414, 896, "大屏安卓"), (1280, 800, "电脑")):
            pg = b.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=2 if vw < 500 else 1,
                            is_mobile=vw < 500, has_touch=vw < 500)
            problems = []
            pg.on("pageerror", lambda e, pr=problems: pr.append(str(e)))
            pg.on("console", lambda m, pr=problems: pr.append(m.text) if m.type == "error" else None)
            pg.goto(path.as_uri() + "?to=" + urllib.parse.quote("测试宾客"))
            pg.wait_for_timeout(900)
            r = pg.evaluate(QA_JS)
            for pr in problems:
                errs.append(f"{name}：脚本报错 {pr}")
            if r["overflowX"]:
                errs.append(f"{name}：页面能左右滑动，有东西超出了屏幕宽度")
            if vw < 500:
                for bt in r["btns"]:
                    if bt["h"] < 43.5 or bt["w"] < 43.5:
                        warns.append(f"{name}：按钮「{bt['text']}」只有 {bt['w']:.0f}x{bt['h']:.0f}，手指不好点（至少 44x44）")
            if not any("测试宾客" in x for x in r["tpl"]):
                errs.append(f"{name}：链接里的 ?to= 称呼没有显示出来")
            if vw == 390:
                for bt in r["btns"]:
                    if bt["href"] in ("#", "", None) and bt["action"] not in ("copy",):
                        warns.append(f"按钮「{bt['text']}」还没有链接（{bt['action']}）")
                copy_btn = pg.locator('.btn[data-action="copy"]')
                if copy_btn.count():
                    copy_btn.first.scroll_into_view_if_needed()
                    copy_btn.first.click()
                    pg.wait_for_timeout(300)
                    msg = pg.evaluate("() => document.querySelector('.toast').textContent")
                    if not msg:
                        errs.append("点「复制地址」没有任何反馈")
                # long preview: every screen one after another
                pg.add_style_tag(content="main.h5{height:auto!important;overflow:visible!important}html,body{height:auto!important;overflow:visible!important}"
                                         "html.anim .rv{opacity:1!important;transform:none!important;transition:none!important}.toast{display:none}.dots{display:none}")
                pg.wait_for_timeout(200)
                shot = path.parent / f"{item_id}-preview.png"
                pg.screenshot(path=str(shot), full_page=True)
                shots.append(str(shot))
            pg.close()
        b.close()
    return errs, sorted(set(warns)), shots


def build(spec_path, out_dir=None, run_qa=True):
    spec_path = Path(spec_path).resolve()
    raw = load_json(spec_path)
    if not any(it.get("type") == "h5" for it in raw.get("items") or []):
        return []
    out = Path(out_dir or spec_path.parent / "out").resolve()
    direction = resolve_tokens(spec_brand(raw))
    results = []
    for it in raw.get("items") or []:
        if it.get("type") != "h5":
            continue
        filled = dict(it)
        filled["content"] = render.fill_facts(it.get("content") or {}, raw.get("facts") or {})
        path, info = assemble(raw, filled, out, direction, spec_path.parent)
        e, w, shots = qa(path, it["id"]) if run_qa else ([], [], [])
        if info["bytes"] > 2_500_000:
            w.append(f"文件有 {info['bytes'] / 1e6:.1f} MB，手机流量下打开会慢")
        if info["font_notes"]:
            w += [f"字体：{n}" for n in info["font_notes"]]
        days = countdown_days(filled["content"])
        results.append({"name": f"h5:{it['id']}", "html": str(path), "png": shots[0] if shots else None, "errors": e, "warnings": w,
                        "todo": [], "info": {**info, "countdown_days_today": days}})
        print(f"  h5/{path.name}  {info['bytes'] / 1024:.0f} KB（字体 {info['font_bytes'] / 1024:.0f} KB）"
              f"{'，' + str(len(info['links'])) + ' 个专属链接' if info['links'] else ''}")
    (out / "h5").mkdir(parents=True, exist_ok=True)
    save_json(out / "h5" / "h5_qa.json", {"files": results})
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--no-qa", action="store_true")
    a = ap.parse_args()
    res = build(a.spec, a.out, not a.no_qa)
    bad = sum(len(r["errors"]) for r in res)
    for r in res:
        for e in r["errors"]:
            print("  ERROR", e)
        for w in r["warnings"]:
            print("  warn ", w)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
