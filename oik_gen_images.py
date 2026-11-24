# -*- coding: utf-8 -*-
"""
これ、韓国だけ — 장면 이미지 생성기 (무료 경로: Pollinations.ai FLUX)

API 키 불필요. Pollinations.ai 의 FLUX 모델을 쓴다.

    python gen_images.py ep64.json              # 없는 것만
    python gen_images.py ep64.json --force      # 전부 다시
    python gen_images.py ep64.json --only s01_カフェ.png
    python gen_images.py ep64.json --dry-run    # 목록만

GENIMG_MODEL env: flux(기본) / flux-realism / turbo
"""
import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image

W, H = 1920, 1080
MODEL = os.environ.get("GENIMG_MODEL", "flux")
ENDPOINT = "https://image.pollinations.ai/prompt/{prompt}"

_DEFAULT_STYLE_PRE = (
    "Handmade paper craft diorama photograph, layered cut-paper figures with visible "
    "fold creases and torn paper edges, matte off-white and warm paper stock, small "
    "paper puppet people with simple ink-drawn faces, miniature papercraft set, "
)
_DEFAULT_STYLE_PRE_OBJECT = (
    "Handmade paper craft still life photograph, layered cut-paper objects with visible "
    "fold creases and torn paper edges, matte off-white paper stock, no people, no "
    "characters, miniature papercraft set, macro close-up, "
)
_DEFAULT_STYLE_SUF = (
    ", soft diffused daylight from one side, gentle drop shadows between paper layers, "
    "muted ink-navy and persimmon orange accents on warm off-white background, "
    "shallow depth of field, wide horizontal 16:9 composition, no text, no letters, no watermark"
)

STYLE_PRE        = os.environ.get("GENIMG_STYLE_PRE")        or _DEFAULT_STYLE_PRE
STYLE_PRE_OBJECT = os.environ.get("GENIMG_STYLE_PRE_OBJECT") or _DEFAULT_STYLE_PRE_OBJECT
STYLE_SUF        = os.environ.get("GENIMG_STYLE_SUF")        or _DEFAULT_STYLE_SUF


def generate(prompt, tries=6):
    encoded = urllib.parse.quote(prompt, safe="")
    url = ENDPOINT.format(prompt=encoded) + (
        "?width=%d&height=%d&model=%s&nologo=true&enhance=false&seed=%d"
        % (W, H, MODEL, int(time.time()) % 10000)
    )
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "oik-gen/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
            if len(raw) < 8000:
                print("      응답이 너무 짧음(%d bytes), 재시도 %d" % (len(raw), k + 1))
                time.sleep(5 * (k + 1))
                continue
            if is_blank(raw):
                print("      새까만 이미지, 재시도 %d" % (k + 1))
                time.sleep(5)
                continue
            return raw
        except urllib.error.HTTPError as e:
            msg = e.read()[:120].decode("utf-8", "replace").replace("\n", " ")
            print("      HTTP %d, 재시도 %d  %s" % (e.code, k + 1, msg))
            if e.code == 429:
                wait = 30 * (k + 1)
                print("      %d초 대기..." % wait)
                time.sleep(wait)
            else:
                time.sleep(5 * (k + 1))
        except Exception as e:
            print("      %s, 재시도 %d" % (type(e).__name__, k + 1))
            time.sleep(5 * (k + 1))
    return None


def is_blank(raw):
    try:
        import numpy as np
        a = np.asarray(
            Image.open(io.BytesIO(raw)).convert("L").resize((160, 284)),
            dtype="float32")
        return float(a.std()) < 6.0
    except Exception:
        return False


def fit(raw):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    src, dst = im.width / im.height, W / H
    if abs(src - dst) > 0.005:
        if src > dst:
            w = int(im.height * dst)
            im = im.crop(((im.width - w) // 2, 0, (im.width + w) // 2, im.height))
        else:
            h = int(im.width / dst)
            im = im.crop((0, (im.height - h) // 2, im.width, (im.height + h) // 2))
    return im.resize((W, H), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only",  help="이 파일명 하나만 만든다")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes-paid", action="store_true", help="(무시됨)")
    ap.add_argument("--max", type=int, default=999, help="(무시됨)")
    a = ap.parse_args()

    spec = json.load(io.open(a.spec, encoding="utf-8"))
    base_dir = os.path.dirname(os.path.abspath(a.spec))
    ep = int(spec.get("episode", 0))
    out_dir = os.path.join(base_dir, spec.get("images_dir", "ep%02d_images" % ep))
    os.makedirs(out_dir, exist_ok=True)

    jobs = []
    for i, s in enumerate(spec.get("segments", []), 1):
        if s.get("img") and s.get("prompt"):
            jobs.append((i, s["img"], s["prompt"], s.get("style", "character")))
    if a.only:
        jobs = [j for j in jobs if j[1] == a.only]
    if not jobs:
        sys.exit("생성할 대상이 없습니다.")

    todo = [j for j in jobs
            if a.force or not os.path.exists(os.path.join(out_dir, j[1]))]

    print("[무료 경로] Pollinations.ai  모델: %s" % MODEL)
    print("%d화  대상 %d장 (새로 만들 것 %d장) -> %s"
          % (ep, len(jobs), len(todo), out_dir))
    if a.dry_run:
        for i, name, _, _ in todo:
            print("  컷%02d  %s" % (i, name))
        return
    if not todo:
        print("전부 이미 있음.")
        return

    print("")
    made = skipped = failed = 0
    for i, name, mid, style in jobs:
        path = os.path.join(out_dir, name)
        if os.path.exists(path) and not a.force:
            print("  컷%02d  %s  (이미 있음)" % (i, name))
            skipped += 1
            continue
        t0 = time.time()
        pre = STYLE_PRE_OBJECT if style == "object" else STYLE_PRE
        raw = generate(pre + mid + STYLE_SUF)
        if not raw:
            print("  컷%02d  %s  실패" % (i, name))
            failed += 1
            continue
        fit(raw).save(path)
        print("  컷%02d  %s  %.1f초" % (i, name, time.time() - t0))
        made += 1
        if made < len(todo):
            time.sleep(2)

    print("\n생성 %d / 건너뜀 %d / 실패 %d" % (made, skipped, failed))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

