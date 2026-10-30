"""One command from spec to delivery.

  python pipeline.py spec.json [--out DIR] [--config PATH] [--no-images] [--hd]

Steps: validate spec -> fonts -> AI images (only if a model is configured) -> render -> QA ->
overview sheet -> prompts.md -> brand.md / brand.json. Exit code 1 when QA still has errors.
"""
import argparse
import re
import sys
from pathlib import Path

import brand as brand_mod
import check
import prompts
import render
import sheet
from art import MOTIFS
from common import load_json, load_ref
from layouts import LAYOUTS

KEYS = {
    "poster": {"kicker", "headline", "sub", "offer", "details", "cta", "qr", "big_number", "org", "body", "issuer", "date_line",
               "tags", "note", "art_label", "big_title", "lines", "looks"},
    "menu": {"title", "subtitle", "sections", "details", "note", "qr"},
    "invitation": {"kicker", "title", "big_number", "guest", "salutation", "body", "details", "rsvp", "closing",
                   "host", "date_line", "qr"},
    "certificate": {"title", "subtitle", "recipient", "recipient_suffix", "recipients", "body", "award", "body_after",
                    "issuer", "date", "signers", "seal", "number"},
    "card": {"name", "name_en", "title", "org", "contacts", "qr", "slogan"},
    "brandkit": {"name", "tagline", "monogram", "name_en"},
    "tablecard": {"number", "label", "guests", "event", "date", "name", "role"},
    "h5": {"kicker", "title", "host", "guest", "default_guest", "invite_line", "salutation", "body", "closing", "when",
           "date_text", "big_number", "details", "venue", "address", "map", "schedule", "rsvp", "rsvp_url", "rsvp_label",
           "contacts", "date_line", "music", "share_title", "share_desc", "nav_label", "countdown_label", "after_label",
           "letter_label", "info_label", "schedule_label"},
}
KEYS["xhs"] = {"title", "sub", "kicker", "tag", "stickers", "badges", "items", "photos", "labels", "color", "colors", "series",
               "handle", "date", "app", "title_pos", "align", "font", "split", "cells"}
REQUIRED = {"invitation": ["title"], "card": ["name"], "h5": ["title"], "xhs": ["title"]}


CONCEPT_KEYS = {"idea", "scene", "interlock", "look", "headline_style"}
CONCEPT_KEYS |= {k + "_en" for k in CONCEPT_KEYS} | {"palette", "text"}
PHONE = re.compile(r"\d[\d\- ]{6,}\d")
PRICE = re.compile(r"[¥￥]\s*\d|\d+(\.\d+)?\s*元")


def check_concept(it, facts):
    """mode ai = the model draws the whole poster, text included. Only short, low-risk words go to the model."""
    errs, warns = [], []
    iid, typ, mode, k = it.get("id"), it.get("type"), it.get("mode", "layout"), it.get("concept")
    if mode not in ("layout", "ai"):
        errs.append(f"{iid}: mode '{mode}' unknown (layout or ai)")
    if mode == "ai" and typ != "poster":
        errs.append(f"{iid}: mode ai is for posters only; text on a {typ} must be exact, keep it on layout")
    if mode == "ai" and not (k and (k.get("scene") or k.get("scene_en"))):
        errs.append(f"{iid}: mode ai needs concept.scene, the picture the model draws (see poster-craft.md)")
    if not k:
        return errs, warns
    if not isinstance(k, dict):
        return errs + [f"{iid}: concept must be an object"], warns
    for key in k:
        if key not in CONCEPT_KEYS:
            warns.append(f"{iid}: concept.{key} is not used ({', '.join(sorted(CONCEPT_KEYS))})")
    for col in k.get("palette") or []:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(col)):
            errs.append(f"{iid}: concept.palette '{col}' must be a #RRGGBB colour")
    if not (k.get("interlock") or k.get("interlock_en")):
        warns.append(f"{iid}: concept.interlock missing; say exactly which thing covers which character (poster-craft.md)")
    raw = [t if isinstance(t, str) else (t or {}).get("text", "") for t in k.get("text") or []]
    lines, small = prompts.concept_texts(it, facts)
    if len(raw) > 5:
        errs.append(f"{iid}: concept.text has {len(raw)} labels; a model writes 5 or fewer reliably")
    for r in raw:
        filled = prompts.fill_facts(r, facts)
        if filled is None:
            warns.append(f"{iid}: concept text '{r}' needs a fact that is missing; it is left out of the prompt")
        elif len(filled.replace(" ", "")) > 18:
            warns.append(f"{iid}: concept text '{r}' is long; models misspell long small text, keep it to about 16 characters")
    if mode == "ai":
        if len("".join(lines)) > 12:
            warns.append(f"{iid}: headline has {len(''.join(lines))} characters; 4 to 8 reads best when the model draws it")
        for s in lines + [x["text"] for x in small]:
            if PHONE.search(s):
                errs.append(f"{iid}: '{s}' looks like a phone number; never let the model draw it, put it in content and use layout")
            elif PRICE.search(s):
                warns.append(f"{iid}: '{s}' is a price; a wrong digit costs money, check it in the image or move it to layout")
    return errs, warns


def validate(spec):
    errs, warns = [], []
    dirs, plats = load_ref("directions.json"), load_ref("platforms.json")
    b = spec.get("brand") or {}
    if b.get("direction") not in dirs:
        errs.append(f"brand.direction '{b.get('direction')}' unknown; pick one of {', '.join(dirs)}")
    ids = set()
    for it in spec.get("items") or []:
        iid = it.get("id")
        if not iid or iid in ids:
            errs.append(f"item id missing or repeated: {iid}")
        ids.add(iid)
        typ = it.get("type")
        if typ not in LAYOUTS:
            errs.append(f"{iid}: type '{typ}' unknown ({', '.join(LAYOUTS)})")
            continue
        if it.get("layout") and it["layout"] not in LAYOUTS[typ]:
            errs.append(f"{iid}: layout '{it['layout']}' unknown for {typ} ({', '.join(LAYOUTS[typ])})")
        for s in it.get("sizes") or []:
            if s not in plats and "x" not in s:
                errs.append(f"{iid}: size '{s}' unknown ({', '.join(plats)} or WxH)")
        c = it.get("content") or {}
        known = KEYS[typ]
        batch = it.get("batch") or []
        for k in REQUIRED.get(typ, []):
            if not c.get(k) and not (batch and all(isinstance(b, dict) and b.get(k) for b in batch)):
                errs.append(f"{iid}: content.{k} is required for {typ}")
        if typ == "certificate" and not (c.get("recipient") or c.get("recipients") or it.get("batch")):
            errs.append(f"{iid}: certificate needs content.recipient, content.recipients or batch")
        for k in c:
            if k not in known:
                warns.append(f"{iid}: content.{k} is not used by {typ} layouts")
        a = it.get("art") or {}
        if a.get("style"):
            import artstyle
            if a["style"] not in artstyle.STYLES:
                warns.append(f"{iid}: art.style '{a['style']}' unknown, flat is used ({', '.join(artstyle.STYLES)})")
        for g in a.get("ingredients") or []:
            if g not in MOTIFS:
                warns.append(f"{iid}: ingredient '{g}' unknown ({', '.join(sorted(MOTIFS))})")
        if a.get("motif") and a["motif"] not in MOTIFS:
            warns.append(f"{iid}: motif '{a['motif']}' unknown, a gift box is drawn instead ({', '.join(MOTIFS)})")
        if typ == "poster":
            h = (c.get("headline") or "").replace("**", "")
            if not h:
                errs.append(f"{iid}: headline is empty")
            for line in h.split("\n"):
                if len(line) > 12:
                    warns.append(f"{iid}: headline line '{line}' has {len(line)} characters; 8 or fewer per line reads best")
            if len(c.get("details") or []) > 4:
                warns.append(f"{iid}: more than 4 detail rows crowd a poster")
        e2, w2 = check_concept(it, spec.get("facts") or {})
        errs += e2
        warns += w2
        if typ == "xhs":
            lay = it.get("layout") or "photo"
            lines = [x for x in str(c.get("title") or "").replace("**", "").split("\n") if x.strip()]
            if lay in ("photo", "grid", "doodle") and any(len(x) > 9 for x in lines):
                warns.append(f"{iid}: title line over 9 characters; cover type reads best at 4 to 8 per line, break it with \\n")
            if lay == "photo" and not a.get("image") and not a.get("subject"):
                warns.append(f"{iid}: photo cover without art.image; a placeholder is drawn until the user's photo is added")
            if lay == "photo" and a.get("image") and not a.get("focus"):
                warns.append(f"{iid}: art.focus missing; look at the photo and give the face box [x, y, w, h] so the title stays off it")
            if lay in ("memo", "ranking") and not c.get("items"):
                errs.append(f"{iid}: {lay} cover needs content.items")
        if typ == "h5":
            if not (c.get("when") or {}).get("start"):
                warns.append(f"{iid}: content.when.start missing (like 2027-05-22T17:30); no countdown and no calendar button")
            if not c.get("rsvp_url"):
                warns.append(f"{iid}: content.rsvp_url missing; the RSVP button shows a placeholder until a questionnaire link is added")
        if typ == "menu":
            n = sum(len(s.get("items") or []) for s in c.get("sections") or [])
            if n == 0:
                errs.append(f"{iid}: menu has no items")
            if n > 40:
                warns.append(f"{iid}: {n} dishes; split into two menus or use a3")
    return errs, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--config")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--hd", action="store_true")
    a = ap.parse_args()
    spec_path = Path(a.spec).resolve()
    errs, warns = validate(load_json(spec_path))
    for w in warns:
        print("spec warn ", w)
    if errs:
        for e in errs:
            print("spec ERROR", e)
        sys.exit(2)
    if not a.no_images:
        import images
        images.run(spec_path, a.config)
    out, _ = render.render(spec_path, a.out, hd=a.hd)
    if not a.no_images:
        import aiposter
        aiposter.run(spec_path, out, a.config)
    import h5
    h5.build(spec_path, out)
    qa = check.run(spec_path, out)
    sheet.make(out)
    prompts.build(spec_path, out)
    brand_mod.build(spec_path, out)
    print(check.summary(qa))
    print(f"\n交付目录 {out}\n  成品图 *.png（印刷尺寸另有 *.pdf）\n  overview.png 总览\n  prompts.md 生图提示词\n"
          f"  brand.md / brand.json 品牌小卡\n  src/*.html 可编辑源文件\n  qa.json 检查结果"
          + ("\n  *-ai.png 生图模型按创意概念画的整张海报（字要看图核对），同名不带 -ai 的是排版版" if list(out.glob("*-ai.png")) else "")
          + ("\n  h5/*.html 手机互动页（-preview.png 长图预览，-links.md 每位宾客的专属链接）" if (out / "h5").exists() else ""))
    sys.exit(1 if qa["errors"] else 0)


if __name__ == "__main__":
    main()
