#!/usr/bin/env python3
"""手工打造的高細節阿爾宙斯模型（取代原本只有 9 個方塊的程序生出版本）。

設計要點
- 四足站姿、長頸、灰白面罩、金色十字輪（4 段弧 + 4 根輻條 + 中央綠寶石）、三段尾巴
- 全部使用 box UV：每個方塊指向一張「純色色塊」，所以不會有接縫錯位，也不需要手畫 UV
- 貼圖是 512×512 的 8×8 色塊表，每個色塊 64×64
- 骨頭命名刻意配合 fix_models_anim 的分類規則：
    body / torso / torso2      → 身
    neck / neck2 / neck3       → 頸（只做微幅點頭）
    head                       → 頭
    leg0..leg3                 → 腿（只有上段進動畫，小腿與蹄是子骨頭，跟著父骨頭走）
    tail / tail2 / tail3       → 尾
    ear_l / ear_r              → 耳

用法：
  python3 tools/gen_arceus_model.py packs/pokemon
  python3 tools/gen_arceus_model.py packs/pokemon --shiny
"""
import json
import math
import os
import sys

from PIL import Image

W = H = 512
CELL = 64
COLORS = [
    (0xF4, 0xF2, 0xEC),  # 0 身體白
    (0xE3, 0xE0, 0xD6),  # 1 腹部淡灰
    (0x8A, 0x8D, 0x85),  # 2 面罩灰
    (0x4A, 0x4C, 0x48),  # 3 深灰
    (0xE8, 0xC5, 0x5C),  # 4 金色
    (0xB9, 0x92, 0x2F),  # 5 暗金
    (0x4F, 0xC7, 0x7A),  # 6 綠寶石
    (0x2F, 0x7A, 0x4A),  # 7 深綠
    (0xC2, 0x3B, 0x2E),  # 8 紅眼
    (0x1A, 0x1A, 0x1A),  # 9 黑
    (0xF5, 0xE3, 0xA8),  # 10 亮金
    (0x3A, 0x3A, 0x38),  # 11 蹄
    (0xFA, 0xF8, 0xF2),  # 12 亮白
    (0xB8, 0xBB, 0xB2),  # 13 淺灰綠
    (0x7E, 0x20, 0x18),  # 14 暗紅
    (0xFF, 0xFF, 0xFF),  # 15 純白
]
NAMES = {"white": 0, "belly": 1, "mask": 2, "dark": 3, "gold": 4, "goldD": 5,
         "jewel": 6, "jewelD": 7, "eye": 8, "black": 9, "goldL": 10, "hoof": 11,
         "whiteL": 12, "greyL": 13, "eyeD": 14, "pure": 15}


def uv_of(color):
    i = NAMES[color] if isinstance(color, str) else color
    return [(i % 8) * CELL, (i // 8) * CELL]


class Model:
    def __init__(self):
        self.bones = []

    def bone(self, name, parent=None, pivot=(0, 0, 0), rotation=None):
        if isinstance(parent, dict):        # 允許直接傳父骨頭物件
            parent = parent["name"]
        b = {"name": name, "pivot": list(pivot)}
        if parent:
            b["parent"] = parent
        if rotation:
            b["rotation"] = list(rotation)
        b["cubes"] = []
        self.bones.append(b)
        return b

    @staticmethod
    def cube(bone, x0, y0, z0, sx, sy, sz, color, inflate=0.0, rotation=None, pivot=None):
        c = {"origin": [x0, y0, z0], "size": [sx, sy, sz], "uv": uv_of(color)}
        if inflate:
            c["inflate"] = inflate
        if rotation:
            c["rotation"] = list(rotation)
            c["pivot"] = list(pivot if pivot else [x0 + sx / 2, y0 + sy / 2, z0 + sz / 2])
        bone["cubes"].append(c)

    def geo(self, identifier="geometry.poke_arceus_detailed"):
        return {
            "format_version": "1.12.0",
            "minecraft:geometry": [{
                "description": {
                    "identifier": identifier,
                    "texture_width": W,
                    "texture_height": H,
                    "visible_bounds_width": 6,
                    "visible_bounds_height": 6,
                    "visible_bounds_offset": [0, 2.5, 0],
                },
                "bones": self.bones,
            }],
        }


def build():
    m = Model()
    C = Model.cube

    # ---------------- 身軀（四足，前 -z） ----------------
    body = m.bone("body", pivot=(0, 24, 0))
    C(body, -7, 19, 2, 14, 9, 12, "white")            # 後臀
    C(body, -8, 20, -8, 16, 9, 11, "white")           # 胸腔
    C(body, -6.5, 18.5, -3, 13, 3, 12, "belly")       # 腹部淡色
    C(body, -5, 26.5, -6, 10, 3, 14, "white")         # 背脊隆起
    C(body, -4, 27, 6, 8, 2, 5, "greyL")              # 臀部灰紋

    torso = m.bone("torso", parent="body", pivot=(0, 24, -6))
    C(torso, -6, 21, -12, 12, 6, 5, "white")          # 肩部
    C(torso, -3, 20, -13.5, 6, 4, 2, "belly")         # 胸口淡色
    torso2 = m.bone("torso2", parent="torso", pivot=(0, 27, -8))
    C(torso2, -4.5, 27, -11, 9, 4, 4, "white")

    # ---------------- 脖子（往上往前） ----------------
    n1 = m.bone("neck", parent="torso2", pivot=(0, 28, -9))
    C(n1, -3.5, 28, -12, 7, 6, 6, "white")
    C(n1, -4.5, 30, -6, 9, 3, 5, "greyL")             # 頸後的灰色鬃毛
    n2 = m.bone("neck2", parent="neck", pivot=(0, 34, -10))
    C(n2, -3, 34, -13, 6, 5, 5, "white")
    C(n2, -4, 36, -8, 8, 2.5, 4, "greyL")
    n3 = m.bone("neck3", parent="neck2", pivot=(0, 39, -11))
    C(n3, -2.5, 39, -14, 5, 4, 5, "white")
    C(n3, -3.5, 41, -9, 7, 2, 4, "mask")

    # ---------------- 頭 ----------------
    head = m.bone("head", parent="neck3", pivot=(0, 43, -11.5))
    C(head, -4, 43, -16, 8, 5, 9, "white")            # 顱
    C(head, -3, 43, -21, 6, 3.5, 6, "white")          # 吻部
    C(head, -2.5, 42.2, -20, 5, 1.5, 5, "mask")       # 下顎
    C(head, -4.2, 44, -15, 0.8, 3.5, 6, "mask")       # 左頰面罩
    C(head, 3.4, 44, -15, 0.8, 3.5, 6, "mask")        # 右頰面罩
    C(head, -2.6, 46.2, -19.4, 2, 1.6, 1.2, "eye")    # 左眼
    C(head, 0.6, 46.2, -19.4, 2, 1.6, 1.2, "eye")     # 右眼
    C(head, -2, 46.4, -19.9, 0.8, 0.9, 0.4, "eyeD")   # 左瞳
    C(head, 1.2, 46.4, -19.9, 0.8, 0.9, 0.4, "eyeD")  # 右瞳
    C(head, -1.2, 44.4, -21.6, 2.4, 1.2, 1, "gold")   # 鼻樑金飾
    C(head, -1, 47.6, -12, 2, 1.6, 6, "goldL")        # 頭頂金色脊冠

    ear_l = m.bone("ear_l", parent="head", pivot=(-3.4, 47, -12))
    C(ear_l, -5.4, 47, -13, 2, 5, 2.5, "gold", rotation=[0, 0, 18], pivot=[-4.4, 47, -12])
    C(ear_l, -6.2, 50.5, -13.4, 1.6, 2, 1.8, "goldL", rotation=[0, 0, 18], pivot=[-4.4, 47, -12])
    ear_r = m.bone("ear_r", parent="head", pivot=(3.4, 47, -12))
    C(ear_r, 3.4, 47, -13, 2, 5, 2.5, "gold", rotation=[0, 0, -18], pivot=[4.4, 47, -12])
    C(ear_r, 4.6, 50.5, -13.4, 1.6, 2, 1.8, "goldL", rotation=[0, 0, -18], pivot=[4.4, 47, -12])

    # ---------------- 金色十字輪（環面在 YZ 平面，側面看才是一整個圓） ----------------
    ring = m.bone("ring", parent="body", pivot=(0, 25, 0))
    R = 17.0
    for k in range(32):                                  # 環體：32 顆小方塊圍成一圈
        a = 2 * math.pi * k / 32
        py, pz = R * math.sin(a), R * math.cos(a)
        C(ring, -2.3, 25 + py - 2.3, pz - 2.3, 4.6, 4.6, 4.6, "gold" if k % 2 == 0 else "goldD")
    for base in (45, 135, 225, 315):                     # 四根斜輻條
        a = math.radians(base)
        for k in range(1, 5):
            r = R * k / 5.0
            C(ring, -1.2, 25 + r * math.sin(a) - 1.2, r * math.cos(a) - 1.2, 2.4, 2.4, 2.4, "goldL")
    for sx in (-1, 1):                                   # 左右兩側的十字圓盤 + 綠寶石
        C(ring, sx * 8.2 - 0.6 if sx < 0 else 7.6, 21.5, -3, 1.6, 7, 6, "goldD")
        C(ring, sx * 8.4 - 0.5 if sx < 0 else 7.9, 20.5, -4, 1.2, 9, 8, "gold")
        gem_x = -9.4 if sx < 0 else 8.2
        C(ring, gem_x, 22.4, -2.4, 1.4, 5.2, 4.8, "jewel")
        C(ring, gem_x - 0.3 if sx < 0 else gem_x + 1.1, 23.6, -1.2, 0.6, 2.8, 2.4, "jewelD")

    # ---------------- 四條腿（只有上段進動畫） ----------------
    legs = [("leg0", -7, -9), ("leg1", 7, -9), ("leg2", -7, 9), ("leg3", 7, 9)]
    for name, x, z in legs:
        upper = m.bone(name, parent="body", pivot=(x, 21, z))
        C(upper, x - 3.5, 12, z - 3.5, 7, 10, 7, "white")
        C(upper, x - 3.9, 18, z - 3.9, 7.8, 2.5, 7.8, "belly")     # 大腿灰色環
        lower = m.bone(name + "_lower", parent=name, pivot=(x, 12, z))
        C(lower, x - 2.6, 5, z - 2.6, 5.2, 7, 5.2, "white")
        C(lower, x - 2.8, 8.5, z - 2.8, 5.6, 1.6, 5.6, "greyL")
        hoof = m.bone(name + "_hoof", parent=name + "_lower", pivot=(x, 5, z))
        C(hoof, x - 3, 0, z - 3.6, 6, 5, 7.2, "white")
        C(hoof, x - 3.2, 0, z - 3.8, 6.4, 1.6, 7.6, "hoof")       # 蹄底
        C(hoof, x - 1.2, 1.4, z - 4.2, 2.4, 2.2, 1, "gold")       # 前蹄金飾

    # ---------------- 尾巴 ----------------
    t1 = m.bone("tail", parent="body", pivot=(0, 25, 13))
    C(t1, -2.5, 23, 13, 5, 5, 6, "white", rotation=[-18, 0, 0], pivot=[0, 25, 13])
    t2 = m.bone("tail2", parent="tail", pivot=(0, 26, 18))
    C(t2, -2, 25, 18, 4, 4, 5, "white", rotation=[-28, 0, 0], pivot=[0, 26, 18])
    t3 = m.bone("tail3", parent="tail2", pivot=(0, 28, 23))
    C(t3, -2.6, 27, 23, 5.2, 5.2, 4, "greyL", rotation=[-34, 0, 0], pivot=[0, 28, 23])
    C(t3, -1.4, 31, 24, 2.8, 3, 2.4, "gold", rotation=[-34, 0, 0], pivot=[0, 28, 23])
    return m


def make_texture(path, shiny=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for i, (r, g, b) in enumerate(COLORS):
        if shiny:                      # 異色：白 → 淡金、金 → 銀、綠寶石 → 藍
            if i in (0, 12, 15):
                r, g, b = 0xFA, 0xF3, 0xD8
            elif i in (4, 10):
                r, g, b = 0xD6, 0xDC, 0xE6
            elif i in (5,):
                r, g, b = 0x98, 0xA2, 0xB4
            elif i in (6, 7):
                r, g, b = (0x5A, 0xA8, 0xE8) if i == 6 else (0x2A, 0x5A, 0x8C)
        x0, y0 = (i % 8) * CELL, (i // 8) * CELL
        for y in range(y0, y0 + CELL):
            for x in range(x0, x0 + CELL):
                px[x, y] = (r, g, b, 255)
    img.save(path)


def main(pack_dir, shiny=False):
    rp = os.path.join(pack_dir, "rp")
    geo_path = os.path.join(rp, "models", "entity", "arceus.geo.json")
    tex_path = os.path.join(rp, "textures", "entity", "pokemon", "arceus" + ("_shiny" if shiny else "") + ".png")
    model = build()
    if shiny:
        # 異色沿用同一份幾何，只換貼圖
        make_texture(tex_path, shiny=True)
        print("異色貼圖 →", tex_path)
        return
    os.makedirs(os.path.dirname(geo_path), exist_ok=True)
    os.makedirs(os.path.dirname(tex_path), exist_ok=True)
    json.dump(model.geo(), open(geo_path, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    make_texture(tex_path)
    cubes = sum(len(b["cubes"]) for b in model.bones)
    print(f"幾何 → {geo_path}（骨骼 {len(model.bones)}、方塊 {cubes}）")
    print(f"貼圖 → {tex_path}")

    # 綁進 client entity
    ent_path = os.path.join(rp, "entity", "arceus.entity.json")
    if os.path.exists(ent_path):
        for pid in ("arceus", "arceus_shiny"):
            p = os.path.join(rp, "entity", f"{pid}.entity.json")
            if not os.path.exists(p):
                continue
            d = json.load(open(p, encoding="utf-8"))
            desc = d["minecraft:client_entity"]["description"]
            desc["geometry"] = {"default": "geometry.poke_arceus_detailed"}
            desc["textures"] = {"default": f"textures/entity/pokemon/{pid}"}
            json.dump(d, open(p, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
            print("已綁定:", p)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "packs/pokemon", shiny="--shiny" in sys.argv)
