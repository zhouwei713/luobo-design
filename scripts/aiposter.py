"""Whole posters drawn by the image model from the concept card (items with "mode": "ai").

  python aiposter.py spec.json [--out DIR] [--config PATH] [--force]

For every screen size of the item: build the concept prompt for that shape, generate, keep the raw
image in OUT/ai/, and save OUT/<item>-<size>-ai.png resized to the platform's pixel size. Print sizes
are skipped (a generated image is too small for 300 dpi); the layout version covers them.

The layout version of the same item is always rendered too. It is the fallback when no model is
configured or a call fails, and the version to use when every character must be exact.

A rerun with the same prompt and model reuses the earlier image, so nothing is paid twice.
Writes OUT/ai_report.json, which check.py and sheet.py read.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from common import canvas, load_json, resolve_tokens, save_json, spec_brand
from imagegen import ImageGen, find_config
from prompts import concept_prompts

FAMILY = {"openai": "gpt-image-2", "ark": "seedream", "gemini": "nano-banana"}


def cover(img, w, h):
    """Scale to cover w x h and crop the centre; the model's ratio is close but rarely exact."""
    s = max(w / img.width, h / img.height)
    im = img.convert("RGB").resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h)), s


def run(spec_path, out_dir=None, config=None, force=False):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    out = Path(out_dir or spec_path.parent / "out")
    items = [it for it in spec.get("items") or [] if it.get("mode") == "ai"]
    report_path = out / "ai_report.json"
    if not items:
        if report_path.exists():  # an earlier run had ai items; do not let stale posters reach the overview
            save_json(report_path, {"posters": []})
        return []
    prev = {}
    if report_path.exists():
        prev = {r["name"]: r for r in load_json(report_path).get("posters", []) if r.get("png")}
    gen = ImageGen(find_config(config, spec_path.parent))
    ok, why = gen.available()
    if not ok:
        print(f"ai posters: skipped ({why}); the layout versions stand in, prompts.md has the concept prompts")
        save_json(report_path, {"posters": [], "skipped": why})
        return []
    brand = spec.get("brand") or {}
    d = resolve_tokens(spec_brand(spec))
    fam = FAMILY.get(gen.provider, "gpt-image-2")
    posters = []
    for it in items:
        for size in it.get("sizes") or ["portrait"]:
            cv = canvas(size)
            if cv["kind"] == "print":
                print(f"ai posters: {it['id']}-{size} is a print size, the layout version is used")
                continue
            cp = concept_prompts(it, brand, d, size, spec.get("facts"))
            prompt = cp[fam]
            name = f"{it['id']}-{size}-ai"
            png = out / f"{name}.png"
            raw = out / "ai" / f"{name}-raw.png"
            raw.parent.mkdir(parents=True, exist_ok=True)
            key = hashlib.md5(f"{gen.provider}|{gen.model}|{prompt}".encode("utf-8")).hexdigest()
            old = prev.get(name)
            if not force and old and old.get("hash") == key and png.exists() and raw.exists():
                posters.append(old)
                print(f"ai posters: {name}.png reused (same prompt)")
                continue
            rw, rh = (int(x) for x in cp["aspect"].split(":"))
            try:
                img, _ = gen.generate(prompt, rw * 256, rh * 256, out=str(raw))
            except Exception as e:  # noqa: BLE001
                print(f"ai posters: {name} failed ({e}); the layout version stands in")
                posters.append({"name": name, "item": it["id"], "size": size, "error": str(e)[:300]})
                continue
            img.save(raw)
            W, H = round(cv["w"] * cv.get("scale", 1)), round(cv["h"] * cv.get("scale", 1))
            fitted, s = cover(img, W, H)
            fitted.save(png)
            task = raw.with_suffix(".task.json")
            rec = {"name": name, "item": it["id"], "size": size, "png": str(png), "raw": str(raw),
                   "texts": cp["texts"], "hash": key, "provider": gen.provider, "model": gen.model,
                   "source_px": [img.width, img.height], "upscale": round(s, 2)}
            if task.exists():
                rec["taskId"] = json.loads(task.read_text(encoding="utf-8")).get("taskId")
            posters.append(rec)
            print(f"ai posters: {name}.png {W}x{H} from {img.width}x{img.height} ({gen.provider}:{gen.model})")
    save_json(report_path, {"posters": posters})
    return posters


def qa_files(out):
    """Entries for qa.json. The model drew the words, so a person has to read them before delivery."""
    p = Path(out) / "ai_report.json"
    if not p.exists():
        return []
    files = []
    for r in load_json(p).get("posters", []):
        if r.get("error"):
            files.append({"name": r["name"], "png": None, "errors": [],
                          "warnings": [f"整图生成失败，交付排版版：{r['error'][:120]}"], "todo": []})
            continue
        warns = ["整图里的字是模型画的，交付前看图逐字核对：" + "、".join(f"「{t}」" for t in r["texts"])]
        if r.get("upscale", 1) > 1.5:
            warns.append(f"原图只有 {r['source_px'][0]}x{r['source_px'][1]}，放大了 {r['upscale']} 倍，"
                         "手机上看没问题，印刷和大屏用排版版")
        files.append({"name": r["name"], "png": r["png"], "errors": [], "warnings": warns, "todo": []})
    return files


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--config")
    ap.add_argument("--force", action="store_true", help="generate again even when the prompt has not changed")
    a = ap.parse_args()
    run(a.spec, a.out, a.config, a.force)
