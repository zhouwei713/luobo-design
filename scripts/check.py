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
            errs.append(f"文字放不下，已缩到最小 {f['fs']:.0f}px 仍溢出（{f['id']}），请删减文案或换版式")
    texts = [t for t in r.get("texts", []) if t["w"] > 0 and t["h"] > 0 and t["text"].strip()]
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
    for im in r.get("imgs", []):
        if not im["ok"]:
            errs.append(f"图片没加载出来：{(im['src'] or '')[-60:]}")
    return errs, warns, todo


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
        for path, s in list(walk_strings(it.get("content") or {})) + [(f"concept.text[{i}]", x) for i, x in enumerate(drawn)]:
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
    h5q = out / "h5" / "h5_qa.json"
    if h5q.exists():  # the stitched phone pages, tested on several screen sizes by h5.py
        names = {it["id"] for it in spec.get("items") or [] if it.get("type") == "h5"}
        files += [f for f in load_json(h5q).get("files", []) if f["name"].split(":", 1)[-1] in names]
    import aiposter
    files += aiposter.qa_files(out)  # whole posters drawn by the model: their words need a human read
    hits = copy_check(spec)
    font_notes = [f"{k}: {v}" for k, v in rep.get("fonts", {}).items() if v.startswith("fallback")]
    n_err = sum(len(f["errors"]) for f in files) + sum(1 for h in hits if h["level"] == "error")
    qa = {"files": files, "copy": hits, "fonts": font_notes, "errors": n_err,
          "warnings": sum(len(f["warnings"]) for f in files) + sum(1 for h in hits if h["level"] == "warn"),
          "todo": sorted({x for f in files for x in f["todo"]})}
    save_json(out / "qa.json", qa)
    return qa


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
    if qa["todo"]:
        lines.append("待补信息：" + "；".join(x.replace("待补真实信息：", "") for x in qa["todo"]))
    lines.append(f"共 {qa['errors']} 个错误，{qa['warnings']} 个提醒")
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
