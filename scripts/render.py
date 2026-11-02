"""Render every item x size of a design spec to PNG (and PDF for print sizes).

  python render.py spec.json [--out DIR] [--only ITEM_ID] [--hd]

Writes DIR/<item>-<size>.png, print sizes also .pdf, the HTML sources under DIR/src/,
and DIR/render_report.json (fit results and every text box) for check.py.
"""
import argparse
import copy
import math
import re
import sys
import time
from pathlib import Path

import layouts
from common import canvas, load_json, resolve_tokens, spec_brand, save_json
from fonts import font_css


def fill_facts(obj, facts):
    """Replace {fact} in copy with the fact; a missing fact becomes a visible 【placeholder】."""
    labels = {"phone": "电话", "address": "地址", "date": "日期", "time": "时间", "hours": "营业时间",
              "wechat": "微信", "price": "价格", "name": "名称"}
    if isinstance(obj, str):
        def rep(m):
            k = m.group(1)
            v = facts.get(k)
            if v in (None, ""):
                return f"【{labels.get(k, k)}】"
            return str(v)
        return re.sub(r"\{([a-z_][a-z0-9_]*)\}", rep, obj)
    if isinstance(obj, list):
        return [fill_facts(x, facts) for x in obj]
    if isinstance(obj, dict):
        return {k: fill_facts(v, facts) for k, v in obj.items()}
    return obj


def _is_tall(p):
    try:
        from PIL import Image
        with Image.open(p) as im:
            return im.height > im.width * 1.4
    except Exception:  # noqa: BLE001
        return False


def to_uri(p, base):
    if not p or re.match(r"^(https?|data|file):", str(p)):
        return p
    q = Path(p)
    if not q.is_absolute():
        q = (base / q).resolve()
    return q.as_uri() if q.exists() else None


def expand(items):
    """batch -> one item per person (certificates, invitations); cards -> front and back."""
    out = []
    for it in items:
        if it["type"] == "h5":  # one phone page = one screen per render; h5.py stitches them together
            from layouts_h5 import pages_for
            c = it.get("content") or {}
            b = it.get("batch") or []
            first = b[0] if b else None
            guest = (first if isinstance(first, str) else (first or {}).get("guest")) if first else None
            for n, pg in enumerate(it.get("_h5_pages") or pages_for(it), 1):
                one = copy.deepcopy(it)
                one.pop("batch", None)
                one.update({"type": "h5page", "layout": pg, "sizes": ["h5"], "id": f"{it['id']}-{n}-{pg}",
                            "_h5_of": it["id"], "_page": pg, "_uid0": n * 1000})
                if guest and not c.get("guest"):
                    one["content"]["guest"] = guest
                out.append(one)
            continue
        batch = it.get("batch") or (it.get("content") or {}).get("recipients")
        if batch:
            key = {"invitation": "guest", "certificate": "recipient"}.get(it["type"])
            if it["type"] == "tablecard":
                key = "name" if it.get("layout") == "tent" else "number"
            key = key or "recipient"
            for n, entry in enumerate(batch, 1):
                e = {key: entry} if isinstance(entry, str) else dict(entry)
                one = copy.deepcopy(it)
                one.pop("batch", None)
                one["content"].pop("recipients", None)
                one["content"].update(e)
                if "number" in one["content"]:
                    one["content"]["number"] = str(one["content"]["number"]).replace("{n}", f"{n:03d}")
                one["id"] = f"{it['id']}-{n:02d}"
                one["_batch_of"] = it["id"]
                out.append(one)
            continue
        num = (it.get("content") or {}).get("number")
        if num and "{n}" in str(num):
            it = copy.deepcopy(it)
            it["content"]["number"] = str(num).replace("{n}", "001")
        if it["type"] == "card" and not it.get("_side"):
            for side in ("front", "back"):
                one = copy.deepcopy(it)
                one["_side"] = side
                one["id"] = f"{it['id']}-{side}"
                out.append(one)
            continue
        out.append(it)
    return out


def prepare(spec, base):
    spec = copy.deepcopy(spec)
    spec["items"] = expand(spec.get("items") or [])
    facts = spec.get("facts") or {}
    brand = spec.get("brand") or {}
    if brand.get("logo"):
        brand["logo"] = to_uri(brand["logo"], base)
    from common import festival_of
    fest = festival_of(spec.get("festival"))
    for it in spec.get("items", []):
        it["content"] = fill_facts(it.get("content") or {}, facts)
        if it.get("size_copy"):
            it["size_copy"] = fill_facts(it["size_copy"], facts)
        if fest and fest.get("motifs"):
            a = it.setdefault("art", {})
            if not a.get("image") and not a.get("motif"):
                a["motif"] = fest["motifs"][0]  # no picture chosen: the festival's own motif
        a = it.get("art") or {}
        if a.get("image"):
            a["image"] = to_uri(a["image"], base)
        ph = it["content"].get("photos")
        if isinstance(ph, list):  # note covers: the user's own photos for grids and comparisons
            it["content"]["photos"] = [(dict(x, src=to_uri(x["src"], base)) if isinstance(x, dict) and x.get("src")
                                        else (to_uri(x, base) if isinstance(x, str) and x else x)) for x in ph]
        q = it["content"].get("qr")
        if isinstance(q, dict) and q.get("src"):
            q["src"] = to_uri(q["src"], base)
        elif q is None and facts.get("qr") and it.get("qr", True):
            pass
    return spec


REPORT_JS = """() => {
  const cv = document.getElementById('canvas').getBoundingClientRect();
  const texts = Array.from(document.querySelectorAll('.t')).map(el => {
    const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return {id: el.id, role: el.dataset.role, c: el.dataset.c, on: el.dataset.on, text: el.innerText,
            fs: parseFloat(cs.fontSize), weight: cs.fontWeight, family: cs.fontFamily,
            x: r.left - cv.left, y: r.top - cv.top, w: r.width, h: r.height,
            placeholder: !!el.dataset.placeholder, grp: (el.closest('[data-grp]') || {dataset: {}}).dataset.grp || null};
  });
  // characters on the last line of wrapped text: one lonely character reads as a mistake in Chinese
  for (const t of texts) {
    if (!['headline', 'sub', 'body', 'badge'].includes(t.role)) continue;
    const el = document.getElementById(t.id); if (!el) continue;
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const tops = [];
    let n; while ((n = walker.nextNode())) {
      for (let i = 0; i < n.length; i++) {
        const ch = n.data[i]; if (/\\s/.test(ch)) continue;
        const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
        const b = r.getBoundingClientRect(); if (b.width === 0) continue;
        tops.push([Math.round(b.top), ch]);
      }
    }
    const lines = {}; for (const [y, ch] of tops) { const k = Object.keys(lines).find(v => Math.abs(v - y) < t.fs * 0.5); (lines[k ?? y] = lines[k ?? y] || []).push(ch); }
    const keys = Object.keys(lines).map(Number).sort((a, b) => a - b);
    t.lines = keys.length; t.last_line = keys.length ? lines[keys[keys.length - 1]].join('') : '';
  }
  const imgs = Array.from(document.querySelectorAll('img')).map(el => ({src: el.getAttribute('src'), ok: el.complete && el.naturalWidth > 0}));
  // pictures on the page (photos, illustrations, art), outermost only, for the empty-band and spacing checks
  const area = cv.width * cv.height;
  const vis = Array.from(document.querySelectorAll('#canvas img, #canvas .art, #canvas svg, #canvas [data-art]'))
    .filter(el => !el.closest('.t') && !el.closest('.pattern'));
  const outer = vis.filter(el => !vis.some(o => o !== el && o.contains(el)));
  const blocks = outer.map(el => { const r = el.getBoundingClientRect();
    const x = Math.max(r.left, cv.left), y = Math.max(r.top, cv.top), x2 = Math.min(r.right, cv.right), y2 = Math.min(r.bottom, cv.bottom);
    return {kind: el.tagName.toLowerCase() === 'img' ? 'img' : 'art', x: x - cv.left, y: y - cv.top, w: Math.max(0, x2 - x), h: Math.max(0, y2 - y)}; })
    .filter(b => b.w * b.h > area * 0.004);
  return {fit: window.__fit || [], texts, imgs, blocks, w: cv.width, h: cv.height};
}"""


SKIP_KEYS = {"photos", "qr", "map", "music", "rsvp_url", "color", "colors", "src", "image", "font", "align", "title_pos",
             "split", "app", "series"}


def content_fields(obj, path=""):
    """Every piece of copy in an item's content as (path, text): what the studio page lets people retype."""
    out = []
    if isinstance(obj, str):
        if obj.strip() and not re.match(r"^(https?|data|file):|.*\.(png|jpe?g|webp|svg|gif)$", obj.strip(), re.I):
            out.append((path, obj))
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            out += content_fields(x, f"{path}.{i}" if path else str(i))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in SKIP_KEYS or k.startswith("_"):
                continue
            out += content_fields(v, f"{path}.{k}" if path else k)
    return out


FIELDS_JS = """(targets) => {
  const norm = s => (s || '').replace(/[\\s\\u200b\\u00ad]+/g, '');
  const cv = document.getElementById('canvas'); const c = cv.getBoundingClientRect();
  const els = Array.from(cv.querySelectorAll('*')).filter(el => {
    const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return false;
    const cs = getComputedStyle(el); return cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity || 1) > 0.05;
  }).map(el => ({el, t: norm(el.textContent)}));
  const out = [];
  for (const tg of targets) {
    const want = norm(tg.text); if (!want) continue;
    let hits = els.filter(e => e.t === want);
    if (!hits.length && want.length >= 4) {  // the copy may sit inside a longer line ("立减20元" in "新客券 立减20元")
      hits = els.filter(e => e.t.includes(want) && want.length / e.t.length >= 0.5);
      const best = Math.min(...hits.map(e => e.t.length)); hits = hits.filter(e => e.t.length === best);
    }
    hits = hits.filter(h => !hits.some(o => o !== h && h.el.contains(o.el)));  // innermost only
    if (!hits.length) continue;
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const h of hits) { const r = h.el.getBoundingClientRect(); x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); }
    out.push({path: tg.path, x: x0 - c.left, y: y0 - c.top, w: x1 - x0, h: y1 - y0});
  }
  return out;
}"""


def for_size(it, size, cv):
    """Copy written for one size (size_copy) replaces the shared copy on that size only.
    Keys: a size id ("square") or an orientation ("landscape"); the size id wins. Returns (item, key used)."""
    sc = it.get("size_copy") or {}
    sel = size if size in sc else (cv.get("orient") if cv.get("orient") in sc else None)
    if not sel:
        return it, None
    one = copy.deepcopy(it)
    one["content"] = {**(one.get("content") or {}), **copy.deepcopy(sc[sel])}
    one["_size_copy"] = sel
    return one, sel


def raw_id(it):
    """The id of the item as written in spec.json (batch copies, card sides and h5 screens point back to it)."""
    if it.get("_batch_of"):
        return it["_batch_of"]
    if it.get("_h5_of"):
        return it["_h5_of"]
    if it.get("_side"):
        return re.sub(r"-(front|back)$", "", it["id"])
    return it["id"]


def write_logos(browser, logos, folder):
    """SVG files (outlined, no fonts needed) plus transparent PNGs at 1200 px wide."""
    folder.mkdir(parents=True, exist_ok=True)
    pg = browser.new_page(viewport={"width": 1400, "height": 1400})
    for key, lg in logos.items():
        if key.startswith("_"):
            continue
        for variant in ("svg", "reversed", "icon"):
            svg = lg.get(variant)
            if not svg:
                continue
            stem = f"{key}-{lg['kind']}" + ("" if variant == "svg" else f"-{variant}")
            (folder / f"{stem}.svg").write_text(svg, encoding="utf-8")
            styled = svg.replace("<svg ", '<svg style="width:100%;height:auto;display:block" ', 1)
            pg.set_content('<html><body style="margin:0;background:transparent">'
                           f'<div id="l" style="display:inline-block;width:1200px">{styled}</div></body></html>')
            pg.locator("#l").screenshot(path=str(folder / f"{stem}.png"), omit_background=True)
    pg.close()
    if not logos.get("_outlined"):
        print("  NOTE some logo text could not be outlined (font or brotli missing); those SVGs use live text")


def render(spec_path, out_dir=None, only=None, hd=False):
    spec_path = Path(spec_path).resolve()
    base = spec_path.parent
    raw = load_json(spec_path)
    spec = prepare(raw, base)
    out = Path(out_dir or base / "out").resolve()
    (out / "src").mkdir(parents=True, exist_ok=True)
    for it in spec.get("items", []):  # screenshots get their frame here, once; layouts then treat them as pictures
        a = it.get("art") or {}
        if a.get("screenshot") and not a.get("image"):
            src = Path(a["screenshot"]) if Path(a["screenshot"]).is_absolute() else base / a["screenshot"]
            if src.exists():
                import shotframe
                kind = a.get("frame") or ("phone" if _is_tall(src) else "browser")
                framed = shotframe.framed_path(src, out / "assets", kind, dark=bool(a.get("frame_dark")))
                from PIL import Image
                with Image.open(framed) as fim:
                    ar = fim.width / fim.height
                a.update({"image": framed.as_uri(), "image_fit": "contain", "_shot": kind, "_shot_ar": round(ar, 3)})
            else:
                print(f"  ! {it['id']}: screenshot not found: {a['screenshot']}", file=sys.stderr)
    direction = resolve_tokens(spec_brand(spec))
    fonts_needed = {direction["display"]["font"], direction["body"]["font"]}
    from layouts_artthemes import FONTS as THEME_FONTS  # art themes bring their own title fonts
    fonts_needed |= {THEME_FONTS[a["style"]] for a in ((it.get("art") or {}) for it in spec.get("items", [])) if a.get("style") in THEME_FONTS}
    from layouts_trend import LAYOUT_FONTS  # trend layouts mix several display faces
    from layouts_xhs import LAYOUT_FONTS as XHS_FONTS  # note covers: chunky outlined type, hand lettering
    for it in spec.get("items", []):
        table = XHS_FONTS if it.get("type") == "xhs" else LAYOUT_FONTS
        fonts_needed |= set(table.get(it.get("layout") or ("photo" if it.get("type") == "xhs" else ""), ()))
    css, fstatus = font_css(fonts_needed)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright is required: pip install playwright && python -m playwright install chromium")
    report = {"spec": str(spec_path), "direction": direction["id"], "tokens": direction["tokens"],
              "fonts": fstatus, "color_notes": direction.get("color_notes") or [], "renders": []}
    jobs = []
    for it in spec.get("items", []):
        if only and only not in (it["id"], raw_id(it)):
            continue
        for size in it.get("sizes") or ["portrait"]:
            jobs.append((it, size))
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--allow-file-access-from-files", "--font-render-hinting=none"])
        for it0, size in jobs:
            cv = canvas(size)
            it, sel = for_size(it0, size, cv)
            html = layouts.build(it, spec.get("brand") or {}, direction, cv, spec.get("facts") or {}, css)
            name = f"{it['id']}-{size}"
            src = out / "src" / f"{name}.html"
            src.write_text(html, encoding="utf-8")
            if it.get("_logos"):
                write_logos(browser, it["_logos"], out / "logos")
            scale = cv["scale"] * (2 if (hd and cv["kind"] == "screen") or cv["id"] == "h5" else 1)
            vw, vh = math.ceil(cv["w"]), math.ceil(cv["h"])
            page = browser.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=scale)
            page.goto(src.as_uri())
            t0 = time.time()
            try:
                page.wait_for_function("window.__fitDone === true", timeout=60000)
            except Exception:  # noqa: BLE001
                print(f"  ! {name}: fit script did not finish", file=sys.stderr)
            page.wait_for_timeout(150)
            rep = page.evaluate(REPORT_JS)
            try:
                own = set((it0.get("size_copy") or {}).get(sel) or {}) if sel else set()
                rep["fields"] = page.evaluate(FIELDS_JS, [{"path": (f"@{sel}.{pth}" if pth.split(".")[0] in own else pth),
                                                           "text": txt.replace("**", "")}
                                                          for pth, txt in content_fields(it.get("content") or {})])
            except Exception:  # noqa: BLE001  the studio page just loses click-to-edit on this one
                rep["fields"] = []
            if it["type"] == "h5page":  # keep the fitted markup: h5.py stitches these screens together as they are
                frozen = page.evaluate("() => document.getElementById('canvas').innerHTML")
                (out / "src" / f"{name}.frozen.html").write_text(frozen, encoding="utf-8")
            png = out / f"{name}.png"
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": cv["w"], "height": cv["h"]})
            entry = {"item": it["id"], "raw_item": raw_id(it), "size_copy": sel, "type": it["type"], "layout": it.get("layout"), "size": size,
                     "png": str(png), "html": str(src), "canvas": {k: cv[k] for k in ("w", "h", "kind", "safe_px", "u", "min_px", "orient", "bleed_px")},
                     **rep}
            if cv["kind"] == "print":
                pdf = out / f"{name}.pdf"
                page.pdf(path=str(pdf), width=f"{cv['page_mm'][0]}mm", height=f"{cv['page_mm'][1]}mm",
                         print_background=True, page_ranges="1")
                entry["pdf"] = str(pdf)
            report["renders"].append(entry)
            page.close()
            print(f"  {name}.png  {cv['w']:.0f}x{cv['h']:.0f}{' + pdf' if cv['kind'] == 'print' else ''}  ({time.time() - t0:.1f}s)")
        browser.close()
    prev = out / "render_report.json"
    if only and prev.exists():  # re-rendering one item: keep what the others reported last time
        try:
            old = load_json(prev)
            report["renders"] = [r for r in old.get("renders", []) if r.get("raw_item", r.get("item")) != only
                                 and r.get("item") != only] + report["renders"]
        except Exception:  # noqa: BLE001
            pass
    save_json(out / "render_report.json", report)
    return out, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--only")
    ap.add_argument("--hd", action="store_true", help="screen sizes at 2x")
    a = ap.parse_args()
    out, rep = render(a.spec, a.out, a.only, a.hd)
    bad = [k for k, v in rep["fonts"].items() if v.startswith("fallback")]
    if bad:
        print("NOTE fonts fell back to system fonts:", ", ".join(bad))
    print(f"rendered {len(rep['renders'])} files -> {out}")


if __name__ == "__main__":
    main()
