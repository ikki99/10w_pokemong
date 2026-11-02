#!/usr/bin/env python3
"""生成 Minecraft Bedrock 寶可夢怪物 add-on（BP + RP）

用法:  python3 gen_pokemon.py [-o packs/pokemon] [--only pikachu] [--check]
產出:
  <out>/bp/   行為包：entity 定義、lang
  <out>/rp/   資源包：client entity、geometry、texture、animation
"""
import argparse
import json
import os
import struct
import uuid
import zlib

from PIL import Image, ImageDraw

# ---------------------------------------------------------------- 色彩工具

def hx(s: str):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def shade(rgb, f):
    if f >= 0:
        return tuple(min(255, int(c + (255 - c) * f)) for c in rgb)
    return tuple(max(0, int(c * (1 + f))) for c in rgb)


# ---------------------------------------------------------------- 物種設定
# body/head/legs 尺寸以 Minecraft 像素（16 = 1 格）
SPECS = [
    # id, 中文, 英文, hp, speed, body(w,h,d), head(w,h,d), legs(w,h,d), ears, 尾巴型, 調色盤, 臉, 額外配件
    dict(id="pikachu", zh="皮卡丘", en="Pikachu", hp=32, speed=0.35,
         body=(7, 6, 9), head=(9, 8, 8), legs=(2, 3, 3), ears=((2, 5, 1), (2, 5, 1)),
         tail="zigzag", stance="quad", ear_tip="#3A2A18", cheeks=True,
         pal=dict(body="#F7D02C", accent="#E03C3C", belly="#FCEA8A", limb="#F7D02C",
                  ear="#F7D02C", tail="#F7D02C"),
         face=dict(eye="#1A1A1A", eye_hl="#FFFFFF", cheek="#E03C3C", mouth="#7A3B12"),
         hostile=False, family=["poke", "pikachu", "electric"], scale=1.0),

    dict(id="eevee", zh="伊布", en="Eevee", hp=34, speed=0.33,
         body=(7, 6, 9), head=(8, 8, 8), legs=(2, 3, 3), ears=((3, 6, 2), (3, 6, 2)),
         tail="bushy", stance="quad",
         pal=dict(body="#B98A4E", accent="#F1E3C3", belly="#F1E3C3", limb="#B98A4E",
                  ear="#8A6435", tail="#F1E3C3"),
         face=dict(eye="#3A2412", eye_hl="#FFFFFF", cheek=None, mouth="#5A3A1A"),
         hostile=False, family=["poke", "eevee", "normal"], scale=1.0),

    dict(id="bulbasaur", zh="妙蛙種子", en="Bulbasaur", hp=40, speed=0.27,
         body=(10, 7, 11), head=(8, 7, 8), legs=(3, 2, 4), ears=((1, 3, 1), (1, 3, 1)),
         tail="none", stance="quad", bulb=True,
         pal=dict(body="#79BF6A", accent="#3F7A34", belly="#A8D89A", limb="#79BF6A",
                  ear="#6AAE5C", tail="#79BF6A"),
         face=dict(eye="#B03030", eye_hl="#FFFFFF", cheek=None, mouth="#2F5A28"),
         hostile=False, family=["poke", "bulbasaur", "grass"], scale=1.05),

    dict(id="charmander", zh="小火龍", en="Charmander", hp=36, speed=0.31,
         body=(7, 6, 8), head=(8, 8, 7), legs=(2, 3, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="flame", stance="biped",
         pal=dict(body="#F08030", accent="#FFC98A", belly="#F8D8A8", limb="#F08030",
                  ear="#F08030", tail="#F08030"),
         face=dict(eye="#1E4E8C", eye_hl="#FFFFFF", cheek=None, mouth="#8A3E10"),
         hostile=False, family=["poke", "charmander", "fire"], scale=1.0),

    dict(id="squirtle", zh="傑尼龜", en="Squirtle", hp=38, speed=0.29,
         body=(8, 6, 9), head=(8, 8, 8), legs=(2, 3, 3), ears=((1, 2, 1), (1, 2, 1)),
         tail="thin", stance="biped", shell=True,
         pal=dict(body="#7EC0EA", accent="#A9713C", belly="#F3E3B8", limb="#7EC0EA",
                  ear="#7EC0EA", tail="#7EC0EA", wing="#A9713C"),
         face=dict(eye="#5A2A1A", eye_hl="#FFFFFF", cheek=None, mouth="#3A5A7A"),
         hostile=False, family=["poke", "squirtle", "water"], scale=1.0),

    dict(id="jigglypuff", zh="胖丁", en="Jigglypuff", hp=44, speed=0.26,
         body=(11, 10, 10), head=(11, 9, 10), legs=(2, 2, 3), ears=((3, 5, 2), (3, 5, 2)),
         tail="none", stance="biped", cheeks=True,
         pal=dict(body="#F6C6D8", accent="#E9A8BF", belly="#FBE4EC", limb="#F6C6D8",
                  ear="#F6C6D8", tail="#F6C6D8"),
         face=dict(eye="#2A5FA8", eye_hl="#FFFFFF", cheek="#E9A8BF", mouth="#8A4A5A"),
         hostile=False, family=["poke", "jigglypuff", "fairy"], scale=1.05),

    dict(id="meowth", zh="喵喵", en="Meowth", hp=34, speed=0.34,
         body=(7, 6, 8), head=(8, 7, 8), legs=(2, 3, 3), ears=((2, 4, 1), (2, 4, 1)),
         tail="thin", stance="biped", ear_tip="#3A2A18", coin=True,
         pal=dict(body="#F2E4B0", accent="#F5C518", belly="#FBF3D8", limb="#F2E4B0",
                  ear="#F2E4B0", tail="#F2E4B0"),
         face=dict(eye="#2A2A2A", eye_hl="#FFFFFF", cheek=None, mouth="#8A6A2A"),
         hostile=False, family=["poke", "meowth", "normal"], scale=1.0),

    dict(id="gengar", zh="耿鬼", en="Gengar", hp=52, speed=0.36,
         body=(9, 9, 9), head=(10, 9, 9), legs=(2, 3, 3), ears=((2, 4, 1), (2, 4, 1)),
         tail="zigzag", stance="biped",
         pal=dict(body="#7B62A3", accent="#5B4780", belly="#9A85BE", limb="#7B62A3",
                  ear="#7B62A3", tail="#7B62A3"),
         face=dict(eye="#D93A3A", eye_hl="#FFD9D9", cheek=None, mouth="#F5F5F5"),
         hostile=True, family=["poke", "gengar", "ghost"], scale=1.05,

         damage=6),

    dict(id="snorlax", zh="卡比獸", en="Snorlax", hp=140, speed=0.18,
         body=(14, 13, 12), head=(12, 10, 11), legs=(4, 4, 5), ears=((2, 3, 1), (2, 3, 1)),
         tail="none", stance="biped",
         pal=dict(body="#3E6E8E", accent="#2C526B", belly="#EDE4CE", limb="#3E6E8E",
                  ear="#3E6E8E", tail="#3E6E8E"),
         face=dict(eye="#1A1A1A", eye_hl="#FFFFFF", cheek=None, mouth="#2C526B"),
         hostile=False, family=["poke", "snorlax", "normal"], scale=1.6),

    dict(id="dragonite", zh="快龍", en="Dragonite", hp=100, speed=0.32,
         body=(9, 8, 11), head=(9, 8, 8), legs=(3, 3, 4), ears=((1, 3, 1), (1, 3, 1)),
         tail="thin", stance="quad", wings=True,
         pal=dict(body="#E8B44A", accent="#C89030", belly="#F7E9C0", limb="#E8B44A",
                  ear="#E8B44A", tail="#E8B44A", wing="#7FC4E8"),
         face=dict(eye="#3A5A8A", eye_hl="#FFFFFF", cheek=None, mouth="#8A6A2A"),
         hostile=False, family=["poke", "dragonite", "dragon"], scale=1.5, damage=7),

    dict(id="charizard", zh="噴火龍", en="Charizard", hp=110, speed=0.34,
         body=(10, 9, 12), head=(9, 9, 9), legs=(3, 4, 4), ears=((2, 4, 1), (2, 4, 1)),
         tail="flame", stance="biped", wings=True, horn=True,
         pal=dict(body="#F08030", accent="#FFC98A", belly="#F8D8A8", limb="#F08030",
                  ear="#F08030", tail="#F08030", wing="#2F6E8F"),
         face=dict(eye="#2A6AA8", eye_hl="#FFFFFF", cheek=None, mouth="#8A3E10"),
         hostile=False, family=["poke", "charizard", "fire"], scale=1.7, damage=9),

    dict(id="mewtwo", zh="超夢", en="Mewtwo", hp=160, speed=0.38,
         body=(9, 10, 9), head=(9, 9, 8), legs=(3, 5, 4), ears=((2, 5, 1), (2, 5, 1)),
         tail="thin", stance="biped",
         pal=dict(body="#D9CCE8", accent="#9A7FC4", belly="#E9E0F2", limb="#D9C0E0",
                  ear="#9A7FC4", tail="#9A7FC4"),
         face=dict(eye="#7A4AC0", eye_hl="#FFFFFF", cheek=None, mouth="#6A5A7A"),
         hostile=True, family=["poke", "mewtwo", "psychic"], scale=1.55, damage=12),
]

SOUNDS = {
    "pikachu": "mob.cat.meow",
    "eevee": "mob.fox.ambient",
    "bulbasaur": "mob.slime.small",
    "charmander": "mob.blaze.breathe",
    "squirtle": "mob.turtle.ambient_land",
    "jigglypuff": "mob.ghast.moan",
    "meowth": "mob.cat.meow",
    "gengar": "mob.endermen.stare",
    "snorlax": "mob.polar_bear.ambient",
    "dragonite": "mob.enderdragon.growl",
    "charizard": "mob.enderdragon.flap",
    "mewtwo": "mob.wither.ambient",
}

FACES = [  # 立方體 UV 展開（Bedrock/Boxbench 規則）
    ("top",    lambda w, h, d: (d, 0, w, d)),
    ("bottom", lambda w, h, d: (d + w, 0, w, d)),
    ("right",  lambda w, h, d: (0, d, d, h)),
    ("front",  lambda w, h, d: (d, d, w, h)),
    ("left",   lambda w, h, d: (d + w, d, d, h)),
    ("back",   lambda w, h, d: (2 * d + w, d, w, h)),
]


def net_dims(w, h, d):
    return (2 * (d + w), d + h)


# ---------------------------------------------------------------- 貼圖繪製

class Atlas:
    """把每個立方體的 UV 展開區塊排進一張貼圖（貨架式打包）"""

    def __init__(self, size=128, pad=2):
        self.size = size
        self.pad = pad
        self.img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)
        self.cursor_x = 0
        self.cursor_y = 0
        self.row_h = 0


    def alloc_net(self, nw, nh):
        if self.cursor_x + nw + self.pad > self.size:
            self.cursor_x = 0
            self.cursor_y += self.row_h + self.pad
            self.row_h = 0
        if self.cursor_y + nh + self.pad > self.size:
            raise RuntimeError(f"貼圖空間不足（需要 {self.size}x{self.size} 以上）")
        pos = (self.cursor_x, self.cursor_y)
        self.cursor_x += nw + self.pad
        self.row_h = max(self.row_h, nh)
        return pos


def paint_cube(atlas, uvx, uvy, w, h, d, base, accents=None, face=None, face_style=None):
    """把一個立方體的 UV 展開區塊著色；face 存在時在 front 面畫眼睛嘴巴"""
    accents = accents or {}
    for name, fn in FACES:
        ox, oy, fw, fh = fn(w, h, d)
        col = base
        if name == "top":
            col = accents.get("top", shade(base, 0.18))
        elif name == "bottom":
            col = accents.get("bottom", shade(base, -0.22))
        elif name in ("right", "left"):
            col = accents.get("side", shade(base, -0.08))
        elif name == "front":
            col = accents.get("front", base)
        elif name == "back":
            col = accents.get("back", shade(base, -0.12))
        atlas.draw.rectangle([uvx + ox, uvy + oy, uvx + ox + fw - 1, uvy + oy + fh - 1], fill=col)

    if face and face_style:
        ox, oy, fw, fh = dict(FACES)["front"](w, h, d)
        fx, fy = uvx + ox, uvy + oy
        paint_face(atlas.draw, fx, fy, fw, fh, face, face_style)


def paint_face(dr, fx, fy, fw, fh, face, style):
    """在 8~10 px 的臉上畫眼睛/腮紅/嘴"""
    eye = face["eye"]
    hl = face["eye_hl"]
    mouth = face["mouth"]
    ex = max(1, fw // 4)
    ey = max(1, fh // 3)
    ew = max(1, fw // 6)
    eh = max(1, fh // 5)
    lx, rx = fx + ex - ew // 2, fx + fw - ex - ew // 2
    # 眼白底 + 瞳孔
    for x in (lx, rx):
        dr.rectangle([x, fy + ey, x + ew, fy + ey + eh], fill=hl)
        dr.rectangle([x + (1 if ew > 2 else 0), fy + ey, x + ew - (1 if ew > 2 else 0), fy + ey + eh - 1], fill=eye)
    if face.get("cheek") and style.get("cheek"):
        cr = max(1, fw // 7)
        for cx in (fx + ex - cr, fx + fw - ex - cr + 1):
            dr.ellipse([cx, fy + ey + eh + 1, cx + cr, fy + ey + eh + 1 + cr], fill=face["cheek"])
    # 嘴
    my = fy + ey + eh + max(1, fh // 4)
    mw = max(2, fw // 4)
    dr.line([fx + (fw - mw) // 2, my, fx + (fw + mw) // 2, my], fill=mouth, width=1)
    if style.get("smile"):
        dr.point([fx + (fw - mw) // 2, my + 1], fill=mouth)
        dr.point([fx + (fw + mw) // 2, my + 1], fill=mouth)


# ---------------------------------------------------------------- 幾何生成

def build_geometry(spec, atlas):
    bw, bh, bd = spec["body"]
    hw, hh, hd = spec["head"]
    lw, lh, ld = spec["legs"]
    pal = {k: hx(v) for k, v in spec["pal"].items()}
    DEFAULT_FACE = dict(eye="#1A1A1A", eye_hl="#FFFFFF", cheek=None, mouth="#5A3A2A")
    face = {k: (hx(v) if v else None) for k, v in (spec.get("face") or DEFAULT_FACE).items()}
    cubes = {b: [] for b in ["body", "head", "ear_l", "ear_r", "tail", "leg0", "leg1", "leg2", "leg3", "wing_l", "wing_r", "extra"]}

    base_y = lh
    body_y0 = base_y
    head_y0 = body_y0 + bh

    # --- 身體
    nw, nh = net_dims(bw, bh, bd)
    ux, uy = atlas.alloc_net(nw, nh)
    paint_cube(atlas, ux, uy, bw, bh, bd, pal["body"],
               accents={"front": pal["belly"], "top": shade(pal["body"], 0.12)}, face=None)
    cubes["body"].append(dict(origin=[-bw / 2, body_y0, -bd / 2], size=[bw, bh, bd], uv=[ux, uy]))

    # --- 頭（front 面畫臉）
    nw, nh = net_dims(hw, hh, hd)
    ux, uy = atlas.alloc_net(nw, nh)
    paint_cube(atlas, ux, uy, hw, hh, hd, pal["body"],
               accents={"front": shade(pal["body"], 0.06)}, face=face,
               face_style=dict(cheek=spec["id"] in ("pikachu",), smile=spec["id"] in ("pikachu", "jigglypuff", "eevee")))
    head_z = -hd / 2 - 1
    cubes["head"].append(dict(origin=[-hw / 2, head_y0, head_z], size=[hw, hh, hd], uv=[ux, uy]))

    # --- 耳朵
    for i, e in enumerate(spec["ears"][:2]):
        ew, eh2, ed = e
        bone = "ear_l" if i == 0 else "ear_r"
        nw, nh = net_dims(ew, eh2, ed)
        ux2, uy2 = atlas.alloc_net(nw, nh)
        paint_cube(atlas, ux2, uy2, ew, eh2, ed, pal["accent"],
                   accents={"top": shade(pal["accent"], -0.15)})
        x = (-hw / 2 + 1) if i == 0 else (hw / 2 - 1 - ew)
        cubes[bone].append(dict(origin=[x, head_y0 + hh - 1, head_z + 1], size=[ew, eh2, ed], uv=[ux2, uy2]))

    # --- 尾巴
    t = spec["tail"]
    if t != "none":
        tw, th, td = (3, 3, 4) if t == "bushy" else (2, 2, 5)
        nw, nh = net_dims(tw, th, td)
        ux3, uy3 = atlas.alloc_net(nw, nh)
        paint_cube(atlas, ux3, uy3, tw, th, td, pal["accent"])
        cubes["tail"].append(dict(origin=[-tw / 2, body_y0 + bh - th - 1, bd / 2 - 1], size=[tw, th, td], uv=[ux3, uy3]))
        if t == "zigzag":  # 皮卡丘的閃電尾：再接兩段往上翹
            for k in range(2):
                sw, sh2, sd = (2, 2, 3)
                nw, nh = net_dims(sw, sh2, sd)
                ux4, uy4 = atlas.alloc_net(nw, nh)
                paint_cube(atlas, ux4, uy4, sw, sh2, sd, pal["accent"])
                cubes["tail"].append(dict(origin=[-sw / 2 + (-1) ** k, body_y0 + bh - th - 1 + (k + 1) * 3,
                                                 bd / 2 + 1 + k], size=[sw, sh2, sd], uv=[ux4, uy4]))
        if t == "flame":  # 尾巴火焰
            fw2, fh2, fd2 = 3, 4, 3
            nw, nh = net_dims(fw2, fh2, fd2)
            ux5, uy5 = atlas.alloc_net(nw, nh)
            paint_cube(atlas, ux5, uy5, fw2, fh2, fd2, hx("#FFB000"),
                       accents={"top": hx("#FFE066"), "bottom": hx("#E03C1C")})
            cubes["tail"].append(dict(origin=[-fw2 / 2, body_y0 + bh - 1, bd / 2 + 2], size=[fw2, fh2, fd2], uv=[ux5, uy5]))

    # --- 四條腿
    for i, (x, z) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        nw, nh = net_dims(lw, lh, ld)
        ux6, uy6 = atlas.alloc_net(nw, nh)
        paint_cube(atlas, ux6, uy6, lw, lh, ld, pal["limb"], accents={"bottom": shade(pal["limb"], -0.3)})
        px = (x * (bw / 2 - lw / 2 + 0.5)) - lw if x < 0 else (x * (bw / 2 - lw / 2) - lw / 2)
        px = -bw / 2 + 0.5 if x < 0 else bw / 2 - lw - 0.5
        pz = -bd / 2 + 1 if z < 0 else bd / 2 - ld - 1
        cubes[f"leg{i}"].append(dict(origin=[px, 0, pz], size=[lw, lh, ld], uv=[ux6, uy6]))

    # --- 翅膀
    if spec.get("wings"):
        for i in range(2):
            ww, wh2, wd = 1, 6, 5
            nw, nh = net_dims(ww, wh2, wd)
            ux7, uy7 = atlas.alloc_net(nw, nh)
            paint_cube(atlas, ux7, uy7, ww, wh2, wd, pal["accent"])
            bone = "wing_l" if i == 0 else "wing_r"
            x = -bw / 2 - 1 if i == 0 else bw / 2
            cubes[bone].append(dict(origin=[x, body_y0 + bh - wh2 + 1, -wd / 2], size=[ww, wh2, wd], uv=[ux7, uy7]))

    # --- 龜殼
    if spec.get("shell"):
        sw, sh2, sd = bw + 1, bh + 1, bd + 1
        nw, nh = net_dims(sw, sh2, sd)
        ux8, uy8 = atlas.alloc_net(nw, nh)
        paint_cube(atlas, ux8, uy8, sw, sh2, sd, pal["accent"], accents={"top": shade(pal["accent"], 0.15)})
        cubes["extra"].append(dict(origin=[-sw / 2, body_y0 - 0.5, -sd / 2 + 0.5], size=[sw, sh2, sd], uv=[ux8, uy8]))

    # --- 妙蛙種子的種子
    if spec.get("bulb"):
        bw2, bh2, bd2 = 7, 6, 7
        nw, nh = net_dims(bw2, bh2, bd2)
        ux9, uy9 = atlas.alloc_net(nw, nh)
        paint_cube(atlas, ux9, uy9, bw2, bh2, bd2, hx("#5B9E4A"), accents={"top": hx("#7CC46A")})
        cubes["extra"].append(dict(origin=[-bw2 / 2, body_y0 + bh - 1, -bd2 / 2 + 1], size=[bw2, bh2, bd2], uv=[ux9, uy9]))

    # --- 喵喵的金幣
    if spec.get("coin"):
        cw, ch, cd = 3, 2, 1
        nw, nh = net_dims(cw, ch, cd)
        ux10, uy10 = atlas.alloc_net(nw, nh)
        paint_cube(atlas, ux10, uy10, cw, ch, cd, hx("#F5C518"))
        cubes["extra"].append(dict(origin=[-cw / 2, head_y0 + hh - 1, head_z + 1], size=[cw, ch, cd], uv=[ux10, uy10]))

    # --- 組 bones
    bones = []
    bones.append(dict(name="body", pivot=[0, body_y0, 0], cubes=cubes["body"]))
    bones.append(dict(name="head", parent="body", pivot=[0, head_y0, head_z], cubes=cubes["head"]))
    if cubes["ear_l"]:
        bones.append(dict(name="ear_l", parent="head", pivot=[-hw / 4, head_y0 + hh - 1, head_z + 1], cubes=cubes["ear_l"]))
        bones.append(dict(name="ear_r", parent="head", pivot=[hw / 4, head_y0 + hh - 1, head_z + 1], cubes=cubes["ear_r"]))
    if cubes["tail"]:
        bones.append(dict(name="tail", parent="body", pivot=[0, body_y0 + bh - 2, bd / 2], cubes=cubes["tail"]))
    if cubes["wing_l"]:
        bones.append(dict(name="wing_l", parent="body", pivot=[-bw / 2, body_y0 + bh - 2, 0], cubes=cubes["wing_l"]))
        bones.append(dict(name="wing_r", parent="body", pivot=[bw / 2, body_y0 + bh - 2, 0], cubes=cubes["wing_r"]))
    if cubes["extra"]:
        bones.append(dict(name="extra", parent="body", pivot=[0, body_y0 + bh, 0], cubes=cubes["extra"]))
    for i in range(4):
        if cubes[f"leg{i}"]:
            bones.append(dict(name=f"leg{i}", parent="body", pivot=[0, lh, 0], cubes=cubes[f"leg{i}"]))

    geo = {
        "format_version": "1.21.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": f"geometry.poke_{spec['id']}",
                "texture_width": atlas.size,
                "texture_height": atlas.size,
                "visible_bounds_width": max(4, bw / 8 + 1),
                "visible_bounds_height": max(2, (body_y0 + bh + hh) / 16 + 0.5),
                "visible_bounds_offset": [0, (body_y0 + bh + hh) / 32, 0],
            },
            "bones": bones,
        }],
    }
    return geo


# ---------------------------------------------------------------- 行為檔

def build_entity(spec):
    hostile = spec.get("hostile", False)
    dmg = spec.get("damage", 4)
    w = max(0.6, spec["body"][0] / 16 * 0.9)
    h = (spec["legs"][1] + spec["body"][1] + spec["head"][1]) / 16

    comps = {
        "minecraft:type_family": {"family": list(spec["family"]) + ["monster" if hostile else "passive"]},
        "minecraft:health": {"value": spec["hp"], "max": spec["hp"]},
        "minecraft:collision_box": {"width": round(w, 2), "height": round(h, 2)},
        "minecraft:movement": {"value": spec["speed"]},
        "minecraft:movement.basic": {},
        "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_water": True, "can_pass_doors": True},
        "minecraft:jump.static": {},
        "minecraft:can_climb": {},
        "minecraft:physics": {},
        "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
        "minecraft:knockback_resistance": {"value": 0.1},
        "minecraft:nameable": {},
        "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
        "minecraft:despawn": {"despawn_from_distance": {}},
        "minecraft:ambient_sound_interval": {
            "event_name": SOUNDS.get(spec["id"], "mob.cat.meow"),
            "range": 16,
            "value": 8.0,
        },
        "minecraft:behavior.float": {"priority": 0},
        "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.85},
        "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 8, "probability": 0.02},
        "minecraft:behavior.random_look_around": {"priority": 8},
        # ---- 馴服 / 跟隨主人（讓 AI 自己走路，不用腳本硬拉）----
        "minecraft:is_tamed": {},
        "minecraft:tameable": {
            "probability": 1.0,
            "tame_items": ["poke:pokeball"],
            "tame_event": {"event": "poke:on_tame", "target": "self"},
        },
        "minecraft:behavior.follow_owner": {
            "priority": 0,
            "speed_multiplier": 1.4,
            "start_distance": 6,
            "stop_distance": 2.5,
        },
        "minecraft:behavior.hurt_by_target": {"priority": 1},
        "minecraft:behavior.panic": {"priority": 3, "speed_multiplier": 1.4},
    }
    # ---- 會飛的物種：改用飛行導航 + 空中漫遊，不再用走路 ----
    if spec.get("flyer"):
        comps["minecraft:movement"] = {"value": round(spec["speed"] * 1.5, 3)}
        comps.pop("minecraft:movement.basic", None)
        comps.pop("minecraft:navigation.walk", None)
        comps.pop("minecraft:behavior.random_stroll", None)
        comps.pop("minecraft:jump.static", None)
        comps["minecraft:movement.fly"] = {}
        comps["minecraft:navigation.fly"] = {
            "can_path_over_water": True,
            "avoid_water": False,
            "can_pass_doors": False,
            "can_open_doors": False,
            "avoid_sun": False,
            "can_walk": False,
            "can_breach": True,
            "can_sink": False,
        }
        comps["minecraft:can_fly"] = {}
        comps["minecraft:behavior.float_wander"] = {
            "priority": 2,
            "xz_dist": 14,
            "y_dist": 8,
            "y_offset": 4.0,
            "random_reselect": True,
            "float_duration": [1.0, 3.0],
        }

    if hostile:
        comps["minecraft:behavior.nearest_attackable_target"] = {
            "priority": 2,
            "must_see": True,
            "within_radius": 20,
            "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"},
                              "max_dist": 20}],
        }
        comps["minecraft:behavior.melee_attack"] = {
            "priority": 3, "speed_multiplier": 1.2, "track_target": True, "reach_multiplier": 1.6,
        }
        comps["minecraft:attack"] = {"damage": dmg}
        comps.pop("minecraft:behavior.panic", None)
    else:
        # 非敵對物種也給基本攻擊力與「打怪」行為：被收服的夥伴才會幫忙
        comps["minecraft:attack"] = {"damage": dmg if spec.get("damage") else 3}
        comps["minecraft:behavior.melee_attack"] = {
            "priority": 4, "speed_multiplier": 1.2, "track_target": True, "reach_multiplier": 1.8,
        }
        comps["minecraft:behavior.nearest_attackable_target"] = {
            "priority": 5, "must_see": True, "within_radius": 10,
            "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "monster"},
                              "max_dist": 10}],
        }

    return {
        "format_version": "1.21.0",
        "minecraft:entity": {
            "description": {
                "identifier": f"poke:{spec['id']}",
                "is_spawnable": True,
                "is_summonable": True,
                "is_experimental": False,
                "spawn_category": "monster" if hostile else "creature",
            },
            "components": comps,
            "events": {"poke:on_tame": {}},
        },
    }


def build_client_entity(spec):
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": f"poke:{spec['id']}",
                "min_engine_version": "1.21.0",
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": f"textures/entity/pokemon/{spec['id']}"},
                "geometry": {"default": f"geometry.poke_{spec['id']}"},
                "animations": {
                    "walk": "animation.poke.walk",
                    "idle": "animation.poke.idle",
                    "look": "animation.common.look_at_target",
                },
                "scripts": {
                    "animate": [{"walk": "query.modified_move_speed"}, "idle", "look"],
                    "scale": str(spec.get("scale", 1.0)),
                },
                "render_controllers": ["controller.render.default"],
            }
        },
    }


ANIMATIONS = {
    "format_version": "1.8.0",
    "animations": {
        "animation.poke.walk": {
            "loop": True,
            "animation_length": 1.0,
            "bones": {
                "leg0": {"rotation": {"0.0": [35, 0, 0], "0.5": [-35, 0, 0], "1.0": [35, 0, 0]}},
                "leg1": {"rotation": {"0.0": [-35, 0, 0], "0.5": [35, 0, 0], "1.0": [-35, 0, 0]}},
                "leg2": {"rotation": {"0.0": [-35, 0, 0], "0.5": [35, 0, 0], "1.0": [-35, 0, 0]}},
                "leg3": {"rotation": {"0.0": [35, 0, 0], "0.5": [-35, 0, 0], "1.0": [35, 0, 0]}},
                "body": {"position": {"0.0": [0, 0, 0], "0.25": [0, 0.4, 0], "0.5": [0, 0, 0],
                                      "0.75": [0, 0.4, 0], "1.0": [0, 0, 0]}},
                "tail": {"rotation": {"0.0": [0, -12, 0], "0.5": [0, 12, 0], "1.0": [0, -12, 0]}},
            },
        },
        "animation.poke.idle": {
            "loop": True,
            "animation_length": 2.0,
            "bones": {
                "body": {"position": {"0.0": [0, 0, 0], "1.0": [0, 0.3, 0], "2.0": [0, 0, 0]}},
                "head": {"rotation": {"0.0": [0, 0, 0], "0.7": [0, 8, 0], "1.4": [0, -8, 0], "2.0": [0, 0, 0]}},
                "ear_l": {"rotation": {"0.0": [0, 0, 0], "1.0": [-8, 0, 0], "2.0": [0, 0, 0]}},
                "ear_r": {"rotation": {"0.0": [0, 0, 0], "1.0": [-8, 0, 0], "2.0": [0, 0, 0]}},
            },
        },
    },
}


# ---------------------------------------------------------------- 腳本技能

ABILITY_JS = r"""
import { world, system } from "@minecraft/server";

const TAG = "[Poke]";
console.log(TAG + " abilities module loaded");

const COOLDOWN_TICKS = 80;               // 4 秒
const last = new Map();                  // entityId -> tick

function offCooldown(entity) {
  const now = system.currentTick;
  const t = last.get(entity.id) ?? -9999;
  if (now - t < COOLDOWN_TICKS) return false;
  last.set(entity.id, now);
  return true;
}

function fx(dim, loc, particle, sound, pitch = 1) {
  try { dim.spawnParticle(particle, loc); } catch (e) {}
  if (sound) {
    try { dim.playSound(sound, loc, { volume: 1, pitch }); } catch (e) {}
  }
}

function vecAdd(a, b) { return { x: a.x + b.x, y: a.y + b.y, z: a.z + b.z }; }

// ---- 個別招式 -------------------------------------------------------------

const MOVES = {
  thunder(defender, attacker) {
    const d = defender.dimension, loc = attacker.location;
    fx(d, loc, "minecraft:basic_flame_particle", "random.explode", 1.6);
    fx(d, vecAdd(loc, { x: 0, y: 1, z: 0 }), "minecraft:critical_hit_emitter", "ambient.weather.thunder", 1.2);
    attacker.applyDamage(4, { cause: "lightning", damagingEntity: defender });
    try { attacker.addEffect("slowness", 60, { amplifier: 1 }); } catch (e) {}
    return "皮卡丘：十萬伏特！";
  },

  ember(defender, attacker) {
    fx(attacker.dimension, attacker.location, "minecraft:basic_flame_particle", "mob.blaze.breathe", 1.4);
    attacker.setOnFire(5, true);
    attacker.applyDamage(3, { cause: "fire", damagingEntity: defender });
    return "小火龍：火花！";
  },

  flamethrower(defender, attacker) {
    fx(attacker.dimension, attacker.location, "minecraft:basic_flame_particle", "mob.enderdragon.flap", 1.1);
    attacker.setOnFire(8, true);
    attacker.applyDamage(6, { cause: "fire", damagingEntity: defender });
    return "噴火龍：噴射火焰！";
  },

  watergun(defender, attacker) {
    fx(attacker.dimension, attacker.location, "minecraft:basic_smoke_particle", "random.splash", 1.3);
    attacker.applyDamage(3, { cause: "entityAttack", damagingEntity: defender });
    try {
      const dx = attacker.location.x - defender.location.x;
      const dz = attacker.location.z - defender.location.z;
      const len = Math.max(0.1, Math.hypot(dx, dz));
      attacker.applyKnockback((dx / len) * 1.6, (dz / len) * 1.6, 1.6, 0.4);
    } catch (e) {}
    return "傑尼龜：水槍！";
  },

  vinesnare(defender, attacker) {
    fx(attacker.dimension, attacker.location, "minecraft:villager_happy", "mob.shulker.shoot", 0.7);
    try { attacker.addEffect("slowness", 100, { amplifier: 3 }); } catch (e) {}
    try { attacker.addEffect("poison", 80, { amplifier: 0 }); } catch (e) {}
    return "妙蛙種子：藤鞭纏繞！";
  },

  swift(defender, attacker) {
    fx(defender.dimension, defender.location, "minecraft:critical_hit_emitter", "mob.arrow.hit_player", 1.5);
    attacker.applyDamage(2, { cause: "entityAttack", damagingEntity: defender });
    try { defender.addEffect("speed", 200, { amplifier: 1 }); } catch (e) {}
    return "伊布：電光一閃！";
  },

  payday(defender, attacker) {
    fx(attacker.dimension, attacker.location, "minecraft:critical_hit_emitter", "random.orb", 1.2);
    attacker.applyDamage(3, { cause: "entityAttack", damagingEntity: defender });
    return "喵喵：聚寶功！";
  },

  sing(defender, attacker) {
    const dim = defender.dimension;
    fx(dim, defender.location, "minecraft:heart_particle", "mob.ghast.moan", 1.8);
    let n = 0;
    for (const p of dim.getPlayers({ location: defender.location, maxDistance: 10 })) {
      try {
        p.addEffect("blindness", 120, { amplifier: 0 });
        p.addEffect("slowness", 120, { amplifier: 2 });
        try { p.sendMessage("§d胖丁：搖籃曲…你開始想睡了"); } catch (e) {}
        n++;
      } catch (e) {}
    }
    return n ? `胖丁：搖籃曲！${n} 人陷入睡意` : "胖丁：搖籃曲！";
  },

  shadow(defender, attacker) {
    const dim = defender.dimension;
    const loc = attacker.location;
    fx(dim, loc, "minecraft:basic_smoke_particle", "mob.endermen.portal", 0.9);
    try {
      // 傳送到攻擊者背後
      const behind = { x: loc.x + 1.2, y: loc.y, z: loc.z + 1.2 };
      defender.teleport(behind, { dimension: dim });
    } catch (e) {}
    try { attacker.addEffect("darkness", 100, { amplifier: 0 }); } catch (e) {}
    attacker.applyDamage(4, { cause: "magic", damagingEntity: defender });
    return "耿鬼：暗影潛襲！";
  },

  bodyslam(defender, attacker) {
    fx(attacker.dimension, attacker.location, "minecraft:basic_smoke_particle", "mob.iron_golem.step", 0.6);
    attacker.applyDamage(5, { cause: "entityAttack", damagingEntity: defender });
    try {
      const dx = attacker.location.x - defender.location.x;
      const dz = attacker.location.z - defender.location.z;
      const len = Math.max(0.1, Math.hypot(dx, dz));
      attacker.applyKnockback((dx / len) * 3, (dz / len) * 3, 2.4, 0.8);
    } catch (e) {}
    return "卡比獸：重磅衝撞！";
  },

  dragontail(defender, attacker) {
    fx(attacker.dimension, attacker.location, "minecraft:critical_hit_emitter", "mob.enderdragon.growl", 1.3);
    attacker.applyDamage(6, { cause: "entityAttack", damagingEntity: defender });
    try {
      const dx = attacker.location.x - defender.location.x;
      const dz = attacker.location.z - defender.location.z;
      const len = Math.max(0.1, Math.hypot(dx, dz));
      attacker.applyKnockback((dx / len) * 2.5, (dz / len) * 2.5, 2.0, 0.9);
    } catch (e) {}
    return "快龍：龍尾！";
  },

  psychic(defender, attacker) {
    fx(attacker.dimension, attacker.location, "minecraft:villager_happy", "mob.shulker.teleport", 0.6);
    attacker.applyDamage(7, { cause: "magic", damagingEntity: defender });
    try { attacker.addEffect("levitation", 40, { amplifier: 3 }); } catch (e) {}
    try { attacker.addEffect("weakness", 120, { amplifier: 2 }); } catch (e) {}
    return "超夢：幻象光線！";
  },
};

// 每隻寶可夢對應的招式
const ABILITY = {
  "poke:pikachu": "thunder",
  "poke:eevee": "swift",
  "poke:bulbasaur": "vinesnare",
  "poke:charmander": "ember",
  "poke:squirtle": "watergun",
  "poke:jigglypuff": "sing",
  "poke:meowth": "payday",
  "poke:gengar": "shadow",
  "poke:snorlax": "bodyslam",
  "poke:dragonite": "dragontail",
  "poke:charizard": "flamethrower",
  "poke:mewtwo": "psychic",
};

function runMove(defender, attacker) {
  const moveId = ABILITY[defender.typeId];
  if (!moveId) return;
  if (!offCooldown(defender)) return;
  const fn = MOVES[moveId];
  if (!fn) return;
  try {
    const msg = fn(defender, attacker);
    if (msg) console.log(`${TAG} ${msg}`);
  } catch (e) {
    console.log(`${TAG} move error ${moveId}: ${e}`);
  }
}

// 玩家打寶可夢 → 寶可夢反擊
world.afterEvents.entityHitEntity.subscribe((ev) => {
  const attacker = ev.damagingEntity;
  const defender = ev.hitEntity;
  try {
    if (!defender || !ABILITY[defender.typeId]) return;
    if (!attacker || attacker.typeId !== "minecraft:player") return;
    runMove(defender, attacker);
  } catch (e) {}
});

// 測試/手動觸發： /scriptevent poke:demo <寶可夢 id>  → 在附近生一隻雞當靶
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (!ev.id.startsWith("poke:")) return;
  const sub = ev.id.slice(5);
  const src = ev.sourceEntity;

  if (sub === "help") {
    const lines = [
      `${TAG} 指令：`,
      "  /scriptevent poke:list    列出所有寶可夢與招式",
      "  /scriptevent poke:demo    用雞當靶，隨機測一隻的招式",
      "  /scriptevent poke:demo_all 全部招式各測一次",
    ];
    if (src && src.typeId === "minecraft:player") lines.forEach((l) => src.sendMessage(l));
    else lines.forEach((l) => console.log(l));
    return;
  }

  if (sub === "list") {
    for (const [id, move] of Object.entries(ABILITY)) {
      const line = `${TAG} ${id} -> ${move}`;
      if (src && src.typeId === "minecraft:player") src.sendMessage(line);
      else console.log(line);
    }
    return;
  }

  const dim = world.getDimension("overworld");
  const base = src && src.location ? src.location : { x: 0, y: 100, z: 0 };

  const demoOne = (pokeId) => {
    const move = ABILITY[pokeId];
    if (!move) { console.log(`${TAG} 沒有這隻：${pokeId}`); return; }
    let defender, target;
    try {
      defender = dim.spawnEntity(pokeId, { x: base.x + 2, y: base.y, z: base.z });
      target = dim.spawnEntity("minecraft:chicken", { x: base.x + 4, y: base.y, z: base.z });
    } catch (e) {
      console.log(`${TAG} 生成失敗（需要附近有已載入區塊 / tickingarea）：${e}`);
      return;
    }
    const hp0 = target.getComponent("minecraft:health")?.currentValue;
    console.log(`${TAG} 測試 ${pokeId} -> ${move}（雞 HP ${hp0}）`);
    runMove(defender, target);
    const hp1 = target.getComponent("minecraft:health")?.currentValue;
    console.log(`${TAG} 結果：雞 HP ${hp0} -> ${hp1}`);
    try { defender.remove(); } catch (e) {}
  };

  if (sub === "demo") {
    const keys = Object.keys(ABILITY);
    demoOne(keys[Math.floor(Math.random() * keys.length)]);
  } else if (sub === "demo_all") {
    Object.keys(ABILITY).forEach(demoOne);
  }
}, { namespaces: ["poke"] });
"""


# ---------------------------------------------------------------- 生成規則

SPAWN_PROFILES = {
    # id: (population_control, brightness, biomes, weight, herd)
    "pikachu":    ("animal",  (7, 15), ["plains", "forest", "sunflower_plains"], 12, (1, 3)),
    "eevee":      ("animal",  (7, 15), ["forest", "taiga", "birch_forest"], 10, (1, 2)),
    "bulbasaur":  ("animal",  (5, 15), ["swamp", "jungle", "forest"], 10, (1, 3)),
    "charmander": ("animal",  (5, 15), ["desert", "savanna", "mesa"], 9, (1, 2)),
    "squirtle":   ("animal",  (5, 15), ["beach", "river", "swamp"], 9, (1, 3)),
    "jigglypuff": ("animal",  (5, 15), ["meadow", "flower_forest", "plains"], 8, (1, 2)),
    "meowth":     ("animal",  (5, 15), ["village", "plains", "savanna"], 8, (1, 2)),
    "gengar":     ("monster", (0, 7),  ["roofed", "swamp", "forest"], 12, (1, 2)),
    "snorlax":    ("animal",  (7, 15), ["plains", "forest", "meadow"], 4, (1, 1)),
    "dragonite":  ("animal",  (7, 15), ["mountains", "frozen_peaks", "stony_peaks"], 4, (1, 1)),
    "charizard":  ("monster", (0, 7),  ["mesa", "mountains", "savanna"], 3, (1, 1)),
    "mewtwo":     ("monster", (0, 7),  ["roofed", "deep_dark", "stony_peaks"], 1, (1, 1)),
}


def build_spawn_rule(spec):
    pid = spec["id"]
    pop, (lo, hi), biomes, weight, (hmin, hmax) = SPAWN_PROFILES[pid]
    return {
        "format_version": "1.8.0",
        "minecraft:spawn_rules": {
            "description": {"identifier": f"poke:{pid}", "population_control": pop},
            "conditions": [{
                "minecraft:spawns_on_surface": {},
                "minecraft:brightness_filter": {"min": lo, "max": hi, "adjust_for_weather": False},
                "minecraft:weight": {"default": weight},
                "minecraft:herd": {"min_size": hmin, "max_size": hmax},
                "minecraft:biome_filter": {
                    "any_of": [{"test": "has_biome_tag", "operator": "==", "value": b} for b in biomes]
                },
                "minecraft:density_limit": {"surface": 3},
            }],
        },
    }


# ---------------------------------------------------------------- 物品（精靈球 / 圖鑑）

ITEMS = {
    "pokeball": dict(zh="精靈球", en="Poké Ball", stack=16,
                     desc="對著寶可夢使用可以捕捉。血越少成功率越高。"),
    "greatball": dict(zh="高級球", en="Great Ball", stack=16,
                      desc="比精靈球更好的球，成功率 +15%。"),
    "ultraball": dict(zh="超級球", en="Ultra Ball", stack=16,
                      desc="性能優異的球，成功率 +30%。"),
    "masterball": dict(zh="大師球", en="Master Ball", stack=4,
                       desc="性能最好的球，一定抓得住。"),
    "potion": dict(zh="傷藥", en="Potion", stack=16,
                   desc="對著自己的寶可夢使用，回復 60 點生命。"),
    "rarecandy": dict(zh="神奇糖果", en="Rare Candy", stack=8,
                      desc="給夥伴吃：全回復，並暫時強化攻防。"),
    "berry": dict(zh="樹果", en="Berry", stack=16,
                  desc="自己吃可以回復 6 點生命。"),
    "pokedex": dict(zh="寶可夢圖鑑", en="Pokédex", stack=1,
                    desc="顯示已捕獲的寶可夢與次數。"),
}


def build_item(item_id, meta):
    return {
        "format_version": "1.21.0",
        "minecraft:item": {
            "description": {
                "identifier": f"poke:{item_id}",
                "menu_category": {"category": "equipment"},
            },
            "components": {
                "minecraft:icon": {"textures": {"default": f"poke_{item_id}"}},
                "minecraft:max_stack_size": meta["stack"],
                "minecraft:display_name": {"value": meta["zh"]},
            },
        },
    }


def draw_item_textures(dirpath):
    """16x16 的物品圖示：精靈球 + 圖鑑"""
    os.makedirs(dirpath, exist_ok=True)

    # 精靈球：上半紅、下半白、中間黑帶、中央按鈕
    ball = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(ball)
    d.ellipse([1, 1, 14, 14], fill=(232, 232, 232, 255), outline=(24, 24, 24, 255))
    d.ellipse([1, 1, 14, 8], fill=(214, 40, 40, 255), outline=(24, 24, 24, 255))
    d.rectangle([1, 7, 14, 8], fill=(24, 24, 24, 255))
    d.ellipse([6, 6, 9, 9], fill=(245, 245, 245, 255), outline=(24, 24, 24, 255))
    d.point([7, 7], fill=(120, 120, 120, 255))
    d.point([4, 3], fill=(255, 150, 150, 255))   # 高光
    ball.save(os.path.join(dirpath, "pokeball.png"))

    # 圖鑑：紅色機身 + 藍色鏡頭 + 指示燈
    dex = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(dex)
    d.rectangle([2, 1, 13, 14], fill=(200, 40, 40, 255), outline=(24, 24, 24, 255))
    d.rectangle([2, 1, 13, 4], fill=(160, 28, 28, 255), outline=(24, 24, 24, 255))
    d.ellipse([4, 5, 9, 10], fill=(90, 180, 240, 255), outline=(24, 24, 24, 255))
    d.point([6, 7], fill=(230, 245, 255, 255))
    d.rectangle([10, 6, 11, 6], fill=(80, 220, 120, 255))
    d.rectangle([10, 8, 11, 8], fill=(250, 210, 80, 255))
    d.rectangle([4, 11, 11, 12], fill=(40, 40, 40, 255))
    dex.save(os.path.join(dirpath, "pokedex.png"))

    # 各種球：換上蓋顏色 + 條紋
    def ball_icon(fname, top, accent, button=(245, 245, 245)):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        dr.ellipse([1, 1, 14, 14], fill=(232, 232, 232, 255), outline=(24, 24, 24, 255))
        dr.ellipse([1, 1, 14, 8], fill=top + (255,), outline=(24, 24, 24, 255))
        dr.rectangle([1, 7, 14, 8], fill=(24, 24, 24, 255))
        if accent:
            dr.rectangle([3, 2, 4, 6], fill=accent + (255,))
            dr.rectangle([11, 2, 12, 6], fill=accent + (255,))
        dr.ellipse([6, 6, 9, 9], fill=button + (255,), outline=(24, 24, 24, 255))
        dr.point([7, 7], fill=(120, 120, 120, 255))
        dr.point([4, 3], fill=(255, 255, 255, 200))
        img.save(os.path.join(dirpath, fname))

    ball_icon("greatball.png", (60, 120, 220), (220, 60, 60))
    ball_icon("ultraball.png", (40, 40, 48), (250, 200, 60))
    ball_icon("masterball.png", (140, 70, 190), (240, 140, 200))

    # 傷藥：噴霧瓶，粉紅藥水
    pot = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(pot)
    d.rectangle([6, 1, 9, 3], fill=(200, 200, 205, 255), outline=(24, 24, 24, 255))
    d.rectangle([3, 4, 12, 14], fill=(235, 245, 250, 255), outline=(24, 24, 24, 255))
    d.rectangle([4, 8, 11, 13], fill=(235, 80, 120, 255))
    d.rectangle([4, 5, 11, 7], fill=(250, 250, 252, 255))
    d.rectangle([6, 9, 9, 10], fill=(255, 255, 255, 230))
    pot.save(os.path.join(dirpath, "potion.png"))

    # 神奇糖果：彩色糖塊 + 高光
    candy = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(candy)
    d.rectangle([2, 4, 13, 12], fill=(240, 180, 220, 255), outline=(160, 60, 120, 255))
    d.rectangle([2, 4, 13, 6], fill=(250, 220, 240, 255))
    d.rectangle([4, 7, 5, 8], fill=(255, 255, 255, 230))
    d.point([10, 9], fill=(255, 255, 255, 200))
    d.rectangle([6, 2, 9, 3], fill=(120, 200, 120, 255))
    candy.save(os.path.join(dirpath, "rarecandy.png"))

    # 樹果：紅色果實 + 綠葉
    berry = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(berry)
    d.ellipse([2, 5, 13, 14], fill=(220, 50, 60, 255), outline=(90, 20, 25, 255))
    d.ellipse([4, 7, 6, 9], fill=(255, 160, 170, 200))
    d.rectangle([7, 1, 8, 5], fill=(80, 150, 60, 255))
    d.ellipse([8, 1, 12, 4], fill=(110, 190, 80, 255))
    berry.save(os.path.join(dirpath, "berry.png"))


ITEM_TEXTURE_JSON = {
    "resource_pack_name": "pokemon",
    "texture_name": "atlas.items",
    "texture_data": {
        "poke_pokeball": {"textures": "textures/items/pokeball"},
        "poke_greatball": {"textures": "textures/items/greatball"},
        "poke_ultraball": {"textures": "textures/items/ultraball"},
        "poke_masterball": {"textures": "textures/items/masterball"},
        "poke_potion": {"textures": "textures/items/potion"},
        "poke_rarecandy": {"textures": "textures/items/rarecandy"},
        "poke_berry": {"textures": "textures/items/berry"},
        "poke_pokedex": {"textures": "textures/items/pokedex"},
    },
}


# ---------------------------------------------------------------- 主流程





# ---------------------------------------------------------------- 第二批物種
# 資料放在 poke_species.py，模型貼圖仍由 import_cobblemon_models.py 匯入
try:
    from poke_species import NEW_SPECS, NEW_SPAWN_PROFILES
except ImportError:                     # 單獨執行時也不炸
    NEW_SPECS, NEW_SPAWN_PROFILES = [], {}

# ---------------------------------------------------------------- 第三批：傳說
try:
    from poke_legendaries import LEGENDARY_SPECS, LEGENDARY_SPAWN_PROFILES
    from poke_extra_legendaries import EXTRA_SPECS, EXTRA_SPAWN_PROFILES
    LEGENDARY_SPECS = LEGENDARY_SPECS + EXTRA_SPECS
    LEGENDARY_SPAWN_PROFILES = {**LEGENDARY_SPAWN_PROFILES, **EXTRA_SPAWN_PROFILES}

    NEW_SPECS = NEW_SPECS + LEGENDARY_SPECS
    NEW_SPAWN_PROFILES = {**NEW_SPAWN_PROFILES, **LEGENDARY_SPAWN_PROFILES}
except ImportError:
    pass

SPECS = SPECS + NEW_SPECS
SPAWN_PROFILES = {**SPAWN_PROFILES, **NEW_SPAWN_PROFILES}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="packs/pokemon")
    ap.add_argument("--only", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    specs = [s for s in SPECS if not args.only or s["id"] == args.only]
    out = args.out
    bp_ent = os.path.join(out, "bp", "entities")
    bp_rules = os.path.join(out, "bp", "spawn_rules")
    bp_scripts = os.path.join(out, "bp", "scripts")
    bp_items = os.path.join(out, "bp", "items")
    rp_items_tex = os.path.join(out, "rp", "textures", "items")
    rp_ent = os.path.join(out, "rp", "entity")
    rp_geo = os.path.join(out, "rp", "models", "entity")
    rp_tex = os.path.join(out, "rp", "textures", "entity", "pokemon")
    rp_anim = os.path.join(out, "rp", "animations")
    for d in (bp_ent, bp_rules, bp_scripts, bp_items, rp_ent, rp_geo, rp_tex, rp_anim):
        os.makedirs(d, exist_ok=True)

    lang_bp = []
    lang_rp = []

    for spec in specs:
        atlas = Atlas(size=192)
        geo = build_geometry(spec, atlas)
        atlas.img.save(os.path.join(rp_tex, f"{spec['id']}.png"))

        with open(os.path.join(rp_geo, f"{spec['id']}.geo.json"), "w", encoding="utf-8") as f:
            json.dump(geo, f, indent=2, ensure_ascii=False)
        with open(os.path.join(rp_ent, f"{spec['id']}.entity.json"), "w", encoding="utf-8") as f:
            json.dump(build_client_entity(spec), f, indent=2, ensure_ascii=False)
        with open(os.path.join(bp_ent, f"{spec['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(build_entity(spec), f, indent=2, ensure_ascii=False)
        with open(os.path.join(bp_rules, f"{spec['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(build_spawn_rule(spec), f, indent=2, ensure_ascii=False)

        lang_bp.append(f"entity.poke:{spec['id']}.name={spec['zh']}")
        lang_bp.append(f"item.spawn_egg.entity.poke:{spec['id']}.name={spec['zh']} 生怪蛋")
        lang_rp.append(f"entity.poke:{spec['id']}.name={spec['zh']}")
        # 生怪蛋的名稱一定要寫進「資材包」的 lang，客戶端才翻得出來（只有 bp 會顯示 item.spawn_egg.entity.poke:xxx.name 這種原始 key）
        lang_rp.append(f"item.spawn_egg.entity.poke:{spec['id']}.name={spec['zh']} 生怪蛋")
        print(f"  {spec['zh']:<8} poke:{spec['id']:<12} hp={spec['hp']:<4} hostile={spec['hostile']}")

    with open(os.path.join(rp_anim, "poke.animations.json"), "w", encoding="utf-8") as f:
        json.dump(ANIMATIONS, f, indent=2, ensure_ascii=False)

    # 物品
    for item_id, meta in ITEMS.items():
        with open(os.path.join(bp_items, f"{item_id}.json"), "w", encoding="utf-8") as f:
            json.dump(build_item(item_id, meta), f, indent=2, ensure_ascii=False)
        lang_bp.append(f"item.poke:{item_id}={meta['zh']}")
        lang_rp.append(f"item.poke:{item_id}={meta['zh']}")
    draw_item_textures(rp_items_tex)
    with open(os.path.join(out, "rp", "textures", "item_texture.json"), "w", encoding="utf-8") as f:
        json.dump(ITEM_TEXTURE_JSON, f, indent=2, ensure_ascii=False)

    # 招式腳本（Script API）：優先用 tools/poke_main.js，沒有就用內嵌版
    js_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poke_main.js")
    if os.path.exists(js_src):
        with open(js_src, encoding="utf-8") as f:
            js = f.read()
        print("  腳本來源: tools/poke_main.js")
    else:
        js = ABILITY_JS
    with open(os.path.join(bp_scripts, "main.js"), "w", encoding="utf-8") as f:
        f.write(js)

    # manifest（UUID 固定，重跑不會變）
    def uid(seed):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"hermes-pokemon-{seed}"))

    bp_manifest = {
        "format_version": 2,
        "header": {
            "name": "Pokémon 怪物包 (行為)",
            "description": "12 隻寶可夢怪物：AI、數值、生怪蛋",
            "uuid": uid("bp"),
            "version": [2, 0, 0],
            "min_engine_version": [1, 21, 0],
        },
        "modules": [
            {"type": "data", "uuid": uid("bp-module"), "version": [2, 0, 0]},
            {"type": "script", "language": "javascript", "uuid": uid("bp-script"), "version": [1, 0, 0], "entry": "scripts/main.js"},
        ],
        "dependencies": [
            {"uuid": uid("rp"), "version": [2, 0, 0]},
            {"module_name": "@minecraft/server", "version": "2.10.0"},
            {"module_name": "@minecraft/server-ui", "version": "2.0.0"},
        ],
    }
    rp_manifest = {
        "format_version": 2,
        "header": {
            "name": "Pokémon 怪物包 (資源)",
            "description": "模型、貼圖、動畫",
            "uuid": uid("rp"),
            "version": [2, 0, 0],
            "min_engine_version": [1, 21, 0],
        },
        "modules": [{"type": "resources", "uuid": uid("rp-module"), "version": [2, 0, 0]}],
    }
    for path, man in ((os.path.join(out, "bp", "manifest.json"), bp_manifest),
                      (os.path.join(out, "rp", "manifest.json"), rp_manifest)):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=2, ensure_ascii=False)

    for sub, lines in (("bp", lang_bp), ("rp", lang_rp)):
        texts = os.path.join(out, sub, "texts")
        os.makedirs(texts, exist_ok=True)
        with open(os.path.join(texts, "zh_CN.lang"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        with open(os.path.join(texts, "en_US.lang"), "w", encoding="utf-8") as f:
            f.write("\n".join(
                l.replace(s["zh"], s["en"]) for l, s in zip([x for x in lines if x.startswith("entity.")], specs)
            ) + "\n")

    print(f"\n完成：{len(specs)} 隻 → {out}")
    print("BP uuid:", bp_manifest["header"]["uuid"])
    print("RP uuid:", rp_manifest["header"]["uuid"])


if __name__ == "__main__":
    main()
