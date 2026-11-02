"""Real photos from free stock libraries, for when there is no image model and no photo from the user.

  python stock.py search "latte art cafe" [--n 6] [--orient portrait|landscape|square] [--provider auto|pexels|unsplash|openverse]
                  [--dest DIR]
  python stock.py credits [--dest DIR]          # who to credit for the photos in use

Only libraries whose licence allows commercial use are searched:
  pexels     Pexels licence, free for commercial use, no credit required. Needs PEXELS_API_KEY (free).
  unsplash   Unsplash licence, free for commercial use; credit appreciated. Needs UNSPLASH_ACCESS_KEY (free).
  openverse  Creative Commons search without a key, filtered to licences that allow commercial use and
             changes (CC0, public domain, CC BY). CC BY photos must carry the author's credit on the design.
auto tries them in that order and uses the first that answers.

Candidates are saved to DIR (default ./assets/stock), with a numbered contact sheet to choose from, and every
file is written to DIR/SOURCES.md and SOURCES.json: where it came from, who took it, the licence and whether a
credit is required. Search in English for the best results; Pexels also understands Chinese.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

UA = "luobo-design/stock (+https://github.com/zhouwei713/luobo-design)"
OK_CC = {"cc0", "pdm", "by"}  # commercial use and changes allowed; sa/nd/nc are left out on purpose


def fetch(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _json(url, headers=None):
    return json.loads(fetch(url, headers).decode("utf-8"))


# ------------------------------------------------------------------ providers -> common records
def pexels(q, n, orient):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise LookupError("没有 PEXELS_API_KEY")
    params = {"query": q, "per_page": n, "locale": "zh-CN" if re.search(r"[一-鿿]", q) else "en-US"}
    if orient:
        params["orientation"] = orient
    data = _json("https://api.pexels.com/v1/search?" + urllib.parse.urlencode(params), {"Authorization": key})
    return [parse_pexels(p) for p in data.get("photos", [])]


def parse_pexels(p):
    return {"provider": "pexels", "id": str(p["id"]), "download": p["src"].get("large2x") or p["src"]["original"],
            "page": p.get("url"), "author": p.get("photographer"), "author_url": p.get("photographer_url"),
            "license": "Pexels License", "license_url": "https://www.pexels.com/license/", "credit_required": False,
            "credit": f"Photo by {p.get('photographer')} on Pexels", "w": p.get("width"), "h": p.get("height"),
            "alt": p.get("alt") or ""}


def unsplash(q, n, orient):
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        raise LookupError("没有 UNSPLASH_ACCESS_KEY")
    params = {"query": q, "per_page": n}
    if orient:
        params["orientation"] = "squarish" if orient == "square" else orient
    data = _json("https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(params), {"Authorization": f"Client-ID {key}"})
    return [parse_unsplash(p) for p in data.get("results", [])]


def parse_unsplash(p):
    u = p.get("user") or {}
    return {"provider": "unsplash", "id": p["id"], "download": (p.get("urls") or {}).get("regular"),
            "page": (p.get("links") or {}).get("html"), "author": u.get("name"), "author_url": (u.get("links") or {}).get("html"),
            "license": "Unsplash License", "license_url": "https://unsplash.com/license", "credit_required": False,
            "credit": f"Photo by {u.get('name')} on Unsplash", "w": p.get("width"), "h": p.get("height"),
            "alt": p.get("alt_description") or "", "_ping": (p.get("links") or {}).get("download_location")}


def openverse(q, n, orient):
    params = {"q": q, "page_size": max(n * 2, 10), "license": ",".join(sorted(OK_CC)), "mature": "false"}
    if orient:
        params["aspect_ratio"] = {"portrait": "tall", "landscape": "wide", "square": "square"}[orient]
    data = _json("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(params))
    out = [parse_openverse(p) for p in data.get("results", [])]
    return [r for r in out if r][:n]


def parse_openverse(p):
    lic = (p.get("license") or "").lower()
    if lic not in OK_CC:
        return None
    ver = p.get("license_version") or ""
    name = {"cc0": "CC0", "pdm": "Public Domain Mark", "by": f"CC BY {ver}".strip()}[lic]
    return {"provider": "openverse", "id": p["id"], "download": p.get("url"), "page": p.get("foreign_landing_url"),
            "author": p.get("creator"), "author_url": p.get("creator_url"), "license": name, "license_url": p.get("license_url"),
            "credit_required": lic == "by", "credit": p.get("attribution") or f"{p.get('title')} by {p.get('creator')} ({name})",
            "w": p.get("width"), "h": p.get("height"), "alt": p.get("title") or "", "source": p.get("source")}


PROVIDERS = {"pexels": pexels, "unsplash": unsplash, "openverse": openverse}


# ------------------------------------------------------------------ search, save, record
def search(q, n=6, orient=None, provider="auto", dest="assets/stock"):
    order = ["pexels", "unsplash", "openverse"] if provider == "auto" else [provider]
    errors, recs, used = [], [], None
    for name in order:
        try:
            recs = PROVIDERS[name](q, n, orient)
            used = name
            if recs:
                break
            errors.append(f"{name}：没有结果")
        except LookupError as e:
            errors.append(f"{name}：{e}")
        except Exception as e:  # noqa: BLE001  network refused, quota, bad answer
            errors.append(f"{name}：{str(e)[:120]}")
    if not recs:
        return {"ok": False, "query": q, "errors": errors,
                "next": "图库都没拿到图：换个英文关键词再试，或者请用户提供自己的照片，或者用程序插画"}
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w]+", "-", q.lower()).strip("-")[:30] or "photo"
    saved = []
    for i, r in enumerate(recs, 1):
        if not r.get("download"):
            continue
        ext = ".png" if r["download"].lower().split("?")[0].endswith(".png") else ".jpg"
        path = dest / f"{slug}-{used}-{i}{ext}"
        try:
            path.write_bytes(fetch(r["download"], timeout=60))
        except Exception as e:  # noqa: BLE001
            errors.append(f"下载失败 {r['page']}：{str(e)[:80]}")
            continue
        if r.get("_ping"):  # Unsplash asks API users to report each download
            try:
                fetch(r["_ping"] + ("&" if "?" in r["_ping"] else "?") + "client_id=" + os.environ.get("UNSPLASH_ACCESS_KEY", ""))
            except Exception:  # noqa: BLE001
                pass
        rec = {k: v for k, v in r.items() if not k.startswith("_")}
        rec.update({"file": path.name, "n": i, "query": q, "date": date.today().isoformat()})
        saved.append(rec)
    record(dest, saved)
    sheet = contact_sheet(dest, saved, slug) if saved else None
    need = [s["file"] for s in saved if s["credit_required"]]
    return {"ok": bool(saved), "provider": used, "query": q, "files": [str(dest / s["file"]) for s in saved],
            "sheet": str(sheet) if sheet else None, "credit_required": need, "errors": errors,
            "next": ("打开 sheet 看图选一张（按编号），把路径写进 art.image；"
                     + ("带署名要求的图（credit_required）用了就要在画面上写出处，或者换一张不需要署名的。" if need else "")
                     + "交付时告诉用户图来自哪个图库，SOURCES.md 里有记录")}


def record(dest, saved):
    jp = dest / "SOURCES.json"
    old = json.loads(jp.read_text(encoding="utf-8")) if jp.exists() else []
    keep = {s["file"] for s in saved}
    allrec = [o for o in old if o.get("file") not in keep] + saved
    jp.write_text(json.dumps(allrec, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# 图片来源\n", "这些照片来自免费图库，许可都允许商用。标了“要署名”的，用在设计里时画面上要写出处。\n",
          "| 文件 | 图库 | 作者 | 许可 | 要署名 | 原图页面 |", "|---|---|---|---|---|---|"]
    for r in allrec:
        md.append(f"| {r['file']} | {r['provider']} | {r.get('author') or ''} | {r['license']} | "
                  f"{'要，写：' + r['credit'] if r['credit_required'] else '不用'} | {r.get('page') or ''} |")
    (dest / "SOURCES.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def contact_sheet(dest, saved, slug):
    from PIL import Image, ImageDraw
    from sheet import font
    th = 360
    tiles = []
    for s in saved:
        try:
            im = Image.open(dest / s["file"]).convert("RGB")
        except Exception:  # noqa: BLE001
            continue
        im.thumbnail((th * 2, th))
        tiles.append((s, im))
    if not tiles:
        return None
    W = sum(im.width for _, im in tiles) + 24 * (len(tiles) + 1)
    sheet = Image.new("RGB", (W, th + 90), "#F2F0EC")
    d = ImageDraw.Draw(sheet)
    x = 24
    f = font(26)
    for s, im in tiles:
        sheet.paste(im, (x, 24))
        d.text((x, th + 36), f"{s['n']}  {s['license']}{' 要署名' if s['credit_required'] else ''}", fill="#333333", font=f)
        x += im.width + 24
    out = dest / f"sheet-{slug}.png"
    sheet.save(out)
    return out


def credits(dest="assets/stock"):
    jp = Path(dest) / "SOURCES.json"
    if not jp.exists():
        return {"credits": []}
    return {"credits": [{"file": r["file"], "credit": r["credit"], "required": r["credit_required"], "page": r.get("page")}
                        for r in json.loads(jp.read_text(encoding="utf-8"))]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["search", "credits"])
    ap.add_argument("query", nargs="?")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--orient", choices=["portrait", "landscape", "square"])
    ap.add_argument("--provider", choices=["auto", "pexels", "unsplash", "openverse"], default="auto")
    ap.add_argument("--dest", default="assets/stock")
    a = ap.parse_args()
    if a.cmd == "search":
        if not a.query:
            sys.exit("用法 stock.py search 关键词")
        res = search(a.query, a.n, a.orient, a.provider, a.dest)
    else:
        res = credits(a.dest)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
