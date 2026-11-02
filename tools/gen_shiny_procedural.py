#!/usr/bin/env python3
"""為沒有上游異色素材的物種（我們自己程序生成的 4 隻）合成異色貼圖。

做法：把所有像素做色相偏移 + 提亮，保留 alpha。
輸出 rp/textures/entity/pokemon/<id>_shiny.png（已存在則跳過）。
"""
import glob
import os
import sys

from PIL import Image

RP = sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon/rp"
TEX = os.path.join(RP, "textures", "entity", "pokemon")
SHIFT = {"dialga": 150, "palkia": 95, "giratina": 60, "arceus": 200}


def hue_shift(img, deg, sat=1.25, val=1.12):
    hsv = img.convert("RGBA").convert("RGB").convert("HSV")
    h, s, v = hsv.split()
    h = h.point(lambda x: (x + int(deg / 360 * 255)) % 255)
    s = s.point(lambda x: min(255, int(x * sat)))
    v = v.point(lambda x: min(255, int(x * val)))
    out = Image.merge("HSV", (h, s, v)).convert("RGB")
    out.putalpha(img.convert("RGBA").split()[-1])
    return out


made = 0
for pid, deg in SHIFT.items():
    src = os.path.join(TEX, f"{pid}.png")
    dst = os.path.join(TEX, f"{pid}_shiny.png")
    if not os.path.exists(src):
        print(f"  ✘ {pid} 沒有基礎貼圖")
        continue
    if os.path.exists(dst):
        print(f"  · {pid} 已有異色，跳過")
        continue
    img = Image.open(src).convert("RGBA")
    hue_shift(img, deg).save(dst)
    made += 1
    print(f"  ✔ {pid}_shiny.png（色相 +{deg}°）")

print(f"合成異色貼圖 {made} 張；現有 shiny 檔數 "
      f"{len(glob.glob(os.path.join(TEX, '*_shiny.png')))}")
