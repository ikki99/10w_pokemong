#!/usr/bin/env python3
"""用 add-on 自己的素材生成宣傳圖（不是示意圖，每一隻都是遊戲裡實際載入的模型）。

輸出 promo/
  hero.png       1600×900   主視覺（含標題、數字、九宮格）
  square.png     1080×1080  方形版（朋友圈 / 文章頭圖）
  features.png   1200×800   四個功能區塊
  eggwall.png    1600×900   112 顆生怪蛋牆
  shiny.png      1600×900   異色對照牆
"""
import glob
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_dex_icons as R  # noqa: E402

FONT_BOLD = "/home/wngx99/.fonts/NotoSerifCJKsc-Bold.otf"
FONT_UI = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
BG = (13, 15, 20)
BG2 = (22, 26, 34)
GOLD = (232, 197, 92)
WHITE = (240, 242, 248)
GREY = (146, 154, 168)


def F(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def canvas(w, h):
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    # 徑向漸層 + 細點陣，避免死黑
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=(int(BG2[0] + (BG[0] - BG2[0]) * t),
                                        int(BG2[1] + (BG[1] - BG2[1]) * t),
                                        int(BG2[2] + (BG[2] - BG2[2]) * t)))
    for x in range(0, w, 28):
        for y in range(0, h, 28):
            d.point((x, y), fill=(38, 42, 52))
    return img


def glow(img, box, color):
    """在指定區域疊一層柔光（先模糊再加，避免生硬邊緣）。"""
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(box, fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(28))
    return Image.blend(img, Image.blend(img, layer, 0.0).point(lambda v: v), 0) if False else Image.blend(img, img, 0)


def render_big(rp, pid, px=384, shiny=False):
    out = f"/tmp/promo_{pid}{'_s' if shiny else ''}.png"
    R.SIZE = px
    R.SS = 2
    R.render(rp, pid, out, shiny=shiny)
    R.SIZE = 96
    R.SS = 3
    try:
        return Image.open(out).convert("RGBA")
    except Exception:
        return None


def text(d, xy, s, f, fill=WHITE, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def hero(rp, out):
    W, H = 1600, 900
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=GOLD)
    text(d, (80, 92), "Minecraft 基岩版 · 開源同人", F(FONT_UI, 30), GOLD)
    text(d, (78, 140), "寶可夢", F(FONT_BOLD, 116), WHITE)
    text(d, (80, 274), "在自己的世界裡抓皮卡丘", F(FONT_BOLD, 52), WHITE)
    text(d, (80, 348), "自架伺服器就能玩，Switch、手機、電腦都通", F(FONT_UI, 32), GREY)
    stats = [("57", "種寶可夢"), ("112", "個實體（含異色）"), ("28", "種精靈球"), ("3", "種語言")]
    x = 82
    for num, label in stats:
        text(d, (x, 452), num, F(FONT_BOLD, 66), GOLD)
        text(d, (x, 528), label, F(FONT_UI, 24), GREY)
        x += 250
    # CTA 徽章
    d.rounded_rectangle([82, 610, 640, 684], radius=14, fill=(232, 197, 92))
    text(d, (110, 632), "GitHub 開源 · ikki99/10w_pokemong", F(FONT_UI, 28), (20, 20, 24))
    d.rounded_rectangle([82, 706, 300, 748], radius=10, outline=(92, 98, 112), width=2)
    text(d, (104, 716), "非商業 · 不可販售", F(FONT_UI, 22), (198, 204, 216))
    grid = ["charizard", "pikachu", "rayquaza", "tyranitar", "lugia", "mewtwo",
            "arceus", "gengar", "dragapult"]
    gx, gy, cell = 900, 120, 210
    for i, pid in enumerate(grid):
        im = render_big(rp, pid, 320)
        if not im:
            continue
        im = im.resize((cell, cell), Image.LANCZOS)
        cx, cy = gx + (i % 3) * (cell + 18), gy + (i // 3) * (cell + 18)
        box = Image.new("RGBA", (cell + 16, cell + 16), (26, 30, 38, 255))
        box.alpha_composite(im, (8, 8))
        img.paste(box, (cx, cy), box)
    img.save(out)
    print("hero.png", img.size)


def square(rp, out):
    S = 1080
    img = canvas(S, S)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S, 5], fill=GOLD)
    text(d, (64, 70), "寶可夢", F(FONT_BOLD, 92), WHITE)
    text(d, (64, 176), "Minecraft 基岩版模組", F(FONT_BOLD, 40), GOLD)
    ids = ["lugia", "charizard", "rayquaza", "tyranitar", "mewtwo", "gengar"]
    cell = 250
    for i, pid in enumerate(ids):
        im = render_big(rp, pid, 320)
        if not im:
            continue
        im = im.resize((cell, cell), Image.LANCZOS)
        x = 64 + (i % 3) * (cell + 20)
        y = 260 + (i // 3) * (cell + 16)
        img.paste(im, (x, y), im)
    text(d, (64, 810), "57 種寶可夢 · 112 個實體 · 開源", F(FONT_UI, 34), WHITE)
    text(d, (64, 866), "github.com/ikki99/10w_pokemong", F(FONT_UI, 26), GREY)
    text(d, (64, 920), "非商業同人 · 不可上架市集", F(FONT_UI, 22), GREY)
    img.save(out)
    print("square.png", img.size)


def features(rp, out, tex=None):
    W, H = 1200, 800
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    text(d, (60, 56), "57 種寶可夢，在你自己的伺服器裡", F(FONT_BOLD, 54), WHITE)
    bricks = [
        ("poke_pokeball", "28 種精靈球", "血量越低越好抓，附捕捉演出"),
        ("poke_pokedex", "圖鑑 GUI", "分頁瀏覽，左側顯示縮圖"),
        ("poke_egg_charizard", "112 顆生怪蛋", "每顆有自己的圖示與三語名字"),
        ("poke_fire_stone", "56 種道具", "10 種進化石、6 種樹果、8 枚徽章"),
    ]
    for i, (icon, title, sub) in enumerate(bricks):
        cx = 60 + (i % 2) * 560
        cy = 200 + (i // 2) * 280
        d.rectangle([cx, cy, cx + 500, cy + 220], fill=(24, 28, 36), outline=(44, 50, 62), width=2)
        info = tex.get(icon)
        path = None
        if info and isinstance(info.get("textures"), str):
            path = os.path.join(rp, info["textures"] + ".png")
        if not path or not os.path.exists(path):
            cand = glob.glob(os.path.join(rp, "textures", "items", f"*{icon.replace('poke_', '')}*.png"))
            path = cand[0] if cand else None
        if path and os.path.exists(path):
            ic = Image.open(path).convert("RGBA").resize((96, 96), Image.LANCZOS)
            img.paste(ic, (cx + 24, cy + 62), ic)
        text(d, (cx + 136, cy + 62), title, F(FONT_BOLD, 34), WHITE)
        text(d, (cx + 136, cy + 108), sub, F(FONT_UI, 24), GREY)
        text(d, (cx + 24, cy + 168), "v5.0.0 · 2026", F(FONT_UI, 19), (86, 94, 108))
    text(d, (60, H - 66), "github.com/ikki99/10w_pokemong", F(FONT_UI, 26), GREY)
    img.save(out)
    print("features.png", img.size)


def eggwall(rp, out):
    W, H = 1600, 900
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    eggs = sorted(glob.glob(os.path.join(rp, "textures", "items", "egg_*.png")))
    cols, cell = 16, 78
    total_w = cols * cell
    x0 = (W - total_w) // 2
    y0 = 210
    for i, p in enumerate(eggs):
        im = Image.open(p).convert("RGBA").resize((cell - 12, cell - 12), Image.LANCZOS)
        x = x0 + (i % cols) * cell
        y = y0 + (i // cols) * cell
        img.paste(im, (x, y), im)
    text(d, (W // 2, 92), "112 顆生怪蛋", F(FONT_BOLD, 72), WHITE, anchor="ma")
    text(d, (W // 2, 176), "每一顆都有自己的圖示，而且都有名字", F(FONT_UI, 30), GREY, anchor="ma")
    text(d, (W // 2, H - 60), "寶可夢 · Minecraft 基岩版 · 開源同人", F(FONT_UI, 24), GOLD, anchor="ma")
    img.save(out)
    print("eggwall.png", img.size)


def shiny(rp, out):
    W, H = 1600, 900
    img = canvas(W, H)
    d = ImageDraw.Draw(img)
    ids = ["charizard", "pikachu", "rayquaza", "lugia", "tyranitar", "mewtwo"]
    cell = 210
    for i, pid in enumerate(ids):
        a = render_big(rp, pid, 300)
        b = render_big(rp, pid, 300, shiny=True)
        y = 210 + (i // 3) * (cell + 30)
        x = 150 + (i % 3) * (cell * 2 + 60)
        if a:
            img.paste(a.resize((cell, cell), Image.LANCZOS), (x, y), a.resize((cell, cell), Image.LANCZOS))
        if b:
            img.paste(b.resize((cell, cell), Image.LANCZOS), (x + cell + 10, y), b.resize((cell, cell), Image.LANCZOS))
    text(d, (W // 2, 92), "異色機率 1/64", F(FONT_BOLD, 72), WHITE, anchor="ma")
    text(d, (W // 2, 176), "左邊是普通，右邊是異色，各有自己的貼圖與名字", F(FONT_UI, 30), GREY, anchor="ma")
    text(d, (W // 2, H - 60), "寶可夢 · Minecraft 基岩版 · 開源同人", F(FONT_UI, 24), GOLD, anchor="ma")
    img.save(out)
    print("shiny.png", img.size)


def main(pack_dir, out_dir):
    rp = os.path.join(pack_dir, "rp")
    os.makedirs(out_dir, exist_ok=True)
    hero(rp, os.path.join(out_dir, "hero.png"))
    square(rp, os.path.join(out_dir, "square.png"))
    tex = json.load(open(os.path.join(rp, "textures", "item_texture.json"), encoding="utf-8"))["texture_data"]
    features(rp, os.path.join(out_dir, "features.png"), tex)
    eggwall(rp, os.path.join(out_dir, "eggwall.png"))
    shiny(rp, os.path.join(out_dir, "shiny.png"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon",
         sys.argv[2] if len(sys.argv) > 2 else "promo")
