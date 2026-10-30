"""Generate the picture each item needs with the configured image model.

  python images.py spec.json [--config PATH] [--force]

Uses the asset prompt from prompts.py for the provider's model family, saves images/<item>.png
next to the spec and writes art.image back into the spec. Cut-outs get their white background removed.
No provider configured -> nothing happens and the layouts keep their procedural art.
"""
import argparse
from pathlib import Path

from common import load_json, resolve_tokens, spec_brand, save_json
from imagegen import ImageGen, find_config, remove_background, trim_transparent
from prompts import asset_prompts

FAMILY = {"openai": "gpt-image-2", "ark": "seedream", "gemini": "nano-banana"}


def run(spec_path, config=None, force=False):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    cfg = find_config(config, spec_path.parent)
    gen = ImageGen(cfg)
    ok, why = gen.available()
    if not ok:
        print(f"images: skipped ({why}); layouts use procedural art, prompts.md has the prompts")
        return 0
    d = resolve_tokens(spec_brand(spec))
    industry = (spec.get("profile") or {}).get("industry", "")
    fam = FAMILY.get(gen.provider, "gpt-image-2")
    made = 0
    for it in spec.get("items", []):
        a = it.setdefault("art", {})
        if a.get("image") and not (force and a.get("generated")):
            continue
        if it.get("layout") == "notice" and not (a.get("motif") or a.get("subject")):
            continue  # a plain notice has no picture; generating one would be paid for and then shown uninvited
        if it["type"] == "xhs" and ((it.get("layout") or "photo") not in ("photo", "doodle") or not a.get("subject")):
            continue  # note covers use the user's own photos; the model only paints when a subject is written
        if it.get("mode") == "ai":
            continue  # the model draws the whole poster in aiposter.py; its layout fallback keeps procedural art
        if a.get("generate") is False or it["type"] in ("brandkit", "card", "certificate", "h5"):
            continue  # logos and documents keep vector marks; their prompts are in prompts.md
        import artstyle
        p = asset_prompts(it, artstyle.styled_direction(d, a.get("style")), industry)
        prompt = p[fam]
        if p["mode"] == "cutout" and gen.provider == "hiapi":  # native transparency: ask for an isolated subject, not white
            prompt = prompt.replace("Background: plain pure white, soft contact shadow only.",
                                    "Background: none, fully transparent. Isolated subject only, no scene, no shadow.")
        w, h = (int(x) for x in p["aspect"].split(":"))
        out = spec_path.parent / "images" / f"{it['id']}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            img, native = gen.generate(prompt, w * 256, h * 256, transparent=(p["mode"] == "cutout"), out=str(out))
        except Exception as e:  # noqa: BLE001
            print(f"images: {it['id']} failed ({e}); keeping procedural art")
            continue
        if p["mode"] == "cutout" and not native:
            img = trim_transparent(remove_background(img))
        img.save(out)
        a["image"] = f"images/{out.name}"
        a["generated"] = True
        a["image_fit"] = "contain" if p["mode"] == "cutout" else "cover"
        if it["type"] == "xhs" and p["mode"] == "scene":
            a.setdefault("focus", [0.05, 0.32, 0.9, 0.63])  # the prompt asked for the subject low and a calm top
        made += 1
        print(f"images: {it['id']} -> {a['image']} ({gen.provider}:{gen.model})")
    if made:
        save_json(spec_path, spec)
    return made


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--config")
    ap.add_argument("--force", action="store_true", help="regenerate images made by an earlier run")
    a = ap.parse_args()
    run(a.spec, a.config, a.force)
