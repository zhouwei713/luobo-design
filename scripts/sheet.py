"""Contact sheet of every rendered file, one row per item, labelled with size and QA marks.

  python sheet.py OUT_DIR [--h 640]
Writes OUT_DIR/overview.png. Reads OUT_DIR/qa.json when present to mark files with problems.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/System/Library/Fonts/PingFang.ttc",
              "C:/Windows/Fonts/msyh.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make(out_dir, h=640):
    out = Path(out_dir)
    rep = json.loads((out / "render_report.json").read_text(encoding="utf-8"))
    qa = {}
    if (out / "qa.json").exists():
        for f in json.loads((out / "qa.json").read_text(encoding="utf-8")).get("files", []):
            qa[f["name"]] = f
    rows, order = {}, []
    for r in rep["renders"]:
        if r["item"] not in rows:
            rows[r["item"]] = []
            order.append(r["item"])
        rows[r["item"]].append(r)
    aip = out / "ai_report.json"
    if aip.exists():  # whole posters from the model sit first in their item's row
        for r in json.loads(aip.read_text(encoding="utf-8")).get("posters", []):
            if r.get("png") and Path(r["png"]).exists():
                if r["item"] not in rows:
                    rows[r["item"]] = []
                    order.append(r["item"])
                rows[r["item"]].insert(0, {**r, "layout": "AI 整图"})
    gap, lab = 28, 46
    f = font(24)
    built = []
    for item in order:
        tiles = []
        for r in rows[item]:
            im = Image.open(r["png"]).convert("RGB")
            im = im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)
            tiles.append((r, im))
        w = sum(im.width for _, im in tiles) + gap * (len(tiles) - 1)
        row = Image.new("RGB", (w, h + lab), "#ECECEC")
        d = ImageDraw.Draw(row)
        x = 0
        for r, im in tiles:
            row.paste(im, (x, lab))
            name = r.get("name") or f"{r['item']}-{r['size']}"
            q = qa.get(name, {})
            mark = "  ✗ " + str(len(q.get("errors", []))) if q.get("errors") else ("  ! " + str(len(q.get("warnings", []))) if q.get("warnings") else "  ✓")
            d.text((x, 8), f"{r['size']}  {r.get('layout') or ''}{mark}", fill="#C0392B" if q.get("errors") else "#333", font=f)
            x += im.width + gap
        built.append(row)
    W = max(r.width for r in built) + 2 * gap
    H = sum(r.height for r in built) + gap * (len(built) + 1)
    sheet = Image.new("RGB", (W, H), "#ECECEC")
    y = gap
    for r in built:
        sheet.paste(r, (gap, y))
        y += r.height + gap
    p = out / "overview.png"
    sheet.save(p)
    return p


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--h", type=int, default=640)
    a = ap.parse_args()
    print(make(a.out, a.h))
