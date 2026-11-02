#!/usr/bin/env python3
"""生成生怪蛋圖示：底殼顏色 = 該物種主色，疊加層 = 一張 16x16 的臉。

自訂實體的生怪蛋在沒有 spawn_egg 定義時是「全黑」的，
所以要在 client entity 的 description.spawn_egg 裡給 base_color / overlay_color / texture。

用法: python3 tools/gen_egg_icons.py <rp_dir>
輸出: <rp_dir>/textures/items/egg_<id>.png、更新 item_texture.json、
      改寫 <rp_dir>/entity/*.entity.json 的 spawn_egg，最後印出一張預覽圖。
"""
import glob
import json
import os
import sys
from collections import Counter

from PIL import Image, ImageDraw

# 物種主色（拿不到貼圖時的後備）
# 策展配色優先：直接從貼圖算主色會偏暗、偏綠（貼圖含陰影/多部件），辨識度差
CURATED = {
    "pikachu": "#F7D02C", "eevee": "#C9A66B", "bulbasaur": "#7AC74C",
    "charmander": "#EE8130", "squirtle": "#6390F0", "jigglypuff": "#F7A8C4",
    "meowth": "#E8D9A0", "gengar": "#7B62A3", "snorlax": "#5C6B7A",
    "dragonite": "#E8A05A", "charizard": "#E8823A", "mewtwo": "#B0A6C8",
    # 第二批
    "psyduck": "#F5D67B", "gyarados": "#2F6FD0", "lapras": "#6BA8D8",
    "machamp": "#8A8AA0", "alakazam": "#E8C24A", "onix": "#8A8A8E",
    "lucario": "#3A6BD8", "gardevoir": "#DCE8E8", "greninja": "#3A7BD8",
    "mimikyu": "#C8B888", "sylveon": "#F2C8D8", "garchomp": "#3A5A8A",
}


def dominant_color(img):
    """取不透明像素裡最常見的顏色（量化到 16 級，避免雜訊）。"""
    rgba = img.convert("RGBA")
    cnt = Counter()
    for r, g, b, a in rgba.getdata():
        if a < 128:
            continue
        cnt[(r // 16 * 16, g // 16 * 16, b // 16 * 16)] += 1
    if not cnt:
        return None
    r, g, b = cnt.most_common(1)[0][0]
    return f"#{r + 8:02X}{g + 8:02X}{b + 8:02X}"


def shade(hex_color, factor):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda v: max(0, min(255, int(v * factor)))
    return f"#{f(r):02X}{f(g):02X}{f(b):02X}"


def make_face(base_hex, seed_dark):
    """16x16 透明底，畫眼睛 + 嘴（畫在蛋的中上位置）。"""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark = seed_dark
    white = (255, 255, 255, 235)

    # 兩顆眼白
    d.rectangle([3, 5, 6, 8], fill=white)
    d.rectangle([9, 5, 12, 8], fill=white)
    # 瞳孔
    d.rectangle([5, 6, 6, 8], fill=dark)
    d.rectangle([9, 6, 10, 8], fill=dark)
    # 嘴
    d.rectangle([6, 10, 9, 10], fill=dark)
    d.point((6, 11), fill=dark)
    d.point((9, 11), fill=dark)
    # 腮紅
    cheek = shade(base_hex, 1.25)
    cr, cg, cb = (int(cheek.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    d.rectangle([1, 9, 2, 10], fill=(cr, cg, cb, 200))
    d.rectangle([13, 9, 14, 10], fill=(cr, cg, cb, 200))
    return img


def make_egg_sprite(base_hex, portrait, size=32):
    """蛋形外殼（主色 + 陰影 + 描邊）＋ 裡面貼 3D 頭像，並用蛋形遮罩裁切。

    生怪蛋的 overlay 貼圖是「原樣疊上去」的，不會被蛋形裁切，
    所以蛋形要自己畫進貼圖裡，然後把 base_color / overlay_color 都設成白色避免二次著色。
    """
    w = size
    img = Image.new("RGBA", (w, w), (0, 0, 0, 0))

    # 蛋形遮罩
    mask = Image.new("L", (w, w), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([w * 0.14, w * 0.06, w * 0.86, w * 0.96], fill=255)

    # 蛋殼底色（上亮下暗，做出球形感）
    shell = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shell)
    h = base_hex.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    for y in range(w):
        t = y / max(1, w - 1)
        f = 1.18 - 0.42 * t
        sd.line([(0, y), (w, y)], fill=(min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), 255))
    img.paste(shell, (0, 0), mask)

    # 頭像：等比塞進蛋的中段
    if portrait is not None:
        pw = int(w * 0.74)
        head = portrait.copy()
        head.thumbnail((pw, pw), Image.LANCZOS)
        hx = (w - head.width) // 2
        hy = int(w * 0.10) + (pw - head.height) // 2
        layer = Image.new("RGBA", (w, w), (0, 0, 0, 0))
        layer.paste(head, (hx, hy), head)
        la = layer.split()[3].point(lambda v: v)
        clip = Image.composite(layer.split()[3], Image.new("L", (w, w), 0), mask)
        layer.putalpha(clip)
        img.alpha_composite(layer)

    # 描邊 + 高光
    d = ImageDraw.Draw(img)
    d.ellipse([w * 0.14, w * 0.06, w * 0.86, w * 0.96],
              outline=(28, 28, 28, 235), width=max(1, w // 24))
    d.ellipse([w * 0.26, w * 0.13, w * 0.40, w * 0.24], fill=(255, 255, 255, 90))
    return img


def main(rp_dir):
    tex_dir = os.path.join(rp_dir, "textures", "entity", "pokemon")
    out_dir = os.path.join(rp_dir, "textures", "items")
    os.makedirs(out_dir, exist_ok=True)

    item_tex_path = os.path.join(rp_dir, "textures", "item_texture.json")
    item_tex = json.load(open(item_tex_path, encoding="utf-8"))
    item_tex.setdefault("texture_data", {})

    colors = {}
    previews = []

    for ent_path in sorted(glob.glob(os.path.join(rp_dir, "entity", "*.entity.json"))):
        pid = os.path.basename(ent_path).replace(".entity.json", "")
        tex_path = os.path.join(tex_dir, f"{pid}.png")
        base = CURATED.get(pid)
        if not base:
            base = "#888888"
            if os.path.exists(tex_path):
                base = dominant_color(Image.open(tex_path)) or base
        colors[pid] = base

        portrait_path = os.path.join(out_dir, f"portrait_{pid}.png")
        portrait = Image.open(portrait_path).convert("RGBA") if os.path.exists(portrait_path) else None
        sprite = make_egg_sprite(base, portrait, size=32)
        sprite_path = os.path.join(out_dir, f"egg_{pid}.png")
        sprite.save(sprite_path)

        key = f"poke_egg_{pid}"
        item_tex["texture_data"][key] = {"textures": f"textures/items/egg_{pid}"}

        d = json.load(open(ent_path, encoding="utf-8"))
        desc = d["minecraft:client_entity"]["description"]
        desc["spawn_egg"] = {
            # 白底白疊加：外觀完全由我們的貼圖決定（蛋形已畫進貼圖）
            "base_color": "#FFFFFF",
            "overlay_color": "#FFFFFF",
            "texture": key,
            "texture_index": 0,
        }
        json.dump(d, open(ent_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        previews.append((pid, base, sprite))
        print(f"  {pid:12s} base={base} 頭像={'有' if portrait else '無'}")

    json.dump(item_tex, open(item_tex_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"item_texture.json 共 {len(item_tex['texture_data'])} 個條目")

    # 預覽圖：12 顆蛋排成一列（蛋殼 = 主色，中央貼臉）
    cols = 8
    cell = 96
    pad = 6
    rows = (len(previews) + cols - 1) // cols
    prev = Image.new("RGBA", (cols * (cell + pad) + pad, rows * (cell + pad) + pad), (32, 32, 40, 255))
    for i, (pid, base, sprite) in enumerate(previews):
        big = sprite.resize((cell, cell), Image.NEAREST)
        prev.alpha_composite(big, (pad + (i % cols) * (cell + pad), pad + (i // cols) * (cell + pad)))
    prev_path = "/tmp/egg_preview.png"
    prev.save(prev_path)
    print(f"預覽圖: {prev_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "packs/pokemon/rp")
