# -*- coding: utf-8 -*-
"""
これ、韓国だけ — 장면 이미지 생성기 (예비 경로: Gemini)

주 경로는 weird-econ-dict/gen_images.py 의 NVIDIA FLUX.1-dev 다.
그쪽이 죽었을 때만 이걸 쓴다. 인터페이스·출력물은 동일하다.

    python gen_images_alt.py ep62.json --dry-run              # 몇 장·얼마인지만 본다
    python gen_images_alt.py ep62.json --yes-paid             # 없는 것만
    python gen_images_alt.py ep62.json --yes-paid --only s01_草刈り.png

**이 경로는 돈이 나간다.** --yes-paid 없이는 한 장도 만들지 않고, 한 번에
8장을 넘기면 멈춘다(--max 로만 풀 수 있다). pro 이미지 모델은 GENIMG_ALLOW_PRO=1
을 따로 받아야 한다. --force 는 이미 있는 그림까지 전부 다시 사는 것이므로
정말 화풍을 갈아엎을 때만 쓴다.

주 경로와 같은 것:
  - 세그먼트의 `img` + `prompt` 를 읽어 epNN_images/ 에 1080x1920 PNG
  - GENIMG_STYLE_PRE / _PRE_OBJECT / _SUF 환경변수로 화풍을 받는다
  - 이미 있는 파일은 건너뛴다
  - 새까만 이미지는 재시도로 거른다

다른 것:
  - 모델이 다르므로 **화풍이 FLUX 와 100% 같지는 않다.**
    한 장 뽑아 1~61화와 나란히 놓고 눈으로 확인한 뒤에 전편을 돌린다.

키: 환경변수 GEMINI_API_KEY, 없으면 ~/.config/ai-skills/api_keys.json
"""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

from PIL import Image

W, H = 1920, 1080
MODEL = os.environ.get("GENIMG_GEMINI_MODEL") or "gemini-2.5-flash-image"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL

# ── 과금 가드 ────────────────────────────────────────────────────────────────
# 2026-08-28~29 에 이 경로로 10화를 한꺼번에 재생성하다 ₩72,083 이 나갔다.
# 자동 충전이 세 번 돌 때까지 아무도 몰랐다. 그래서 이 스크립트는
#   ① 부르는 쪽이 --yes-paid 로 유료임을 인정해야 하고
#   ② 한 번에 MAX_DEFAULT 장을 넘기지 못하며
#   ③ 비싼 pro 모델은 따로 한 번 더 허락을 받아야
# 돈을 쓴다. 기본 경로(무료 FLUX)로 되돌릴 수 있으면 그쪽이 언제나 옳다.
PRICE_USD = {          # 장당 개략치. 정확한 청구액이 아니라 제동을 걸기 위한 숫자다.
    "gemini-2.5-flash-image": 0.039,
    "gemini-3.1-flash-image": 0.039,
    "gemini-3-pro-image": 0.134,
}
USD_KRW = 1400
MAX_DEFAULT = 8        # 한 편 분량(6~7컷)보다 딱 한 장 넉넉하다

def unit_cost():
    for k, v in PRICE_USD.items():
        if MODEL.startswith(k):
            return v
    return 0.15        # 모르는 모델이면 비싸다고 가정한다

def guard(n_jobs, yes_paid):
    """돈이 나가기 전에 멈춰 세운다."""
    won = int(n_jobs * unit_cost() * USD_KRW)
    print("[유료 경로] %s  %d장  예상 약 ₩%s\n" % (MODEL, n_jobs, format(won, ",")))
    if "pro" in MODEL and os.environ.get("GENIMG_ALLOW_PRO") != "1":
        sys.exit("pro 이미지 모델은 flash 의 3배 이상입니다. 정말 필요하면 "
                 "GENIMG_ALLOW_PRO=1 을 붙이십시오. 아니면 GENIMG_GEMINI_MODEL 을 "
                 "gemini-2.5-flash-image 로 두십시오.")
    if not yes_paid:
        sys.exit("이 경로는 과금됩니다. 무료 FLUX(weird-econ-dict/gen_images.py)가 "
                 "정말 죽었는지 먼저 확인하고, 맞다면 --yes-paid 를 붙이십시오. "
                 "확인만 하려면 --dry-run 을 쓰십시오.")

_DEFAULT_STYLE_PRE = (
    "Stop-motion claymation film still, Aardman-style handmade clay puppet characters "
    "with sculpted expressive faces and real fabric clothing, "
)
_DEFAULT_STYLE_PRE_OBJECT = (
    "Stop-motion claymation still life photograph, handmade plasticine props, no people, "
)
_DEFAULT_STYLE_SUF = ", wide horizontal 16:9 composition, no text, no letters, no watermark"

STYLE_PRE = os.environ.get("GENIMG_STYLE_PRE") or _DEFAULT_STYLE_PRE
STYLE_PRE_OBJECT = os.environ.get("GENIMG_STYLE_PRE_OBJECT") or _DEFAULT_STYLE_PRE_OBJECT
STYLE_SUF = os.environ.get("GENIMG_STYLE_SUF") or _DEFAULT_STYLE_SUF

def api_key():
    """결제 붙은 키를 먼저 찾는다.

    무료 등급 키는 이미지 모델 할당량이 limit 0 이라 429 만 돌아온다(2026-08 실측).
    결제 계정이 연결된 프로젝트의 키를 GEMINI_API_KEY_PAID 로 따로 둔다 —
    GEMINI_API_KEY 를 덮어쓰면 다른 스킬 호출까지 전부 과금 대상이 되기 때문이다.
    """
    names = ("GEMINI_API_KEY_PAID", "GEMINI_API_KEY", "gemini", "GEMINI")
    for n in names[:2]:
        k = os.environ.get(n)
        if k:
            return k
    p = os.path.join(os.path.expanduser("~"), ".config", "ai-skills", "api_keys.json")
    if os.path.exists(p):
        with io.open(p, encoding="utf-8") as f:
            d = json.load(f)
        for name in names:
            if d.get(name):
                return d[name]
    sys.exit("GEMINI_API_KEY_PAID 가 없습니다. ~/.config/ai-skills/api_keys.json 에 넣으십시오.")

def generate(prompt, key, tries=5):
    """실패하면 다시 시도한다. 429(할당량)는 대기 시간을 늘려가며 기다린다."""
    head = {"Content-Type": "application/json", "x-goog-api-key": key}
    # responseModalities 를 안 주면 이미지 대신 "여기 그림입니다" 라는 **텍스트**가
    # 200 으로 돌아온다. 빈 응답으로 오해하기 쉬운 자리다(2026-08 실측).
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": "16:9"}},
    }
    for k in range(tries):
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(ENDPOINT, json.dumps(body).encode(), head),
                timeout=180)
            d = json.loads(r.read().decode())
            for p in (d.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
                inline = p.get("inlineData") or p.get("inline_data")
                if inline and inline.get("data"):
                    raw = base64.b64decode(inline["data"])
                    if not is_blank(raw):
                        return raw
                    print("      새까만 이미지, 재시도 %d" % (k + 1))
                    break
            else:
                print("      이미지 없는 응답, 재시도 %d" % (k + 1))
        except urllib.error.HTTPError as e:
            msg = e.read()[:120].decode("utf8", "replace").replace("\n", " ")
            print("      HTTP %d, 재시도 %d  %s" % (e.code, k + 1, msg))
            if e.code == 429:
                time.sleep(30 * (k + 1))
                continue
            # aspectRatio 를 안 받는 버전이면 빼고 다시 간다
            # aspectRatio 를 안 받는 버전이면 그것만 뺀다. generationConfig 를
            # 통째로 지우면 responseModalities 까지 날아가 텍스트가 돌아온다.
            if e.code == 400 and "imageConfig" in body.get("generationConfig", {}):
                body["generationConfig"].pop("imageConfig", None)
                print("      imageConfig 제거하고 재시도")
        except Exception as e:
            print("      %s, 재시도 %d" % (type(e).__name__, k + 1))
        time.sleep(3)
    return None

def is_blank(raw):
    try:
        import numpy as np
        a = np.asarray(Image.open(io.BytesIO(raw)).convert("L").resize((160, 284)),
                       dtype="float32")
        return float(a.std()) < 6.0
    except Exception:
        return False

def fit(raw):
    """1080x1920 으로 맞춘다. 비율이 어긋나면 가운데를 잘라낸다."""
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
    ap.add_argument("--force", action="store_true", help="이미 있는 파일도 다시 만든다")
    ap.add_argument("--only", help="이 파일명 하나만 만든다")
    ap.add_argument("--yes-paid", action="store_true",
                    help="과금을 인정한다. 이게 없으면 한 장도 만들지 않는다")
    ap.add_argument("--dry-run", action="store_true",
                    help="무엇을 몇 장 만들지와 예상 비용만 찍고 끝낸다")
    ap.add_argument("--max", type=int, default=MAX_DEFAULT,
                    help="한 번에 만들 최대 장수 (기본 %d)" % MAX_DEFAULT)
    a = ap.parse_args()

    spec = json.load(io.open(a.spec, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.spec))
    ep = int(spec.get("episode", 0))
    out_dir = os.path.join(base, spec.get("images_dir", "ep%02d_images" % ep))
    os.makedirs(out_dir, exist_ok=True)

    jobs = []
    for i, s in enumerate(spec.get("segments", []), 1):
        if s.get("img") and s.get("prompt"):
            jobs.append((i, s["img"], s["prompt"], s.get("style", "character")))
    if a.only:
        jobs = [j for j in jobs if j[1] == a.only]
    if not jobs:
        sys.exit("생성할 대상이 없습니다. 세그먼트에 img 와 prompt 가 함께 있어야 합니다.")

    # 이미 있는 파일은 돈이 안 나가므로 예상 비용에서 뺀다. --force 는 전부 다시 산다.
    todo = [j for j in jobs
            if a.force or not os.path.exists(os.path.join(out_dir, j[1]))]
    print("%d화  대상 %d장 (새로 살 것 %d장) -> %s  [예비경로]"
          % (ep, len(jobs), len(todo), out_dir))
    guard(len(todo), a.yes_paid or a.dry_run)
    if a.dry_run:
        for i, name, _, _ in todo:
            print("  컷%02d  %s" % (i, name))
        return
    if len(todo) > a.max:
        sys.exit("한 번에 %d장은 너무 많습니다(상한 %d). 8/29 에 이렇게 10화를 몰아 "
                 "돌리다 ₩72,083 이 나갔습니다. --only 로 나눠 돌리거나 정말 필요하면 "
                 "--max 를 명시하십시오." % (len(todo), a.max))
    key = api_key()
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
        raw = generate(pre + mid + STYLE_SUF, key)
        if not raw:
            print("  컷%02d  %s  실패" % (i, name))
            failed += 1
            continue
        fit(raw).save(path)
        print("  컷%02d  %s  %4.1f초" % (i, name, time.time() - t0))
        made += 1
    print("\n생성 %d / 건너뜀 %d / 실패 %d" % (made, skipped, failed))
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
