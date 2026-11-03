#!/usr/bin/env python3
"""手工打造的高細節阿爾宙斯模型。

設計要點
- 珍珠白的纖長四足身形、灰色條紋腹部、狹長灰面與綠眼紅瞳
- 頭冠與後掠金角，腹前正面可見的十字金輪和四顆綠寶石
- 方塊 UV 共用 512×512 調色板貼圖；貼圖加入細微明暗與像素紋理
- 骨頭命名刻意配合 fix_models_anim 的分類規則：
    body / torso / torso2      → 身
    neck / neck2 / neck3       → 頸（只做微幅點頭）
    head / crest / horn_l/r    → 頭、頭冠與後掠金角
    ring                       → 正面十字金輪
    leg0..leg3                 → 腿（只有上段進動畫，小腿與蹄是子骨頭，跟著父骨頭走）
    tail / tail2 / tail3       → 尾

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
    (0xF6, 0xF4, 0xEE),  # 0 珍珠白身體
    (0xC9, 0xCE, 0xC8),  # 1 腹部淺灰
    (0x7D, 0x83, 0x7D),  # 2 面罩與腹部深條紋
    (0x4B, 0x50, 0x4D),  # 3 深灰陰影
    (0xD6, 0xA2, 0x27),  # 4 飽和金色
    (0x8F, 0x62, 0x12),  # 5 暗金陰影
    (0x63, 0xC9, 0x7C),  # 6 綠寶石與眼睛
    (0x2B, 0x75, 0x4C),  # 7 深綠切面
    (0xC2, 0x3B, 0x2E),  # 8 暖紅細節
    (0x1A, 0x1A, 0x1A),  # 9 黑
    (0xF4, 0xD4, 0x68),  # 10 亮金高光
    (0x8F, 0x6B, 0x25),  # 11 金色蹄底
    (0xFC, 0xFA, 0xF6),  # 12 亮白
    (0xAE, 0xB5, 0xAF),  # 13 淺灰綠
    (0x9C, 0x2A, 0x36),  # 14 紅色瞳孔
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
    """Arceus Normal form: pearl-white equine body and frontal gold cross-wheel."""
    m = Model()
    C = Model.cube

    body = m.bone("body", pivot=(0, 22, 0))
    C(body, -6, 17, -8, 12, 10, 22, "white")
    C(body, -5.5, 18, 9, 11, 8, 9, "white")
    C(body, -5, 16, -7, 10, 3, 19, "belly")
    C(body, -5, 26, -7, 10, 2, 18, "whiteL")
    C(body, -4.8, 17, 8, 9.6, 7, 6, "whiteL")
    # The original design has a visibly ribbed gray underside, not one flat belly patch.
    for i, x in enumerate((-3.6, -1.8, 0, 1.8, 3.6)):
        C(body, x - 0.55, 16.5, -5.5, 1.1, 4.5, 2.2 + (i % 2), "mask")
        C(body, x - 0.45, 16.8, 1.5, 0.9, 4.1, 2.4, "greyL")

    torso = m.bone("torso", parent="body", pivot=(0, 22, -7))
    C(torso, -5.5, 20, -15, 11, 8, 12, "white")
    C(torso, -4.5, 17.5, -14, 9, 3, 9, "belly")
    C(torso, -4.2, 19, -16, 8.4, 3, 2, "whiteL")
    torso2 = m.bone("torso2", parent="torso", pivot=(0, 25, -10))
    C(torso2, -4.4, 23, -18, 8.8, 7, 9, "white")
    C(torso2, -3.7, 22, -19, 7.4, 2.4, 2, "belly")
    for x in (-2.5, -0.8, 0.8, 2.5):
        C(torso2, x - 0.4, 20.5, -19.2, 0.8, 3.5, 1, "mask")

    neck = m.bone("neck", parent="torso2", pivot=(0, 28, -15))
    C(neck, -3.4, 27, -20, 6.8, 9, 7, "white")
    C(neck, -3.5, 28, -21, 7, 4, 2, "whiteL")
    neck2 = m.bone("neck2", parent="neck", pivot=(0, 35, -18))
    C(neck2, -2.8, 34, -24, 5.6, 8, 7, "white")
    C(neck2, -3, 35, -25, 6, 4.8, 2, "belly")
    for x in (-1.8, 0, 1.8):
        C(neck2, x - 0.45, 31.5, -25.3, 0.9, 4.8, 0.8, "mask")
    neck3 = m.bone("neck3", parent="neck2", pivot=(0, 41, -22))
    C(neck3, -2.4, 40, -28, 4.8, 6, 7, "white")
    C(neck3, -2.8, 41, -29, 5.6, 2.4, 2, "mask")

    head = m.bone("head", parent="neck3", pivot=(0, 44, -25))
    # Horse-like skull and tapered muzzle, with the familiar slate-gray face.
    C(head, -3.2, 42.5, -32, 6.4, 6.2, 8, "white")
    C(head, -2.4, 42, -38, 4.8, 3.7, 8, "whiteL")
    C(head, -2.15, 42.8, -39, 4.3, 1.6, 5.6, "mask")
    C(head, -3.25, 44, -34, 6.5, 2.6, 4.4, "mask")
    # Green eyes with restrained red pupils; no gold band across the muzzle.
    for x in (-2.25, 1.25):
        C(head, x, 45.3, -36.3, 1.4, 1.6, 0.8, "jewel")
        C(head, x + 0.45, 45.6, -37.0, 0.55, 0.9, 0.35, "eyeD")
        C(head, x - 0.3, 46.55, -36.9, 0.45, 0.35, 0.3, "pure")
    C(head, -0.9, 45.2, -39.4, 1.8, 0.9, 0.7, "dark")

    # A narrow crown sweep sits behind the brow instead of two rabbit-like prongs.
    crest = m.bone("crest", parent="head", pivot=(0, 47, -29))
    C(crest, -1.5, 46, -29, 3, 3.2, 3, "goldD")
    C(crest, -1.2, 48, -27, 2.4, 4.5, 3, "gold")
    C(crest, -0.85, 51, -24.8, 1.7, 4.2, 2.6, "goldL")
    C(crest, -0.5, 54, -22.8, 1, 3, 2, "gold")
    C(crest, -0.3, 56, -21.4, 0.6, 1.5, 1.5, "goldL")

    horn_l = m.bone("horn_l", parent="head", pivot=(-3.1, 46, -28))
    C(horn_l, -4.5, 44, -29, 2.2, 4.8, 3, "goldD", rotation=[24, 0, -18], pivot=[-3.5, 46, -27])
    C(horn_l, -5.3, 47, -26, 1.8, 3.6, 2.4, "gold", rotation=[28, 0, -24], pivot=[-3.5, 46, -27])
    C(horn_l, -5.6, 49, -24, 1.2, 2, 1.8, "goldL", rotation=[32, 0, -24], pivot=[-3.5, 46, -27])
    horn_r = m.bone("horn_r", parent="head", pivot=(3.1, 46, -28))
    C(horn_r, 2.3, 44, -29, 2.2, 4.8, 3, "goldD", rotation=[24, 0, 18], pivot=[3.5, 46, -27])
    C(horn_r, 3.5, 47, -26, 1.8, 3.6, 2.4, "gold", rotation=[28, 0, 24], pivot=[3.5, 46, -27])
    C(horn_r, 4.1, 49, -24, 1.2, 2, 1.8, "goldL", rotation=[32, 0, 24], pivot=[3.5, 46, -27])

    # The signature wheel is a face-on cross with four green gems, not an edge-on yellow loop.
    # One raised cross-wheel sits on the front of the body, matching Arceus's single halo.
    ring = m.bone("ring", parent="body", pivot=(0, 22, -1))
    center_y, radius, segments = 22, 14, 28
    for layer_index, layer_z in enumerate((-16.2,)):
        for quadrant in range(4):
            arc = m.bone(f"wheel_rim_{layer_index}_{quadrant}", parent="ring",
                         pivot=(0, center_y, layer_z), rotation=(0, 0, quadrant * 90))
            for j in range(7):
                angle_deg = -45 + j * 15
                angle = math.radians(angle_deg)
                cx, cy = radius * math.cos(angle), center_y + radius * math.sin(angle)
                C(arc, cx - 1.25, cy - 1.8, layer_z - 1.3, 2.5, 3.6, 2.6,
                  "goldL" if j in (0, 6) else ("goldD" if j % 2 else "gold"),
                  rotation=[0, 0, angle_deg], pivot=[cx, cy, layer_z])
        # A true plus-shaped cross joins the four settings across the open wheel.
        C(ring, -12, center_y - 1.65, layer_z - 1.3, 24, 3.3, 2.6, "gold")
        C(ring, -1.65, center_y - 12, layer_z - 1.3, 3.3, 24, 2.6, "goldL")
        for gx, gy in ((10.5, center_y), (-10.5, center_y), (0, center_y + 10.5), (0, center_y - 10.5)):
            C(ring, gx - 2.55, gy - 2.55, layer_z - 1.75, 5.1, 5.1, 3.5, "goldD")
            C(ring, gx - 1.8, gy - 1.8, layer_z - 1.95, 3.6, 3.6, 3.9, "jewel")
            C(ring, gx - 1.25, gy + 0.2, layer_z - 2.1, 0.9, 0.8, 0.35, "pure")

    for name, x, z in (("leg0", -5.8, -9), ("leg1", 5.8, -9), ("leg2", -5.8, 9), ("leg3", 5.8, 9)):
        upper = m.bone(name, parent="body", pivot=(x, 19, z))
        C(upper, x - 1.7, 10, z - 2.2, 3.4, 10, 4.4, "white")
        C(upper, x - 2.1, 17, z - 2.5, 4.2, 2.2, 5, "whiteL")
        lower = m.bone(name + "_lower", parent=name, pivot=(x, 10, z))
        C(lower, x - 1.2, 3, z - 1.7, 2.4, 8, 3.4, "white")
        C(lower, x - 1.35, 7, z - 1.9, 2.7, 1.4, 3.8, "mask")
        hoof = m.bone(name + "_hoof", parent=name + "_lower", pivot=(x, 3, z))
        C(hoof, x - 1.75, 0, z - 2.5, 3.5, 3.2, 5, "gold")
        C(hoof, x - 1.85, 0, z - 2.7, 3.7, 1.2, 5.4, "goldD")
        C(hoof, x - 1.1, 2, z - 2.9, 2.2, 0.65, 0.4, "goldL")

    tail = m.bone("tail", parent="body", pivot=(0, 23, 14))
    C(tail, -1.6, 21, 14, 3.2, 3.2, 7, "white", rotation=[-12, 0, 0], pivot=[0, 23, 14])
    C(tail, -2.1, 22.5, 19, 4.2, 2, 6, "whiteL")
    tail2 = m.bone("tail2", parent="tail", pivot=(0, 23, 20))
    C(tail2, -1.1, 21.5, 20, 2.2, 2.5, 7, "white", rotation=[-18, 0, 0], pivot=[0, 23, 20])
    tail3 = m.bone("tail3", parent="tail2", pivot=(0, 24, 27))
    C(tail3, -1.5, 23, 27, 3, 3.5, 5, "whiteL", rotation=[-22, 0, 0], pivot=[0, 24, 27])
    C(tail3, -0.7, 26, 30, 1.4, 2, 2, "gold")
    return m
def make_texture(path, shiny=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for i, (r, g, b) in enumerate(COLORS):
        if shiny:                      # 異色：身體轉為奶金色，保留金輪與綠寶石識別
            if i in (0, 12, 15):
                r, g, b = 0xF1, 0xD8, 0x91
            elif i == 1:
                r, g, b = 0xC9, 0xB7, 0x79
            elif i in (2, 13):
                r, g, b = 0x8B, 0x7C, 0x62
            elif i in (4, 10):
                r, g, b = 0xD5, 0x9C, 0x2F
            elif i == 5:
                r, g, b = 0x86, 0x55, 0x16
        x0, y0 = (i % 8) * CELL, (i // 8) * CELL
        for y in range(CELL):
            for x in range(CELL):
                shade = 1.08 - 0.16 * (y / (CELL - 1))
                shade += 0.035 * (1 - x / (CELL - 1))
                px[x0 + x, y0 + y] = tuple(max(0, min(255, int(c * shade))) for c in (r, g, b)) + (255,)
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
            desc["animations"] = {
                "idle": "animation.poke_arceus.idle",
                "walk": "animation.poke_arceus.walk",
                "fly": "animation.poke_arceus.fly",
                "attack": "animation.poke_arceus.attack",
            }
            desc["scripts"] = {"animate": [
                {"idle": "query.modified_move_speed <= 0.05"},
                {"walk": "query.modified_move_speed > 0.05 && query.is_on_ground"},
                {"fly": "query.modified_move_speed > 0.05 && !query.is_on_ground"},
                {"attack": "query.property('poke:attack')"},
            ]}
            json.dump(d, open(p, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
            print("已綁定:", p)

    animations = {"format_version": "1.8.0", "animations": {
        "animation.poke_arceus.idle": {
            "loop": True, "animation_length": 3.0,
            "bones": {
                "body": {"position": {"0.0": [0, 0, 0], "1.5": [0, 0.35, 0], "3.0": [0, 0, 0]},
                         "rotation": {"0.0": [0, 0, 0], "1.5": [1, 0, 0], "3.0": [0, 0, 0]}},
                "torso": {"rotation": {"0.0": [0, 0, 0], "1.5": [-1.5, 0, 0], "3.0": [0, 0, 0]}},
                "head": {"rotation": {"0.0": [0, 0, 0], "0.8": [2, 5, 0], "1.7": [0, -6, 0], "3.0": [0, 0, 0]}},
                "neck": {"rotation": {"0.0": [0, 0, 0], "1.5": [1.5, 0, 0], "3.0": [0, 0, 0]}},
                "ring": {"rotation": {"0.0": [0, 0, 0], "1.5": [0, 0, 5], "3.0": [0, 0, 0]}},
                "tail": {"rotation": {"0.0": [0, 8, 0], "1.5": [0, -8, 0], "3.0": [0, 8, 0]}},
                "tail2": {"rotation": {"0.0": [0, 5, 0], "1.5": [0, -5, 0], "3.0": [0, 5, 0]}},
                "tail3": {"rotation": {"0.0": [0, 3, 0], "1.5": [0, -3, 0], "3.0": [0, 3, 0]}},
            },
        },
        "animation.poke_arceus.walk": {
            "loop": True, "animation_length": 0.9,
            "bones": {
                "leg0": {"rotation": {"0.0": [24, 0, 0], "0.45": [-24, 0, 0], "0.9": [24, 0, 0]}},
                "leg1": {"rotation": {"0.0": [-24, 0, 0], "0.45": [24, 0, 0], "0.9": [-24, 0, 0]}},
                "leg2": {"rotation": {"0.0": [-24, 0, 0], "0.45": [24, 0, 0], "0.9": [-24, 0, 0]}},
                "leg3": {"rotation": {"0.0": [24, 0, 0], "0.45": [-24, 0, 0], "0.9": [24, 0, 0]}},
                "body": {"position": {"0.0": [0, 0, 0], "0.225": [0, 0.7, 0], "0.45": [0, 0, 0], "0.675": [0, 0.7, 0], "0.9": [0, 0, 0]}},
                "head": {"rotation": {"0.0": [-2, 0, 0], "0.45": [3, 0, 0], "0.9": [-2, 0, 0]}},
                "ring": {"rotation": {"0.0": [0, 0, -3], "0.45": [0, 0, 3], "0.9": [0, 0, -3]}},
                "tail": {"rotation": {"0.0": [0, 12, 0], "0.45": [0, -12, 0], "0.9": [0, 12, 0]}},
                "tail2": {"rotation": {"0.0": [0, 8, 0], "0.45": [0, -8, 0], "0.9": [0, 8, 0]}},
            },
        },
        "animation.poke_arceus.fly": {
            "loop": True, "animation_length": 1.6,
            "bones": {
                "body": {"position": {"0.0": [0, 0, 0], "0.8": [0, 2.0, 0], "1.6": [0, 0, 0]},
                         "rotation": {"0.0": [-3, 0, 0], "0.8": [3, 0, 0], "1.6": [-3, 0, 0]}},
                "torso": {"rotation": {"0.0": [2, 0, 0], "0.8": [-2, 0, 0], "1.6": [2, 0, 0]}},
                "leg0": {"rotation": [ -28, 0, 0 ]}, "leg1": {"rotation": [ -28, 0, 0 ]},
                "leg2": {"rotation": [ -22, 0, 0 ]}, "leg3": {"rotation": [ -22, 0, 0 ]},
                "ring": {"rotation": {"0.0": [0, 0, -8], "0.8": [0, 0, 8], "1.6": [0, 0, -8]}},
                "tail": {"rotation": {"0.0": [0, 10, 0], "0.8": [0, -10, 0], "1.6": [0, 10, 0]}},
                "tail2": {"rotation": {"0.0": [0, 7, 0], "0.8": [0, -7, 0], "1.6": [0, 7, 0]}},
                "tail3": {"rotation": {"0.0": [0, 4, 0], "0.8": [0, -4, 0], "1.6": [0, 4, 0]}},
                "head": {"rotation": {"0.0": [1, 0, 0], "0.8": [-2, 0, 0], "1.6": [1, 0, 0]}},
            },
        },
        "animation.poke_arceus.attack": {
            "animation_length": 0.7,
            "bones": {
                "body": {"position": {"0.0": [0, 0, 0], "0.18": [0, 0, -1], "0.34": [0, 0, 1.5], "0.7": [0, 0, 0]},
                         "rotation": {"0.0": [0, 0, 0], "0.18": [-8, 0, 0], "0.34": [16, 0, 0], "0.7": [0, 0, 0]}},
                "head": {"rotation": {"0.0": [0, 0, 0], "0.18": [-5, 0, 0], "0.34": [20, 0, 0], "0.7": [0, 0, 0]}},
                "leg0": {"rotation": {"0.0": [0, 0, 0], "0.18": [-20, 0, 0], "0.34": [32, 0, 0], "0.7": [0, 0, 0]}},
                "leg1": {"rotation": {"0.0": [0, 0, 0], "0.18": [-20, 0, 0], "0.34": [32, 0, 0], "0.7": [0, 0, 0]}},
                "ring": {"rotation": {"0.0": [0, 0, 0], "0.18": [0, 0, -18], "0.34": [0, 0, 32], "0.7": [0, 0, 0]}},
                "tail": {"rotation": {"0.0": [0, 0, 0], "0.34": [0, -18, 0], "0.7": [0, 0, 0]}},
                "tail2": {"rotation": {"0.0": [0, 0, 0], "0.34": [0, -12, 0], "0.7": [0, 0, 0]}},
            },
        },
    }}
    anim_path = os.path.join(rp, "animations", "arceus.animations.json")
    os.makedirs(os.path.dirname(anim_path), exist_ok=True)
    with open(anim_path, "w", encoding="utf-8") as f:
        json.dump(animations, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "packs/pokemon", shiny="--shiny" in sys.argv)
