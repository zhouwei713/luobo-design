"""Write the brand file: brand.md for people, brand.json for the next design (and other skills).

  python brand.py spec.json [--out DIR]

The next time the same shop or account asks for something, put brand.json's values back into
spec.brand (direction, tokens, fonts, voice) and every new item matches the old ones.
"""
import argparse
from pathlib import Path

from common import SKILL_VERSION, contrast, load_json, load_ref, resolve_tokens, spec_brand, save_json

ROLE_ZH = {"bg": ("底色", "大面积背景，约占画面六到八成"), "surface": ("卡片色", "信息卡、价目区的底"),
           "ink": ("主文字", "标题和正文"), "muted": ("次文字", "说明、备注"),
           "accent": ("强调色", "优惠、价格、贴纸，一屏最多两处"), "accent2": ("辅助色", "小装饰、吸管、星星这类点缀")}


def build(spec_path, out_dir=None):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    out = Path(out_dir or spec_path.parent / "out")
    brand = spec.get("brand") or {}
    d = resolve_tokens(brand)  # the brand card never stores a festival palette
    t = d["tokens"]
    fonts = load_ref("fonts.json")
    prof = spec.get("profile") or {}
    name = brand.get("name") or spec.get("project") or "未命名"
    data = {"name": name, "direction": d["id"], "tokens": {k: t[k] for k in ROLE_ZH},
            "fonts": {"display": d["display"], "body": d["body"]}, "shape": d["shape"],
            "pattern": d.get("pattern"), "texture": d.get("texture"), "image_style": d["image_style"],
            "voice": brand.get("voice"), "tagline": brand.get("tagline"), "logo": brand.get("logo"),
            "made_with": f"luobo-design {SKILL_VERSION}"}
    md = [f"# {name} 品牌小卡\n",
          f"视觉方向是「{d['name']}」，{d['mood']}。以后做新物料时把 brand.json 交给 luobo-design，配色、字体和气质会自动对上。\n",
          "## 颜色\n", "| 角色 | 色值 | 用在哪 | 和底色的对比度 |", "|---|---|---|---|"]
    for k, (zh, use) in ROLE_ZH.items():
        md.append(f"| {zh} | `{t[k]}` | {use} | {contrast(t[k], t['bg']):.1f} |")
    disp, body = fonts.get(d["display"]["font"], {}), fonts.get(d["body"]["font"], {})
    md += ["", "## 字体\n",
           f"标题用 {disp.get('family')}，{disp.get('feel', '')}，授权 {disp.get('license', '系统字体')}。",
           f"正文用 {body.get('family')}，{body.get('feel', '')}，授权 {body.get('license', '系统字体')}。",
           "中文标题行距 1.2 左右，正文 1.5，中文不要压字距。一张图最多两种字体、三种字重。", "",
           "## 形状和质感\n",
           f"圆角 {d['shape']['radius']} 个单位（短边的百分之一为一个单位），装饰风格 {d['shape'].get('deco')}，"
           f"底纹 {d.get('pattern')}，质感 {d.get('texture')}。", "",
           "## 配图风格\n", f"写生图提示词时把这句放进风格部分：{d['image_style']}", "",
           "## 要避开的\n", d.get("avoid", ""), ""]
    if brand.get("voice"):
        md += ["## 说话的语气\n", brand["voice"], ""]
    src = []
    for k, zh in (("confirmed", "用户确认的"), ("inferred", "根据描述推断的"), ("defaulted", "用了默认值的"), ("missing", "还缺的")):
        if prof.get(k):
            src.append(f"- {zh}：{'；'.join(prof[k])}")
    if src:
        md += ["## 这些设定从哪来\n"] + src + [""]
    out.mkdir(parents=True, exist_ok=True)
    save_json(out / "brand.json", data)
    (out / "brand.md").write_text("\n".join(md), encoding="utf-8")
    return out / "brand.md"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out")
    a = ap.parse_args()
    print(build(a.spec, a.out))
