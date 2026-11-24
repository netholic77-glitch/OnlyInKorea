# -*- coding: utf-8 -*-
"""Shrink channel_profile.png so the four trigrams survive YouTube's circular crop -> channel_profile_circle.png"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
S, SCALE = 800, 0.74

im = Image.open(os.path.join(HERE, "channel_profile.png")).convert("RGB")
n = round(S * SCALE)
small = np.array(im.resize((n, n), Image.LANCZOS))
off = (S - n) // 2

k = n / 800  # sample plain paper from the left margin between the top trigram and the hat brim
paper = np.median(small[int(160 * k):int(240 * k), :int(20 * k)].reshape(-1, 3), axis=0)
rng = np.random.default_rng(5)
canvas = np.clip(paper + rng.integers(-5, 6, (S, S, 1)), 0, 255).astype(np.uint8)
canvas[S - n:, off:off + n] = small  # bottom-aligned so the robe still runs off the edge
Image.fromarray(canvas).save(os.path.join(HERE, "channel_profile_circle.png"))

prev = Image.fromarray(canvas).resize((400, 400))
mask = Image.new("L", (400, 400), 0)
from PIL import ImageDraw
ImageDraw.Draw(mask).ellipse((0, 0, 399, 399), fill=255)
out = Image.new("RGB", (400, 400), "white"); out.paste(prev, mask=mask)
out.save(os.path.join(HERE, "_preview", "profile_circle_preview.png"))
print("OK")
