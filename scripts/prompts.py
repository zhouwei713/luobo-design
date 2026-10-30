"""Image prompts for every item, written for three model families, plus a one-shot poster prompt.

  python prompts.py spec.json [--out DIR]
Writes DIR/prompts.md (for people: copy and paste) and DIR/prompts.json (for images.py).

Two kinds of prompt per item:
  asset   the picture the layout needs (product cut-out or background scene); text is never drawn by
          the model, the layout sets it. This is what images.py sends when a model is configured.
  poster  the whole design in one image, text included, for people who want to paste one prompt into
          GPT Image / 即梦 / Nano Banana. Small text is left out on purpose: models still misspell it.
"""
import argparse
from pathlib import Path

from common import canvas, load_json, resolve_tokens, spec_brand, save_json

AVOID_EN = ("any text, letters, numbers, watermark, logo, extra objects, cluttered background, distorted shapes, "
            "plastic CGI look, oversaturated colours, purple-blue gradient")
AVOID_ZH = "文字、字母、数字、水印、logo、多余物体、杂乱背景、变形、塑料质感、过饱和、紫蓝渐变"
FOOD_EN = "appetising, fresh, real texture, tiny condensation droplets where it fits"
FOOD_ZH = "看起来很好吃，新鲜，真实质感"


KIND_EN = {"poster": "poster", "menu": "menu board", "invitation": "invitation card", "certificate": "certificate",
           "card": "business card"}
KIND_ZH = {"poster": "海报", "menu": "菜单", "invitation": "邀请函", "certificate": "证书", "card": "名片"}


def logo_prompts(item, brand, d):
    """Logo concepts. The model draws the symbol; the Chinese wordmark is set from real fonts afterwards."""
    c = item.get("content") or {}
    t = d["tokens"]
    name = c.get("name") or brand.get("name") or ""
    a = item.get("art") or {}
    idea_en = a.get("subject_en") or a.get("subject") or "a simple symbol that fits the brand"
    idea_zh = a.get("subject") or "一个能代表品牌的简洁图形"
    gpt = (f"Use case: logo symbol for \"{name}\", a {d['name_en']} style brand ({d['mood']}).\n"
           f"Subject: {idea_en}. One bold, simple, memorable symbol, readable at 32 px.\n"
           f"Style: flat vector logo mark, solid shapes, at most two colours {t['accent']} and {t['ink']}, no gradients, no shadows.\n"
           f"Layout: centred on a plain white background, generous margin, a 3 by 3 grid of nine different concepts.\n"
           f"Avoid: any text or letters, mockups, 3D, photorealism, clip-art look, purple-blue gradient.")
    seed = (f"为品牌“{name}”设计 logo 图形，{d['name']}风格，{d['mood']}。主体：{idea_zh}。扁平矢量风格，实心几何形，"
            f"最多两种颜色 {t['accent']} 和 {t['ink']}，不要渐变和阴影，图形简洁好记，缩小到很小也能认出来。"
            f"白色背景，九宫格排列九个不同方案，四周留白。不要出现任何文字和字母，不要样机，不要立体效果。")
    nano = (f"Sketch nine different logo symbols for a brand called {name}, laid out in a clean 3 by 3 grid on white. "
            f"Each is a flat vector mark built from a few solid shapes in {t['accent']} and {t['ink']}, inspired by {idea_en}, "
            f"simple enough to recognise at favicon size. No text, no gradients, no mockups.")
    return {"mode": "logo", "aspect": "1:1", "gpt-image-2": gpt, "seedream": seed, "nano-banana": nano}


def ratio(w, h):
    from math import gcd
    w, h = round(w), round(h)
    g = gcd(w, h)
    r = f"{w // g}:{h // g}"
    common = {"3:4": 0.75, "4:5": 0.8, "1:1": 1, "9:16": 0.5625, "16:9": 1.778, "4:3": 1.333, "2:3": 0.667, "3:2": 1.5}
    return r if r in common else min(common, key=lambda k: abs(common[k] - w / h))


def asset_slot(item):
    """What the layout needs from a model for this item, and in which shape."""
    a = item.get("art") or {}
    lay = item.get("layout") or ""
    xhs_photo = item.get("type") == "xhs" and (lay or "photo") == "photo"
    mode = a.get("mode") or ("scene" if lay == "photo-full" or xhs_photo else "cutout")
    size = (item.get("sizes") or ["portrait"])[0]
    cv = canvas(size)
    if mode == "scene":
        return mode, ratio(cv["w"], cv["h"])
    return mode, ("3:4" if lay in ("art-hero", "art-frame") else "4:5")  # art layouts give the drawing a tall slot


def festival_words(d):
    f = d.get("festival")
    if not f:
        return "", ""
    return (f" Festive theme for {f['name']} (Chinese calendar occasion), with tasteful seasonal details.",
            f"带{f['name']}的节日氛围，节日元素点到为止。")


def asset_prompts(item, d, industry):
    a = item.get("art") or {}
    fe_en, fe_zh = festival_words(d)
    mode, ar = asset_slot(item)
    t = d["tokens"]
    k = item.get("concept") or {}  # without its own subject the picture follows the concept scene
    subj_en = a.get("subject_en") or a.get("subject") or k.get("scene_en") or k.get("scene") or "the product"
    subj_zh = a.get("subject") or a.get("subject_en") or k.get("scene") or "产品"
    art_avoid_en = art_avoid_zh = ""
    if d.get("_art_style"):  # the style comes first and the subject is described in its terms
        import artstyle
        subj_en, subj_zh, art_avoid_en, art_avoid_zh = artstyle.styled_subject(d["_art_style"], subj_en, subj_zh)
    setting_en = a.get("setting_en") or ""
    setting_zh = a.get("setting") or ""
    food = industry == "food" and not d.get("_art_style")  # an art style replaces the food-photo look
    palette_en = f"brand colours {t['accent']} and {t['accent2']} as small accents, background family {t['bg']}"
    palette_zh = f"点缀品牌色 {t['accent']} 和 {t['accent2']}，整体色调接近 {t['bg']}"
    if mode == "cutout":
        gpt = (f"Use case: product cut-out for a {d['name_en']} style {item['type']}; it will be placed on a coloured layout.\n"
               f"Subject: {subj_en}. Single object, centred, fully visible with a little margin on every side.\n"
               f"Background: plain pure white, soft contact shadow only.\n"
               f"Style: {d['image_style']}{', ' + FOOD_EN if food else ''}.\n"
               f"Palette: {palette_en}.\n"
               f"Lighting: soft studio light from the upper left, gentle highlight on the edges.{fe_en}\n"
               f"Aspect ratio: {ar}.\nAvoid: {AVOID_EN}, hands, cropped edges.")
        nano = (f"{'An illustration' if d.get('_art_style') else 'A studio product shot'} of {subj_en}, alone and centred on a plain pure white background with a soft "
                f"contact shadow, fully in frame with breathing room around it. The look is {d['image_style']}"
                f"{', ' + FOOD_EN if food else ''}; small touches of {t['accent']} and {t['accent2']}. "
                f"Soft light from the upper left. No text, no logo, no hands. Aspect ratio {ar}.")
        seed = (f"{subj_zh}，单个主体居中，完整入画，四周留白，纯白背景，只有柔和的接触阴影，"
                f"{d['name']}风格，{d.get('image_style_zh', '') + '，' if d.get('_art_style') else ''}{FOOD_ZH + '，' if food else ''}{palette_zh}，左上方柔光，{fe_zh}"
                f"画面比例 {ar}，不要：{AVOID_ZH}、手、主体被裁切")
    else:
        cover = item.get("type") == "xhs"  # a note cover: the headline goes on top, the subject fills the rest
        keep = a.get("keep_clear") or ("top 30%" if cover else "lower 40%")
        keep_zh = a.get("keep_clear_zh") or ("上方 30%" if cover else "下方 40%")
        where_en = "the lower two thirds, close up and filling the frame" if cover else "the upper half"
        where_zh = "画面下方三分之二，近景，占满画面" if cover else "画面上半部分"
        gpt = (f"Use case: full-bleed background photo for a {d['name_en']} style {item['type']}; headline text will be set on top later.\n"
               f"Subject: {subj_en}.{(' Setting: ' + setting_en + '.') if setting_en else ''}\n"
               f"Composition: main subject in {where_en}; keep the {keep} calm, simple and slightly darker so text stays readable.\n"
               f"Style: {d['image_style']}{', ' + FOOD_EN if food else ''}.\n"
               f"Palette: {palette_en}.\nAspect ratio: {ar}.\nAvoid: {AVOID_EN}.")
        nano = (f"A photograph of {subj_en}{(' in ' + setting_en) if setting_en else ''}, framed so the subject sits in "
                f"{where_en} while the {keep} stays calm, simple and a little darker for a headline. The look is "
                f"{d['image_style']}{', ' + FOOD_EN if food else ''}. Colour accents {t['accent']} and {t['accent2']}. "
                f"No text or logos. Aspect ratio {ar}.")
        seed = (f"{subj_zh}{('，' + setting_zh) if setting_zh else ''}，主体在{where_zh}，{keep_zh}保持干净简洁、略暗，"
                f"方便后期放标题，{d['name']}风格，{d.get('image_style_zh', d['image_style'])}，{FOOD_ZH + '，' if food else ''}{palette_zh}，"
                f"画面比例 {ar}，不要：{AVOID_ZH}")
    if d.get("_art_style"):
        lead_en = f"Art style comes first and must hold in every detail: {d['image_style']}.\n"
        gpt = lead_en + gpt.replace("Lighting: soft studio light from the upper left, gentle highlight on the edges.", "Lighting: whatever suits the art style.")
        gpt = gpt.replace("Avoid: ", f"Avoid: {art_avoid_en}, ", 1)
        nano = (f"In the style of {d['image_style']}: " + nano.replace("Soft light from the upper left. ", "")
                + f" Strictly avoid {art_avoid_en}.")
        seed = (f"画风最重要：{d.get('image_style_zh', d['image_style'])}。" + seed.replace("左上方柔光，", "")).replace("不要：", f"不要：{art_avoid_zh}、", 1)
    return {"mode": mode, "aspect": ar, "gpt-image-2": gpt, "nano-banana": nano, "seedream": seed}


def poster_prompts(item, brand, d):
    """Whole poster in one image. Only big text; everything small is added by hand afterwards."""
    fe_en, fe_zh = festival_words(d)
    c = item.get("content") or {}
    t = d["tokens"]
    size = (item.get("sizes") or ["portrait"])[0]
    cv = canvas(size)
    ar = ratio(cv["w"], cv["h"])
    a = item.get("art") or {}
    subj_zh = a.get("subject") or "主产品"
    subj_en = a.get("subject_en") or a.get("subject") or "the product"
    head = (c.get("headline") or c.get("title") or c.get("name") or "").replace("**", "")
    offer = (c.get("offer") or {}).get("big")
    name = brand.get("name")
    lines = head.split("\n")
    quoted_zh = "”和“".join(lines)
    quoted_en = '" / "'.join(lines)
    gpt = (f"A {d['name_en']} style {KIND_EN.get(item['type'], 'poster')} for {name or 'a local shop'}, aspect ratio {ar}.\n"
           f"Layout: top third holds the headline in very large bold Chinese characters, set exactly as \"{quoted_en}\""
           f"{' (one line each)' if len(lines) > 1 else ''}; centre shows {subj_en}; "
           + (f"a round sticker at the upper right of the product reads exactly \"{offer}\"; " if offer else "")
           + (f"small brand name \"{name}\" at the top left; " if name else "")
           + "bottom 18% is an empty light panel with no text (details are added later).\n"
           f"Colours: background {t['bg']}, text {t['ink']}, accent {t['accent']}, secondary {t['accent2']}.\n"
           f"Style: {d['image_style']}. Clean print-ready graphic design, generous margins.{fe_en}\n"
           f"Render only the quoted text, spelled exactly, nothing else written anywhere.")
    seed = (f"一张{d['name']}风格的{KIND_ZH.get(item['type'], '海报')}，画面比例 {ar}。"
            f"上方三分之一是超大号粗体中文标题，逐字写“{quoted_zh}”{'，分行排列' if len(lines) > 1 else ''}；"
            f"中间是{subj_zh}；"
            + (f"产品右上角一个圆形贴纸，写“{offer}”；" if offer else "")
            + (f"左上角小字品牌名“{name}”；" if name else "")
            + f"底部留出约 18% 的空白浅色区域，不写任何字。配色：背景 {t['bg']}，文字 {t['ink']}，强调色 {t['accent']}，辅助色 {t['accent2']}。"
            f"{d.get('image_style_zh', d['image_style'])}，干净的平面设计，四周留足边距。{fe_zh}除了引号里的文字，画面上不要出现其他任何文字。")
    nano = (f"Design a {d['name_en']} style {KIND_EN.get(item['type'], 'poster')} in aspect ratio {ar}. "
            f"Across the top third, the headline in large bold Chinese characters reading exactly \"{quoted_en}\". "
            f"In the middle, {subj_en}. "
            + (f"A round sticker near the product says \"{offer}\". " if offer else "")
            + f"Leave the bottom fifth as a plain light panel without text. Background {t['bg']}, accents {t['accent']} "
            f"and {t['accent2']}. {d['image_style']}. No other text anywhere.")
    return {"aspect": ar, "gpt-image-2": gpt, "seedream": seed, "nano-banana": nano}


ORIENT = {"portrait": ("vertical", "竖版"), "square": ("square", "方形"), "landscape": ("horizontal", "横版")}
OCCLUDE_EN = ("Every headline character must stay readable. Anything placed in front of a character covers at most "
              "a third of it, and the first character stays fully visible.")
OCCLUDE_ZH = "标题每个字都要认得出，挡在字前面的东西最多盖住这个字的三分之一，第一个字完整露出。"


def fill_facts(s, facts):
    """{date} -> the fact; None when a fact is missing (a model must never draw a placeholder)."""
    import re
    miss = [m for m in re.findall(r"\{([a-z_]+)\}", s) if not (facts or {}).get(m)]
    if miss or "【" in s:
        return None
    return re.sub(r"\{([a-z_]+)\}", lambda m: str(facts[m.group(1)]), s)


def concept_texts(item, facts=None):
    """The words the model is allowed to draw: the headline plus a few short labels."""
    c = item.get("content") or {}
    k = item.get("concept") or {}
    head = (c.get("headline") or "").replace("**", "")
    lines = [x for x in (fill_facts(head, facts) or head).split("\n") if x.strip()]
    small = []
    for t in k.get("text") or []:
        t = dict(text=t) if isinstance(t, str) else dict(t)
        t["text"] = fill_facts(t.get("text") or "", facts)
        if t["text"]:
            small.append(t)
    return lines, small


def concept_prompts(item, brand, d, size=None, facts=None):
    """Whole poster from the concept card: the model draws picture and text together.

    The concept is written by the designer (you), the script only assembles it so every prompt carries
    the same safeguards: exact quoted text, a short whitelist of words, the occlusion limit, the palette."""
    k = item.get("concept") or {}
    t = d["tokens"]
    size = size or (item.get("sizes") or ["portrait"])[0]
    cv = canvas(size)
    ar = ratio(cv["w"], cv["h"])
    shape = "portrait" if cv["w"] < cv["h"] * 0.95 else ("landscape" if cv["w"] > cv["h"] * 1.05 else "square")
    o_en, o_zh = ORIENT[shape]
    name = brand.get("name") or ""
    kind_en, kind_zh = KIND_EN.get(item["type"], "poster"), KIND_ZH.get(item["type"], "海报")
    lines, small = concept_texts(item, facts)
    pal = k.get("palette") or [t["bg"], t["ink"], t["accent"]]
    accent = pal[-1]

    def en(key):
        return k.get(key + "_en") or k.get(key) or ""

    def zh(key):
        return k.get(key) or k.get(key + "_en") or ""

    q_en = " / ".join(f"\"{x}\"" for x in lines)
    q_zh = "”“".join(lines)
    small_en = ", ".join(f"\"{s['text']}\" {s.get('where_en') or s.get('where') or ''}".strip() for s in small)
    small_zh = "，".join(f"{s.get('where') or s.get('where_en') or ''}写“{s['text']}”" for s in small)
    hs_en = en("headline_style") or "massive heavy Chinese sans serif, tightly set"
    hs_zh = zh("headline_style") or "超粗黑体，字距紧"
    custom = k.get("headline_style") or k.get("headline_style_en")  # a written style says its own line count
    nlines_en = f", {len(lines)} lines" if len(lines) > 1 and not custom else ""
    nlines_zh = f"，分{len(lines)}行" if len(lines) > 1 and not custom else ""
    for_en = f" for {name}" if name else ""
    for_zh = f"，品牌叫“{name}”" if name else ""
    idea_en = en("idea")
    gpt = (f"A {o_en} {ar} {kind_en}{for_en}. One idea carries the whole design"
           + (f", {idea_en}" if idea_en else "") + ".\n"
           f"{en('scene')}\n"
           f"The headline reads exactly {q_en} in {hs_en}{nlines_en}, the biggest thing on the page.\n"
           + (f"{en('interlock')} " if k.get("interlock") or k.get("interlock_en") else "") + OCCLUDE_EN + "\n"
           + (f"A few tiny supporting texts used as decoration, {small_en}.\n" if small else "")
           + f"Main colours {', '.join(pal)}, nothing else competing with them; the accent {accent} appears in one or two places only.\n"
           + (f"{en('look')}\n" if k.get("look") or k.get("look_en") else "")
           + "Generous empty space, clean print-ready graphic design. Render only the quoted text, spelled exactly, "
             "no other writing anywhere, no watermark.")
    seed = (f"一张{o_zh} {ar} 的{kind_zh}{for_zh}。整张图只讲一个想法"
            + (f"，{zh('idea')}" if k.get("idea") else "") + "。"
            f"{zh('scene')}"
            f"标题逐字写“{q_zh}”，{hs_zh}{nlines_zh}，是画面里最大的东西。"
            + (f"{zh('interlock')}。" if k.get("interlock") or k.get("interlock_en") else "") + OCCLUDE_ZH
            + (f"小字只当装饰，{small_zh}。" if small else "")
            + f"主色是 {'、'.join(pal)}，别的颜色不要抢戏，强调色 {accent} 只出现在一两处。"
            + (f"{zh('look')}。" if k.get("look") else "")
            + "大量留白，干净的平面设计。除了引号里的字，画面上不要出现其他任何文字，不要水印。")
    seed = seed.replace("。。", "。")
    nano = (f"Design a {o_en} {kind_en}{for_en} in aspect ratio {ar}. {en('scene')} "
            f"The headline, as large as possible, reads exactly {q_en} in {hs_en}. "
            + (f"{en('interlock')} " if k.get("interlock") or k.get("interlock_en") else "")
            + "Keep every headline character readable. "
            + (f"Tiny decorative labels {small_en}. " if small else "")
            + f"Palette {', '.join(pal)}, accent {accent} used sparingly. {en('look')} No other text anywhere.")
    return {"aspect": ar, "size": size, "texts": lines + [s["text"] for s in small],
            "gpt-image-2": gpt, "seedream": seed, "nano-banana": nano}


MODEL_NOTES = {
    "gpt-image-2": "GPT Image 2：排版和指定文字最听话；尺寸只有 1024x1024 / 1024x1536 / 1536x1024，选最接近的比例；没有透明背景，抠图要在本地去白底。",
    "seedream": "Seedream / 即梦：中文提示词效果最好，大号中文标题基本能写对，小字容易错；建议出 2K 以上。",
    "nano-banana": "Nano Banana 2（gemini-3.1-flash-image）：照片质感和材质最好，用一段自然的描述比堆关键词更好；中文字偏弱，尽量不让它写字。",
}


def build(spec_path, out_dir=None):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    out = Path(out_dir or spec_path.parent / "out")
    brand = spec.get("brand") or {}
    d = resolve_tokens(spec_brand(spec))
    industry = (spec.get("profile") or {}).get("industry", "")
    data, md = {}, [f"# {spec.get('project') or brand.get('name') or '设计'}：生图提示词\n",
                    f"视觉方向：{d['name']}（{d['id']}）。每个提示词都能直接复制到对应平台使用。\n",
                    "## 三个模型怎么选\n"] + [f"- {v}" for v in MODEL_NOTES.values()] + [""]
    for it in spec.get("items", []):
        if it["type"] == "h5":
            continue  # phone pages reuse the vector motifs; a cover photo can be generated with the poster prompts
        if it["type"] == "brandkit":
            lp = logo_prompts(it, brand, d)
            data[it["id"]] = {"logo": lp}
            md += [f"## {it['id']}：logo 图形方案\n",
                   "让模型只画图形，一次出九个方案挑选。中文字标别让模型写，用 brandkit 里排好的字标和选中的图形组合。\n"]
            for m in ("gpt-image-2", "seedream", "nano-banana"):
                md += [f"**{m}**\n", "```text", lp[m], "```", ""]
            continue
        import artstyle
        di = artstyle.styled_direction(d, (it.get("art") or {}).get("style"))
        ap = asset_prompts(it, di, industry)
        if it["type"] == "xhs":
            if not (it.get("art") or {}).get("subject"):
                continue  # a note cover built from the user's photos needs no prompt
            data[it["id"]] = {"asset": ap}
            md += [f"## {it['id']}：小红书封面的画面，比例 {ap['aspect']}\n",
                   "只生成画面，字由排版程序压上去。真人出镜的封面更推荐用自己拍的照片。\n"]
            for m in ("gpt-image-2", "seedream", "nano-banana"):
                md += [f"**{m}**\n", "```text", ap[m], "```", ""]
            continue
        if it.get("concept"):
            cp = concept_prompts(it, brand, d, facts=spec.get("facts"))
            data[it["id"]] = {"asset": ap, "concept": cp}
            k = it["concept"]
            md += [f"## {it['id']}\n", f"### 按创意概念一步出整张图，比例 {cp['aspect']}（推荐）\n",
                   f"想法是“{k.get('idea', '')}”。模型连图带字一起画，出图后要逐字核对这几处文字："
                   + "、".join(f"“{x}”" for x in cp["texts"]) + "。\n"]
            for m in ("gpt-image-2", "seedream", "nano-banana"):
                md += [f"**{m}**\n", "```text", cp[m], "```", ""]
            kind = "抠图素材" if ap["mode"] == "cutout" else "整幅背景图"
            md += [f"### 只要画面，字由排版程序来排：{kind}，比例 {ap['aspect']}\n"]
            for m in ("gpt-image-2", "seedream", "nano-banana"):
                md += [f"**{m}**\n", "```text", ap[m], "```", ""]
            continue
        pp = poster_prompts(it, brand, di)
        data[it["id"]] = {"asset": ap, "poster": pp}
        kind = "抠图素材（放进版式里，字由排版程序来排）" if ap["mode"] == "cutout" else "整幅背景图（标题后期叠在上面）"
        md += [f"## {it['id']}\n", f"### 素材图：{kind}，比例 {ap['aspect']}\n"]
        for m in ("gpt-image-2", "seedream", "nano-banana"):
            md += [f"**{m}**\n", "```text", ap[m], "```", ""]
        md += [f"### 整张图一步生成（含大标题），比例 {pp['aspect']}\n",
               "想在生图平台里直接出一张完整的图时用这组。小字（地址、电话、价格）不让模型写，出图后自己加，或者用排版版本。\n"]
        for m in ("gpt-image-2", "seedream", "nano-banana"):
            md += [f"**{m}**\n", "```text", pp[m], "```", ""]
    out.mkdir(parents=True, exist_ok=True)
    save_json(out / "prompts.json", data)
    (out / "prompts.md").write_text("\n".join(md), encoding="utf-8")
    return out / "prompts.md"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    a = ap.parse_args()
    print(build(a.spec, a.out))
