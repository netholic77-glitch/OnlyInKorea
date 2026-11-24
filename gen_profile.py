# -*- coding: utf-8 -*-
"""Channel profile picture: one Codex image, center-cropped to a square 800x800 -> channel_profile.png"""
import importlib.util, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "oik_gen_codex.py"))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

PROMPT = (c.g.STYLE_PRE +
          "a calm, slightly mysterious jeoseung saja, the traditional Korean folk messenger of the afterlife, as a "
          "stylized paper-craft figure: head and shoulders only, facing the viewer, placed in the exact center of "
          "the frame with wide empty margins on the left and right. Wide-brimmed black horsehair gat hat with a "
          "chin string, plain black hanbok robe with a white collar band, pale cream paper face with simple "
          "half-closed eyes and a faint knowing smile. Not scary, no blood, no skulls. An original design from "
          "folk tradition, not any film, drama, or cartoon character. Behind the hat, a large paper-cut taegeuk "
          "circle from the South Korean flag (Taegukgi): a circle split by an S-shaped curve, red half on top and "
          "blue half on the bottom, exactly like the flag's emblem, with the four black trigram bars "
          "(geon, gon, gam, ri) placed small at the diagonal corners around it, on white paper. "
          "Very few elements, strong silhouette, high contrast so it stays readable at 48 pixels. Plain warm cream "
          "paper background. No text, no letters." + c.g.STYLE_SUF)

if __name__ == "__main__":
    raw = os.path.join(HERE, "ep01_images", "profile_raw.png")
    if not c.one(c.codex_exe(), PROMPT, raw):
        raise SystemExit("FAIL")
    im = Image.open(raw).convert("RGB")
    s = min(im.size)
    x, y = (im.width - s) // 2, (im.height - s) // 2
    im.crop((x, y, x + s, y + s)).resize((800, 800), Image.LANCZOS).save(os.path.join(HERE, "channel_profile.png"))
    print("OK")
