"""QA for a rendered design: run after render.py.

  python check.py spec.json [--out DIR]

Per file: text cut off, text outside the safe area, font below the platform minimum,
contrast, overlapping text, a lone character on the last line, missing images.
Whole spec: copy risk words (广告法), unfilled 【placeholders】, font fallbacks.
Writes DIR/qa.json and prints a summary. Exit code 1 when any error remains.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from common import contrast, load_json, load_ref, save_json

PUNCT = set("，。！？、；：,.!?;:）)」』”’》】")


def color_of(name, tokens):
    if not name:
        return None
    if name.startswith("#"):
        return name
    return tokens.get(name)


def boxes_overlap(a, b):
    x = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    y = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return x * y


def contains(a, b, tol=1):
    return (a["x"] - tol <= b["x"] and a["y"] - tol <= b["y"] and a["x"] + a["w"] + tol >= b["x"] + b["w"]
            and a["y"] + a["h"] + tol >= b["y"] + b["h"])


def check_render(r, tokens):
    errs, warns, todo = [], [], []
    cv = r["canvas"]
    W, H, safe, u = cv["w"], cv["h"], cv["safe_px"], cv["u"]
    minb, minc = cv["min_px"]["body"], cv["min_px"]["caption"]
    for f in r.get("fit", []):
        if f["overflow"]:
            more = ""
            if f.get("ovpx") and f.get("cw") and f.get("fs"):
                lines = f["ovpx"] / (f["fs"] * 1.35)
                cut = max(2, round(lines * f["cw"] / f["fs"]))
                more = f"，多出约 {f['ovpx']:.0f}px，差不多要删 {cut} 个字" if lines >= 0.3 else f"，只多出 {f['ovpx']:.0f}px，删两三个字或少一个标点就够"
            errs.append(f"文字放不下，已缩到最小 {f['fs']:.0f}px 仍溢出（{f['id']}）{more}，请删减文案或换版式")
    texts = [t for t in r.get("texts", []) if t["w"] > 0 and t["h"] > 0 and t["text"].strip() and t["role"] != "credit"]
    for t in texts:
        name = t["text"].strip().replace("\n", " ")[:16]
        if t.get("placeholder"):
            todo.append(f"待补真实信息：{name}")
        # canvas / safe zone
        if t["x"] < -1 or t["y"] < -1 or t["x"] + t["w"] > W + 1 or t["y"] + t["h"] > H + 1:
            errs.append(f"文字超出画布：{name}")
        elif (t["x"] < safe - 2 or t["y"] < safe - 2 or t["x"] + t["w"] > W - safe + 2 or t["y"] + t["h"] > H - safe + 2):
            warns.append(f"文字贴边，超出安全区：{name}")
        # size
        floor = minb if t["role"] in ("body", "sub") else minc
        if t["fs"] < floor - 0.5:
            errs.append(f"字号 {t['fs']:.0f}px 低于该尺寸的最低要求 {floor}px：{name}")
        # contrast
        if t["on"] != "image":
            fg, bg = color_of(t["c"], tokens), color_of(t["on"], tokens)
            if fg and bg:
                cr = contrast(fg, bg)
                need = 3.0 if t["fs"] >= 3.0 * u else 4.5
                if cr < need:
                    (errs if cr < need - 1 else warns).append(f"对比度 {cr:.1f} 低于 {need}：{name}")
        # lonely last character
        last = (t.get("last_line") or "").strip()
        if t.get("lines", 0) > 1 and len([c for c in last if c not in PUNCT]) <= 1:
            warns.append(f"末行只剩一个字「{last}」：{name}，建议手动断行或改字数")
    # overlapping text boxes (nested spans are fine)
    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if contains(a, b) or contains(b, a) or (a.get("grp") and a.get("grp") == b.get("grp")):
                continue
            ov = boxes_overlap(a, b)
            if ov > 0.08 * min(a["w"] * a["h"], b["w"] * b["h"]):
                errs.append(f"文字互相压住：「{a['text'][:8]}」和「{b['text'][:8]}」".replace("\n", ""))
    warns += space_check(r, texts)
    warns += thumb_check(r, texts, tokens)
    for im in r.get("imgs", []):
        if not im["ok"]:
            errs.append(f"图片没加载出来：{(im['src'] or '')[-60:]}")
    return errs, warns, todo


def title_squeeze(renders):
    """The same headline on several sizes: where it had to shrink far below its size on the item's main
    size, the copy is too long for that shape. A short title for that size (size_copy) reads better."""
    by = {}
    for r in renders:
        roles = {t["id"]: t["role"] for t in r.get("texts", [])}
        fs = [f["fs"] for f in r.get("fit", []) if roles.get(f["id"]) in ("headline", "title") and f.get("fs")]
        if fs:
            cv = r["canvas"]
            by.setdefault(r.get("raw_item") or r["item"], []).append((r, max(fs) / min(cv["w"], cv["h"])))
    out = []
    seen = set()
    for r in renders:  # one long manual line: the type gets small everywhere, not only on the odd size
        iid = r.get("raw_item") or r["item"]
        if iid in seen or r["canvas"].get("kind") == "print" or r.get("type") in ("h5page", "menu", "certificate"):
            continue
        if r.get("layout") in ("textcard", "memo"):  # a quote or a note screenshot reads as a sentence on purpose
            continue
        for t in r.get("texts", []):
            if t["role"] in ("headline", "title"):
                n = max((len([c for c in ln if c.strip() and c not in PUNCT]) for ln in t["text"].split("\n")), default=0)
                if n > 9:
                    seen.add(iid)
                    out.append((f"{r['item']}-{r['size']}", f"标题有一行 {n} 个字，超过 9 个字手机上读着累，字也被挤小："
                                "缩短或者按意思再拆一行；方图和横版可以在 size_copy 里写个短标题"))
                break
    for rows in by.values():
        if len(rows) < 2:
            continue
        main = rows[0][1]
        for r, rel in rows[1:]:
            if r.get("size_copy") or r["canvas"].get("kind") == "print":
                continue
            if rel < main * 0.68:
                out.append((f"{r['item']}-{r['size']}", f"标题在这个尺寸只剩主尺寸的 {rel / main:.0%} 大，字太多挤不下："
                            f"给这个尺寸写个短标题（size_copy.{r['size']}.headline）"))
    return out


def thumb_check(r, texts, tokens):
    """Words on a photo, seen the way a feed shows them: the picture shrunk to 360 px wide.
    Compares each line's colour with what is actually behind it in the rendered pixels."""
    on_photo = [t for t in texts if t.get("on") == "image" and t["role"] in ("headline", "sub", "body", "label") and t["w"] > 4]
    if not on_photo or not r.get("png") or not Path(r["png"]).exists():
        return []
    try:
        from PIL import Image
    except ImportError:
        return []
    im = Image.open(r["png"]).convert("RGB")
    k = 360 / im.width
    small = im.resize((360, max(1, round(im.height * k))))
    warns = []
    for t in on_photo:
        fg = color_of(t.get("c"), tokens)
        if not fg or not fg.startswith("#"):
            continue
        fr = tuple(int(fg[i:i + 2], 16) for i in (1, 3, 5))
        box = (int(t["x"] * k), int(t["y"] * k), int((t["x"] + t["w"]) * k) + 1, int((t["y"] + t["h"]) * k) + 1)
        px = list(small.crop(box).getdata())
        bg = [p for p in px if sum((a - b) ** 2 for a, b in zip(p, fr)) > 90 ** 2]
        if len(px) < 20 or len(bg) < len(px) * 0.2:
            continue
        mid = ["%02X" % sorted(c[i] for c in bg)[len(bg) // 2] for i in range(3)]
        cr = contrast(fg, "#" + "".join(mid))
        need = 3.0 if t["role"] == "headline" else 4.0
        if cr < need:
            name = t["text"].strip().replace("\n", " ")[:12]
            warns.append(f"缩成手机小图后「{name}」压在照片上看不清（对比度约 {cr:.1f}）：把字挪到照片安静的地方，或换张照片")
    return warns


NO_SPACE_CHECK = {"h5page", "card", "tablecard", "brandkit"}


def space_check(r, texts):
    """Empty bands nobody meant (a page that ends half way down) and a headline sitting on the next block."""
    if r.get("type") in NO_SPACE_CHECK:
        return []
    cv = r["canvas"]
    W, H = cv["w"], cv["h"]
    blocks = r.get("blocks") or []
    if any(b["w"] * b["h"] > 0.5 * W * H for b in blocks):
        return []  # a full-bleed photo or illustration fills the page by itself
    items = [(t["x"], t["y"], t["w"], t["h"], t["role"]) for t in texts] + [(b["x"], b["y"], b["w"], b["h"], b["kind"]) for b in blocks]
    items = [i for i in items if i[3] > 0 and i[1] < H and i[1] + i[3] > 0]
    if len(items) < 2:
        return []
    big = [t for t in texts if t["fs"] >= 2.2 * cv["u"]]
    if len(big) <= 1 and r.get("layout") in ("textcard", "memo", "notice", "type-hero", "art-frame") or len(texts) <= 2:
        return []  # one statement set in the middle of the page: the empty space is the design
    warns = []
    spans = sorted((max(0, y), min(H, y + h)) for x, y, w, h, _ in items)
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    gap = max([merged[i + 1][0] - merged[i][1] for i in range(len(merged) - 1)] or [0])
    tall = cv.get("orient") != "landscape"
    calm = r.get("layout") in ("swiss", "magazine")  # these leave air on purpose; only a real hole counts
    if gap > H * ((0.3 if calm else 0.24) if tall else 0.33):
        warns.append(f"画面中间空了一大块（约占高度的 {gap / H:.0%}）：放大主图或标题，或者把下半部分的内容往上收")
    bottom = H - merged[-1][1] - cv["safe_px"]
    if tall and bottom > H * 0.17:
        warns.append(f"底部空了约 {bottom / H:.0%}：内容没撑满，放大字或图，或者加一条有用的信息")
    for t in texts:
        if t["role"] not in ("headline", "title"):
            continue
        below = [i for i in items if i[1] >= t["y"] + t["h"] * 0.6 and i[4] not in ("headline", "title")
                 and min(t["x"] + t["w"], i[0] + i[2]) - max(t["x"], i[0]) > 0.3 * min(t["w"], i[2])]
        if below:
            nxt = min(below, key=lambda i: i[1])
            g = nxt[1] - (t["y"] + t["h"])
            if -2 < g < min(W, H) * 0.008:
                warns.append(f"标题和下面的内容几乎贴在一起（间距 {max(0, g):.0f}px）：标题下面留出一点空")
        break
    return warns


def credit_check(spec, base):
    """Stock photos whose licence asks for the author's name on the design (stock.py records it in SOURCES.json)."""
    hits, books = [], {}
    for it in spec.get("items", []):
        a, c = it.get("art") or {}, it.get("content") or {}
        pics = [a.get("image")] + [(x.get("src") if isinstance(x, dict) else x) for x in (c.get("photos") or [])]
        for pic in pics:
            if not pic or not isinstance(pic, str) or pic.startswith(("http", "data:")):
                continue
            f = Path(pic) if Path(pic).is_absolute() else base / pic
            book = f.parent / "SOURCES.json"
            if book not in books:
                try:
                    books[book] = {r["file"]: r for r in json.loads(book.read_text(encoding="utf-8"))} if book.exists() else {}
                except Exception:  # noqa: BLE001
                    books[book] = {}
            r = books[book].get(f.name)
            if r and r.get("credit_required"):
                said = json.dumps(c, ensure_ascii=False)
                if not (r.get("author") and r["author"] in said):
                    hits.append({"level": "warn", "item": it["id"], "field": "art.image", "text": f.name, "hit": f.name,
                                 "why": f"这张照片的许可要求署名，画面上要写“{r['credit']}”（写进 content.credit，会排成右下角一行小字），或者换一张不用署名的图"})
    return hits


def walk_strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            yield from walk_strings(x, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("src", "image", "motif", "image_fit"):
                continue
            yield from walk_strings(v, f"{path}.{k}" if path else k)


def copy_check(spec):
    rules = load_ref("copy_words.json")["rules"]
    hits = []
    facts = spec.get("facts") or {}
    for it in spec.get("items", []):
        drawn = [t if isinstance(t, str) else t.get("text", "") for t in (it.get("concept") or {}).get("text") or []]
        for path, s in (list(walk_strings(it.get("content") or {})) + list(walk_strings(it.get("size_copy") or {}, "size_copy"))
                        + [(f"concept.text[{i}]", x) for i, x in enumerate(drawn)]):
            s2 = re.sub(r"\{([a-z_]+)\}", lambda m: str(facts.get(m.group(1), "")), s)
            for rule in rules:
                if it.get("type") in rule.get("skip_items", []):
                    continue
                if rule.get("only_items") and it.get("type") not in rule["only_items"]:
                    continue
                pats = [re.escape(w) for w in rule.get("words", [])] + rule.get("patterns", [])
                for pat in pats:
                    for m in re.finditer(pat, s2):
                        hits.append({"level": rule["level"], "item": it["id"], "field": path, "text": s2,
                                     "hit": m.group(0), "why": rule["why"]})
    # facts the brief never confirmed but the copy states as numbers
    return hits


def run(spec_path, out_dir=None):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    out = Path(out_dir or spec_path.parent / "out")
    rep = load_json(out / "render_report.json")
    tokens = rep["tokens"]
    files = []
    for r in rep["renders"]:
        e, w, t = check_render(r, tokens)
        files.append({"name": f"{r['item']}-{r['size']}", "png": r["png"], "errors": e, "warnings": w,
                      "todo": sorted(set(t))})
    for name, msg in title_squeeze(rep["renders"]):
        next(f for f in files if f["name"] == name)["warnings"].append(msg)
    h5q = out / "h5" / "h5_qa.json"
    if h5q.exists():  # the stitched phone pages, tested on several screen sizes by h5.py
        names = {it["id"] for it in spec.get("items") or [] if it.get("type") == "h5"}
        files += [f for f in load_json(h5q).get("files", []) if f["name"].split(":", 1)[-1] in names]
    import aiposter
    files += aiposter.qa_files(out)  # whole posters drawn by the model: their words need a human read
    hits = copy_check(spec) + credit_check(spec, spec_path.parent)
    font_notes = [f"{k}: {v}" for k, v in rep.get("fonts", {}).items() if v.startswith("fallback")]
    n_err = sum(len(f["errors"]) for f in files) + sum(1 for h in hits if h["level"] == "error")
    qa = {"files": files, "copy": hits, "fonts": font_notes, "errors": n_err,
          "warnings": sum(len(f["warnings"]) for f in files) + sum(1 for h in hits if h["level"] == "warn"),
          "todo": sorted({x for f in files for x in f["todo"]}),
          "colors": [f"{ROLE_ZH.get(n['role'], n['role'])} {n['from']} 调成了 {n['to']}：{n['why']}" for n in rep.get("color_notes") or []]}
    qa["next"] = next_steps(qa, out)
    save_json(out / "qa.json", qa)
    return qa


FIXES = [  # problem text -> what to do about it, in the order an agent should work through them
    ("文字放不下", "删减这段文案，或换一个字少也撑得住的版式；别靠缩小字号硬塞"),
    ("文字超出画布", "文案太长或手动断行太宽，缩短这一行"),
    ("文字互相压住", "两段字撞在一起：删减其中一段，或去掉 tags、details 里不必要的条目"),
    ("字号", "这个尺寸放不下这么多字，删减文案或从 sizes 里去掉这个尺寸"),
    ("图片没加载出来", "检查图片路径（相对 spec.json 所在目录），或者删掉这张图用程序插画"),
    ("对比度", "在 brand.tokens 里换一个深一点或浅一点的颜色，或用 studio 编辑页调色"),
    ("文字贴边", "这行字太长，缩短一点或手动断行"),
    ("画面中间空了一大块", "放大主图或标题，或者换一个能撑满竖版的版式；别加没意义的装饰去填"),
    ("底部空了", "放大字或图，或者把有用的信息（地址、时间、二维码）放到底部"),
    ("标题和下面的内容几乎贴在一起", "加大标题下方的间距，或者把副标题删短一行"),
    ("缩成手机小图后", "先试着把标题挪到照片里干净、颜色单一的区域（title_pos、art.focus），不行再换照片；别用一大片黑色盖住照片"),
    ("末行只剩一个字", "在标题里手动断行，或加减一两个字"),
    ("标题有一行", "标题每行最好不超过 8 个字；照 spec.md 的短标题写法压一压"),
    ("标题在这个尺寸只剩", "按 spec.md 的短标题写法，在 size_copy 里给这个尺寸写四到十个字的标题"),
    ("整图里的字是模型画的", "看图逐字核对 -ai.png；有错字就重新生成或交付排版版"),
    ("整图生成失败", "交付排版版，告诉用户整图这次没生成出来"),
]


ROLE_ZH = {"accent": "主色", "accent2": "辅色", "ink": "文字色"}


def next_steps(qa, out):
    """What to do now, so the agent does not have to work it out from the raw list."""
    steps, seen = [], set()
    problems = [(lvl, m, f["name"]) for f in qa["files"] for lvl, ms in (("error", f["errors"]), ("warn", f["warnings"])) for m in ms]
    for key, fix in FIXES:
        names = sorted({n for lvl, m, n in problems if m.startswith(key) or key in m[:12]})
        if names and key not in seen:
            seen.add(key)
            lvl = "先改" if any(lvl == "error" for lvl, m, n in problems if key in m[:12] and n in names) else "最好改"
            steps.append(f"{lvl}：{key}（{'、'.join(names[:4])}{'等' if len(names) > 4 else ''}）。{fix}")
    errs = [h for h in qa["copy"] if h["level"] == "error"]
    if errs:
        steps.append("先改文案：" + "；".join(f"「{h['hit']}」{h['why']}" for h in errs[:3]))
    if [h for h in qa["copy"] if h["level"] != "error"]:
        steps.append("交付时把 qa.json 里 copy 的提醒告诉用户，让用户决定改不改")
    if qa["todo"]:
        steps.append("把待补信息列给用户：" + "；".join(x.replace("待补真实信息：", "") for x in qa["todo"][:5])
                     + "。拿到后写进 spec.facts 重跑")
    if qa.get("colors"):
        steps.append("交付时告诉用户品牌色做了微调（" + "；".join(qa["colors"]) + "）。用户坚持用原色，在 spec.brand 里写 \"exact_colors\": true 再重跑")
    if qa["fonts"]:
        steps.append("字体退回了系统字体，联网后重跑 setup_check.py --install；交付时说明一下")
    if qa["errors"]:
        steps.append("改完重跑 pipeline.py（只改了一件物料可以用 render.py --only 物料 id 再跑 check.py）")
    else:
        steps.append("看一眼 overview.png" + (" 和 preview-*.png" if list(Path(out).glob("preview-*.png")) else "")
                     + "（看不了图就跳过，在交付时请用户自己看），然后交付；用户想自己改字调色，告诉他打开 editor.html")
    return steps


def summary(qa):
    lines = []
    for f in qa["files"]:
        mark = "✗" if f["errors"] else ("!" if f["warnings"] else "✓")
        lines.append(f"{mark} {f['name']}")
        for e in f["errors"]:
            lines.append(f"    ERROR {e}")
        for w in f["warnings"]:
            lines.append(f"    warn  {w}")
    for h in qa["copy"]:
        lines.append(f"{'ERROR' if h['level'] == 'error' else 'warn '} 文案「{h['hit']}」({h['item']}.{h['field']})：{h['why']}")
    for n in qa["fonts"]:
        lines.append(f"note  字体回退 {n}")
    for n in qa.get("colors") or []:
        lines.append(f"note  颜色微调 {n}")
    if qa["todo"]:
        lines.append("待补信息：" + "；".join(x.replace("待补真实信息：", "") for x in qa["todo"]))
    lines.append(f"共 {qa['errors']} 个错误，{qa['warnings']} 个提醒")
    if qa.get("next"):
        lines.append("下一步：")
        lines += [f"  {n}. {s}" for n, s in enumerate(qa["next"], 1)]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    a = ap.parse_args()
    qa = run(a.spec, a.out)
    print(summary(qa))
    sys.exit(1 if qa["errors"] else 0)


if __name__ == "__main__":
    main()
