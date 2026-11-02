"""What the work looks like once it is posted: covers inside a note feed, posters inside a friends' feed.

  python preview.py spec.json [--out DIR]

Writes DIR/preview-feed.png (note covers at the size people actually see them, between other cards)
and DIR/preview-moments.png (posters as a single picture in a friends' feed post). Generic phone
screens drawn here, no app's logo or trade dress. Read them at 100%: a title you can't read here
won't be read in the app either.
"""
import argparse
import html
import json
import re
from pathlib import Path

from common import load_json, resolve_tokens, spec_brand

FONT = '"PingFang SC","Noto Sans CJK SC","Source Han Sans SC","Microsoft YaHei",sans-serif'
FILLERS = [  # neighbour cards: busy enough to compete for attention, with no readable text inside
    ("#E9D8C4", "#C9A27E", "周末去哪儿｜城郊小众露营地", "阿桃", "1.2万"),
    ("#CFE0E8", "#7FA7BC", "通勤穿搭一周不重样", "Mia", "8634"),
    ("#E8E0F0", "#A792C8", "租房改造 花了不到五百块", "小周同学", "2.3万"),
    ("#F3D9D9", "#D98C8C", "低脂晚餐 十分钟搞定", "厨房日记", "5120"),
    ("#DCE8D4", "#8FB57C", "新手养绿植别踩这几个坑", "植物君", "967"),
    ("#F1E6C8", "#CDAE5E", "第一次带爸妈出国玩", "旅行的猫", "3.4万"),
]


def clean(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def renders_by_item(out):
    rep = load_json(out / "render_report.json")
    by = {}
    for r in rep.get("renders", []):
        by.setdefault(r.get("raw_item") or r["item"], []).append(r)
    return by


def filler_card(i, wide):
    bg, fg, title, who, likes = FILLERS[i % len(FILLERS)]
    h = 230 if i % 3 == 0 else 190 if i % 3 == 1 else 250
    shapes = (f'<div style="position:absolute;left:18%;top:22%;width:64%;height:46%;border-radius:{"50%" if i % 2 else "14px"};background:{fg};opacity:.55"></div>'
              f'<div style="position:absolute;left:8%;bottom:10%;width:40%;height:14%;border-radius:8px;background:#fff;opacity:.5"></div>')
    return card_html(f'<div style="position:relative;width:100%;height:{h}px;background:{bg}">{shapes}</div>', title, who, likes, "#B9B2AA")


def card_html(img, title, who, likes, dot):
    return (f'<div class="card">{img}<div class="ct">{html.escape(title)}</div>'
            f'<div class="cm"><i style="background:{dot}"></i><span>{html.escape(who)}</span><b>♡ {likes}</b></div></div>')


PHONE_CSS = f"""
*{{box-sizing:border-box}} body{{margin:0;background:#E9E6E1;font-family:{FONT};-webkit-font-smoothing:antialiased}}
.wrap{{display:flex;gap:40px;padding:40px;align-items:flex-start}}
.phone{{width:390px;background:#fff;border-radius:36px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.18);border:10px solid #1F1D1B}}
.status{{height:34px;display:flex;justify-content:space-between;align-items:center;padding:0 22px;font-size:13px;font-weight:600;color:#222}}
.cap{{font-size:13px;color:#6F6862;margin:0 0 10px;line-height:1.5;max-width:390px}}
.cap b{{color:#26221E;font-size:15px;display:block;margin-bottom:2px}}
"""


def feed_page(items, brand_name, accent):
    """Two-column note feed; our covers sit in the first screen, the rest are neighbours."""
    cols = [[], []]
    ours = []
    for it, r in items:
        c = it.get("content") or {}
        img = f'<img src="{Path(r["png"]).as_uri()}" style="display:block;width:100%;height:auto">'
        ours.append(card_html(img, clean(c.get("title")) or clean(it.get("id")), clean(c.get("handle")) or brand_name, "2864", accent))
    slots = []
    fi = 0
    for n in range(max(6, len(ours) * 2 + 2)):
        if ours and n in (1, 2, 5, 6, 9, 10)[: len(ours)]:
            slots.append(ours.pop(0))
        else:
            slots.append(filler_card(fi, False))
            fi += 1
    slots += ours
    for n, s in enumerate(slots):
        cols[n % 2].append(s)
    body = "".join(f'<div class="col">{"".join(c)}</div>' for c in cols)
    css = PHONE_CSS + """
.top{display:flex;gap:18px;justify-content:center;align-items:center;height:40px;font-size:15px;color:#8A847E}
.top b{color:#222;font-weight:700;border-bottom:2px solid #222;padding-bottom:2px}
.search{margin:4px 14px 8px;height:30px;border-radius:15px;background:#F2F0ED}
.grid{display:flex;gap:6px;padding:0 6px 10px;background:#F6F5F3;align-items:flex-start}
.col{flex:1;display:flex;flex-direction:column;gap:6px;min-width:0}
.card{background:#fff;border-radius:6px;overflow:hidden;flex:none}
.ct{font-size:13px;line-height:1.35;color:#222;padding:7px 8px 4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.cm{display:flex;align-items:center;gap:5px;padding:0 8px 8px;font-size:11px;color:#8A847E}
.cm i{width:16px;height:16px;border-radius:50%;flex:none}
.cm span{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cm b{font-weight:400}
"""
    phone = (f'<div class="phone"><div class="status"><span>9:41</span><span>●●● ▮</span></div>'
             f'<div class="top"><span>关注</span><b>发现</b><span>附近</span></div><div class="search"></div>'
             f'<div class="grid">{body}</div></div>')
    note = '<p class="cap"><b>发出去在信息流里的样子</b>手机上按百分之百看：标题一眼读得出来、在左右的卡片里跳得出来，才算过关。</p>'
    return f"<html><head><meta charset='utf-8'><style>{css}</style></head><body><div class='wrap'><div>{note}{phone}</div></div></body></html>"


def moments_page(posts, brand_name, accent):
    css = PHONE_CSS + """
.bar{height:44px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:600;border-bottom:1px solid #EEE}
.post{display:flex;gap:10px;padding:14px 14px 12px;border-bottom:1px solid #F0F0F0}
.av{width:42px;height:42px;border-radius:6px;flex:none;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:18px}
.pb{flex:1;min-width:0}
.nm{color:#4A5C88;font-weight:600;font-size:15px;margin-bottom:3px}
.tx{font-size:15px;line-height:1.5;color:#222;margin-bottom:8px}
.pic{display:block;max-width:220px;max-height:220px;width:auto;height:auto}
.ft{display:flex;justify-content:space-between;font-size:12px;color:#A09A94;margin-top:8px}
.ft span:last-child{background:#F2F2F2;border-radius:4px;padding:0 8px;color:#4A5C88}
"""
    body = ""
    for n, (it, r, text) in enumerate(posts):
        name = brand_name or "我"
        body += (f'<div class="post"><div class="av" style="background:{accent}">{html.escape(name[:1])}</div><div class="pb">'
                 f'<div class="nm">{html.escape(name)}</div><div class="tx">{html.escape(text)}</div>'
                 f'<img class="pic" src="{Path(r["png"]).as_uri()}"><div class="ft"><span>{n * 2 + 1}小时前</span><span>··</span></div></div></div>')
    phone = (f'<div class="phone"><div class="status"><span>9:41</span><span>●●● ▮</span></div><div class="bar">朋友圈</div>'
             f'{body}<div style="height:30px"></div></div>')
    note = '<p class="cap"><b>发到朋友圈的样子</b>单张图在朋友圈里只有这么大，点开前大家只看得到这一眼。标题和主体要在这个尺寸下就看得清。</p>'
    return f"<html><head><meta charset='utf-8'><style>{css}</style></head><body><div class='wrap'><div>{note}{phone}</div></div></body></html>"


def shoot(page_html, path):
    from playwright.sync_api import sync_playwright
    tmp = path.with_suffix(".html")
    tmp.write_text(page_html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 520, "height": 900}, device_scale_factor=2)
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(300)
        pg.locator(".wrap").screenshot(path=str(path))
        b.close()
    tmp.unlink()


def build(spec_path, out_dir=None):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    out = Path(out_dir or spec_path.parent / "out")
    by = renders_by_item(out)
    brand = spec.get("brand") or {}
    try:
        accent = resolve_tokens(spec_brand(spec))["tokens"]["accent"]
    except SystemExit:
        accent = "#E8641E"
    made = []
    covers = []
    posts = []
    for it in spec.get("items", []):
        rs = by.get(it.get("id")) or []
        if not rs:
            continue
        if it.get("type") == "xhs":
            r = next((x for x in rs if x["size"] in ("xhs", "portrait")), rs[0])
            covers.append((it, r))
        elif it.get("type") == "poster":
            r = next((x for x in rs if x["size"] == "portrait"), None) or next((x for x in rs if x["size"] == "square"), None)
            if r:
                c = it.get("content") or {}
                ai = Path(r["png"].replace(".png", "-ai.png"))
                if ai.exists():
                    r = {**r, "png": str(ai)}
                text = clean(c.get("sub")) or clean(c.get("headline")) or clean(c.get("kicker"))
                posts.append((it, r, text[:60]))
    if covers:
        p = out / "preview-feed.png"
        shoot(feed_page(covers[:4], brand.get("name") or "", accent), p)
        made.append(p)
    if posts:
        p = out / "preview-moments.png"
        shoot(moments_page(posts[:3], brand.get("name") or "", accent), p)
        made.append(p)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    a = ap.parse_args()
    print(json.dumps([str(p) for p in build(a.spec, a.out)], ensure_ascii=False))


if __name__ == "__main__":
    main()
