"""Brand profiles: what a shop or account settled on, kept for the next order.

  python brands.py list                         # saved brands, newest first
  python brands.py show NAME                    # one profile as JSON
  python brands.py apply spec.json [--name NAME] [--force]
        fill spec.brand and spec.facts from the profile (what the spec already says wins, unless --force)
  python brands.py save spec.json [--out DIR]   # pipeline.py does this after every run
  python brands.py forget NAME

A profile holds the direction, brand colours and fonts, voice, tagline, logo (copied in) and the facts
that rarely change: phone, address, WeChat, opening hours, QR code. Event facts (dates, prices, coupons)
are never kept. The library lives in ~/.config/luobo-design/brands/ (LUOBO_DESIGN_HOME moves it);
a luobo-brands/ folder in the working directory is used instead when one exists.
Set "remember": false in spec.brand to keep a brand out of the library.
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from common import SKILL_VERSION, load_json, save_json

STABLE_FACTS = ("phone", "address", "wechat", "hours", "qr", "website", "store", "douyin", "xhs", "email", "org", "slogan")
BRAND_KEYS = ("direction", "tokens", "fonts", "voice", "tagline", "name_en", "logo")


def library():
    local = Path.cwd() / "luobo-brands"
    if local.is_dir():
        return local
    home = os.environ.get("LUOBO_DESIGN_HOME")
    root = Path(home).expanduser() if home else Path.home() / ".config" / "luobo-design"
    return root / "brands"


def slug(name):
    s = re.sub(r"[\s/\\:*?\"<>|]+", "-", name.strip()).strip("-.")
    return s[:60] or "brand"


def profile_path(name):
    return library() / slug(name) / "brand.json"


def all_profiles():
    lib = library()
    out = []
    if lib.is_dir():
        for p in lib.glob("*/brand.json"):
            try:
                out.append(load_json(p))
            except Exception:  # noqa: BLE001
                continue
    return sorted(out, key=lambda d: d.get("updated", ""), reverse=True)


def find(name):
    """Exact name first, then an alias, then a name that contains / is contained in the query."""
    if not name:
        return None
    p = profile_path(name)
    if p.exists():
        return load_json(p)
    q = name.strip()
    profs = all_profiles()
    for d in profs:
        if q in (d.get("aliases") or []):
            return d
    hits = [d for d in profs if q in d.get("name", "") or d.get("name", "") in q]
    return hits[0] if len(hits) == 1 else None


def save(spec_path, out=None, quiet=False):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    brand = spec.get("brand") or {}
    name = (brand.get("name") or "").strip()
    if not name or brand.get("remember") is False:
        return None
    path = profile_path(name)
    old = load_json(path) if path.exists() else {}
    prof = dict(old)
    prof.update({"name": name, "updated": datetime.now().isoformat(timespec="seconds"), "made_with": f"luobo-design {SKILL_VERSION}"})
    prof.setdefault("created", prof["updated"])
    b = prof.setdefault("brand", {})
    if not spec.get("festival"):  # a festival run borrows colours; never let it overwrite the everyday look
        for k in BRAND_KEYS:
            if k == "logo":
                continue
            if brand.get(k):
                b[k] = brand[k]
            elif k == "tokens" and "tokens" in b and brand.get("direction") and brand.get("direction") != old.get("brand", {}).get("direction"):
                b.pop("tokens")  # a new direction without fixed colours: the old fixed colours belonged to the old look
    logo = brand.get("logo")
    if logo and not re.match(r"^(https?|data):", str(logo)):
        src = Path(logo) if Path(logo).is_absolute() else spec_path.parent / logo
        if src.exists() and src.is_file():
            dst = path.parent / f"logo{src.suffix.lower()}"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
            b["logo"] = str(dst)
    facts = prof.setdefault("facts", {})
    for k, v in (spec.get("facts") or {}).items():
        if k in STABLE_FACTS and isinstance(v, str) and v.strip() and "【" not in v:
            facts[k] = v
    industry = (spec.get("profile") or {}).get("industry")
    if industry:
        prof["industry"] = industry
    out_dir = Path(out) if out else spec_path.parent / "out"
    card = out_dir / "brand.json"
    if card.exists() and not spec.get("festival"):
        try:
            prof["palette"] = load_json(card).get("tokens")  # the resolved colours, for people and other skills
        except Exception:  # noqa: BLE001
            pass
    hist = prof.setdefault("history", [])
    entry = {"at": prof["updated"][:10], "project": spec.get("project") or "", "items": [i.get("type") for i in spec.get("items", [])],
             "spec": str(spec_path)}
    hist[:] = [h for h in hist if h.get("spec") != entry["spec"]] + [entry]
    del hist[:-20]
    save_json(path, prof)
    if not quiet:
        print(json.dumps({"saved": name, "file": str(path), "new": not old}, ensure_ascii=False))
    return path


def apply(spec_path, name=None, force=False):
    spec_path = Path(spec_path).resolve()
    spec = load_json(spec_path)
    brand = spec.setdefault("brand", {})
    prof = find(name or brand.get("name"))
    if not prof:
        return {"applied": False, "reason": "没有这个品牌的档案", "known": [d["name"] for d in all_profiles()]}
    filled = []
    if not brand.get("name"):
        brand["name"] = prof["name"]
        filled.append("name")
    for k, v in (prof.get("brand") or {}).items():
        if k == "logo" and v and not Path(v).exists():
            continue
        if force or not brand.get(k):
            brand[k] = v
            filled.append(k)
    facts = spec.setdefault("facts", {})
    for k, v in (prof.get("facts") or {}).items():
        if force or not facts.get(k):
            facts[k] = v
            filled.append(f"facts.{k}")
    if prof.get("industry"):
        spec.setdefault("profile", {}).setdefault("industry", prof["industry"])
    save_json(spec_path, spec)
    return {"applied": True, "brand": prof["name"], "filled": filled,
            "next": "brand 和常用信息已经填进 spec.json。方向已定就不用再出三个方向，节日物料除外"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["list", "show", "apply", "save", "forget"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--name")
    ap.add_argument("--out")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.cmd == "list":
        rows = [{"name": d["name"], "industry": d.get("industry"), "direction": (d.get("brand") or {}).get("direction"),
                 "updated": d.get("updated", "")[:10], "orders": len(d.get("history") or [])} for d in all_profiles()]
        return print(json.dumps({"library": str(library()), "brands": rows}, ensure_ascii=False, indent=1))
    if not a.arg:
        sys.exit("缺参数，见 brands.py --help")
    if a.cmd == "show":
        d = find(a.arg)
        if not d:
            sys.exit(f"没有“{a.arg}”的档案")
        return print(json.dumps(d, ensure_ascii=False, indent=1))
    if a.cmd == "apply":
        return print(json.dumps(apply(a.arg, a.name, a.force), ensure_ascii=False, indent=1))
    if a.cmd == "save":
        p = save(a.arg, a.out)
        if not p:
            print(json.dumps({"saved": None, "reason": "spec.brand 没有 name，或写了 remember: false"}, ensure_ascii=False))
        return
    if a.cmd == "forget":
        d = find(a.arg)
        if not d:
            sys.exit(f"没有“{a.arg}”的档案")
        shutil.rmtree(profile_path(d["name"]).parent)
        return print(json.dumps({"forgot": d["name"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
