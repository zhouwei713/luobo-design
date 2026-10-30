"""Configurable AI image generation with graceful fallback (shared design with luobo-ppt).

Config lookup order (first found wins):
  1. --config PATH
  2. env LUOBO_DESIGN_CONFIG
  3. ./luobo-design.config.json, then <spec dir>/luobo-design.config.json
  4. ~/.config/luobo-design/config.json
  5. <skill>/config.json
  6. luobo-ppt's config (same format), so one key serves both skills
If nothing is found but env LUOBO_DESIGN_PROVIDER is set, a config is built from env.
No config -> provider "none" -> layouts use procedural art and the prompts are delivered for the user.

Providers:
  openai             OpenAI Images API (gpt-image-2, gpt-image-1.x). gpt-image-2 has no transparent output,
                     so cutouts are asked on plain white and the background is removed locally.
  gemini             Gemini image models (Nano Banana 2 = gemini-3.1-flash-image), generateContent.
  ark                Volcengine Ark Seedream (即梦), OpenAI-style images endpoint. Use the model id your console shows.
  openai_compatible  Any service exposing POST {base_url}/images/generations.
  hiapi              HiAPI async task API (POST /v1/tasks, poll GET /v1/tasks/{id}), default model
                     gpt-image-2.5-flare/text-to-image. Transparent PNG comes back natively at 1K.
  command            Run a local command template; it must write the PNG to {out}.
See templates/config.example.json and references/imagegen.md.
"""
import base64
import io
import json
import os
import shlex
import subprocess
import time
from pathlib import Path

from common import SKILL_DIR

DEFAULTS = {
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-image-2", "api_key_env": "OPENAI_API_KEY"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-3.1-flash-image",
               "api_key_env": "GEMINI_API_KEY"},
    "ark": {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-seedream-4-0-250828",
            "api_key_env": "ARK_API_KEY"},
    "openai_compatible": {"api_key_env": "IMAGE_API_KEY"},
    "hiapi": {"base_url": "https://api.hiapi.ai", "model": "gpt-image-2.5-flare/text-to-image", "api_key_env": "HIAPI_API_KEY"},
}
HIAPI_RATIOS = {"1:1": 1, "3:2": 1.5, "2:3": 2 / 3, "4:3": 4 / 3, "3:4": 3 / 4, "16:9": 16 / 9, "9:16": 9 / 16, "21:9": 21 / 9,
                "27:16": 27 / 16, "16:27": 16 / 27, "9:8": 9 / 8, "8:9": 8 / 9}


def find_config(explicit=None, work_dir=None):
    cands = []
    if explicit:
        cands.append(Path(explicit))
    if os.environ.get("LUOBO_DESIGN_CONFIG"):
        cands.append(Path(os.environ["LUOBO_DESIGN_CONFIG"]))
    cands.append(Path.cwd() / "luobo-design.config.json")
    if work_dir:
        cands.append(Path(work_dir) / "luobo-design.config.json")
    cands.append(Path.home() / ".config" / "luobo-design" / "config.json")
    cands.append(SKILL_DIR / "config.json")
    if os.environ.get("LUOBO_PPT_CONFIG"):
        cands.append(Path(os.environ["LUOBO_PPT_CONFIG"]))
    cands.append(Path.home() / ".config" / "luobo-ppt" / "config.json")
    for c in cands:
        if c.exists():
            with open(c, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["_path"] = str(c)
            return cfg
    prov = os.environ.get("LUOBO_DESIGN_PROVIDER")
    if prov:
        g = lambda k: os.environ.get(f"LUOBO_DESIGN_{k}")
        return {"provider": prov, "model": g("MODEL"), "base_url": g("BASE_URL"), "_path": "env"}
    return {"provider": "none", "_path": None}


class DownloadError(RuntimeError):
    """The image was made (and paid for) but could not be fetched: retry the download, never the generation."""


class ImageGen:
    def __init__(self, cfg):
        self.cfg = dict(cfg or {})
        self.provider = (self.cfg.get("provider") or "none").lower()
        d = DEFAULTS.get(self.provider, {})
        self.base_url = (self.cfg.get("base_url") or d.get("base_url") or "").rstrip("/")
        self.model = self.cfg.get("model") or d.get("model")
        key_env = self.cfg.get("api_key_env") or d.get("api_key_env")
        self.api_key = self.cfg.get("api_key") or (os.environ.get(key_env) if key_env else None)
        self.timeout = int(self.cfg.get("timeout", 180))
        self.extra = self.cfg.get("extra", {})
        self.retries = int(self.cfg.get("retries", 1))

    # ------------------------------------------------------------ status
    def available(self):
        if self.provider in ("none", "", None):
            return False, "no image provider configured"
        if self.provider == "command":
            return (bool(self.cfg.get("command")), "command template missing")
        if self.provider not in DEFAULTS:
            return False, f"unknown provider '{self.provider}'"
        if not self.api_key:
            return False, f"api key missing for {self.provider}"
        if not self.base_url:
            return False, "base_url missing"
        return True, f"{self.provider}:{self.model}"

    def use_for(self, kind):
        u = self.cfg.get("use_for", {"hero": True, "background": False})
        return bool(u.get(kind, kind == "hero"))

    # ------------------------------------------------------------ main
    def generate(self, prompt, w, h, transparent=False, out=None):
        """Returns (PIL.Image RGBA, native_transparent: bool)."""
        last = None
        for attempt in range(self.retries + 1):
            try:
                fn = getattr(self, "_gen_" + self.provider)
                return fn(prompt, w, h, transparent, out)
            except DownloadError:
                raise
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"{self.provider} failed: {last}")

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _img(data_b64=None, url=None, raw=None):
        from PIL import Image
        if data_b64:
            raw = base64.b64decode(data_b64)
        elif url:
            import requests
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            raw = r.content
        return Image.open(io.BytesIO(raw)).convert("RGBA")

    def _post(self, url, body, headers):
        import requests
        body = {**body, **self.extra}
        r = requests.post(url, json=body, headers=headers, timeout=self.timeout)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
        return r.json()

    @staticmethod
    def _aspect_size(w, h, options):
        ar = w / h
        return min(options, key=lambda s: abs((s[0] / s[1]) - ar))

    # ------------------------------------------------------------ providers
    def _gen_openai(self, prompt, w, h, transparent, out):
        m = (self.model or "").lower()
        if m.startswith("dall-e-3"):
            sw, sh = self._aspect_size(w, h, [(1024, 1024), (1792, 1024), (1024, 1792)])
        else:
            sw, sh = self._aspect_size(w, h, [(1024, 1024), (1536, 1024), (1024, 1536)])
        body = {"model": self.model, "prompt": prompt, "size": f"{sw}x{sh}", "n": 1}
        native = False
        if m.startswith("gpt-image"):
            body["quality"] = self.cfg.get("quality", "medium")
            if transparent and not m.startswith("gpt-image-2"):
                body["background"] = "transparent"
                body["output_format"] = "png"
                native = True
        else:
            body["response_format"] = "b64_json"
        js = self._post(f"{self.base_url}/images/generations", body,
                        {"Authorization": f"Bearer {self.api_key}"})
        d = js["data"][0]
        return self._img(d.get("b64_json"), d.get("url")), native

    def _gen_openai_compatible(self, prompt, w, h, transparent, out):
        size = self.cfg.get("size") or "{}x{}".format(*self._aspect_size(w, h, [(1024, 1024), (1536, 1024), (1024, 1536)]))
        body = {"model": self.model, "prompt": prompt, "size": size, "n": 1,
                "response_format": self.cfg.get("response_format", "b64_json")}
        js = self._post(f"{self.base_url}/images/generations", body,
                        {"Authorization": f"Bearer {self.api_key}"})
        d = js["data"][0]
        return self._img(d.get("b64_json"), d.get("url")), False

    def _gen_ark(self, prompt, w, h, transparent, out):
        # Seedream accepts WxH (roughly 1K..4K); keep aspect, long side 2048
        ar = w / h
        sw, sh = (2048, int(2048 / ar)) if ar >= 1 else (int(2048 * ar), 2048)
        sw, sh = max(1024, sw - sw % 8), max(1024, sh - sh % 8)
        body = {"model": self.model, "prompt": prompt, "size": self.cfg.get("size", f"{sw}x{sh}"),
                "response_format": "b64_json", "watermark": False}
        js = self._post(f"{self.base_url}/images/generations", body,
                        {"Authorization": f"Bearer {self.api_key}"})
        d = js["data"][0]
        return self._img(d.get("b64_json"), d.get("url")), False

    def _gen_gemini(self, prompt, w, h, transparent, out):
        ratios = {"1:1": 1, "4:3": 4 / 3, "3:4": 3 / 4, "16:9": 16 / 9, "9:16": 9 / 16, "3:2": 1.5, "2:3": 2 / 3}
        ar = min(ratios, key=lambda k: abs(ratios[k] - w / h))
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": ar}}}
        js = self._post(f"{self.base_url}/models/{self.model}:generateContent", body,
                        {"x-goog-api-key": self.api_key})
        for cand in js.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                data = part.get("inlineData") or part.get("inline_data")
                if data and data.get("data"):
                    return self._img(data["data"]), False
        raise RuntimeError("no image in Gemini response: " + json.dumps(js)[:300])

    def _gen_hiapi(self, prompt, w, h, transparent, out):
        """Async: submit a task, poll until success, download data.output[0].url before it expires."""
        import requests
        ar = min(HIAPI_RATIOS, key=lambda k: abs(HIAPI_RATIOS[k] - w / h))
        # transparency only works at 1K; larger sizes come back opaque
        res = "1K" if transparent else self.cfg.get("resolution", "2K")
        inp = {"prompt": prompt[:8000], "aspect_ratio": ar, "resolution": res,
               "background": "transparent" if transparent else self.cfg.get("background", "opaque")}
        inp.update(self.extra.get("input", {}) if isinstance(self.extra.get("input"), dict) else {})
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        r = requests.post(f"{self.base_url}/v1/tasks", json={"model": self.model, "input": inp}, headers=headers, timeout=60)
        if r.status_code == 400:
            # some accounts or models only allow one resolution; the error names it, so resubmit once with it.
            # a 400 is rejected before any task exists, so nothing has been charged yet
            import re
            m = re.search(r"resolution: value must be '([^']+)'", r.text)
            if m and m.group(1) != inp["resolution"]:
                inp["resolution"] = m.group(1)
                r = requests.post(f"{self.base_url}/v1/tasks", json={"model": self.model, "input": inp},
                                  headers=headers, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
        js = r.json()
        task = (js.get("data") or {}).get("taskId") or js.get("taskId")
        if not task:
            raise RuntimeError("no taskId in response: " + json.dumps(js, ensure_ascii=False)[:300])
        log = Path(str(out)).with_suffix(".task.json") if out else None  # keep the task id: it is the receipt
        rec = {"provider": "hiapi", "model": self.model, "taskId": task,
               "submitted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if log:
            log.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        deadline = time.time() + self.timeout
        wait = float(self.cfg.get("poll_seconds", 3))
        while time.time() < deadline:
            time.sleep(wait)
            q = requests.get(f"{self.base_url}/v1/tasks/{task}", headers=headers, timeout=60)
            if q.status_code >= 400:
                raise RuntimeError(f"poll HTTP {q.status_code}: {q.text[:300]}")
            d = q.json().get("data") or q.json()
            status = d.get("status")
            if status == "success":
                outs = d.get("output") or []
                url = outs[0].get("url") if outs and isinstance(outs[0], dict) else (outs[0] if outs else None)
                if not url:
                    raise RuntimeError("task finished without an image url")
                if log:
                    rec.update({"status": "success", "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "url": url})
                    log.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                err = None
                for i in range(3):
                    try:
                        return self._img(url=url), transparent
                    except Exception as e:  # noqa: BLE001
                        err = e
                        time.sleep(2 * (i + 1))
                host = url.split("/")[2] if "//" in url else url
                raise DownloadError(f"image ready but download from {host} failed ({err}). "
                                    f"Allow {host} in the network settings, or open it in a browser before it expires: {url}")
            if status == "fail" and log:
                rec.update({"status": "fail", "error": d.get("error")})
                log.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            if status == "fail":
                raise RuntimeError(f"task {task} failed: {json.dumps(d.get('error'), ensure_ascii=False)[:300]}")
            wait = min(wait * 1.3, 10)
        raise RuntimeError(f"task {task} still not done after {self.timeout}s")

    def _gen_command(self, prompt, w, h, transparent, out):
        from PIL import Image
        out = Path(out or "gen.png")
        pf = out.with_suffix(".prompt.txt")
        pf.write_text(prompt, encoding="utf-8")
        cmd = self.cfg["command"].format(prompt_file=shlex.quote(str(pf)), out=shlex.quote(str(out)),
                                         w=w, h=h, prompt=shlex.quote(prompt))
        subprocess.run(cmd, shell=True, check=True, timeout=self.timeout)
        return Image.open(out).convert("RGBA"), bool(self.cfg.get("native_transparent", False))


# ---------------------------------------------------------------- background removal
def remove_background(img, tol=26, feather=1.2):
    """Make the flat background transparent.

    Uses rembg when installed; otherwise flood-fills from the borders on the
    border color (prompts ask for a plain white background, which this handles well).
    """
    try:
        from rembg import remove  # type: ignore
        return remove(img)
    except Exception:
        pass
    import numpy as np
    from PIL import Image, ImageFilter
    from scipy import ndimage
    a = np.asarray(img.convert("RGB")).astype(int)
    h, w, _ = a.shape
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bgc = np.median(border, axis=0)
    dist = np.sqrt(((a - bgc) ** 2).sum(-1))
    cand = dist < tol
    lab, _n = ndimage.label(cand)
    edge_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bgmask = np.isin(lab, list(edge_labels))
    alpha = np.where(bgmask, 0, 255).astype("uint8")
    al = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(feather))
    out = img.convert("RGBA")
    out.putalpha(al)
    return out


def trim_transparent(img, pad=0.04):
    bbox = img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    p = int(max(img.size) * pad)
    return img.crop((max(0, x0 - p), max(0, y0 - p), min(img.width, x1 + p), min(img.height, y1 + p)))


def main():
    """Quick test: python imagegen.py --test "a red apple" --out apple.png [--ratio 3:4] [--transparent]"""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True, help="prompt")
    ap.add_argument("--out", default="imagegen-test.png")
    ap.add_argument("--ratio", default="3:4")
    ap.add_argument("--transparent", action="store_true")
    ap.add_argument("--config")
    ap.add_argument("--provider", help="skip the config file and use this provider with its default model and key env")
    a = ap.parse_args()
    cfg = {"provider": a.provider} if a.provider else find_config(a.config)
    gen = ImageGen(cfg)
    ok, why = gen.available()
    if not ok:
        raise SystemExit(f"not ready: {why}")
    rw, rh = (int(x) for x in a.ratio.split(":"))
    print(f"generating with {why} ...")
    t0 = time.time()
    img, native = gen.generate(a.test, rw * 256, rh * 256, transparent=a.transparent, out=a.out)
    if a.transparent and not native:
        img = trim_transparent(remove_background(img))
    img.save(a.out)
    print(f"saved {a.out} {img.size[0]}x{img.size[1]} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
