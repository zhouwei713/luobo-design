"""The studio page: change copy, colours and pictures after delivery, and leave comments on the image.

  python studio.py open spec.json [--out DIR] [--port 4800] [--no-browser]
        live page on this computer: every save re-renders all sizes of what changed
  python studio.py build spec.json [--out DIR]
        DIR/editor.html, a single file that works offline: edits and comments export as 修改单.json
  python studio.py comments spec.json [--out DIR] [--all] [--wait [SECONDS]]
        the open comments (what the person asked for, where on which picture); --wait blocks until a new one
  python studio.py reply spec.json ID TEXT [--resolve]
        answer a comment on the page (after the change is made)
  python studio.py apply spec.json 修改单.json
        an exported edit list -> spec.json (+ its comments into comments.json); then rerun pipeline.py

Everything the page writes goes through spec.json, so a re-run of pipeline.py always reproduces it.
"""
import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from common import load_json, resolve_tokens, save_json, spec_brand

HERE = Path(__file__).resolve().parent
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
COLOR_KEYS = ("accent", "accent2", "bg", "surface", "ink", "muted")
SIZE_NAMES = {"portrait": "竖版", "square": "方图", "story": "手机长图", "landscape": "横版", "wide": "横幅", "screen": "门店屏",
              "a4": "A4", "a3": "A3", "a5": "A5", "h5": "手机页", "xhs": "小红书", "table-card": "桌牌", "tent": "席位卡"}
LOCK = threading.Lock()


# ------------------------------------------------------------------ paths and state
def out_dir(spec_path, out=None):
    return Path(out).resolve() if out else spec_path.parent / "out"


TYPE_NAMES = {"poster": "海报", "menu": "菜单", "invitation": "请柬", "certificate": "证书", "card": "名片", "brandkit": "品牌套件",
              "tablecard": "桌牌", "h5": "电子请柬", "xhs": "小红书封面"}


def item_label(it):
    c = it.get("content") or {}
    if it.get("type") == "tablecard":
        return "席位卡" if it.get("layout") == "tent" else "桌号牌"
    for k in ("headline", "title", "name", "big_title", "kicker"):
        v = c.get(k)
        if isinstance(v, str) and v.strip():
            return re.sub(r"\s+", " ", v.replace("**", "")).strip()[:16]
    return TYPE_NAMES.get(it.get("type"), it.get("id", ""))


def get_path(obj, path):
    for seg in path.split("."):
        if isinstance(obj, list):
            if not seg.isdigit() or int(seg) >= len(obj):
                return None
            obj = obj[int(seg)]
        elif isinstance(obj, dict):
            if seg not in obj:
                return None
            obj = obj[seg]
        else:
            return None
    return obj


def set_path(obj, path, value):
    segs = path.split(".")
    for i, seg in enumerate(segs):
        last = i == len(segs) - 1
        if isinstance(obj, list):
            if not seg.isdigit() or int(seg) >= len(obj):
                raise KeyError(path)
            if last:
                obj[int(seg)] = value
            else:
                obj = obj[int(seg)]
        else:
            if last:
                obj[seg] = value
            else:
                if seg not in obj:
                    raise KeyError(path)
                obj = obj[seg]


def stamp_of(*files):
    h = hashlib.sha1()
    for f in files:
        if f.exists():
            st = f.stat()
            h.update(f"{f.name}{st.st_mtime_ns}{st.st_size}".encode())
    return h.hexdigest()[:12]


def image_slots(spec, base):
    """Pictures a person may swap: the brand logo, each item's main picture, note-cover photos, QR codes."""
    def cur(p):
        if not p or not isinstance(p, str):
            return None, None
        q = Path(p) if Path(p).is_absolute() else (base / p)
        url = None
        try:
            if q.exists() and q.suffix.lower() in IMG_EXT and q.resolve().is_relative_to(base.resolve()):
                url = "@spec/" + q.resolve().relative_to(base.resolve()).as_posix()
        except (OSError, ValueError):
            pass
        return p, url

    slots = []
    brand = spec.get("brand") or {}
    p, u = cur(brand.get("logo"))
    slots.append({"slot": "brand.logo", "label": "品牌 logo", "current": p, "url": u, "global": True})
    for it in spec.get("items", []):
        iid, typ = it.get("id"), it.get("type")
        art, c = it.get("art") or {}, it.get("content") or {}
        if typ in ("poster", "invitation", "menu", "xhs", "h5") or art.get("image"):
            p, u = cur(art.get("image"))
            slots.append({"slot": f"item:{iid}:art.image", "item": iid, "label": "主图" if typ != "xhs" else "封面照片", "current": p, "url": u})
        for n, ph in enumerate(c.get("photos") or []):
            p, u = cur(ph.get("src") if isinstance(ph, dict) else ph)
            slots.append({"slot": f"item:{iid}:content.photos.{n}" + (".src" if isinstance(ph, dict) else ""), "item": iid,
                          "label": f"照片 {n + 1}", "current": p, "url": u})
        q = c.get("qr")
        if isinstance(q, dict):
            p, u = cur(q.get("src"))
            slots.append({"slot": f"item:{iid}:content.qr.src", "item": iid, "label": "二维码", "current": p, "url": u})
    return slots


def build_state(spec_path, out, live=False):
    import render as render_mod
    spec = load_json(spec_path)
    rep_path = out / "render_report.json"
    rep = load_json(rep_path) if rep_path.exists() else {"renders": []}
    by_raw = {}
    for r in rep.get("renders", []):
        by_raw.setdefault(r.get("raw_item") or r["item"], []).append(r)
    items = []
    for it in spec.get("items", []):
        iid = it.get("id")
        views = []
        for r in by_raw.get(iid, []):
            png = Path(r["png"]).name
            if not (out / png).exists():
                continue
            label = SIZE_NAMES.get(r["size"], r["size"])
            if r["item"] != iid:
                tag = r["item"].replace(iid + "-", "")
                batch = it.get("batch") or (it.get("content") or {}).get("recipients") or []
                if tag.isdigit() and 0 < int(tag) <= len(batch):  # a batch copy: name it after its guest or table
                    e = batch[int(tag) - 1]
                    tag = e if isinstance(e, str) else str(next((e[k] for k in ("guest", "recipient", "name", "number") if e.get(k)), tag))
                elif "-" in tag and tag.split("-")[0].isdigit():  # h5 screens: 1-cover -> 第1屏
                    tag = f"第{tag.split('-')[0]}屏"
                tag = {"front": "正面", "back": "背面"}.get(tag, tag)
                label = f"{tag[:8]} · {label}"
            ai = png.replace(".png", "-ai.png")
            views.append({"key": f"{r['item']}|{r['size']}", "label": label, "png": png, "w": r["canvas"]["w"], "h": r["canvas"]["h"],
                          "fields": [f for f in r.get("fields", []) if f["w"] > 0 and f["h"] > 0],
                          "ai_png": ai if (out / ai).exists() else None})
        facts = spec.get("facts") or {}
        raw_c = it.get("content") or {}
        fields = []
        batch_keys = set()
        for b in (it.get("batch") or raw_c.get("recipients") or []):
            if isinstance(b, dict):
                batch_keys |= set(b)
        shown_c = render_mod.fill_facts(raw_c, facts)
        for path, val in render_mod.content_fields(raw_c):
            fields.append({"path": path, "value": val, "shown": get_path(shown_c, path) or val,
                           "readonly": path.split(".")[0] in batch_keys})
        for sel, vals in (it.get("size_copy") or {}).items():  # copy written for one size only
            shown_s = render_mod.fill_facts(vals, facts)
            for path, val in render_mod.content_fields(vals):
                fields.append({"path": f"@{sel}.{path}", "value": val, "shown": get_path(shown_s, path) or val, "readonly": False})
        # fields only a batch entry fills (recipient, guest): shown read-only so a click still lands somewhere
        seen = {f["path"] for f in fields}
        for v in views:
            for b in v["fields"]:
                if b["path"] not in seen:
                    seen.add(b["path"])
                    fields.append({"path": b["path"], "value": "", "shown": "", "readonly": True})
        items.append({"id": iid, "type": it.get("type"), "label": item_label(it), "views": views, "fields": fields,
                      "mode_ai": it.get("mode") == "ai", "batch": bool(it.get("batch") or raw_c.get("recipients"))})
    tokens = (rep.get("tokens") or {})
    try:
        auto = resolve_tokens({**spec_brand(spec), "tokens": {}})["tokens"]
    except SystemExit:
        auto = tokens
    fixed = (spec.get("brand") or {}).get("tokens") or {}
    colors = {k: {"value": (fixed.get(k) or tokens.get(k) or auto.get(k) or "#000000").upper(), "auto": (auto.get(k) or "#000000").upper(),
                  "fixed": bool(fixed.get(k))} for k in COLOR_KEYS if tokens.get(k) or auto.get(k)}
    comments = load_comments(out)
    state = {"title": spec.get("project") or (spec.get("brand") or {}).get("name") or "萝卜设计", "spec": spec_path.name,
             "items": items, "facts": {k: v for k, v in (spec.get("facts") or {}).items() if isinstance(v, str)},
             "colors": colors, "images": image_slots(spec, spec_path.parent), "comments": comments,
             "stamp": stamp_of(rep_path), "cstamp": stamp_of(out / "comments.json"),
             "can_undo": bool(list((out / "studio" / "history").glob("*.json"))) if live else False}
    if not live:  # offline: pictures are referenced next to editor.html; spec-side images are not reachable, drop the preview
        for s in state["images"]:
            s["url"] = None
    return state


# ------------------------------------------------------------------ the page
def page_html(boot):
    tpl = (HERE / "studio.html").read_text(encoding="utf-8")
    return tpl.replace("/*__BOOT__*/", boot, 1)


def build_static(spec_path, out):
    """out/editor.html: the same page with the state baked in, for opening by double-click."""
    state = build_state(spec_path, out, live=False)
    data = json.dumps(state, ensure_ascii=False).replace("</", "<\\/")
    html = page_html(f"window.__MODE__='offline';window.__STATE__={data};")
    path = out / "editor.html"
    path.write_text(html, encoding="utf-8")
    return path


# ------------------------------------------------------------------ comments
def load_comments(out):
    p = out / "comments.json"
    if not p.exists():
        return []
    try:
        return load_json(p).get("comments", [])
    except Exception:  # noqa: BLE001
        return []


def save_comments(out, comments):
    save_json(out / "comments.json", {"comments": comments})


def add_comment(out, spec_path, c):
    comments = load_comments(out)
    n = max([x.get("n", 0) for x in comments] + [0]) + 1
    spec = load_json(spec_path)
    it = next((i for i in spec.get("items", []) if i.get("id") == c.get("item")), None)
    near = None
    if c.get("field") and it:
        v = get_path(it.get("content") or {}, c["field"])
        near = v if isinstance(v, str) else None
    rec = {"id": f"c{n}", "n": n, "item": c.get("item"), "item_label": c.get("item_label") or (item_label(it) if it else c.get("item")),
           "view": c.get("view"), "view_label": c.get("view_label"), "x": c.get("x"), "y": c.get("y"),
           "field": c.get("field"), "field_text": near, "status": "open", "seen": False,
           "at": datetime.now().isoformat(timespec="seconds"), "messages": [{"by": "user", "text": c.get("text", "")}]}
    comments.append(rec)
    save_comments(out, comments)
    return comments


def describe(c):
    where = f"{c.get('item_label') or c.get('item')} 的 {c.get('view_label') or c.get('view')}"
    pos = ""
    if c.get("x") is not None:
        x, y = c["x"], c["y"]
        pos = ("上" if y < .33 else "中" if y < .66 else "下") + ("左" if x < .33 else "中" if x < .66 else "右")
        pos = "正中" if pos == "中中" else pos + "部"
        pos = f"，画面{pos}（x {x:.0%}，y {y:.0%}）"
    f = f"，点在“{c['field']}”上（现在是：{c['field_text']}）" if c.get("field") else ""
    return f"#{c['n']} {where}{pos}{f}"


# ------------------------------------------------------------------ applying edits
def apply_changes(spec, changes, base, src_dir=None):
    """Mutate spec. Returns (touched item ids or None for all, notes for the reply)."""
    touched, everything, notes = set(), False, []
    brand = spec.setdefault("brand", {})
    for ch in changes:
        kind = ch.get("kind")
        if kind == "field":
            it = next((i for i in spec.get("items", []) if i.get("id") == ch.get("item")), None)
            if not it:
                notes.append(f"找不到物料 {ch.get('item')}，这一处没改")
                continue
            try:
                path = ch["path"]
                if path.startswith("@"):  # @square.headline: the copy written for that size
                    sel, path = path[1:].split(".", 1)
                    holder = (it.get("size_copy") or {}).get(sel)
                    if not isinstance(holder, dict):
                        raise KeyError(ch["path"])
                else:
                    holder = it.get("content") or {}
                old = get_path(holder, path)
                if not isinstance(old, str):
                    raise KeyError(ch["path"])
                set_path(holder, path, str(ch.get("value", "")))
                touched.add(it["id"])
            except KeyError:
                notes.append(f"{it['id']} 的 {ch.get('path')} 不是能直接改的文字，这一处没改")
        elif kind == "fact":
            spec.setdefault("facts", {})[ch["key"]] = str(ch.get("value", ""))
            everything = True
        elif kind == "color":
            v = (ch.get("value") or "").strip()
            toks = brand.setdefault("tokens", {})
            if ch.get("key") not in COLOR_KEYS:
                continue
            if v:
                if not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
                    notes.append(f"颜色 {v} 看不懂，没改")
                    continue
                toks[ch["key"]] = v.upper()
            else:
                toks.pop(ch["key"], None)
            if not toks:
                brand.pop("tokens", None)
            everything = True
        elif kind == "image":
            path = ch.get("path")
            if not path and ch.get("file") and src_dir:  # offline edit list: the photo sits next to it, or in the spec folder
                for d in (Path(src_dir), base, base / "assets"):
                    q = d / ch["file"]
                    if q.exists() and q.suffix.lower() in IMG_EXT:
                        dst = base / "assets" / q.name
                        dst.parent.mkdir(exist_ok=True)
                        if q.resolve() != dst.resolve():
                            shutil.copy2(q, dst)
                        path = dst.relative_to(base).as_posix()
                        break
            if not path:
                notes.append(f"换图需要照片文件 {ch.get('file') or ''}，请把它放到 spec 同一个文件夹里再运行一次")
                continue
            slot = ch.get("slot", "")
            if slot == "brand.logo":
                brand["logo"] = path
                everything = True
            elif slot.startswith("item:"):
                _, iid, p = slot.split(":", 2)
                it = next((i for i in spec.get("items", []) if i.get("id") == iid), None)
                if not it:
                    continue
                if p == "art.image":
                    a = it.setdefault("art", {})
                    a["image"] = path
                    a.pop("motif", None) if it.get("type") == "xhs" else None
                else:
                    try:
                        set_path(it, p, path)
                    except KeyError:
                        notes.append(f"{iid} 的 {p} 换不了")
                        continue
                touched.add(iid)
    return (None if everything else sorted(touched)), notes


def rebuild(spec_path, out, items):
    import check
    import h5
    import prompts
    import render
    import sheet
    if items is None:
        render.render(spec_path, out)
    else:
        for iid in items:
            render.render(spec_path, out, only=iid)
    h5.build(spec_path, out)
    try:
        import preview
        preview.build(spec_path, out)
    except Exception as e:  # noqa: BLE001
        print("  preview skipped:", e)
    qa = check.run(spec_path, out)
    sheet.make(out)
    prompts.build(spec_path, out)
    build_static(spec_path, out)
    return qa


def save_spec_with_history(spec_path, out, spec):
    hist = out / "studio" / "history"
    hist.mkdir(parents=True, exist_ok=True)
    shutil.copy2(spec_path, hist / f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.json")
    for old in sorted(hist.glob("*.json"))[:-30]:
        old.unlink()
    save_json(spec_path, spec)


def validate_or_raise(spec):
    from pipeline import validate
    errs, _ = validate(copy.deepcopy(spec))
    if errs:
        raise ValueError("改完以后规格不对：" + "；".join(errs[:3]))


# ------------------------------------------------------------------ server
def make_handler(spec_path, out):
    base = spec_path.parent

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def file(self, root, rel):
            try:
                p = (root / unquote(rel)).resolve()
                if not p.is_relative_to(root.resolve()) or not p.is_file() or p.suffix.lower() not in IMG_EXT | {".pdf"}:
                    raise FileNotFoundError
            except (OSError, ValueError, FileNotFoundError):
                return self.send(404, {"ok": False, "error": "没有这个文件"})
            ctype = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".pdf": "application/pdf"}[p.suffix.lower()]
            self.send(200, p.read_bytes(), ctype)

        def body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > 25 * 1024 * 1024:
                raise ValueError("文件太大")
            return self.rfile.read(n) if n else b""

        def do_GET(self):  # noqa: N802
            u = urlparse(self.path).path
            if u in ("/", "/index.html"):
                return self.send(200, page_html("window.__MODE__='live';").encode(), "text/html; charset=utf-8")
            if u == "/api/state":
                return self.send(200, {"ok": True, "state": build_state(spec_path, out, live=True)})
            if u == "/api/stamp":
                return self.send(200, {"ok": True, "stamp": stamp_of(out / "render_report.json"), "cstamp": stamp_of(out / "comments.json")})
            if u.startswith("/files/@spec/"):
                return self.file(base, u[len("/files/@spec/"):])
            if u.startswith("/files/"):
                return self.file(out, u[len("/files/"):])
            self.send(404, {"ok": False, "error": "没有这个地址"})

        def do_POST(self):  # noqa: N802
            u = urlparse(self.path).path
            try:
                if u == "/api/upload":
                    raw = self.body()
                    name = unquote(self.headers.get("X-Filename") or "photo.jpg")
                    ext = Path(name).suffix.lower()
                    if ext not in IMG_EXT:
                        raise ValueError("只收 png、jpg、webp 照片")
                    stem = re.sub(r"[^\w\-]+", "-", Path(name).stem)[:40].strip("-") or "photo"
                    dst = base / "assets" / f"{stem}-{hashlib.sha1(raw).hexdigest()[:8]}{ext}"
                    dst.parent.mkdir(exist_ok=True)
                    dst.write_bytes(raw)
                    return self.send(200, {"ok": True, "path": dst.relative_to(base).as_posix()})
                data = json.loads(self.body() or b"{}")
                if u == "/api/apply":
                    with LOCK:
                        spec = load_json(spec_path)
                        items, notes = apply_changes(spec, data.get("changes") or [], base)
                        if items == []:
                            raise ValueError("；".join(notes) or "没有可以保存的改动")
                        validate_or_raise(spec)
                        save_spec_with_history(spec_path, out, spec)
                        print(f"  studio: {len(data.get('changes') or [])} 处改动，重出 {'全部' if items is None else '、'.join(items)}", flush=True)
                        qa = rebuild(spec_path, out, items)
                    notes += [f"颜色微调：{c}" for c in qa.get("colors") or []]
                    msg = f"已重新出图，{qa['errors']} 个错误，{qa['warnings']} 个提醒" + ("。" + "；".join(notes) if notes else "")
                    return self.send(200, {"ok": True, "message": msg, "state": build_state(spec_path, out, live=True)})
                if u == "/api/undo":
                    with LOCK:
                        hist = sorted((out / "studio" / "history").glob("*.json"))
                        if not hist:
                            raise ValueError("没有可以撤销的改动")
                        shutil.copy2(hist[-1], spec_path)
                        hist[-1].unlink()
                        rebuild(spec_path, out, None)
                    return self.send(200, {"ok": True, "state": build_state(spec_path, out, live=True)})
                if u == "/api/comment":
                    if not (data.get("text") or "").strip():
                        raise ValueError("意见是空的")
                    with LOCK:
                        cs = add_comment(out, spec_path, data)
                    print(f"  studio: 新意见 {describe(cs[-1])}：{data['text']}", flush=True)
                    return self.send(200, {"ok": True, "comments": cs})
                if u == "/api/comment/resolve":
                    with LOCK:
                        cs = load_comments(out)
                        for c in cs:
                            if c["id"] == data.get("id"):
                                c["status"] = "resolved"
                        save_comments(out, cs)
                    return self.send(200, {"ok": True, "comments": cs})
                self.send(404, {"ok": False, "error": "没有这个地址"})
            except ValueError as e:
                self.send(400, {"ok": False, "error": str(e)})
            except Exception as e:  # noqa: BLE001
                self.send(500, {"ok": False, "error": f"出错了：{e}"})

    return H


def serve(spec_path, out, port, open_browser):
    if not (out / "render_report.json").exists():
        sys.exit(f"{out} 里还没有成品，先运行 pipeline.py")
    srv = None
    for p in range(port, port + 30):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), make_handler(spec_path, out))
            break
        except OSError:
            continue
    if not srv:
        sys.exit("端口都被占用了，换个 --port 试试")
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    save_json(out / "studio" / "server.json", {"url": url, "spec": str(spec_path), "started": datetime.now().isoformat(timespec="seconds")})
    print(json.dumps({"url": url, "next": "把这个地址给用户，在浏览器里打开；用户发来的意见用 studio.py comments --wait 读"}, ensure_ascii=False), flush=True)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


# ------------------------------------------------------------------ cli
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["open", "build", "comments", "reply", "apply"])
    ap.add_argument("spec")
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--out")
    ap.add_argument("--port", type=int, default=4800)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--wait", nargs="?", const=1800, type=int)
    ap.add_argument("--resolve", action="store_true")
    a = ap.parse_args()
    spec_path = Path(a.spec).resolve()
    out = out_dir(spec_path, a.out)

    if a.cmd == "open":
        return serve(spec_path, out, a.port, not a.no_browser)
    if a.cmd == "build":
        p = build_static(spec_path, out)
        return print(json.dumps({"editor": str(p)}, ensure_ascii=False))
    if a.cmd == "comments":
        t0 = time.time()
        while True:
            cs = load_comments(out)
            show = [c for c in cs if a.all or c["status"] != "resolved"]
            fresh = [c for c in show if not c.get("seen")]
            if not a.wait or fresh or time.time() - t0 > a.wait:
                break
            time.sleep(1.5)
        if a.wait:
            show = fresh
        for c in cs:
            if c in show:
                c["seen"] = True
        if show:
            save_comments(out, cs)
        res = {"open": len([c for c in cs if c["status"] != "resolved"]),
               "comments": [{**{k: c.get(k) for k in ("id", "n", "item", "view", "x", "y", "field", "field_text", "status")},
                             "where": describe(c), "messages": c["messages"]} for c in show]}
        res["next"] = ("按意见改 spec.json 后重跑 pipeline.py（或 render.py --only 物料），再用 studio.py reply 回复"
                       if show else ("没有新意见" + ("，等待超时" if a.wait else "")))
        return print(json.dumps(res, ensure_ascii=False, indent=1))
    if a.cmd == "reply":
        if len(a.rest) < 2:
            sys.exit("用法 studio.py reply spec.json ID 回复内容 [--resolve]")
        cid, text = a.rest[0], " ".join(a.rest[1:])
        if text == "-":
            text = sys.stdin.read().strip()
        cs = load_comments(out)
        hit = next((c for c in cs if c["id"] == cid or str(c["n"]) == cid.lstrip("#")), None)
        if not hit:
            sys.exit(f"没有意见 {cid}")
        hit["messages"].append({"by": "agent", "text": text, "at": datetime.now().isoformat(timespec="seconds")})
        if a.resolve:
            hit["status"] = "resolved"
        save_comments(out, cs)
        build_static(spec_path, out) if (out / "render_report.json").exists() else None
        return print(json.dumps({"ok": True, "id": hit["id"], "status": hit["status"]}, ensure_ascii=False))
    if a.cmd == "apply":
        if not a.rest:
            sys.exit("用法 studio.py apply spec.json 修改单.json")
        src = Path(a.rest[0]).resolve()
        doc = load_json(src)
        if doc.get("kind") != "luobo-design-edits":
            sys.exit("这不是萝卜设计导出的修改单")
        spec = load_json(spec_path)
        items, notes = apply_changes(spec, doc.get("changes") or [], spec_path.parent, src.parent)
        n_comments = 0
        for c in doc.get("comments") or []:
            add_comment(out, spec_path, c)
            n_comments += 1
        if items != []:
            validate_or_raise(spec)
            save_spec_with_history(spec_path, out, spec)
        res = {"changed_items": "all" if items is None else items, "comments_added": n_comments, "notes": notes,
               "next": ("重跑 pipeline.py 出新图" if items != [] else "") + ("；" if items != [] and n_comments else "")
               + ("用 studio.py comments 看意见，逐条改完再 reply" if n_comments else "")}
        return print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
