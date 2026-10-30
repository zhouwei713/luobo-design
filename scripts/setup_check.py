#!/usr/bin/env python3
"""Environment check and one-click dependency install for luobo-design.

Usage:
  python setup_check.py                 check only, print a report
  python setup_check.py --install       check, then install what is missing
  python setup_check.py --quick         exit at once if a previous check passed for this version
  python setup_check.py --selftest      also render two sample designs end to end
  python setup_check.py --json          machine-readable report

Typical calls
  installer (install.sh / install.ps1):   setup_check.py --install --selftest
  first use inside an agent (SKILL.md):   setup_check.py --quick --install

What is checked
  required     Python >= 3.9, Pillow, Playwright with its Chromium browser
  recommended  fontTools + brotli (logo outlines, phone-page font subsets, font repair),
               requests (image model APIs), network to the npm registry (open-source Chinese fonts)
  optional     an image model config (luobo-design.config.json or ~/.config/luobo-design/config.json)
The result is cached in ~/.config/luobo-design/setup.json.
Exit code 0 when all required items are present.
"""
import argparse
import importlib
import json
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:  # Chinese output on Windows consoles
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PY_REQUIRED = [("PIL", "Pillow"), ("playwright", "playwright")]
PY_RECOMMENDED = [("fontTools", "fonttools"), ("brotli", "brotli"), ("requests", "requests")]
CACHE = Path.home() / ".config" / "luobo-design" / "setup.json"
OS = platform.system()


def say(msg=""):
    print(msg, flush=True)


def version():
    try:
        from common import SKILL_VERSION
        return SKILL_VERSION
    except Exception:
        return "?"


def has_module(mod):
    try:
        importlib.invalidate_caches()
        importlib.import_module(mod)
        return True
    except Exception:
        return False


def chromium_ok():
    """Can Playwright actually launch Chromium? (installed package is not enough)"""
    if not has_module("playwright"):
        return False, "playwright 没装"
    code = ("from playwright.sync_api import sync_playwright\n"
            "with sync_playwright() as p:\n b=p.chromium.launch(); pg=b.new_page(); pg.set_content('<p>ok</p>'); b.close()\n")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        return True, "可以启动"
    err = (r.stderr or r.stdout).strip().splitlines()
    return False, (err[-1] if err else "启动失败")[:200]


def npm_ok():
    import urllib.request
    try:
        from fonts import REGISTRY
    except Exception:
        REGISTRY = "https://registry.npmjs.org"
    try:
        with urllib.request.urlopen(f"{REGISTRY}/@fontsource%2Fzcool-kuaile", timeout=12) as r:
            return r.status == 200
    except Exception:
        return False


def image_model():
    try:
        from imagegen import ImageGen, find_config
        gen = ImageGen(find_config())
        ok, why = gen.available()
        return ok, why
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:120]


def pip_install(pkgs):
    if not pkgs:
        return True
    say(f"安装 Python 包：{' '.join(pkgs)}")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *pkgs]
    r = subprocess.run(cmd)
    if r.returncode != 0 and OS == "Linux":  # PEP 668 managed environments
        r = subprocess.run(cmd + ["--break-system-packages"])
    if r.returncode != 0:
        r = subprocess.run(cmd + ["--user"])
    return r.returncode == 0


def install_chromium():
    say("安装 Playwright 的 Chromium 浏览器（约 150MB，首次需要几分钟）……")
    r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    if r.returncode != 0:
        return False
    ok, _ = chromium_ok()
    if not ok and OS == "Linux":
        say("Chromium 缺系统库，尝试安装（需要 sudo 权限）……")
        subprocess.run([sys.executable, "-m", "playwright", "install-deps", "chromium"])
    return chromium_ok()[0]


def check():
    rep = {"version": version(), "python": sys.version.split()[0], "os": OS, "items": []}

    def add(level, name, ok, note=""):
        rep["items"].append({"level": level, "name": name, "ok": bool(ok), "note": note})

    add("required", "Python 3.9+", sys.version_info >= (3, 9), rep["python"])
    for mod, pkg in PY_REQUIRED:
        add("required", pkg, has_module(mod))
    ok, note = chromium_ok()
    add("required", "Chromium（渲染用）", ok, note)
    for mod, pkg in PY_RECOMMENDED:
        add("recommended", pkg, has_module(mod), {"fonttools": "logo 转矢量、H5 字体子集", "brotli": "字体压缩",
                                                  "requests": "调用生图模型"}[pkg])
    add("recommended", "能访问 npm 字体源", npm_ok(), "下载开源中文字体；不能联网时退回系统字体")
    ok, why = image_model()
    add("optional", "生图模型", ok, why if ok else "没配置也能用，配图改用程序插画")
    rep["ok"] = all(i["ok"] for i in rep["items"] if i["level"] == "required")
    return rep


def selftest():
    """Render two samples (a poster and a note cover) to a temp folder and confirm the PNGs exist."""
    import pipeline  # noqa: F401  (validates imports)
    import render
    import check as qa
    tmp = Path(tempfile.mkdtemp(prefix="luobo-design-selftest-"))
    spec = {"project": "自测", "profile": {"industry": "food"}, "brand": {"name": "萝卜每天喝", "direction": "pop-fresh"},
            "items": [{"id": "poster", "type": "poster", "layout": "product-hero", "sizes": ["square"],
                       "content": {"kicker": "新品上市", "headline": "橙心萝卜\n今天上新", "sub": "鲜橙胡萝卜果茶"},
                       "art": {"motif": "drink"}},
                      {"id": "cover", "type": "xhs", "layout": "textcard", "sizes": ["portrait"],
                       "content": {"title": "装好了，\n可以开始**设计**了。", "color": "green"}}]}
    p = tmp / "spec.json"
    p.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    out, _ = render.render(p, tmp / "out")
    q = qa.run(p, out)
    pngs = sorted(Path(out).glob("*.png"))
    return {"ok": len(pngs) >= 2 and q["errors"] == 0, "dir": str(out), "files": [x.name for x in pngs], "errors": q["errors"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.quick and CACHE.exists():
        try:
            c = json.loads(CACHE.read_text(encoding="utf-8"))
            if c.get("ok") and c.get("version") == version():
                say(f"环境已检查过（{c.get('checked_at', '')}），可以直接用。")
                return 0
        except Exception:
            pass

    rep = check()
    if a.install:
        miss = [i["name"] for i in rep["items"] if not i["ok"]]
        pkgs = [pkg for mod, pkg in PY_REQUIRED + PY_RECOMMENDED if pkg in miss]
        pip_install(pkgs)
        if "Chromium（渲染用）" in miss or "playwright" in miss:
            install_chromium()
        rep = check()

    if a.selftest and rep["ok"]:
        try:
            rep["selftest"] = selftest()
        except Exception as e:  # noqa: BLE001
            rep["selftest"] = {"ok": False, "error": str(e)[:300]}
        rep["ok"] = rep["ok"] and rep["selftest"]["ok"]

    if rep["ok"]:
        rep["checked_at"] = time.strftime("%Y-%m-%d %H:%M")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")

    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        say(f"\nluobo-design {rep['version']}  ·  Python {rep['python']}  ·  {rep['os']}")
        names = {"required": "必需", "recommended": "推荐", "optional": "可选"}
        for i in rep["items"]:
            say(f"  {'✓' if i['ok'] else '✗'} [{names[i['level']]}] {i['name']}" + (f"  {i['note']}" if i["note"] else ""))
        st = rep.get("selftest")
        if st:
            say(f"  {'✓' if st.get('ok') else '✗'} 自测：" + (f"出了 {len(st.get('files', []))} 张图，在 {st.get('dir')}" if st.get("ok") else str(st)))
        if rep["ok"]:
            say("\n可以用了。")
        else:
            say("\n还缺必需的组件。运行 python setup_check.py --install 自动安装；装不上时按上面的提示手动处理。")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
