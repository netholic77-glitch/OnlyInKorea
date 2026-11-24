# -*- coding: utf-8 -*-
"""Channel banner 2048x1152. Text stays inside YouTube's all-device safe area (1235x338, centered)."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 2048, 1152
SAFE_W, SAFE_H = 1235, 338
PAPER, INK, ACCENT = (239, 230, 214), (31, 42, 58), (232, 133, 58)
F = "C:/Windows/Fonts/"


def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def main(src="s06_city_dawn.png", out="channel_banner.png"):
    bg = cover(Image.open(os.path.join(HERE, "ep01_images", src)).convert("RGB"), W, H)
    bg = Image.blend(bg, Image.new("RGB", (W, H), PAPER), 0.25)

    # paper card behind the text, slightly larger than the safe area, with a soft shadow
    cw, ch = SAFE_W + 40, SAFE_H - 10
    cx, cy = (W - cw) // 2, (H - ch) // 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((cx + 10, cy + 14, cx + cw + 10, cy + ch + 14), 18, fill=(0, 0, 0, 90))
    bg = Image.alpha_composite(bg.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle((cx, cy, cx + cw, cy + ch), 18, fill=PAPER)

    title = ImageFont.truetype(F + "segoeuib.ttf", 132)
    tag = ImageFont.truetype(F + "segoeui.ttf", 44)
    t1, t2 = "ONLY IN KOREA", "Things that exist only in Korea, explained."
    tw = d.textlength(t1, font=title)
    ty = cy + 42
    d.text(((W - tw) / 2, ty), t1, font=title, fill=INK)
    d.rectangle(((W - 220) / 2, ty + 168, (W + 220) / 2, ty + 176), fill=ACCENT)
    d.text(((W - d.textlength(t2, font=tag)) / 2, ty + 196), t2, font=tag, fill=INK)

    bg.convert("RGB").save(os.path.join(HERE, out), quality=95)
    print(out)


if __name__ == "__main__":
    main()
