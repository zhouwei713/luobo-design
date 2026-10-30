"""Fetch the open-licensed display fonts once and build @font-face CSS.

  python fonts.py                 # download every npm font into the cache
  python fonts.py --check         # show what is available

Fonts land in ~/.cache/luobo-design/fonts/<id>-<version>/ (override with LUOBO_DESIGN_FONTS).
No network -> the fallback stack is used; render.py records that in the QA report.
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

from common import CACHE_DIR, load_ref
from fontfix import fix_dir

FONT_DIR = Path(os.environ.get("LUOBO_DESIGN_FONTS") or (CACHE_DIR / "fonts"))
REGISTRY = os.environ.get("LUOBO_DESIGN_NPM", "https://registry.npmjs.org")


def _pkg_dir(fid, spec):
    return FONT_DIR / f"{fid}-{spec['version']}" / "package"


def _fetch(url, timeout=120):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except Exception:
        if shutil.which("curl"):
            out = subprocess.run(["curl", "-sSfL", "--max-time", str(timeout), url], capture_output=True)
            if out.returncode == 0 and out.stdout:
                return out.stdout
        raise


def download(fid, spec):
    dest = _pkg_dir(fid, spec)
    if dest.exists():
        return True, "cached"
    name = spec["npm"].split("/")[-1]
    url = f"{REGISTRY}/{spec['npm']}/-/{name}-{spec['version']}.tgz"
    try:
        data = _fetch(url)
    except Exception as e:  # noqa: BLE001
        return False, f"download failed: {e}"
    tmp = dest.parent.with_suffix(".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        for m in tf.getmembers():  # keep only css + woff2 + licences, refuse odd paths
            if m.name.startswith("/") or ".." in m.name:
                continue
            if m.isfile() and re.search(r"\.(css|woff2|txt|md)$|LICENSE", m.name):
                tf.extract(m, tmp)
    if dest.parent.exists():
        shutil.rmtree(dest.parent)
    tmp.rename(dest.parent)
    return True, "downloaded"


def stack(fid):
    fonts = load_ref("fonts.json")
    spec = fonts.get(fid) or fonts["sans"]
    names = [spec["family"]] + spec.get("fallback", [])
    return ", ".join(n if n in ("serif", "sans-serif") else f"'{n}'" for n in names)


def font_css(font_ids, fetch=True):
    """@font-face CSS for the npm fonts among font_ids. Returns (css, status{id: msg})."""
    fonts = load_ref("fonts.json")
    css, status = [], {}
    for fid in sorted(set(font_ids)):
        spec = fonts.get(fid)
        if not spec:
            status[fid] = "unknown font id, using sans"
            continue
        if spec["source"] != "npm":
            status[fid] = "system"
            continue
        ok, msg = (download(fid, spec) if fetch else (_pkg_dir(fid, spec).exists(), "cache only"))
        if not ok or not _pkg_dir(fid, spec).exists():
            status[fid] = f"fallback ({msg})"
            continue
        base = _pkg_dir(fid, spec)
        fixed = fix_dir(base)  # first use only: a few glyphs in some fonts print as solid blocks
        if fixed:
            print(f"  repaired {len(set(fixed))} glyphs in {spec['family']}")
        for name in spec["css"]:
            p = base / name
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8")
            text = re.sub(r"url\((['\"]?)\./", lambda m: f"url({m.group(1)}{base.as_uri()}/", text)
            text = re.sub(r",\s*url\([^)]*\.woff\)\s*format\('woff'\)", "", text)
            css.append(text)
        status[fid] = "ok"
    return "\n".join(css), status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    fonts = load_ref("fonts.json")
    for fid, spec in fonts.items():
        if spec["source"] != "npm":
            print(f"{fid:8s} system  {spec['family']}")
            continue
        if a.check:
            print(f"{fid:8s} {'ok' if _pkg_dir(fid, spec).exists() else 'missing':7s} {spec['family']}")
        else:
            ok, msg = download(fid, spec)
            print(f"{fid:8s} {msg}")


if __name__ == "__main__":
    main()
