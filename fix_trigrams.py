# -*- coding: utf-8 -*-
"""Replace AI-drawn trigrams on channel_profile.png with the correct Taegukgi ones.
TL geon (3 solid), TR gam (broken/solid/broken), BL ri (solid/broken/solid), BR gon (3 broken)."""
import os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "channel_profile.png")
OUT = os.path.join(HERE, "channel_profile.png")

# corner box (x0, y0, x1, y1), pattern (True = solid), rotation (deg, PIL counter-clockwise)
CORNERS = [
    ((40, 0, 230, 180), (True, True, True), 45),        # geon
    ((580, 0, 770, 180), (False, True, False), -45),     # gam
    ((40, 450, 230, 630), (True, False, True), -45),     # ri
    ((580, 450, 770, 630), (False, False, False), 45),   # gon
]
BAR_L, BAR_T, GAP, SPLIT = 150, 24, 16, 16
INK = (34, 32, 36)


def fill(arr, mask, radius=18):
    """Normalized-convolution fill: masked pixels take the blurred average of nearby unmasked paper."""
    keep = (mask == 0).astype(np.float32)
    blur = lambda a: np.array(Image.fromarray(a).filter(ImageFilter.GaussianBlur(radius)), np.float32)
    w = blur((keep * 255).astype(np.uint8)) / 255 + 1e-4
    ch = [blur((arr[..., i] * keep).astype(np.uint8)) / 255 / w * 255 for i in range(3)]
    filled = np.clip(np.stack(ch, -1), 0, 255)
    return np.where(mask[..., None] > 0, filled, arr).astype(np.uint8)


def dilate(a, k=9):
    return np.array(Image.fromarray(a).filter(ImageFilter.MaxFilter(k)))


def trigram(pattern, angle):
    h = 3 * BAR_T + 2 * GAP
    im = Image.new("RGBA", (BAR_L + 40, h + 40), (0, 0, 0, 0))
    a = np.array(im)
    rng = np.random.default_rng(7)
    for i, solid in enumerate(pattern):
        y = 20 + i * (BAR_T + GAP)
        spans = [(20, 20 + BAR_L)] if solid else [(20, 20 + (BAR_L - SPLIT) // 2), (20 + (BAR_L + SPLIT) // 2, 20 + BAR_L)]
        for x0, x1 in spans:
            tex = INK + rng.integers(-10, 11, (BAR_T, x1 - x0, 1))
            a[y:y + BAR_T, x0:x1, :3] = np.clip(tex, 0, 255)
            a[y:y + BAR_T, x0:x1, 3] = 255
    im = Image.fromarray(a)
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)


def main():
    im = Image.open(SRC).convert("RGB")
    arr = np.array(im)
    mask = np.zeros(arr.shape[:2], np.uint8)
    # near-black and grey only, so the red/blue circle is never masked
    a16 = arr.astype(np.int16)
    ink = (a16.max(axis=2) < 110) & ((a16.max(axis=2) - a16.min(axis=2)) < 30)
    for (x0, y0, x1, y1), _, _ in CORNERS:
        sub = ink[y0:y1, x0:x1].astype(np.uint8) * 255
        mask[y0:y1, x0:x1] = dilate(sub)
    clean = fill(arr, mask)
    noise = np.random.default_rng(3).integers(-4, 5, clean.shape)
    clean = np.where(mask[..., None] > 0, np.clip(clean + noise, 0, 255), clean).astype(np.uint8)
    out = Image.fromarray(clean).convert("RGBA")

    for (x0, y0, x1, y1), pattern, angle in CORNERS:
        t = trigram(pattern, angle)
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        pos = (cx - t.width // 2, cy - t.height // 2)
        shadow = Image.new("RGBA", t.size, (0, 0, 0, 0))
        shadow.putalpha(t.getchannel("A").point(lambda v: v * 0.35))
        out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(4)), (pos[0] + 4, pos[1] + 5))
        out.alpha_composite(t, pos)
    out.convert("RGB").save(OUT)
    print("OK")


if __name__ == "__main__":
    main()
