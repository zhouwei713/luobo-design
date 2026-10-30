"""Three directions to look at before choosing one.

  python directions.py spec.json [--dirs pop-fresh,festive-red,soft-pastel] [--item ID] [--size square]

Renders the main item once per direction, each with its own layout so the three differ in
structure and not only in colour, then puts them side by side with name, mood and palette:
OUT/directions/board.png plus one PNG per direction. Nothing in spec.json changes; once the user
picks, set brand.direction (and the item's layout) to the chosen pair and run pipeline.py.

Direction choice when --dirs is not given: spec.profile.direction_candidates, else the current
brand.direction plus one direction from each of the other two temperature groups.
"""
import argparse
import copy
import json
from pathlib import Path

from PIL import Image, ImageDraw

import render
from check import check_render
from common import festival_of, load_json, load_ref, resolve_tokens, spec_brand, save_json
from layouts import LAYOUTS
from sheet import font

TEMPERATURE = {
    "bold": ["pop-fresh", "festive-red", "sport-bold"],
    "middle": ["warm-hand", "soft-pastel", "campus-fresh", "guochao", "trust-blue", "garden-romance", "xi-red"],
    "quiet": ["clean-minimal", "editorial", "dark-premium"],
}
# which layout shows a direction at its best, in order of preference
LAYOUT_PREF = {
    "poster": {
        "pop-fresh": ["product-hero", "type-hero"], "festive-red": ["type-hero", "product-hero"],
        "sport-bold": ["type-hero", "product-hero"], "trust-blue": ["type-hero", "editorial"],
        "warm-hand": ["product-hero", "editorial"], "soft-pastel": ["product-hero", "editorial"],
        "campus-fresh": ["product-hero", "type-hero"], "guochao": ["editorial", "product-hero"],
        "clean-minimal": ["editorial", "product-hero"], "editorial": ["editorial", "type-hero"],
        "dark-premium": ["editorial", "product-hero"], "garden-romance": ["editorial", "product-hero"], "xi-red": ["editorial", "type-hero"],
    },
    "invitation": {k: (["split", "formal"] if k in TEMPERATURE["bold"] else ["formal", "split"])
                   for k in TEMPERATURE["bold"] + TEMPERATURE["middle"] + TEMPERATURE["quiet"]},
    "certificate": {k: (["modern", "classic"] if k in ("sport-bold", "trust-blue", "pop-fresh") else ["classic", "modern"])
                    for k in TEMPERATURE["bold"] + TEMPERATURE["middle"] + TEMPERATURE["quiet"]},
    "menu": {k: (["cards", "list"] if k in ("soft-pastel", "campus-fresh", "warm-hand", "pop-fresh") else ["list", "cards"])
             for k in TEMPERATURE["bold"] + TEMPERATURE["middle"] + TEMPERATURE["quiet"]},
}


def pick_dirs(spec, explicit=None):
    if explicit:
        return explicit
    cands = (spec.get("profile") or {}).get("direction_candidates")
    if cands:
        return cands[:12]
    cur = (spec.get("brand") or {}).get("direction") or "clean-minimal"
    group = next((g for g, ds in TEMPERATURE.items() if cur in ds), "middle")
    out = [cur]
    for g, ds in TEMPERATURE.items():
        if g != group:
            out.append(ds[0])
    return out[:3]


KEEP = {"notice", "number", "tent"}  # these layouts are what the item is, not a style: only colours change


def assign_layouts(item_type, dirs, photo=False, current=None):
    """One layout per direction, all different when the type has enough layouts."""
    if current in KEEP:
        return [current] * len(dirs)
    used, out = set(), []
    for d in dirs:
        prefs = list(LAYOUT_PREF.get(item_type, {}).get(d, []))
        if photo and item_type == "poster":
            prefs = ["photo-full"] + prefs
        rest = [l for l in LAYOUTS.get(item_type, []) if (l != "photo-full" or photo) and l not in KEEP]
        choice = next((l for l in prefs + rest if l not in used), (prefs + rest)[0])
        used.add(choice)
        out.append(choice)
    return out


def board(tiles, out_path, h=760, per_row=None):
    """tiles: [(png, letter, direction dict, layout)]. More than four options wrap onto several rows."""
    f_big, f_mid, f_small = font(34), font(24), font(20)
    gap, info_h = 36, 190
    ims = []
    for png, *_ in tiles:
        im = Image.open(png).convert("RGB")
        ims.append(im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS))
    n = len(ims)
    per_row = per_row or (n if n <= 4 else (5 if n in (9, 10) else 4))
    rows = [list(range(i, min(i + per_row, n))) for i in range(0, n, per_row)]
    row_h = h + info_h + gap
    W = max(sum(ims[i].width for i in r) + gap * (len(r) + 1) for r in rows)
    canvas = Image.new("RGB", (W, row_h * len(rows) + gap), "#F2F1EE")
    d = ImageDraw.Draw(canvas)
    for ri, r in enumerate(rows):
        x, top = gap, gap + ri * row_h
        for i in r:
            im, (png, letter, dd, layout) = ims[i], tiles[i]
            canvas.paste(im, (x, top))
            y = top + h + 18
            d.text((x, y), f"{letter}  {dd['name']}", fill="#1A1A1A", font=f_big)
            mood = dd["mood"]  # narrow tiles (phone pages): shorten the mood line instead of running into the next tile
            while d.textlength(mood, font=f_mid) > im.width and len(mood) > 2:
                mood = mood[:-2] + "…"
            d.text((x, y + 48), mood, fill="#555555", font=f_mid)
            d.text((x, y + 84), f"版式 {layout}", fill="#888888", font=f_small)
            sx = x
            for k in ("bg", "surface", "ink", "accent", "accent2"):
                c = dd["tokens"][k]
                d.rectangle((sx, y + 120, sx + 44, y + 160), fill=c, outline="#CCCCCC")
                sx += 52
            x += im.width + gap
    canvas.save(out_path)
    return out_path


def run(spec_path, dirs=None, item_id=None, size=None, out_dir=None):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    known = load_ref("directions.json")
    fest = festival_of(spec.get("festival"))
    modes = [None] * 12
    if fest and not dirs and not (spec.get("profile") or {}).get("direction_candidates"):
        # a festival job: the real question is festival colours or the shop's own, so show both,
        # plus one direction the festival suits
        cur = (spec.get("brand") or {}).get("direction") or fest["directions"][0]
        # festival colours would make a third option look like A again, so C keeps its own palette
        other = next((x for x in fest.get("directions", []) if x not in (cur, "festive-red")), None) \
            or next((x for x in ("guochao", "dark-premium", "clean-minimal") if x != cur))
        dirs, modes = [cur, cur, other], ["full", "accent", "accent"]
    else:
        dirs = pick_dirs(spec, dirs)
    for dname in dirs:
        if dname not in known:
            raise SystemExit(f"unknown direction {dname}")
    items = spec.get("items") or []
    item = next((i for i in items if i["id"] == item_id), items[0]) if items else None
    if not item:
        raise SystemExit("spec has no items")
    photo = bool((item.get("art") or {}).get("image")) and (item.get("art") or {}).get("image_fit") == "cover"
    layouts = assign_layouts(item["type"], dirs, photo, item.get("layout"))
    if modes[0] and item.get("layout"):
        layouts[0] = layouts[1] = item["layout"]  # A and B differ only in colour, so they share the layout
    size = size or ("square" if item["type"] == "poster" else ("h5" if item["type"] == "h5" else (item.get("sizes") or ["a4"])[0]))
    if item["type"] == "certificate":  # one sample person is enough to judge a direction
        c = item.get("content") or {}
        if c.get("recipients") or item.get("batch"):
            first = (c.get("recipients") or item.get("batch"))[0]
            item = copy.deepcopy(item)
            item.pop("batch", None)
            item["content"].pop("recipients", None)
            item["content"].update({"recipient": first} if isinstance(first, str) else first)
    out = Path(out_dir or spec_path.parent / "out") / "directions"
    out.mkdir(parents=True, exist_ok=True)
    tiles, meta = [], []
    for letter, dname, layout, mode in zip("ABCDEFGHIJKL", dirs, layouts, modes):
        s = copy.deepcopy(spec)
        s["brand"] = {**(s.get("brand") or {}), "direction": dname}
        if mode:
            s["festival"] = {"id": fest["_id"], "mode": mode}
        if mode != "accent":
            s["brand"].pop("tokens", None)  # show the direction as designed; brand colours come back after the pick
        it = copy.deepcopy(item)
        it.update({"id": f"{letter}-{dname}", "layout": layout, "sizes": [size]})
        if it["type"] == "h5":
            it["_h5_pages"] = ["cover"]  # the cover is enough to judge a direction
        s["items"] = [it]
        tmp = spec_path.parent / f".directions-{letter}-{dname}.json"  # beside the spec so image paths still resolve
        save_json(tmp, s)
        try:
            _, rep = render.render(tmp, out / f"{letter}-{dname}")
        finally:
            tmp.unlink(missing_ok=True)
        errs, warns, _ = check_render(rep["renders"][0], rep["tokens"])
        for e in errs:
            print(f"  {letter} {dname} ERROR {e}")
        png = rep["renders"][0]["png"]
        final = out / f"{letter}-{dname}.png"
        Path(png).replace(final)
        dd = dict(resolve_tokens(spec_brand(s)))
        if mode:
            own = dname == dirs[0]
            dd["name"] += f" · {fest['name']}配色" if mode == "full" else (" · 保留品牌色" if own else f" · {fest['name']}点缀")
            if mode == "accent" and own:
                dd["mood"] = f"平时的颜色不变，只加{fest['name']}的点缀和插画"
        tiles.append((final, letter, dd, layout))
        meta.append({"option": letter, "direction": dname, "festival_mode": mode, "layout": layout, "png": str(final), "errors": errs})
    b = board(tiles, out / "board.png")
    save_json(out / "options.json", {"item": item["id"], "size": size, "options": meta})
    return b, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--dirs", help="comma separated direction ids; three is the usual, up to twelve when the user wants more to compare")
    ap.add_argument("--item")
    ap.add_argument("--size")
    ap.add_argument("--out")
    a = ap.parse_args()
    b, meta = run(a.spec, a.dirs.split(",") if a.dirs else None, a.item, a.size, a.out)
    for m in meta:
        print(f"{m['option']}  {m['direction']:14s} {(m.get('festival_mode') or ''):7s} {m['layout']:13s} {m['png']}")
    print(f"board -> {b}")


if __name__ == "__main__":
    main()
