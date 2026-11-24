# -*- coding: utf-8 -*-
"""One Codex image for the channel banner background -> ep01_images/banner_bg.png"""
import importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c", os.path.join(HERE, "oik_gen_codex.py"))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

PROMPT = (c.g.STYLE_PRE +
          "a wide panoramic Seoul-style cityscape at sunrise: in the middle distance, rows of identical "
          "numbered high-rise apartment blocks; in the foreground, a cluster of traditional hanok houses "
          "with curved dark grey tiled roofs; behind them, layered blue-grey mountains and a large orange "
          "paper sun. Keep the central horizontal band calm and uncluttered (plain sky and distant apartment "
          "rooftops) because text will be placed there. No churches, no domes, no Western buildings, no people, "
          "no text, no signs." + c.g.STYLE_SUF)

if __name__ == "__main__":
    ok = c.one(c.codex_exe(), PROMPT, os.path.join(HERE, "ep01_images", "banner_bg.png"))
    print("OK" if ok else "FAIL")
