#!/usr/bin/env python3
"""產生 README 用的示意圖（從 add-on 自己的貼圖拼成，不是畫假圖）。

輸出 docs/images/*.png：
  species.png  57 種寶可夢 + 中英日名稱
  shiny.png    異色對照（本體 / 異色）
  eggs.png     112 個生怪蛋圖示
  items.png    精靈球與道具
  dex.png      圖鑑頭像
"""
import glob
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
BG = (24, 26, 32)
FG = (232, 236, 244)
SUB = (150, 158, 172)
ACCENT = (90, 170, 255)


def font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def grid(images, cols, cell, pad, labels=None, title=None, label_h=34):
    rows = (len(images) + cols - 1) // cols
    head = 64 if title else 0
    W = cols * cell + (cols + 1) * pad
    H = head + rows * (cell + label_h) + (rows + 1) * pad
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    if title:
        d.text((pad, 18), title, font=font(26), fill=FG)
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        x = pad + c * (cell + pad)
        y = head + pad + r * (cell + label_h + pad)
        box = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
        im2 = im.copy()
        im2 = im2.resize((int(im2.width * min((cell - 8) / im2.width, (cell - 8) / im2.height)),
                          int(im2.height * min((cell - 8) / im2.width, (cell - 8) / im2.height))), Image.LANCZOS)
        box.alpha_composite(im2, ((cell - im2.width) // 2, (cell - im2.height) // 2))
        canvas.paste(box, (x, y), box)
        if labels:
            d.text((x + cell // 2, y + cell + 4), labels[i], font=font(13), fill=SUB, anchor="ma")
    return canvas


def main(pack_dir, out_dir):
    rp = os.path.join(pack_dir, "rp")
    os.makedirs(out_dir, exist_ok=True)
    zh = open(os.path.join(rp, "texts", "zh_CN.lang"), encoding="utf-8").read()
    ja = open(os.path.join(rp, "texts", "ja_JP.lang"), encoding="utf-8").read()
    en = open(os.path.join(rp, "texts", "en_US.lang"), encoding="utf-8").read()
    ZH = dict(re.findall(r"^entity\.poke:([a-z_]+)\.name=(.+)", zh, re.M))
    JA = dict(re.findall(r"^entity\.poke:([a-z_]+)\.name=(.+)", ja, re.M))
    EN = dict(re.findall(r"^entity\.poke:([a-z_]+)\.name=(.+)", en, re.M))

    base = sorted(k for k in ZH if not k.endswith("_shiny"))
    # 實體貼圖是 UV 展開圖，直接拼會變碎片 → 用圖鑑頭像（角色臉）
    tex = {os.path.basename(p)[4:-4]: p for p in glob.glob(os.path.join(rp, "textures", "ui", "dex_*.png"))}

    # 1) 全物種
    imgs, labels = [], []
    for pid in base:
        if pid in tex:
            imgs.append(Image.open(tex[pid]).convert("RGBA"))
            labels.append(f"{ZH[pid]}\n{EN.get(pid, pid)}\n{JA.get(pid, pid)}")
    grid(imgs, 6, 150, 16, labels,
         f"{len(imgs)} species  ·  zh_CN / en_US / ja_JP").save(os.path.join(out_dir, "species.png"))
    print("species.png", len(imgs), "隻")

    # 2) 異色對照
    pairs = []
    for pid in base:
        s = f"{pid}_shiny"
        if pid in tex and s in tex:
            pairs.append((pid, tex[pid], tex[s]))
    imgs, labels = [], []
    for pid, a, b in pairs[:24]:
        for path, tag in ((a, ""), (b, " ✦")):
            imgs.append(Image.open(path).convert("RGBA"))
            labels.append(f"{ZH[pid]}{tag}")
    grid(imgs, 8, 130, 14, labels, f"Shiny variants ({len(pairs)} pairs, 1/64 chance)").save(
        os.path.join(out_dir, "shiny.png"))
    print("shiny pairs", len(pairs))

    # 3) 生怪蛋
    eggs = sorted(glob.glob(os.path.join(rp, "textures", "items", "egg_*.png")))
    grid([Image.open(p).convert("RGBA") for p in eggs], 16, 56, 6, None,
         f"{len(eggs)} spawn eggs").save(os.path.join(out_dir, "eggs.png"))
    print("eggs.png", len(eggs))

    # 4) 圖鑑頭像
    # 圖鑑頭像已併進 species.png，不另外輸出

    # 5) 道具
    ITEMS = dict(re.findall(r"^item\.poke:([a-z_0-9]+)=(.*)", zh, re.M))
    texmap = json.load(open(os.path.join(rp, "textures", "item_texture.json"), encoding="utf-8"))["texture_data"]
    ic = {}
    for key, val in texmap.items():
        path = os.path.join(rp, val["textures"] + ".png") if isinstance(val.get("textures"), str) else None
        if path and os.path.exists(path):
            ic[key] = path
    imgs, labels = [], []
    for iid, name in ITEMS.items():
        key = f"poke_{iid}"
        if key in ic:
            imgs.append(Image.open(ic[key]).convert("RGBA"))
            labels.append(name)
    grid(imgs, 10, 84, 10, labels, f"{len(imgs)} items & balls").save(os.path.join(out_dir, "items.png"))
    print("items.png", len(imgs))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon",
         sys.argv[2] if len(sys.argv) > 2 else "docs/images")
