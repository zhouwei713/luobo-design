"""Concept posters: the agent composes the page itself, the script keeps the rules.

A preset layout can only ever look like a preset. For the one idea a poster is built on (a clock made of
the five tools, a receipt, a boarding pass, a giant one-half), the agent writes the composition as an HTML
fragment per size, and this module turns it into a normal page:

- the canvas, the direction's colours as CSS variables (--bg --surface --ink --muted --accent --accent2
  --accent-text --on-accent --line), --u (1% of the short side), --safe, and font classes .f-<font id>
- every element with data-field="headline" (or "sub", "details.0.v", "offer.big", any content path) gets that
  copy from spec.json, so the copy stays editable in the studio page and the checks read it like any other text
- every text element becomes a checked text node: class t, data-role (from the field, or given), data-c and
  data-on (token names; default ink on bg), an id
- data-fit="MAX,MIN" (px) shrinks the type until it fits its box, like the preset layouts do
- <img data-field="art.image"> gets the item's picture
- data-art marks a shape or a giant glyph that is the picture (the "1" and "2" of a one-half): it is checked as
  art, not as text, so it may run past the margin and under other type. Anything that carries information
  (a price, a date, a name) is never data-art

The fragment is chosen per size: item.html can be one path, or {"portrait": path, "square": path, "a4": path}
(size id first, then orientation, then "default"). A size without a fragment falls back to item.fallback
(a normal layout name; default "jing" in the jing directions, "type-hero" otherwise), so every size still
comes out. Scripts and event handlers are removed from fragments.
"""
import json
import re
from pathlib import Path

from fonts import stack
from layouts import Ctx, esc, page, rich

ROLE_OF = {"headline": "headline", "big_title": "headline", "big_number": "headline", "sub": "sub", "kicker": "label",
           "date_line": "label", "cta": "body", "note": "caption", "credit": "credit"}

FILL_JS = """
<script>
(function(){
  const F = window.__fields || {};
  const ROLE = window.__roles || {};
  let n = 0;
  document.querySelectorAll('#canvas [data-field]').forEach(el => {
    const path = el.dataset.field;
    if (el.tagName === 'IMG') { if (F[path]) el.src = F[path]; return; }
    if (path in F) el.innerHTML = F[path];
    if (!el.dataset.role) el.dataset.role = ROLE[path.split('.')[0]] || (path.startsWith('offer') ? 'badge' : 'body');
  });
  // every element that holds its own text is a checked text node
  document.querySelectorAll('#canvas *').forEach(el => {
    if (['SCRIPT','STYLE','SVG','svg','IMG'].includes(el.tagName) || el.closest('svg')) return;
    if (el.closest('[data-art]')) return;  // a giant glyph used as a picture: checked as art, not as text
    const own = Array.from(el.childNodes).some(c => c.nodeType === 3 && c.data.trim());
    if (!own && !el.dataset.role) return;
    if (el.closest('.t') && el.closest('.t') !== el) return;
    el.classList.add('t');
    if (!el.dataset.role) el.dataset.role = 'body';
    el.classList.add(el.dataset.role);
    if (!el.dataset.c) el.dataset.c = 'ink';
    if (!el.dataset.on) el.dataset.on = 'bg';
    if (!el.id) el.id = 'cx' + (++n);
    if (/【[^】]*】/.test(el.textContent)) el.dataset.placeholder = '1';
  });
  document.querySelectorAll('#canvas [data-fit]').forEach(el => {
    const v = el.dataset.fit;
    if (v && v.includes(',')) { const [mx, mn] = v.split(',').map(parseFloat);
      el.dataset.fit = '1'; el.dataset.max = mx; el.dataset.min = mn; el.style.fontSize = mx + 'px'; }
  });
})();
</script>
"""

SCRIPT = re.compile(r"<script\b.*?</script\s*>", re.I | re.S)
ON_ATTR = re.compile(r"\son[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
TAG_SECTION = re.compile(r"<(?:template|section)\b[^>]*data-size=[\"']([^\"']+)[\"'][^>]*>(.*?)</(?:template|section)\s*>", re.I | re.S)


def clean(html):
    return ON_ATTR.sub("", SCRIPT.sub("", html))


def pick_fragment(item, cv):
    """(source path, html) for this size, or (None, None) when the item has no fragment for it."""
    src = item.get("html")
    if not src:
        return None, None
    if isinstance(src, dict):
        path = src.get(cv["id"]) or src.get(cv["orient"]) or src.get("default")
    else:
        path = src
    if not path:
        return None, None
    p = Path(path)
    if not p.exists():
        return str(p), None
    text = p.read_text(encoding="utf-8")
    secs = {k.strip(): v for k, v in TAG_SECTION.findall(text)}
    if secs:  # one file with <section data-size="portrait">…</section> blocks
        text = secs.get(cv["id"]) or secs.get(cv["orient"]) or secs.get("default")
        if text is None:
            return str(p), None
    return str(p), clean(text)


def field_map(item):
    """Every copy path of the item -> its HTML (with **accent** marks), plus art.image."""
    import render
    out = {path: rich(txt) for path, txt in render.content_fields(item.get("content") or {})}
    img = (item.get("art") or {}).get("image")
    if img:
        out["art.image"] = img
    return out


def css_vars(ctx, fonts):
    t, u = ctx.t, ctx.u
    names = {"bg": "bg", "surface": "surface", "ink": "ink", "muted": "muted", "accent": "accent", "accent2": "accent2",
             "accent-text": "accent_text", "on-accent": "on_accent", "line": "line", "soft": "soft"}
    vs = ";".join(f"--{k}:{t[v]}" for k, v in names.items() if v in t)
    cls = "".join(f".f-{f}{{font-family:{stack(f)}}}" for f in sorted(fonts))
    return (f":root{{{vs};--u:{u:.3f}px;--safe:{ctx.safe:.1f}px;--W:{ctx.W:.0f}px;--H:{ctx.H:.0f}px}}"
            f".canvas{{background:var(--bg)}}{cls}"
            f".f-display{{font-family:{stack(ctx.d['display']['font'])};font-weight:{ctx.d['display'].get('weight', 700)}}}"
            f".f-body{{font-family:{stack(ctx.d['body']['font'])}}}"
            ".pattern{display:none}"
            # an accent word inside text that already sits on the accent (or on ink) must switch colour or it vanishes
            '[data-on="accent"] em.hl{color:var(--bg)}[data-on="ink"] em.hl{color:var(--accent)}'
            '[data-on="accent2"] em.hl{color:var(--ink)}')


def fonts_of(item, direction):
    return set(item.get("fonts") or []) | {direction["display"]["font"], direction["body"]["font"]}


def poster_concept(ctx, fonts_css):
    item = ctx.item
    src, frag = pick_fragment(item, ctx.cv)
    if frag is None:
        # no composition written for this size: a normal layout takes over so the size still ships
        from layouts import BUILDERS
        fb = item.get("fallback") or ("jing" if ctx.d.get("system") else "type-hero")
        one = dict(item, layout=fb, _concept_fallback=src or True)
        return BUILDERS[("poster", fb)](Ctx(one, ctx.brand, ctx.d, ctx.cv, ctx.facts), fonts_css)
    roles = dict(ROLE_OF)
    data = (f"<script>window.__fields={json.dumps(field_map(item), ensure_ascii=False)};"
            f"window.__roles={json.dumps(roles)};</script>")
    body = f'<div class="concept" data-src="{esc(src)}" style="position:absolute;inset:0">{frag}</div>{data}{FILL_JS}'
    return page(ctx, fonts_css, body, css_vars(ctx, fonts_of(item, ctx.d)))


def register(builders, layouts):
    layouts["poster"].append("concept")
    builders[("poster", "concept")] = poster_concept

